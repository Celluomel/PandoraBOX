"""Independent Body process: robot sensors, world model, and Brain bridge.

The Body is the primary owner of Lumina's embodied world model.  This process:

    * polls the ROBOT (the main sensorimetry channel) — GET {ROBOT_URL}/sensors
    * keeps Home Assistant as an auxiliary presence feed only
    * runs the embodied world model loop (``body_runtime_host.worldmodel``)
      close to the sensors/actuators, learning in continuous operation
    * bridges observations to the Brain (websocket) when enabled
    * exposes HTTP endpoints for status, world model state, and control

Dependencies: standard library + optional ``websockets``.  The world model
needs numpy/torch; those imports are lazy, so the host still starts and serves
robot telemetry without them (the world model simply reports unavailable).
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import importlib.util
import ipaddress
import json
import logging
import math
import os
import signal
import ssl
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Empty, Queue
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from body_runtime_host.coordinate_frames import (
    compass_heading_degrees,
    north_up_svg_rotation_degrees,
)
from body_runtime_host.deployment import build_bundle
from body_runtime_host.local_camera import LocalCameraCapture
from body_runtime_host.repository_update import RepositoryUpdater

LOG = logging.getLogger("lumina.body")
ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "body" / "config.json"

# Hardware modules are discovered from the robot/gateway capability contract.
# This catalog only defines the vocabulary and UI metadata; it does not claim
# that optional hardware is present.
FNK0031_MODULE_CATALOG = {
    "camera": {"label": "Camera", "kind": "vision", "source": "robot"},
    "lidar": {"label": "LiDAR", "kind": "range", "source": "robot"},
    "gps": {"label": "GPS", "kind": "localization", "source": "robot"},
    "imu": {"label": "IMU", "kind": "inertial", "source": "robot"},
    "odometry": {"label": "Wheel/servo odometry", "kind": "localization", "source": "robot"},
    "actuators": {"label": "FNK0031 servo actuators", "kind": "actuation", "source": "robot"},
    "gripper": {"label": "Gripper", "kind": "manipulation", "source": "robot"},
    "mmwave_radar": {"label": "mmWave radar", "kind": "range", "source": "robot"},
}


def _locomotion_gait_for_action(action: str) -> str:
    """Translate World Model actions into physical locomotion primitives."""
    # World-model telemetry intentionally exposes a readable action label such
    # as ``forward→table``.  The locomotion controller needs the primitive
    # verb only; otherwise every targeted movement silently became ``idle``.
    normalized = str(action or "").strip().lower()
    for separator in ("→", "->"):
        if separator in normalized:
            normalized = normalized.split(separator, 1)[0].strip()
            break
    return {
        "forward": "forward",
        "sprint": "forward",
        "backward": "backward",
        "retreat": "backward",
        "turn_left": "turn_left",
        "turn_right": "turn_right",
    }.get(normalized, "idle")


def _load_dotenv() -> None:
    for path in (ROOT / "body_venv" / ".env", ROOT / ".body_venv" / ".env", ROOT / ".venv" / ".env", ROOT / ".env"):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _http_get(url: str, token: str = "", timeout: float = 5.0):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    parsed = urlparse(url)
    context = None
    if parsed.scheme == "https":
        context = ssl.create_default_context()
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout, context=context) as response:
        payload = response.read().decode("utf-8")
        return json.loads(payload) if payload else None


def _http_post(url: str, payload: dict, token: str = "", timeout: float = 5.0):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers=headers, method="POST")
    with urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else None


def _payload_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


class BodyHost:
    def __init__(self) -> None:
        self.stop_event = threading.Event()
        self.config = self._load_config()
        self.latest: dict[str, dict] = {}
        self.queue: Queue[dict] = Queue(maxsize=256)
        self._bridge_lock = threading.Lock()
        self._bridge_connected = threading.Event()
        self._bridge_latest: dict[str, dict] = {}
        self.bridge_thread: threading.Thread | None = None
        self.http_server: ThreadingHTTPServer | None = None
        self._worldmodel = None
        self._worldmodel_lock = threading.Lock()
        self._robot_last_ok: float | None = None
        self._robot_last_error = ""
        self._fnk_usb_last_publish = 0.0
        self._fnk_controller = None
        self._fnk_controller_lock = threading.Lock()
        self._fnk_controller_last: dict | None = None
        self._fnk_controller_world_step: int | None = None
        self._fnk_controller_gait = "idle"
        self._fnk_controller_last_tick: float | None = None
        self._fnk_experiment_lock = threading.Lock()
        self._fnk_experiment_thread: threading.Thread | None = None
        self._fnk_experiment_status: dict = {"state": "idle", "completed": 0, "total": 0}
        self._worldmodel_evaluation_lock = threading.Lock()
        self._worldmodel_evaluation_thread: threading.Thread | None = None
        self._worldmodel_evaluation_report_path = ROOT / "data" / "body" / "worldmodel" / "evaluations.jsonl"
        self._worldmodel_capability_path = ROOT / "data" / "body" / "worldmodel" / "capability_gate.json"
        self._fnk_diagnostic_path = ROOT / "data" / "body" / "hardware" / "fnk0031_diagnostic.json"
        self._worldmodel_evaluation_status: dict = self._load_latest_worldmodel_evaluation()
        self._robot_sim = None
        self._robot_sim_lock = threading.RLock()
        self._local_camera: LocalCameraCapture | None = None
        self._local_camera_lock = threading.RLock()
        self._body_vlm_test_lock = threading.Lock()
        self._body_vlm_test_status: dict = {"status": "idle", "job_id": None}
        self._body_vlm_test_thread: threading.Thread | None = None
        self._sensorimotor_test_lock = threading.Lock()
        self._sensorimotor_test_status: dict = {"status": "idle", "job_id": None}
        self._sensorimotor_test_thread: threading.Thread | None = None
        self._ros2_bridge = None
        self._workflow_manager = None
        self._repository_updater = RepositoryUpdater(ROOT)

    @property
    def workflow_manager(self):
        if self._workflow_manager is None:
            from body_runtime_host.workflow_manager import WorkflowManager
            self._workflow_manager = WorkflowManager(self, ROOT / "data" / "body" / "workflows.json")
        return self._workflow_manager

    # ── config ──────────────────────────────────────────────────────────────

    def _load_latest_worldmodel_evaluation(self) -> dict:
        try:
            lines = self._worldmodel_evaluation_report_path.read_text(encoding="utf-8").splitlines()
            if lines:
                latest = json.loads(lines[-1])
                if isinstance(latest, dict):
                    return {"state": "completed", **latest}
        except Exception:
            pass
        return {"state": "idle", "trials": 0}

    def worldmodel_capability_gate(self) -> dict:
        """Return the latest evidence gate independently of live evaluation."""
        try:
            payload = json.loads(self._worldmodel_capability_path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {"state": "unknown"}
        except Exception:
            latest = self.worldmodel_evaluation_status()
            gate = latest.get("capability_gate")
            return gate if isinstance(gate, dict) else {"state": "unknown", "pending_gates": ["evaluation"]}

    def _load_config(self) -> dict:
        if not CONFIG_PATH.exists():
            try:
                CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
                CONFIG_PATH.write_text("{}\n", encoding="utf-8")
                LOG.info("Created default Body configuration at %s", CONFIG_PATH)
                return {}
            except OSError as exc:
                LOG.warning("Could not create default Body configuration at %s: %s", CONFIG_PATH, exc)
        try:
            payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except Exception as exc:
            LOG.warning("Could not load %s: %s", CONFIG_PATH, exc)
            return {}

    def value(self, key: str, fallback=None):
        value = self.config.get(key, fallback)
        if isinstance(value, str) and value.startswith("@env:"):
            return os.environ.get(value[5:], "")
        return value

    def save_discovery(self, entities: list[dict]) -> None:
        serialized = json.dumps(entities, ensure_ascii=False)
        if self.config.get("HOME_ASSISTANT_DISCOVERED_ENTITIES") == serialized:
            return
        self.config["HOME_ASSISTANT_DISCOVERED_ENTITIES"] = serialized
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        safe = dict(self.config)
        safe["HOME_ASSISTANT_TOKEN"] = "@env:HOME_ASSISTANT_TOKEN"
        safe["BODY_BRIDGE_TOKEN"] = "@env:BODY_BRIDGE_TOKEN"
        CONFIG_PATH.write_text(json.dumps(safe, indent=2, ensure_ascii=False), encoding="utf-8")

    def save_config(self) -> None:
        """Persist Body settings while keeping secret values environment-backed."""
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        safe = dict(self.config)
        for key in ("HOME_ASSISTANT_TOKEN", "BODY_BRIDGE_TOKEN", "ROBOT_TOKEN", "FNK0031_TOKEN", "FNK0050_TOKEN", "BODY_LLM_TOKEN"):
            if safe.get(key) and not str(safe[key]).startswith("@env:"):
                safe[key] = f"@env:{key}"
        CONFIG_PATH.write_text(json.dumps(safe, indent=2, ensure_ascii=False), encoding="utf-8")

    def brain_bridge_settings(self) -> dict:
        return {
            "enabled": bool(self.value("BODY_BRIDGE_ENABLED", False)),
            "url": str(self.value("BODY_BRIDGE_URL", "") or ""),
            "token_configured": bool(self.value("BODY_BRIDGE_TOKEN", "")),
            "device_id": str(self.value("BODY_BRIDGE_DEVICE_ID", "body-ventuno") or "body-ventuno"),
            "verify_tls": bool(self.value("BODY_BRIDGE_VERIFY_TLS", True)),
            "connected": self._bridge_connected.is_set(),
        }

    def update_brain_bridge_settings(self, payload: dict) -> dict:
        url = str(payload.get("url", "") or "").strip()
        token = str(payload.get("token", "") or "").strip()
        enabled = bool(payload.get("enabled", False))
        if len(token) > 512 or any(ord(char) < 32 for char in token):
            raise ValueError("Bridge token must be at most 512 characters and contain no control characters")
        if url:
            parsed = urlparse(url)
            if parsed.scheme not in {"ws", "wss"} or not parsed.netloc or parsed.username or parsed.password:
                raise ValueError("Use a ws:// or wss:// Brain bridge URL without embedded credentials")
            if parsed.scheme == "ws" and (parsed.hostname or "").lower() not in {"localhost", "127.0.0.1", "::1"}:
                raise ValueError("Remote Brain bridge connections require wss:// so the bearer token is encrypted in transit")
        if enabled and (not url or not (token or self.value("BODY_BRIDGE_TOKEN", ""))):
            raise ValueError("A Brain bridge URL and bearer token are required before enabling")
        self.config.update({
            "BODY_BRIDGE_ENABLED": enabled,
            "BODY_BRIDGE_URL": url,
            "BODY_BRIDGE_DEVICE_ID": str(payload.get("device_id", "body-ventuno") or "body-ventuno").strip()[:80],
            "BODY_BRIDGE_VERIFY_TLS": bool(payload.get("verify_tls", True)),
        })
        if token:
            os.environ["BODY_BRIDGE_TOKEN"] = token
            self.config["BODY_BRIDGE_TOKEN"] = "@env:BODY_BRIDGE_TOKEN"
            secret_path = ROOT / "body_venv" / ".env"
            secret_path.parent.mkdir(parents=True, exist_ok=True)
            existing = {}
            if secret_path.exists():
                for line in secret_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if "=" in line and not line.lstrip().startswith("#"):
                        key, value = line.split("=", 1)
                        existing[key.strip()] = value.strip()
            existing["BODY_BRIDGE_TOKEN"] = token
            secret_path.write_text("".join(f"{key}={value}\n" for key, value in existing.items()), encoding="utf-8")
        self.save_config()
        return self.brain_bridge_settings()

    def ros2_settings(self) -> dict:
        enabled = bool(self.value("BODY_ROS2_ENABLED", False))
        bridge = self._ros2_bridge
        status = bridge.status() if bridge is not None else self._ros2_probe_status()
        return {
            "enabled": enabled,
            "publish_topic": str(self.value("BODY_ROS2_PUBLISH_TOPIC", "/body/observations")),
            "input_topic": str(self.value("BODY_ROS2_INPUT_TOPIC", "/body/observations_in")),
            "status": status,
            "contract": "pandorabox.body_observation.v1",
            "actuation_enabled": False,
        }

    @staticmethod
    def _ros2_probe_status() -> dict:
        import importlib.util
        available = importlib.util.find_spec("rclpy") is not None
        return {
            "state": "ready-to-enable" if available else "not-installed",
            "available": available,
            "ros_distro": os.environ.get("ROS_DISTRO", ""),
            "domain_id": os.environ.get("ROS_DOMAIN_ID", "0"),
            "last_error": "" if available else "rclpy is not available in this ROS-sourced environment",
            "physical_actuation": "not exposed by this bridge",
            "components": {
                "body_navigation": {"state": "available", "backend": "Body LocalRoutePlanner + safety gate"},
                "task_graph": {"state": "available", "backend": "Body task sequencing and action preconditions"},
                "arm_adapter": {"state": "not-configured", "backend": "requires a robot-specific driver and feedback contract"},
                "ros2_interop": {"state": "available" if available else "unavailable", "backend": "observation bridge only; no motor commands"},
            },
        }

    def _accept_ros2_observation(self, observation: dict) -> None:
        subject = str(observation.get("subject") or "")[:160]
        if not subject:
            return
        now = time.time()
        try:
            confidence = max(0.0, min(1.0, float(observation.get("confidence", 1.0) or 0.0)))
            observed_at = float(observation.get("observed_at") or now)
        except (TypeError, ValueError):
            confidence, observed_at = 0.0, now
        entry = {
            "entity_id": f"ros2.{subject}",
            "source": str(observation.get("source") or "ros2")[:80],
            "kind": str(observation.get("kind") or "sensor")[:80],
            "subject": subject,
            "value": observation.get("value"),
            "unit": str(observation.get("unit") or "")[:40],
            "confidence": confidence,
            "observed_at": observed_at,
            "provenance": observation.get("provenance") if isinstance(observation.get("provenance"), dict) else {"transport": "ros2"},
        }
        self.latest[entry["entity_id"]] = entry
        self._bridge_put(entry)

    def update_ros2_settings(self, payload: dict) -> dict:
        publish_topic = str(payload.get("publish_topic") or "/body/observations").strip()
        input_topic = str(payload.get("input_topic") or "/body/observations_in").strip()
        for topic in (publish_topic, input_topic):
            if not topic.startswith("/") or any(part in {"", ".", ".."} for part in topic.split("/")[1:]):
                raise ValueError("ROS 2 topics must be absolute names, e.g. /body/observations")
        if publish_topic == input_topic:
            raise ValueError("ROS 2 input and output topics must differ to prevent observation loops")
        self.config.update({
            "BODY_ROS2_ENABLED": _payload_bool(payload.get("enabled")),
            "BODY_ROS2_PUBLISH_TOPIC": publish_topic,
            "BODY_ROS2_INPUT_TOPIC": input_topic,
        })
        self.save_config()
        persisted = self._load_config()
        if bool(persisted.get("BODY_ROS2_ENABLED", False)) != bool(self.config["BODY_ROS2_ENABLED"]):
            raise OSError("ROS 2 settings were not persisted")
        self._stop_ros2_bridge()
        if self.config["BODY_ROS2_ENABLED"]:
            self._start_ros2_bridge()
        return {"ok": True, "persisted": True, **self.ros2_settings()}

    def _start_ros2_bridge(self) -> dict:
        from .ros2_bridge import Ros2ObservationBridge
        if self._ros2_bridge is None:
            self._ros2_bridge = Ros2ObservationBridge(
                self._accept_ros2_observation,
                publish_topic=str(self.value("BODY_ROS2_PUBLISH_TOPIC", "/body/observations")),
                input_topic=str(self.value("BODY_ROS2_INPUT_TOPIC", "/body/observations_in")),
            )
        return self._ros2_bridge.start()

    def _stop_ros2_bridge(self) -> None:
        if self._ros2_bridge is not None:
            self._ros2_bridge.stop()

    def camera_settings(self) -> dict:
        startup_enabled = bool(self.value("BODY_CAMERA_STARTUP_ENABLED", False))
        with self._local_camera_lock:
            capture_status = self._local_camera.status() if self._local_camera is not None else {
                "status": "disabled" if not startup_enabled else "not_started",
                "available": False,
                "last_error": "",
            }
        return {
            "interval": max(1.0 / 60.0, float(self.value("BODY_CAMERA_INTERVAL", 0.5) or 0.5)),
            "width": max(640, int(self.value("BODY_CAMERA_WIDTH", 640) or 640)),
            "height": max(480, int(self.value("BODY_CAMERA_HEIGHT", 480) or 480)),
            "profile": str(self.value("BODY_CAMERA_PROFILE", "low_body_front") or "low_body_front"),
            "startup_enabled": startup_enabled,
            "device_index": max(0, int(self.value("BODY_CAMERA_DEVICE_INDEX", 0) or 0)),
            "fps": round(1.0 / max(1.0 / 60.0, float(self.value("BODY_CAMERA_INTERVAL", 0.5) or 0.5)), 2),
            "brain_settings": {
                "autostart": startup_enabled,
                "camera_id": max(0, int(self.value("BODY_CAMERA_DEVICE_INDEX", 0) or 0)),
                "fps": round(1.0 / max(1.0 / 60.0, float(self.value("BODY_CAMERA_INTERVAL", 0.5) or 0.5)), 2),
                "resolution": f"{max(640, int(self.value('BODY_CAMERA_WIDTH', 640) or 640))}x{max(480, int(self.value('BODY_CAMERA_HEIGHT', 480) or 480))}",
                "vlm_model": str(self.value("BODY_LLM_MODEL", "") or ""),
            },
            "vision_mode": str(self.value("BODY_VISION_MODE", "keyword") or "keyword"),
            "vision_llm_mode": str(self.value("BODY_VISION_LLM_MODE", "separate") or "separate"),
            "vlm_model": str(self.value("BODY_LLM_MODEL", "") or ""),
            "face_detection_enabled": bool(self.value("BODY_FACE_DETECTION_ENABLED", False)),
            "face_detection_status": "configured" if bool(self.value("BODY_FACE_DETECTION_ENABLED", False)) else "disabled",
            "capture": capture_status,
        }

    def _camera_provider(self) -> dict:
        with self._local_camera_lock:
            camera = self._local_camera
            return camera.latest() if camera is not None else {}

    def camera_frame(self) -> dict:
        frame = self._camera_provider() or {}
        if frame:
            return {"available": True, "camera": frame}
        settings = self.camera_settings()
        return {
            "available": False,
            "camera": {},
            "status": settings.get("capture", {}).get("status", "disabled"),
            "error": settings.get("capture", {}).get("last_error", ""),
        }

    def _configure_local_camera(self, start: bool | None = None) -> dict:
        settings = self.camera_settings()
        should_start = settings["startup_enabled"] if start is None else bool(start)
        with self._local_camera_lock:
            if self._local_camera is None:
                self._local_camera = LocalCameraCapture(
                    device_index=settings["device_index"], interval=settings["interval"],
                    width=settings["width"], height=settings["height"], profile=settings["profile"],
                )
            else:
                self._local_camera.reconfigure(
                    device_index=settings["device_index"], interval=settings["interval"],
                    width=settings["width"], height=settings["height"], profile=settings["profile"],
                )
            result = self._local_camera.start() if should_start else self._local_camera.stop()
        return result

    def set_camera_capture(self, enabled: bool) -> dict:
        """Start or stop the live camera without changing its boot preference."""
        capture = self._configure_local_camera(start=bool(enabled))
        return {"ok": capture.get("status") in {"starting", "capturing", "stopped"}, **capture}

    def update_camera_settings(self, payload: dict) -> dict:
        # Preserve a manually running stream while applying live capture
        # changes. Startup preference must not unexpectedly stop it.
        with self._local_camera_lock:
            was_capturing = bool(
                self._local_camera is not None
                and self._local_camera.status().get("status") in {"capturing", "starting"}
            )
        self.config["BODY_CAMERA_INTERVAL"] = max(1.0 / 60.0, min(30.0, float(payload.get("interval", 0.5) or 0.5)))
        if payload.get("fps") is not None:
            self.config["BODY_CAMERA_INTERVAL"] = 1.0 / max(1.0, min(60.0, float(payload.get("fps") or 5)))
        self.config["BODY_CAMERA_WIDTH"] = max(640, min(3840, int(payload.get("width", 640) or 640)))
        self.config["BODY_CAMERA_HEIGHT"] = max(480, min(2160, int(payload.get("height", 480) or 480)))
        profile = str(payload.get("profile", "low_body_front") or "low_body_front").strip().lower()
        if profile not in {"low_body_front", "level_body_front", "high_body_front"}:
            raise ValueError("unsupported camera profile")
        self.config["BODY_CAMERA_PROFILE"] = profile
        if payload.get("vision_mode") is not None:
            self.config["BODY_VISION_MODE"] = str(payload.get("vision_mode") or "keyword")
        if payload.get("vision_llm_mode") is not None:
            self.config["BODY_VISION_LLM_MODE"] = str(payload.get("vision_llm_mode") or "separate")
        if payload.get("vlm_model") is not None:
            self.config["BODY_LLM_MODEL"] = str(payload.get("vlm_model") or "").strip()
        self.config["BODY_CAMERA_STARTUP_ENABLED"] = _payload_bool(
            payload.get("startup_enabled"),
            _payload_bool(self.value("BODY_CAMERA_STARTUP_ENABLED", False)),
        )
        self.config["BODY_CAMERA_DEVICE_INDEX"] = max(0, int(payload.get("device_index", self.value("BODY_CAMERA_DEVICE_INDEX", 0)) or 0))
        self.config["BODY_FACE_DETECTION_ENABLED"] = _payload_bool(payload.get("face_detection_enabled"))
        self.save_config()
        self._configure_local_camera(start=was_capturing)
        if self._worldmodel is not None:
            self.reload_worldmodel_source()
        return {"ok": True, **self.camera_settings()}

    def test_body_vlm(self) -> dict:
        """Run one synchronous Body VLM interpretation on the latest scene."""
        wm = self.worldmodel
        if wm is None or wm.source is None:
            return {
                "ok": False,
                "stage": "source_check",
                "error": "world model or sensor source unavailable",
            }
        stage = "observe"
        try:
            obs = wm.source.observe()
            stage = "body_state"
            body = wm.source.body_state()
            stage = "scene_packet"
            packet = wm._scene_packet(obs, body, {}, {})
            stage = "interpret"
            result = wm.scene_interpreter.interpret_now(packet)
            interpreted = result.get("status") == "interpreted"
            grounding = (result.get("semantic_scene") or {}).get("grounding") or {}
            diagnosis = result.get("diagnosis")
            if isinstance(diagnosis, dict) and diagnosis.get("code") == "qnn_model_load_failed":
                diagnosis = self._qnn_memory_snapshot(diagnosis)
                LOG.error("[BodyVLM-QNN] model initialization failed: %s", diagnosis)
            return {
                "ok": interpreted,
                "stage": "complete" if interpreted else "interpret",
                "model": result.get("model") or self.body_llm_settings().get("model"),
                "status": result.get("status"),
                "error": result.get("error"),
                "diagnosis": diagnosis,
                "visual_input": result.get("visual_input"),
                "grounding": grounding,
                "interpretation": result.get("interpretation"),
                "semantic_scene": result.get("semantic_scene"),
                "result": result,
            }
        except Exception as exc:
            LOG.exception("Body VLM test failed during %s", stage)
            return {"ok": False, "stage": stage, "error": str(exc)[:300]}

    def benchmark_body_vlm_profiles(self) -> dict:
        """Compare image scales on one captured frame without changing saved settings."""
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        wm = self.worldmodel
        if wm is None or wm.source is None:
            return {"ok": False, "stage": "source_check", "error": "world model or sensor source unavailable"}
        try:
            obs = wm.source.observe()
            body = wm.source.body_state()
            packet = wm._scene_packet(obs, body, {}, {})
            camera = (packet.get("modalities") or {}).get("camera") or {}
            if not (camera.get("image_base64") or camera.get("image_url")):
                return {"ok": False, "stage": "camera_check", "error": "No camera image available for the profile comparison"}
            # Do not let simulated objects or synthetic sensor readings leak into
            # an image-only benchmark or its downstream grounding step.
            packet = {
                "contract": "body_perception_frame.v2",
                "source": "camera_profile_benchmark",
                "timestamp": camera.get("captured_at") or packet.get("timestamp"),
                "frame_id": camera.get("frame_id") or packet.get("frame_id"),
                "modalities": {"camera": dict(camera)},
                "visual_blind": True,
                "camera_only": True,
            }
        except Exception as exc:
            return {"ok": False, "stage": "scene_capture", "error": str(exc)[:240]}

        target_s = max(1.0, min(60.0, float(self.value("BODY_LLM_TARGET_LATENCY_S", 5.0) or 5.0)))
        widths = [640, 480, 320]
        profiles = []
        baseline_labels: set[str] = set()
        for index, width in enumerate(widths, start=1):
            with self._body_vlm_test_lock:
                self._body_vlm_test_status["progress"] = {
                    "profile": f"{width}px", "index": index, "total": len(widths),
                }
            started = time.monotonic()
            try:
                result = wm.scene_interpreter.interpret_now(
                    packet,
                    visual_options={
                        "image_max_width": width,
                        "bypass_cache": True,
                        "include_sensor_context": False,
                        "camera_only": True,
                    },
                )
            except Exception as exc:
                result = {"status": "error", "error": str(exc)[:240]}
            latency_ms = round((time.monotonic() - started) * 1000.0, 1)
            interpretation = result.get("interpretation") or {}
            if not isinstance(interpretation, dict):
                interpretation = {}
            interpretation = BodySceneInterpreter._normalize_interpretation_schema(interpretation)
            descriptions = interpretation.get("object_descriptions") or []
            labels = {
                str(item.get("label") or item.get("id") or "").strip().lower()
                for item in descriptions if isinstance(item, dict) and (item.get("label") or item.get("id"))
            }
            if index == 1:
                baseline_labels = labels
            coverage = round(len(labels & baseline_labels) / len(baseline_labels), 3) if baseline_labels else 0.0
            summary = str(interpretation.get("scene_summary") or "").strip()
            if not summary and descriptions:
                summary = "Objects described: " + ", ".join(sorted(labels)[:5])
            valid = result.get("status") == "interpreted" and bool(descriptions)
            profiles.append({
                "image_max_width": width,
                "latency_ms": latency_ms,
                "status": result.get("status", "error"),
                "valid_scene_summary": bool(summary),
                "valid_visual_interpretation": valid,
                "described_objects": len(descriptions),
                "baseline_object_coverage": coverage,
                "label_consistency_vs_640": coverage if index > 1 else 1.0,
                "ground_truth_available": False,
                "grounding_evaluated": False,
                "quality_acceptable": valid and (index == 1 or (bool(baseline_labels) and coverage >= 0.8)),
                "summary": summary[:240],
                "object_labels": sorted(labels),
                "error": result.get("error"),
                "visual_input": result.get("visual_input"),
            })

        eligible = [item for item in profiles if item["quality_acceptable"]]
        target_candidates = [item for item in eligible if item["latency_ms"] <= target_s * 1000]
        recommendation = min(target_candidates or eligible, key=lambda item: item["latency_ms"], default=None)
        return {
            "ok": any(item["status"] == "interpreted" for item in profiles),
            "stage": "complete",
            "status": "benchmark_complete",
            "model": self.body_llm_settings().get("model"),
            "target_latency_s": target_s,
            "object_limit": self.body_llm_settings().get("visual_max_objects", 5),
            "token_limit": self.body_llm_settings().get("visual_max_tokens", 128),
            "saved_settings_changed": False,
            "camera_source": camera.get("source"),
            "camera_frame_id": camera.get("frame_id"),
            "camera_captured_at": camera.get("captured_at"),
            "ground_truth_available": False,
            "object_accuracy": None,
            "evaluation_note": (
                "Camera-only benchmark on one captured frame. No annotated ground truth is available; "
                "cross-resolution label consistency is not object accuracy."
            ),
            "recommendation": recommendation,
            "target_met": bool(target_candidates),
            "profiles": profiles,
        }

    @staticmethod
    def _qnn_memory_snapshot(diagnosis: dict) -> dict:
        """Attach Linux shared-memory figures to QNN load diagnostics when available."""
        enriched = dict(diagnosis)
        try:
            values = {}
            for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
                key, _, rest = line.partition(":")
                if key in {"MemAvailable", "CmaTotal", "CmaFree"}:
                    values[key] = int(rest.strip().split()[0])
            enriched["linux_memory_mib"] = {
                key: round(value / 1024, 1) for key, value in values.items()
            }
            if "CmaTotal" in values and "CmaFree" in values:
                enriched["shared_memory_pressure"] = round(
                    1.0 - values["CmaFree"] / max(1, values["CmaTotal"]), 3
                )
        except (OSError, ValueError, IndexError):
            pass
        return enriched

    def start_body_vlm_test(self, mode: str = "single") -> dict:
        """Start a VLM diagnostic without holding the HTTP request open."""
        with self._body_vlm_test_lock:
            if self._body_vlm_test_status.get("status") == "running":
                return {"ok": True, **self._body_vlm_test_status, "reused": True}
            job_id = f"vlm-{time.time_ns()}"
            self._body_vlm_test_status = {
                "ok": True, "status": "running", "job_id": job_id,
                "started_at": time.time(), "result": None,
            }
            self._body_vlm_test_thread = threading.Thread(
                target=self._run_body_vlm_test_job, args=(job_id, mode),
                name="body-vlm-diagnostic", daemon=True,
            )
            self._body_vlm_test_thread.start()
            return dict(self._body_vlm_test_status)

    def _run_body_vlm_test_job(self, job_id: str, mode: str = "single") -> None:
        started = time.monotonic()
        result = self.benchmark_body_vlm_profiles() if mode == "benchmark" else self.test_body_vlm()
        finished_at = time.time()
        with self._body_vlm_test_lock:
            if self._body_vlm_test_status.get("job_id") != job_id:
                return
            self._body_vlm_test_status = {
                "ok": bool(result.get("ok")),
                "status": "completed" if result.get("ok") else "failed",
                "job_id": job_id,
                "started_at": self._body_vlm_test_status.get("started_at"),
                "completed_at": finished_at,
                "latency_ms": round((time.monotonic() - started) * 1000, 1),
                "progress": None,
                "result": result,
            }

    def body_vlm_test_status(self) -> dict:
        with self._body_vlm_test_lock:
            return dict(self._body_vlm_test_status)

    def start_vlm_sensorimotor_test(self, request: dict | None = None) -> dict:
        """Start an explicit VLM + paired-sensor scene suite."""
        roi_compare = bool((request or {}).get("roi_compare", False))
        try:
            scene_count = max(1, min(20, int((request or {}).get("scenes", 3))))
        except (TypeError, ValueError):
            scene_count = 3
        with self._sensorimotor_test_lock:
            if self._sensorimotor_test_status.get("status") == "running":
                return {**self._sensorimotor_test_status, "reused": True}
            job_id = f"sensorimotor-{time.time_ns()}"
            self._sensorimotor_test_status = {
                "status": "running", "job_id": job_id, "started_at": time.time(),
                "progress": {"stage": "starting"}, "result": None,
            }
            self._sensorimotor_test_thread = threading.Thread(
                target=self._run_vlm_sensorimotor_test, args=(job_id, scene_count, roi_compare),
                name="body-vlm-sensorimotor-test", daemon=True,
            )
            self._sensorimotor_test_thread.start()
            return dict(self._sensorimotor_test_status)

    def _run_vlm_sensorimotor_test(self, job_id: str, scene_count: int, roi_compare: bool = False) -> None:
        started = time.monotonic()
        try:
            from body_runtime_host.worldmodel.evaluation import run_vlm_sensorimotor_suite

            def progress(update: dict) -> None:
                with self._sensorimotor_test_lock:
                    if self._sensorimotor_test_status.get("job_id") == job_id:
                        self._sensorimotor_test_status["progress"] = dict(update)

            result = run_vlm_sensorimotor_suite(
                self.config, scene_count=scene_count, roi_compare=roi_compare,
                progress_callback=progress,
            )
            status = str(result.get("status") or "failed")
        except Exception as exc:
            LOG.exception("Body VLM sensorimotor scenario failed")
            result, status = {"status": "failed", "error": str(exc)[:300]}, "failed"
        with self._sensorimotor_test_lock:
            if self._sensorimotor_test_status.get("job_id") != job_id:
                return
            self._sensorimotor_test_status = {
                "status": status, "job_id": job_id,
                "started_at": self._sensorimotor_test_status.get("started_at"),
                "completed_at": time.time(),
                "latency_ms": round((time.monotonic() - started) * 1000.0, 1),
                "progress": None, "result": result,
            }

    def vlm_sensorimotor_test_status(self) -> dict:
        with self._sensorimotor_test_lock:
            return dict(self._sensorimotor_test_status)

    def restart_geniex(self) -> dict:
        """Restart only the local GenieX user service used by the Ventuno VLM."""
        settings = self.body_llm_settings()
        endpoint = urlparse(str(settings.get("base_url") or ""))
        try:
            is_geniex_endpoint = endpoint.hostname in {"127.0.0.1", "localhost", "::1"} and endpoint.port == 18181
        except ValueError:
            is_geniex_endpoint = False
        if not is_geniex_endpoint:
            return {
                "ok": False,
                "status": "not_local_geniex",
                "error": "Restart is available only when Body VLM uses the local GenieX endpoint on port 18181.",
            }
        if os.name != "posix" or not Path("/run/systemd/system").exists():
            return {
                "ok": False,
                "status": "unsupported_platform",
                "error": "GenieX service restart is available from the Linux Ventuno Body runtime.",
            }

        uid = os.getuid()
        runtime_dir = Path(f"/run/user/{uid}")
        bus = runtime_dir / "bus"
        if not bus.exists():
            return {
                "ok": False,
                "status": "user_service_unavailable",
                "error": "The systemd user-service bus is unavailable for this Body account.",
            }
        env = os.environ.copy()
        env["XDG_RUNTIME_DIR"] = str(runtime_dir)
        env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus}"
        try:
            restarted = subprocess.run(
                ["systemctl", "--user", "restart", "geniex.service"],
                capture_output=True, text=True, timeout=30, check=False, env=env,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            LOG.warning("Could not restart local GenieX service: %s", exc)
            return {"ok": False, "status": "restart_failed", "error": str(exc)[:240]}
        if restarted.returncode != 0:
            detail = (restarted.stderr or restarted.stdout or "systemctl restart failed").strip()
            LOG.warning("GenieX restart failed: %s", detail[:240])
            return {"ok": False, "status": "restart_failed", "error": detail[:240]}

        LOG.info("Restarted local VLM inference service geniex.service")
        return {
            "ok": True,
            "status": "restarted",
            "service": "geniex.service",
            "message": "GenieX restarted. Its model will load again on the next VLM request.",
        }

    def test_body_embeddings(self, label: str) -> dict:
        """Run a real semantic-match probe against objects in the latest Body scene."""
        wm = self.worldmodel
        if wm is None or wm.source is None:
            return {"ok": False, "status": "source_unavailable", "error": "World model or sensor source unavailable."}
        try:
            observation = wm.source.observe()
            body = wm.source.body_state()
            packet = wm._scene_packet(observation, body, {}, {})
            known = {
                str(item.get("id")): item
                for item in packet.get("objects", [])
                if isinstance(item, dict) and item.get("id")
            }
            result = wm.scene_interpreter.test_embedding_resolution(label, known)
            LOG.info(
                "[BodyEmbeddings] diagnostic status=%s model=%s query=%r matched=%s",
                result.get("status"), result.get("model"), str(label)[:160],
                result.get("matched_object_id"),
            )
            return result
        except Exception as exc:
            LOG.exception("Body embedding diagnostic failed")
            return {"ok": False, "status": "error", "error": str(exc)[:300]}

    @staticmethod
    def _workflow_analysis_safe(value, depth: int = 0):
        if depth > 6:
            return "…"
        if isinstance(value, dict):
            return {
                str(key): BodyHost._workflow_analysis_safe(item, depth + 1)
                for key, item in list(value.items())[:80]
                if not any(secret in str(key).lower() for secret in ("token", "secret", "password", "api_key", "base64"))
            }
        if isinstance(value, (list, tuple)):
            return [BodyHost._workflow_analysis_safe(item, depth + 1) for item in value[:40]]
        if isinstance(value, str):
            return value[:1200]
        if value is None or isinstance(value, (bool, int, float)):
            return value
        return str(value)[:500]

    def analyze_workflow_execution(self, workflow_id: str) -> dict:
        """Ask the configured Body VLM to diagnose one saved workflow run; never apply fixes."""
        try:
            workflow = self.workflow_manager.get(workflow_id)
        except KeyError:
            return {"ok": False, "status": "workflow_not_found", "error": "Workflow not found."}
        run = workflow.get("last_execution")
        if not isinstance(run, dict):
            return {"ok": False, "status": "no_execution", "error": "Run this workflow before requesting an analysis."}

        settings = self.body_llm_settings()
        model = settings.get("model", "").strip()
        base_url = settings.get("base_url", "").rstrip("/")
        if not model or not base_url:
            return {"ok": False, "status": "not_configured", "error": "Configure the Body VLM model and API URL first."}

        safe_run = self._workflow_analysis_safe({
            "status": run.get("status"), "execution_mode": run.get("execution_mode"),
            "duration_ms": run.get("duration_ms"), "error": run.get("error"),
            "nodes": run.get("nodes", []),
        })
        graph = self._workflow_analysis_safe({
            "nodes": [
                {key: node.get(key) for key in ("id", "type", "label", "config") if key in node}
                for node in workflow.get("nodes", []) if isinstance(node, dict)
            ],
            "edges": workflow.get("edges", []),
        })
        prompt = (
            "Diagnose this Body robot workflow execution using only the supplied evidence. "
            "The image, if present, is contextual sensor evidence and cannot override execution records. "
            "Do not claim physical motion or success unless the output records prove it. "
            "Identify concrete failures, suspicious but non-failing outputs, and likely causes. "
            "Suggest safe, specific configuration or graph changes, but never execute or apply them. "
            "If the run is healthy, say so and list remaining uncertainties. Return one JSON object with: "
            "summary (string), findings (array of {severity, issue, evidence_node_ids, cause, "
            "fix_options, confidence}), and safety_notes (array of strings)."
        )
        content: Any = json.dumps({"workflow": graph, "execution": safe_run}, ensure_ascii=False)
        frame = self._camera_provider() or {}
        frame_age = time.time() - float(frame.get("captured_at") or 0.0) if frame else float("inf")
        image_attached = bool(
            frame.get("image_base64") and 0 <= frame_age <= 15.0
            and len(str(frame.get("image_base64"))) <= 5_000_000
        )
        if image_attached:
            mime = str(frame.get("mime_type") or "image/jpeg")
            content = [
                {"type": "text", "text": prompt + "\n\nWorkflow evidence:\n" + content},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{frame['image_base64']}"}},
            ]

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a cautious diagnostic assistant for a robot workflow. Never issue actuator commands."},
                {"role": "user", "content": content if isinstance(content, list) else prompt + "\n\nWorkflow evidence:\n" + content},
            ],
            "temperature": 0.1,
            "max_tokens": min(1200, max(256, int(settings.get("max_tokens", 512)))),
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        token = str(self.value("BODY_LLM_TOKEN", "") or "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        timeout = min(90.0, max(5.0, float(settings.get("timeout", 30.0))))

        def request_completion(current_payload):
            request = Request(
                f"{base_url}/chat/completions",
                data=json.dumps(current_payload, ensure_ascii=False).encode("utf-8"),
                headers=headers, method="POST",
            )
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))

        try:
            try:
                response = request_completion(payload)
            except HTTPError as exc:
                if exc.code not in {400, 422}:
                    raise
                payload.pop("response_format", None)
                try:
                    response = request_completion(payload)
                except HTTPError as retry_exc:
                    if retry_exc.code not in {400, 422} or not image_attached:
                        raise
                    payload["messages"][1]["content"] = prompt + "\n\nWorkflow evidence:\n" + json.dumps(
                        {"workflow": graph, "execution": safe_run}, ensure_ascii=False,
                    )
                    image_attached = False
                    response = request_completion(payload)
            message = ((response.get("choices") or [{}])[0].get("message") or {})
            raw = message.get("content") or ""
            if isinstance(raw, list):
                raw = "".join(str(part.get("text") or "") for part in raw if isinstance(part, dict))
            from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter
            analysis = BodySceneInterpreter._parse_json_object(str(raw))
            if not isinstance(analysis, dict):
                return {
                    "ok": False, "status": "invalid_response", "model": model,
                    "image_attached": image_attached, "error": "VLM response was not valid JSON.",
                    "raw_response": str(raw)[:1800],
                }
            result = {
                "ok": True, "status": "analyzed", "model": model,
                "workflow_id": workflow_id, "execution_id": run.get("id"),
                "image_attached": image_attached, "analysis": analysis,
                "applied": False,
            }
            LOG.info(
                "[WorkflowVLM] analyzed workflow=%s execution=%s model=%s image=%s findings=%d",
                workflow_id, run.get("id"), model, image_attached,
                len(analysis.get("findings") or []),
            )
            return result
        except Exception as exc:
            LOG.warning(
                "[WorkflowVLM] analysis failed workflow=%s model=%s error=%s",
                workflow_id, model, str(exc)[:240],
            )
            return {
                "ok": False, "status": "provider_error", "model": model,
                "image_attached": image_attached, "error": str(exc)[:300],
            }

    def body_llm_settings(self) -> dict:
        embedding_provider = str(self.value("BODY_LLM_EMBEDDING_PROVIDER", "openai") or "openai")
        embedding_model = str(self.value("BODY_LLM_EMBEDDING_MODEL", "") or "")
        if embedding_provider == "local_fastembed" and (
            not embedding_model or "nomic-embed-text-v1.5" in embedding_model.lower()
        ):
            embedding_model = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        return {
            "enabled": bool(self.value("BODY_LLM_ENABLED", False)),
            "base_url": str(self.value("BODY_LLM_BASE_URL", "http://127.0.0.1:1234/v1") or ""),
            "model": str(self.value("BODY_LLM_MODEL", "") or ""),
            "interval": float(self.value("BODY_LLM_INTERVAL", 8.0) or 8.0),
            "timeout": float(self.value("BODY_LLM_TIMEOUT", 8.0) or 8.0),
            "max_tokens": int(self.value("BODY_LLM_MAX_TOKENS", 360) or 360),
            "visual_max_tokens": max(32, min(512, int(self.value("BODY_LLM_VISUAL_MAX_TOKENS", 128) or 128))),
            "visual_max_objects": max(1, min(10, int(self.value("BODY_LLM_VISUAL_MAX_OBJECTS", 5) or 5))),
            "visual_image_max_width": max(320, min(640, int(self.value("BODY_LLM_VISUAL_IMAGE_MAX_WIDTH", 640) or 640))),
            "radar_focus_enabled": bool(self.value("BODY_LLM_RADAR_FOCUS_ENABLED", True)),
            "target_latency_s": max(1.0, min(60.0, float(self.value("BODY_LLM_TARGET_LATENCY_S", 5.0) or 5.0))),
            "context_window": int(self.value("BODY_LLM_CONTEXT_WINDOW", 50000) or 50000),
            "focus_range_m": float(self.value("BODY_LLM_FOCUS_RANGE_M", 5.0) or 5.0),
            "json_mode": bool(self.value("BODY_LLM_JSON_MODE", True)),
            "embedding_provider": embedding_provider,
            "embedding_model": embedding_model,
            "local_embedding_available": importlib.util.find_spec("fastembed") is not None,
            "embedding_threshold": float(self.value("BODY_LLM_EMBEDDING_THRESHOLD", 0.55) or 0.55),
            "embedding_timeout": float(self.value("BODY_LLM_EMBEDDING_TIMEOUT", 4.0) or 4.0),
            "token_configured": bool(self.value("BODY_LLM_TOKEN", "")),
        }

    def runtime_network_settings(self) -> dict:
        configured_host = str(self.value("BODY_HOST", "127.0.0.1") or "127.0.0.1")
        if configured_host not in {"127.0.0.1", "0.0.0.0"}:
            configured_host = "127.0.0.1"
        active_host = "127.0.0.1"
        active_port = int(self.value("BODY_PORT", 8766) or 8766)
        if self.http_server is not None:
            active_host = str(self.http_server.server_address[0])
            active_port = int(self.http_server.server_address[1])
        return {
            "configured_host": configured_host,
            "active_host": active_host,
            "port": active_port,
            "restart_required": configured_host != active_host,
            "choices": ["127.0.0.1", "0.0.0.0"],
            "authentication": False,
        }

    def update_runtime_network_settings(self, payload: dict) -> dict:
        host = str(payload.get("bind_host", "127.0.0.1") or "127.0.0.1").strip()
        if host not in {"127.0.0.1", "0.0.0.0"}:
            raise ValueError("bind_host must be 127.0.0.1 or 0.0.0.0")
        self.config["BODY_HOST"] = host
        self.save_config()
        return {"ok": True, "settings": self.runtime_network_settings()}

    def deployment_check(self, payload: dict) -> dict:
        target = str(payload.get("target_url", "") or "").strip().rstrip("/")
        if not target:
            return {"ok": False, "error": "target_url is required"}
        try:
            health = _http_get(f"{target}/health", token=str(payload.get("token", "") or ""), timeout=3.0)
            return {"ok": True, "target_url": target, "health": health}
        except Exception as exc:
            return {"ok": False, "target_url": target, "error": str(exc)[:240]}

    def deployment_push(self, payload: dict) -> dict:
        target = str(payload.get("target_url", "") or "").strip().rstrip("/")
        if not target:
            return {"ok": False, "error": "target_url is required"}
        bundle, manifest = build_bundle(ROOT, bool(payload.get("include_learned_model", False)))
        headers = {"Content-Type": "application/zip", "Accept": "application/json"}
        token = str(payload.get("token", "") or "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(f"{target}/deploy", data=bundle, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=30.0) as response:
                raw = response.read().decode("utf-8")
                result = json.loads(raw) if raw else {}
            return {"ok": True, "target_url": target, "manifest": manifest, "remote": result}
        except Exception as exc:
            return {"ok": False, "target_url": target, "manifest": manifest, "error": str(exc)[:300]}

    def deployment_activate(self, payload: dict) -> dict:
        target = str(payload.get("target_url", "") or "").strip().rstrip("/")
        stage_id = str(payload.get("stage_id", "") or "").strip()
        if not target or not stage_id:
            return {"ok": False, "error": "target_url and stage_id are required"}
        try:
            result = _http_post(f"{target}/deploy/activate", {"stage_id": stage_id}, token=str(payload.get("token", "") or ""), timeout=10.0)
            return {"ok": True, "target_url": target, "remote": result}
        except Exception as exc:
            return {"ok": False, "target_url": target, "error": str(exc)[:300]}

    def deployment_restart(self, payload: dict) -> dict:
        target = str(payload.get("target_url", "") or "").strip().rstrip("/")
        if not target:
            return {"ok": False, "error": "target_url is required"}
        try:
            result = _http_post(f"{target}/deploy/restart", {}, token=str(payload.get("token", "") or ""), timeout=45.0)
            return {"ok": True, "target_url": target, "remote": result}
        except Exception as exc:
            return {"ok": False, "target_url": target, "error": str(exc)[:300]}

    def body_llm_models(self) -> dict:
        base = str(self.value("BODY_LLM_BASE_URL", "http://127.0.0.1:1234/v1") or "").rstrip("/")
        try:
            # LM Studio exposes rich model metadata on its native API. The
            # OpenAI-compatible endpoint remains the fallback for providers
            # that do not implement /api/v0/models.
            native_base = base[:-3] if base.endswith("/v1") else base
            try:
                payload = _http_get(f"{native_base}/api/v0/models", timeout=3.0) or {}
                metadata_source = "provider_native_metadata"
            except Exception:
                payload = _http_get(f"{base}/models", timeout=3.0) or {}
                metadata_source = "openai_compatible_metadata"
            models = []
            for item in payload.get("data", []):
                if not isinstance(item, dict) or not item.get("id"):
                    continue
                # Keep the provider metadata small, but preserve the fields
                # needed to audit why a model is marked vision-capable.
                metadata = {
                    key: item[key] for key in (
                        "modalities", "input_modalities", "supported_modalities",
                        "capabilities", "architecture", "type",
                    ) if key in item
                }
                tokens = json.dumps(metadata, ensure_ascii=False).lower()
                explicit_modalities = metadata.get("modalities") or metadata.get("input_modalities") or metadata.get("supported_modalities")
                model_type = str(item.get("type") or "").lower()
                if model_type in {"vlm", "vision", "multimodal"} or any(token in tokens for token in ("vision", "image", "multimodal", "vlm", "visual")):
                    vision = True
                    capability_source = metadata_source
                elif isinstance(explicit_modalities, (list, tuple, set)) and explicit_modalities:
                    vision = False
                    capability_source = metadata_source
                elif model_type in {"llm", "embedding", "embeddings"}:
                    vision = False
                    capability_source = metadata_source
                else:
                    vision = None
                    capability_source = "unknown"
                models.append({
                    "id": str(item["id"]),
                    "vision_capable": vision,
                    "capability_source": capability_source,
                    "type": model_type or None,
                    "metadata": metadata,
                })
            return {"ok": True, "models": models}
        except Exception as exc:
            return {"ok": False, "models": [], "error": str(exc)[:180]}

    def update_body_llm_settings(self, payload: dict) -> dict:
        self.config.update({
            "BODY_LLM_ENABLED": bool(payload.get("enabled", False)),
            "BODY_LLM_BASE_URL": str(payload.get("base_url", "http://127.0.0.1:1234/v1") or "").strip().rstrip("/"),
            "BODY_LLM_MODEL": str(payload.get("model", "") or "").strip(),
            "BODY_LLM_INTERVAL": max(2.0, float(payload.get("interval", 8.0) or 8.0)),
            "BODY_LLM_TIMEOUT": max(1.0, float(payload.get("timeout", 8.0) or 8.0)),
            "BODY_LLM_MAX_TOKENS": max(64, min(2048, int(payload.get("max_tokens", 360) or 360))),
            "BODY_LLM_VISUAL_MAX_TOKENS": max(32, min(512, int(payload.get("visual_max_tokens", 128) or 128))),
            "BODY_LLM_VISUAL_MAX_OBJECTS": max(1, min(10, int(payload.get("visual_max_objects", 5) or 5))),
            "BODY_LLM_VISUAL_IMAGE_MAX_WIDTH": max(320, min(640, int(payload.get("visual_image_max_width", 640) or 640))),
            "BODY_LLM_RADAR_FOCUS_ENABLED": bool(payload.get("radar_focus_enabled", True)),
            "BODY_LLM_TARGET_LATENCY_S": max(1.0, min(60.0, float(payload.get("target_latency_s", 5.0) or 5.0))),
            "BODY_LLM_CONTEXT_WINDOW": max(2048, min(131072, int(payload.get("context_window", 50000) or 50000))),
            "BODY_LLM_JSON_MODE": bool(payload.get("json_mode", True)),
            "BODY_LLM_EMBEDDING_PROVIDER": str(payload.get("embedding_provider", "openai") or "openai").strip().lower()
            if str(payload.get("embedding_provider", "openai") or "openai").strip().lower() in {"openai", "local_fastembed"}
            else "openai",
            "BODY_LLM_EMBEDDING_MODEL": str(payload.get("embedding_model", "text-embedding-nomic-embed-text-v1.5") or "").strip(),
            "BODY_LLM_EMBEDDING_THRESHOLD": max(0.0, min(1.0, float(payload.get("embedding_threshold", 0.55)))),
            "BODY_LLM_EMBEDDING_TIMEOUT": max(1.0, min(8.0, float(payload.get("embedding_timeout", 4.0) or 4.0))),
        })
        token = str(payload.get("token", "") or "").strip()
        if token:
            os.environ["BODY_LLM_TOKEN"] = token
            self.config["BODY_LLM_TOKEN"] = "@env:BODY_LLM_TOKEN"
            secret_path = ROOT / "body_venv" / ".env"
            secret_path.parent.mkdir(parents=True, exist_ok=True)
            existing = {}
            if secret_path.exists():
                for line in secret_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if "=" in line and not line.lstrip().startswith("#"):
                        key, value = line.split("=", 1)
                        existing[key.strip()] = value.strip()
            existing["BODY_LLM_TOKEN"] = token
            secret_path.write_text("".join(f"{key}={value}\n" for key, value in existing.items()), encoding="utf-8")
        self.save_config()
        wm = self._worldmodel
        if wm is not None:
            with wm._lock:
                for key in ("BODY_LLM_ENABLED", "BODY_LLM_BASE_URL", "BODY_LLM_MODEL", "BODY_LLM_INTERVAL", "BODY_LLM_TIMEOUT", "BODY_LLM_MAX_TOKENS", "BODY_LLM_VISUAL_MAX_TOKENS", "BODY_LLM_VISUAL_MAX_OBJECTS", "BODY_LLM_VISUAL_IMAGE_MAX_WIDTH", "BODY_LLM_RADAR_FOCUS_ENABLED", "BODY_LLM_TARGET_LATENCY_S", "BODY_LLM_CONTEXT_WINDOW", "BODY_LLM_JSON_MODE", "BODY_LLM_EMBEDDING_PROVIDER", "BODY_LLM_EMBEDDING_MODEL", "BODY_LLM_EMBEDDING_THRESHOLD", "BODY_LLM_EMBEDDING_TIMEOUT"):
                    wm._cfg[key] = self.config.get(key)
                wm._cfg["BODY_LLM_TOKEN"] = self.value("BODY_LLM_TOKEN", "")
                wm.scene_interpreter._config = wm._cfg
        return {"ok": True, "settings": self.body_llm_settings()}

    def home_assistant_settings(self) -> dict:
        """Return editable Home Assistant settings without exposing the token."""
        token = str(self.value("HOME_ASSISTANT_TOKEN", "") or "")
        return {
            "url": str(self.value("HOME_ASSISTANT_URL", "") or ""),
            "token_configured": bool(token),
            "verify_ssl": bool(self.value("HOME_ASSISTANT_VERIFY_SSL", True)),
            "poll_interval": int(self.value("HOME_ASSISTANT_POLL_INTERVAL", 5) or 5),
            "allowed_domains": str(self.value("HOME_ASSISTANT_ALLOWED_DOMAINS", "") or ""),
            "entities": str(self.value("HOME_ASSISTANT_ENTITIES", "") or ""),
        }

    def update_home_assistant_settings(self, payload: dict) -> dict:
        """Persist Body-owned Home Assistant settings and optional token."""
        values = {
            "HOME_ASSISTANT_URL": str(payload.get("url", "") or "").strip().rstrip("/"),
            "HOME_ASSISTANT_VERIFY_SSL": bool(payload.get("verify_ssl", True)),
            "HOME_ASSISTANT_POLL_INTERVAL": max(1, int(payload.get("poll_interval", 5) or 5)),
            "HOME_ASSISTANT_ALLOWED_DOMAINS": str(payload.get("allowed_domains", "") or "").strip(),
            "HOME_ASSISTANT_ENTITIES": str(payload.get("entities", "") or "").strip(),
        }
        self.config.update(values)
        token = str(payload.get("token", "") or "").strip()
        if token:
            os.environ["HOME_ASSISTANT_TOKEN"] = token
            self.config["HOME_ASSISTANT_TOKEN"] = "@env:HOME_ASSISTANT_TOKEN"
            secret_path = ROOT / "body_venv" / ".env"
            secret_path.parent.mkdir(parents=True, exist_ok=True)
            existing = {}
            if secret_path.exists():
                for line in secret_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if "=" in line and not line.lstrip().startswith("#"):
                        key, value = line.split("=", 1)
                        existing[key.strip()] = value.strip()
            existing["HOME_ASSISTANT_TOKEN"] = token
            secret_path.write_text("".join(f"{key}={value}\n" for key, value in existing.items()), encoding="utf-8")
        self.save_config()
        return {"ok": True, "settings": self.home_assistant_settings()}

    def fnk0050_settings(self) -> dict:
        token = str(self.value("FNK0050_TOKEN", "") or "")
        return {
            "url": str(self.value("FNK0050_URL", "") or ""),
            "token_configured": bool(token),
            "timeout": float(self.value("FNK0050_TIMEOUT", 5.0) or 5.0),
            "poll_interval": int(self.value("FNK0050_POLL_INTERVAL", 5) or 5),
            "snn_enabled": bool(self.value("FNK0050_SNN_ENABLED", False)),
            "actuation_enabled": bool(self.value("FNK0050_ACTUATION_ENABLED", False)),
        }

    def update_fnk0050_settings(self, payload: dict) -> dict:
        self.config.update({
            "FNK0050_URL": str(payload.get("url", "") or "").strip().rstrip("/"),
            "FNK0050_TIMEOUT": max(0.5, float(payload.get("timeout", 5.0) or 5.0)),
            "FNK0050_POLL_INTERVAL": max(1, int(payload.get("poll_interval", 5) or 5)),
            "FNK0050_SNN_ENABLED": bool(payload.get("snn_enabled", False)),
            "FNK0050_ACTUATION_ENABLED": bool(payload.get("actuation_enabled", False)),
        })
        token = str(payload.get("token", "") or "").strip()
        if token:
            os.environ["FNK0050_TOKEN"] = token
            self.config["FNK0050_TOKEN"] = "@env:FNK0050_TOKEN"
            secret_path = ROOT / "body_venv" / ".env"
            secret_path.parent.mkdir(parents=True, exist_ok=True)
            existing = {}
            if secret_path.exists():
                for line in secret_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if "=" in line and not line.lstrip().startswith("#"):
                        key, value = line.split("=", 1)
                        existing[key.strip()] = value.strip()
            existing["FNK0050_TOKEN"] = token
            secret_path.write_text("".join(f"{key}={value}\n" for key, value in existing.items()), encoding="utf-8")
        self.save_config()
        if self._worldmodel is not None:
            self.reload_worldmodel_source()
        return {"ok": True, "settings": self.fnk0050_settings()}

    def fnk0031_settings(self) -> dict:
        token = str(self.value("FNK0031_TOKEN") or self.value("ROBOT_TOKEN", "") or "")
        return {
            "url": self._robot_url(),
            "token_configured": bool(token),
            "timeout": float(self.value("FNK0031_TIMEOUT", self.value("ROBOT_TIMEOUT", 5.0)) or 5.0),
            "poll_interval": int(self.value("FNK0031_POLL_INTERVAL", self.value("ROBOT_POLL_INTERVAL", 5)) or 5),
            "snn_enabled": bool(self.value("FNK0031_SNN_ENABLED", False)),
            "actuation_enabled": bool(self.value("FNK0031_ACTUATION_ENABLED", False)),
            "leg_count": int(self.value("FNK0031_LEG_COUNT", 6) or 6),
            "platform": str(self.value("FNK0031_PLATFORM", "ventuno_q_gateway") or "ventuno_q_gateway"),
            "serial_port": str(self.value("FNK0031_SERIAL_PORT", "") or ""),
        }

    def fnk0031_usb_status(self) -> dict:
        from body_runtime_host.fnk0031_usb import FNK0031USBSource, available_serial_ports

        settings = self.fnk0031_settings()
        port = settings["serial_port"]
        probe = FNK0031USBSource(port, timeout=min(2.0, settings["timeout"])) if port else None
        status = probe.status() if probe else {
            "source": "fnk0031_usb", "transport": "USB serial / stock FNHR framed protocol", "protocol": "fnhr_framed_serial", "port": "",
            "connected": False, "actuation_enabled": settings["actuation_enabled"],
            "pose_available": False, "supply_voltage_v": None, "remote_preserved": True,
            "last_error": "USB serial port is not configured",
            "supported_actions": ["forward", "backward", "turn_left", "turn_right", "stop", "wait"],
        }
        return {
            **status,
            "ports": available_serial_ports(),
            "configured_port": port,
            "plugin_enabled": bool(self.value("BODY_PLUGIN_ROBOT_ENABLED", False)),
        }

    def publish_fnk0031_usb_status(self) -> bool:
        """Forward a read-only FNK USB health snapshot to the Brain bridge."""
        if (
            not bool(self.value("BODY_PLUGIN_ROBOT_ENABLED", False))
            or str(self.value("FNK0031_PLATFORM", "")).lower() != "usb_serial"
        ):
            return False
        interval = max(10.0, float(self.value("FNK0031_POLL_INTERVAL", 5) or 5))
        now = time.monotonic()
        if now - self._fnk_usb_last_publish < interval:
            return False
        self._fnk_usb_last_publish = now
        status = self.fnk0031_usb_status()
        observed_at = time.time()
        value = {
            "connected": bool(status.get("connected")),
            "port": status.get("configured_port") or status.get("port") or "",
            "protocol": status.get("protocol") or "fnhr_framed_serial",
            "actuation_enabled": bool(status.get("actuation_enabled")),
            "pose_available": bool(status.get("pose_available")),
            "supply_voltage_v": status.get("supply_voltage_v"),
            "last_error": str(status.get("last_error") or "")[:240],
        }
        entry = {
            "entity_id": "robot.fnk0031.usb_status",
            "source": "fnk0031_usb",
            "kind": "hardware_status",
            "subject": "fnk0031.usb_status",
            "value": value,
            "unit": "",
            "confidence": 1.0,
            "observed_at": observed_at,
            "provenance": {
                "transport": status.get("transport"),
                "supported_actions": status.get("supported_actions") or [],
                "unsupported_actions": status.get("unsupported_actions") or [],
                "remote_preserved": bool(status.get("remote_preserved", True)),
            },
        }
        self.latest[entry["entity_id"]] = entry
        self._bridge_put(entry)
        LOG.info(
            "Forwarded FNK0031 USB health to Brain: connected=%s port=%s actuation=%s",
            value["connected"], value["port"], value["actuation_enabled"],
        )
        return True

    def fnk0031_modules(self) -> dict:
        """Return discovered FNK0031/VENTUNO modules and their Body state."""
        from body_runtime_host.fnk0031_usb import available_serial_ports

        configured = self.value("FNK0031_MODULES", {})
        if not isinstance(configured, dict):
            configured = {}
        url = self._robot_url()
        source = "configured_robot"
        capabilities = {}
        error = ""
        if url:
            try:
                capabilities = _http_get(
                    f"{url}/capabilities",
                    token=self._robot_token(),
                    timeout=float(self.value("FNK0031_TIMEOUT", 5.0) or 5.0),
                ) or {}
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                error = str(exc)
        if not isinstance(capabilities, dict):
            capabilities = {}
        advertised = capabilities.get("modules") or []
        if not advertised:
            # Older firmware can still describe modules through sensor names.
            advertised = capabilities.get("sensors") or []
        detected = {}
        for item in advertised:
            if isinstance(item, dict):
                module_id = str(item.get("id") or item.get("name") or "").strip().lower()
                details = item
            else:
                module_id = str(item).strip().lower()
                details = {}
            if module_id:
                detected[module_id] = details
        modules = []
        for module_id, metadata in FNK0031_MODULE_CATALOG.items():
            details = detected.get(module_id)
            modules.append({
                "id": module_id,
                **metadata,
                "detected": details is not None,
                "available": details is not None,
                "enabled": bool(configured.get(module_id, details is not None)),
                "details": details or {},
            })
        # Preserve vendor-specific modules without forcing them into the
        # universal catalog, so new VENTUNO hardware remains visible.
        for module_id, details in detected.items():
            if module_id in FNK0031_MODULE_CATALOG:
                continue
            modules.append({
                "id": module_id, "label": str(details.get("label") if isinstance(details, dict) else module_id),
                "kind": str(details.get("kind") if isinstance(details, dict) else "vendor"),
                "source": "robot", "detected": True, "available": True,
                "enabled": bool(configured.get(module_id, True)), "details": details,
            })
        return {
            "ok": not error,
            "source": source,
            "url": url,
            "connected": bool(capabilities),
            "error": error,
            "local_serial_devices": [
                {
                    "device": port["device"],
                    "description": port.get("description") or port.get("product") or "USB serial device",
                    "hardware_id": port.get("hwid", ""),
                    "usb_id": f"{port.get('vid', '')}:{port.get('pid', '')}".strip(":"),
                    "serial_number": port.get("serial_number", ""),
                    "role": (
                        "FNK0031 controller"
                        if str(port["device"]) == str(self.value("FNK0031_SERIAL_PORT", "") or "")
                        else "unassigned USB serial adapter"
                    ),
                    "present": True,
                }
                for port in available_serial_ports()
                if (
                    "USB" in str(port.get("hwid", "")).upper()
                    or "VID:PID=" in str(port.get("hwid", "")).upper()
                    or "/serial/by-id/" in str(port.get("device", ""))
                )
            ],
            "modules": modules,
            "capabilities": capabilities,
        }

    def fnk0031_module_status(self) -> dict:
        """Probe live module health without assuming a particular sensor vendor."""
        discovered = self.fnk0031_modules()
        url = str(discovered.get("url") or "").rstrip("/")
        token = self._robot_token()
        timeout = min(2.0, float(self.value("FNK0031_TIMEOUT", 5.0) or 5.0))
        payload = None
        source = "capabilities_fallback"
        error = ""
        if url:
            for suffix in ("/modules/status", "/module-status", "/sensors/modules"):
                try:
                    candidate = _http_get(f"{url}{suffix}", token=token, timeout=timeout)
                    if isinstance(candidate, dict):
                        payload = candidate
                        source = suffix
                        break
                except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                    error = str(exc)
            if payload is None:
                # Older robot firmware has no module endpoint. Its sensor
                # payload still gives a meaningful live status for core data.
                try:
                    sensors = _http_get(f"{url}/sensors", token=token, timeout=timeout) or {}
                    if isinstance(sensors, dict):
                        payload = {"modules": {
                            "imu": {"status": "online" if sensors.get("imu") else "unknown", "data": sensors.get("imu")},
                            "odometry": {"status": "online" if sensors.get("position") is not None else "unknown", "data": sensors.get("position")},
                            "actuators": {"status": "online" if sensors.get("actuators") else "unknown", "data": sensors.get("actuators")},
                        }}
                        source = "/sensors fallback"
                except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                    error = str(exc)
        raw_modules = (payload or {}).get("modules") if isinstance(payload, dict) else {}
        if isinstance(raw_modules, list):
            raw_modules = {str(item.get("id")): item for item in raw_modules if isinstance(item, dict) and item.get("id")}
        if not isinstance(raw_modules, dict):
            raw_modules = {}
        modules = []
        for module in discovered.get("modules", []):
            module_id = module["id"]
            live = raw_modules.get(module_id) or {}
            status = str(live.get("status") or ("online" if module.get("detected") else "not_detected")).lower()
            modules.append({
                **module,
                "status": status,
                "last_seen": live.get("last_seen") or live.get("timestamp"),
                "error": str(live.get("error") or ""),
                "data": live.get("data", live.get("value")),
            })
        return {
            "ok": bool(discovered.get("connected")) and not error,
            "connected": bool(discovered.get("connected")),
            "url": url,
            "source": source,
            "queried_at": time.time(),
            "error": error,
            "local_serial_devices": discovered.get("local_serial_devices", []),
            "modules": modules,
        }

    def update_fnk0031_module(self, payload: dict) -> dict:
        module_id = str(payload.get("id") or "").strip().lower()
        if not module_id or (module_id not in FNK0031_MODULE_CATALOG and not module_id.replace("_", "").isalnum()):
            raise ValueError("unknown FNK0031 module")
        configured = self.value("FNK0031_MODULES", {})
        if not isinstance(configured, dict):
            configured = {}
        configured[module_id] = bool(payload.get("enabled", False))
        self.config["FNK0031_MODULES"] = configured
        self.save_config()
        return {"ok": True, "persisted": True, **self.fnk0031_modules()}

    def fnk0031_diagnostic(self) -> dict:
        """Run a read-only FNK0031/gateway contract diagnostic.

        The report deliberately stores summaries rather than raw responses so
        a gateway cannot accidentally persist credentials or opaque payloads.
        No command, stop, or actuation endpoint is called here.
        """
        url = self._robot_url()
        settings = self.fnk0031_settings()
        report = {
            "schema": "fnk0031.hardware_diagnostic.v1",
            "timestamp": time.time(),
            "profile": "fnk0031_wifi",
            "url": url,
            "secrets_excluded": True,
            "actuation_enabled": bool(settings.get("actuation_enabled")),
            "checks": {},
            "modules": {},
            "status": "not_configured" if not url else "not_ready",
        }
        if url:
            for name, suffix in (("health", "/health"), ("capabilities", "/capabilities"), ("sensors", "/sensors")):
                try:
                    payload = _http_get(
                        f"{url}{suffix}",
                        token=self._robot_token(),
                        timeout=min(3.0, float(settings.get("timeout", 5.0) or 5.0)),
                    ) or {}
                    if not isinstance(payload, dict):
                        payload = {}
                    report["checks"][name] = {
                        "ok": True,
                        "fields": sorted(str(key) for key in payload.keys()),
                    }
                except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                    report["checks"][name] = {"ok": False, "error": str(exc)[:180]}
            module_report = self.fnk0031_module_status()
            report["modules"] = {
                "connected": bool(module_report.get("connected")),
                "source": module_report.get("source"),
                "error": str(module_report.get("error") or "")[:180],
                "items": [
                    {
                        "id": item.get("id"),
                        "label": item.get("label"),
                        "status": item.get("status"),
                        "detected": bool(item.get("detected")),
                        "enabled": bool(item.get("enabled")),
                        "error": str(item.get("error") or "")[:180],
                    }
                    for item in module_report.get("modules", [])
                ],
            }
            checks = report["checks"]
            if checks.get("health", {}).get("ok") and checks.get("capabilities", {}).get("ok") and checks.get("sensors", {}).get("ok"):
                report["status"] = "ready" if report["modules"].get("connected") else "partial"
        report["passed_checks"] = sum(1 for item in report["checks"].values() if item.get("ok"))
        report["total_checks"] = len(report["checks"])
        self._fnk_diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
        self._fnk_diagnostic_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return report

    def update_fnk0031_settings(self, payload: dict) -> dict:
        platform = str(payload.get("platform", "ventuno_q_gateway") or "ventuno_q_gateway").strip().lower()
        if platform not in {"ventuno_q_gateway", "usb_serial", "esp32", "mega_wifi", "fnk0031_simulator"}:
            raise ValueError("unsupported FNK0031 hardware topology")
        self.config.update({
            "FNK0031_URL": str(payload.get("url", "") or "").strip().rstrip("/"),
            "FNK0031_SERIAL_PORT": str(payload.get("serial_port", self.value("FNK0031_SERIAL_PORT", "")) or "").strip(),
            "FNK0031_TIMEOUT": max(0.5, float(payload.get("timeout", 5.0) or 5.0)),
            "FNK0031_POLL_INTERVAL": max(1, int(payload.get("poll_interval", 5) or 5)),
            "FNK0031_SNN_ENABLED": bool(payload.get("snn_enabled", False)),
            "FNK0031_ACTUATION_ENABLED": bool(payload.get("actuation_enabled", False)),
            "FNK0031_LEG_COUNT": 6,
            "FNK0031_PLATFORM": platform,
        })
        token = str(payload.get("token", "") or "").strip()
        if token:
            os.environ["FNK0031_TOKEN"] = token
            self.config["FNK0031_TOKEN"] = "@env:FNK0031_TOKEN"
            secret_path = ROOT / "body_venv" / ".env"
            secret_path.parent.mkdir(parents=True, exist_ok=True)
            existing = {}
            if secret_path.exists():
                for line in secret_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if "=" in line and not line.lstrip().startswith("#"):
                        key, value = line.split("=", 1)
                        existing[key.strip()] = value.strip()
            existing["FNK0031_TOKEN"] = token
            secret_path.write_text("".join(f"{key}={value}\n" for key, value in existing.items()), encoding="utf-8")
        self.save_config()
        # Treat the disk copy as authoritative.  The controller and the
        # world-model source may already exist with the previous safety flags.
        self.config = self._load_config()
        with self._fnk_controller_lock:
            self._fnk_controller = None
            self._fnk_controller_last = None
            self._fnk_controller_world_step = None
        if self._worldmodel is not None:
            self.reload_worldmodel_source()
        settings = self.fnk0031_settings()
        settings["persisted"] = {
            "snn_enabled": settings["snn_enabled"],
            "actuation_enabled": settings["actuation_enabled"],
        }
        return {"ok": True, "settings": settings}

    def fnk0031_controller_step(self, dt: float = 0.04) -> dict:
        """Advance the local hexapod controller only in the running sim sandbox."""
        wm = self.worldmodel
        simulation_mode = bool(wm is not None and wm.config().get("mode") == "sim")
        if not bool(self.value("BODY_PLUGIN_ROBOT_ENABLED", False)) and not simulation_mode:
            return {"active": False, "reason": "FNK0031 plugin is disabled"}
        if not bool(self.value("FNK0031_SNN_ENABLED", False)):
            return {"active": False, "reason": "SNN locomotion is disabled"}
        if wm is None:
            return {"active": False, "reason": "world model is unavailable"}
        if wm.config().get("mode") != "sim" or not (wm._thread and wm._thread.is_alive()):
            return {"active": False, "reason": "start the simulated world model to run the gait sandbox"}

        with self._fnk_controller_lock:
            if self._fnk_controller is None:
                try:
                    from body_runtime_host.locomotion import FNK0031LocomotionController
                    self._fnk_controller = FNK0031LocomotionController(
                        state_path=ROOT / "data" / "body" / "locomotion" / "fnk0031_snn.npz"
                    )
                except Exception as exc:
                    return {"active": False, "reason": f"locomotion dependencies unavailable: {exc}"}
            with wm._lock:
                decision = dict(wm._last_decision or {})
                sim = wm.sim
                world_action = str(decision.get("action") or "idle")
                gait = _locomotion_gait_for_action(world_action)
                world_step = int(sim.steps) if sim is not None else -1
                worldmodel_pose = ({
                    "body": [round(float(sim.px), 3), round(float(sim.py), 3)],
                    "heading_deg": round(math.degrees(float(sim.heading)), 2),
                    "compass_heading_deg": round(compass_heading_degrees(sim.heading), 2),
                    "svg_heading_deg": round(north_up_svg_rotation_degrees(sim.heading), 2),
                    "step": int(sim.steps),
                } if sim is not None else None)
            controller_dt = max(0.02, min(0.12, float(dt)))
            self._fnk_controller_last = self._fnk_controller.step(
                imu=None, reward=0.0, dt=controller_dt, gait=gait
            )
            self._fnk_controller_world_step = world_step
            self._fnk_controller_gait = gait
            self._fnk_controller_last_tick = time.monotonic()
            return {
                "active": True,
                "mode": "local_simulation",
                "simulation_running": True,
                "gait": gait,
                "world_action": world_action,
                "worldmodel_pose": worldmodel_pose,
                "worldmodel_step": world_step,
                "controller_dt": round(controller_dt, 4),
                "actuation": False,
                "body_heading_deg": round(math.degrees(float(sim.heading)), 1) if sim else 0.0,
                "imu_available": True,
                "imu_source": "simulated_hexapod_plant",
                "reward_source": "synthetic_heuristic",
                "locomotion_verified": False,
                "state_loaded": bool(self._fnk_controller.loaded),
                **self._fnk_controller_last,
                "compass_heading_deg": round(compass_heading_degrees(sim.heading), 2) if sim else 0.0,
                "svg_heading_deg": round(north_up_svg_rotation_degrees(sim.heading), 2) if sim else 90.0,
            }

    def fnk0031_controller_status(self) -> dict:
        # World Model actions are macro-steps, while a leg controller needs a
        # real-time motor clock. Advance the CPG between map updates using
        # elapsed wall time, but keep pose and gait sourced from the same World
        # Model snapshot so the visual body cannot diverge spatially.
        wm = self._worldmodel
        if wm is not None:
            with wm._lock:
                sim = wm.sim
                running = bool(wm._thread and wm._thread.is_alive())
                world_step = int(sim.steps) if sim is not None else -1
            now = time.monotonic()
            elapsed = now - self._fnk_controller_last_tick if self._fnk_controller_last_tick is not None else 0.04
            if running and (world_step != self._fnk_controller_world_step or elapsed >= 0.06):
                self.fnk0031_controller_step(dt=elapsed)
        with self._fnk_controller_lock:
            last = dict(self._fnk_controller_last or {})
            wm = self._worldmodel
            if wm is None:
                return {"active": bool(last), "simulation_running": False, **last,
                        "reason": "world model is unavailable"}
            with wm._lock:
                sim = wm.sim
                decision = dict(wm._last_decision or {})
                simulation_running = bool(wm._thread and wm._thread.is_alive())
                pose = ({
                    "body": [round(float(sim.px), 3), round(float(sim.py), 3)],
                    "heading_deg": round(math.degrees(float(sim.heading)), 2),
                    "compass_heading_deg": round(compass_heading_degrees(sim.heading), 2),
                    "svg_heading_deg": round(north_up_svg_rotation_degrees(sim.heading), 2),
                    "step": int(sim.steps),
                } if sim is not None else None)
                heading = round(math.degrees(float(sim.heading)), 1) if sim is not None else 0.0
            if simulation_running:
                world_action = str(decision.get("action") or "idle")
                gait = _locomotion_gait_for_action(world_action)
            else:
                world_action = "paused"
                gait = self._fnk_controller_gait
            if not last:
                return {"active": False, "simulation_running": simulation_running,
                        "mode": "local_simulation", "gait": gait,
                        "world_action": world_action,
                        "body_heading_deg": heading, "worldmodel_pose": pose,
                        "compass_heading_deg": round(compass_heading_degrees(sim.heading), 2) if sim is not None else 0.0,
                        "svg_heading_deg": round(north_up_svg_rotation_degrees(sim.heading), 2) if sim is not None else 90.0,
                        "reason": "waiting for simulation step"}
            return {
                **last,
                "active": True,
                "mode": "local_simulation",
                "simulation_running": simulation_running,
                "gait": gait,
                "world_action": world_action,
                "body_heading_deg": heading,
                "worldmodel_pose": pose,
                "worldmodel_step": int(pose["step"]) if pose else -1,
                "actuation": False,
                "imu_available": True,
                "imu_source": "simulated_hexapod_plant",
                "reward_source": "synthetic_heuristic",
                "locomotion_verified": False,
                "state_loaded": bool(self._fnk_controller.loaded),
                **self._fnk_controller_last,
                "compass_heading_deg": round(compass_heading_degrees(sim.heading), 2) if sim is not None else 0.0,
                "svg_heading_deg": round(north_up_svg_rotation_degrees(sim.heading), 2) if sim is not None else 90.0,
            }

    def fnk0031_experiment_status(self) -> dict:
        with self._fnk_experiment_lock:
            return dict(self._fnk_experiment_status)

    def start_fnk0031_experiment(self) -> dict:
        with self._fnk_experiment_lock:
            if self._fnk_experiment_thread and self._fnk_experiment_thread.is_alive():
                return dict(self._fnk_experiment_status)
            self._fnk_experiment_status = {"state": "starting", "completed": 0, "total": 40}

            def run() -> None:
                def progress(update: dict) -> None:
                    with self._fnk_experiment_lock:
                        self._fnk_experiment_status.update(update)
                try:
                    from body_runtime_host.locomotion.mujoco_hexapod import run_training_experiment
                    result = run_training_experiment(
                        str(ROOT / "data" / "body" / "locomotion" / "fnk0031_mujoco_snn.npz"),
                        on_progress=progress,
                    )
                    with self._fnk_experiment_lock:
                        self._fnk_experiment_status = {"state": "completed", **result}
                except Exception as exc:
                    LOG.exception("FNK0031 MuJoCo experiment failed")
                    with self._fnk_experiment_lock:
                        self._fnk_experiment_status = {"state": "failed", "error": str(exc)}

            self._fnk_experiment_thread = threading.Thread(
                target=run, name="fnk0031-mujoco-training", daemon=True
            )
            self._fnk_experiment_thread.start()
            return dict(self._fnk_experiment_status)

    def worldmodel_evaluation_status(self) -> dict:
        with self._worldmodel_evaluation_lock:
            return dict(self._worldmodel_evaluation_status)

    def run_video_lidar_replay(self, payload: dict | None = None) -> dict:
        """Replay a local camera video through the Body perception contract.

        This is intentionally synchronous and bounded: it is a diagnostic
        tool, not another sensor loop. The generated JSONL keeps the image and
        estimated range returns together for later VLM/LiDAR comparison.
        """
        payload = payload if isinstance(payload, dict) else {}
        video_path = str(payload.get("video_path") or payload.get("path") or "").strip()
        if not video_path:
            return {"status": "error", "error": "video_path is required"}
        output = payload.get("output_path")
        if not output:
            stamp = time.strftime("%Y%m%d-%H%M%S")
            output = str(ROOT / "data" / "body" / "replays" / f"video-lidar-{stamp}.jsonl")
        try:
            from body_runtime_host.worldmodel.video_lidar import run_video_lidar_replay
            return run_video_lidar_replay(
                video_path,
                sample_fps=float(payload.get("sample_fps", 2.0) or 2.0),
                max_frames=int(payload.get("max_frames", 20) or 20),
                capture_width=int(payload.get("capture_width", 640) or 640),
                capture_height=int(payload.get("capture_height", 480) or 480),
                output_path=str(output),
                camera_height_m=float(payload.get("camera_height_m", 0.24) or 0.24),
                horizontal_fov_deg=float(payload.get("horizontal_fov_deg", 100.0) or 100.0),
                vertical_fov_deg=float(payload.get("vertical_fov_deg", 62.0) or 62.0),
            )
        except Exception as exc:
            LOG.exception("Video/LiDAR replay failed")
            return {"status": "error", "error": str(exc), "video_path": video_path}

    def upload_video_replay(self, payload: dict | None = None) -> dict:
        """Store a browser-selected video inside the Body replay workspace."""
        payload = payload if isinstance(payload, dict) else {}
        filename = Path(str(payload.get("filename") or "capture.mp4")).name
        encoded = str(payload.get("content_base64") or "")
        if not encoded:
            return {"status": "error", "error": "video content is required"}
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as exc:
            return {"status": "error", "error": f"invalid video encoding: {exc}"}
        max_bytes = 256 * 1024 * 1024
        if len(raw) > max_bytes:
            return {"status": "error", "error": "video exceeds the 256 MB upload limit"}
        replay_dir = ROOT / "data" / "body" / "replays" / "uploads"
        replay_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        destination = replay_dir / f"{stamp}-{filename}"
        destination.write_bytes(raw)
        LOG.info("Stored browser-selected video replay %s (%d bytes)", destination, len(raw))
        return {"status": "uploaded", "video_path": str(destination), "filename": filename, "bytes": len(raw)}

    def start_worldmodel_evaluation(self, payload: dict | None = None) -> dict:
        """Run the generic shuffled-scene benchmark outside the Body loop."""
        payload = payload if isinstance(payload, dict) else {}
        trials = max(1, min(250, int(payload.get("trials", 100) or 100)))
        max_steps = max(20, min(1000, int(payload.get("max_steps", 180) or 180)))
        grounding_samples = max(0, min(100, int(payload.get("grounding_samples", 0) or 0)))
        visual_blind = bool(payload.get("visual_blind", True))
        with self._worldmodel_evaluation_lock:
            if self._worldmodel_evaluation_thread and self._worldmodel_evaluation_thread.is_alive():
                return dict(self._worldmodel_evaluation_status)
            self._worldmodel_evaluation_status = {
                "state": "running", "trials": trials, "max_steps": max_steps,
            }

        def run() -> None:
            try:
                from body_runtime_host.worldmodel.evaluation import collect_body_llm_grounding, run_shuffled_trials
                def progress(update: dict) -> None:
                    with self._worldmodel_evaluation_lock:
                        self._worldmodel_evaluation_status.update({"live": update})
                result = run_shuffled_trials(
                    trials=trials,
                    max_steps=max_steps,
                    report_path=self._worldmodel_evaluation_report_path,
                    progress_callback=progress,
                )
                if grounding_samples:
                    result["body_llm_grounding"] = collect_body_llm_grounding(
                        grounding_samples, self.config, visual_blind=visual_blind,
                    )
                gate = result.get("capability_gate")
                if isinstance(gate, dict):
                    self._worldmodel_capability_path.parent.mkdir(parents=True, exist_ok=True)
                    self._worldmodel_capability_path.write_text(
                        json.dumps({"recorded_at": time.time(), **gate}, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                with self._worldmodel_evaluation_lock:
                    self._worldmodel_evaluation_status = {"state": "completed", **result}
            except Exception as exc:
                LOG.exception("World Model shuffled evaluation failed")
                with self._worldmodel_evaluation_lock:
                    self._worldmodel_evaluation_status = {
                        "state": "failed", "trials": trials, "max_steps": max_steps,
                        "error": str(exc),
                    }

        self._worldmodel_evaluation_thread = threading.Thread(
            target=run, name="worldmodel-shuffled-evaluation", daemon=True
        )
        self._worldmodel_evaluation_thread.start()
        return self.worldmodel_evaluation_status()

    def set_plugin_enabled(self, plugin_id: str, enabled: bool) -> dict:
        fields = {
            "home_assistant": "BODY_PLUGIN_HOME_ASSISTANT_ENABLED",
            "robot": "BODY_PLUGIN_ROBOT_ENABLED",
            "fnk0031_wifi": "BODY_PLUGIN_ROBOT_ENABLED",
            "fnk0050_wifi": "BODY_PLUGIN_FNK0050_ENABLED",
            "sim_robot": "BODY_PLUGIN_SIM_ROBOT_ENABLED",
            "world_model": "BODY_WORLDMODEL_ENABLED",
            "mmwave_radar": "BODY_PLUGIN_MMWAVE_RADAR_ENABLED",
            "pc_camera": "BODY_CAMERA_STARTUP_ENABLED",
        }
        field = fields.get(plugin_id)
        if not field:
            raise ValueError(f"unknown Body plugin: {plugin_id}")
        self.config[field] = bool(enabled)
        self.save_config()
        # Confirm the value survived the write instead of reporting success
        # based only on the in-memory dictionary.
        persisted = self._load_config()
        persisted_value = bool(persisted.get(field, False))
        if persisted_value != bool(enabled):
            raise OSError(f"Body configuration was not persisted for {field}")
        if plugin_id == "world_model":
            # Enabling the plugin exposes the Body capability; it must not
            # implicitly launch a physics episode. Simulation is an explicit
            # operator action through POST /worldmodel/run.
            if not enabled and self._worldmodel is not None:
                self._worldmodel.stop()
        elif plugin_id == "pc_camera":
            self._configure_local_camera(start=enabled)
        elif self._worldmodel is not None:
            self.reload_worldmodel_source()
        return {
            "ok": True,
            "plugin": plugin_id,
            "enabled": bool(enabled),
            "persisted": persisted_value,
            "config_path": str(CONFIG_PATH),
            "plugins": self.plugins(),
        }

    # ── Home Assistant (auxiliary presence feed) ───────────────────────────

    def discover(self) -> list[dict]:
        url = str(self.value("HOME_ASSISTANT_URL", "") or "").rstrip("/")
        token = str(self.value("HOME_ASSISTANT_TOKEN", "") or "")
        if not url or not token:
            return []
        parsed = urlparse(url)
        request = Request(f"{url}/api/states", headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
        context = None
        if parsed.scheme == "https" and not bool(self.value("HOME_ASSISTANT_VERIFY_SSL", True)):
            context = ssl._create_unverified_context()
        with urlopen(request, timeout=5, context=context) as response:
            payload = json.loads(response.read().decode("utf-8"))
        allowed = {x.strip().lower() for x in str(self.value("HOME_ASSISTANT_ALLOWED_DOMAINS", "") or "").split(",") if x.strip()}
        selected = {x.strip() for x in str(self.value("HOME_ASSISTANT_SELECTED_ENTITIES", "") or "").split(",") if x.strip()}
        tags = self.value("HOME_ASSISTANT_ENTITY_TAGS", {})
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except Exception:
                tags = {}
        result = []
        for raw in payload if isinstance(payload, list) else []:
            entity_id = str(raw.get("entity_id", ""))
            domain = entity_id.split(".", 1)[0].lower() if "." in entity_id else ""
            if not entity_id or (allowed and domain not in allowed) or (selected and entity_id not in selected):
                continue
            attrs = raw.get("attributes") or {}
            state = raw.get("state")
            device_class = attrs.get("device_class")
            signal_name = None
            if domain == "binary_sensor" and device_class in {"presence", "occupancy", "motion"}:
                signal_name = "presence_detected" if str(state).lower() == "on" else "no_presence"
            result.append({
                "entity_id": entity_id,
                "state": state,
                "friendly_name": attrs.get("friendly_name", entity_id),
                "label": str(tags.get(entity_id) or attrs.get("friendly_name", entity_id)),
                "unit": attrs.get("unit_of_measurement") or "",
                "domain": domain,
                "device_class": device_class,
                "signal": signal_name,
                "last_updated": raw.get("last_updated"),
            })
        return sorted(result, key=lambda item: item["entity_id"])

    def publish(self, item: dict) -> None:
        snapshot = {**item, "source": "home_assistant", "observed_at": time.time()}
        self.latest[item["entity_id"]] = snapshot
        message = {"type": "observation", "observation": {
            "source": "home_assistant",
            "kind": item["domain"],
            "subject": item["label"],
            "value": item["signal"] or item["state"],
            "unit": item["unit"],
            "confidence": 0.98,
            "observed_at": time.time(),
            "provenance": {"entity_id": item["entity_id"], "sensor_last_updated": item["last_updated"]},
        }}
        try:
            self.queue.put_nowait(message)
        except Exception:
            LOG.warning("Body bridge queue is full; dropping observation")

    # ── Robot (MAIN sensorimetry channel) ──────────────────────────────────

    def _robot_url(self) -> str:
        """Prefer the FNK0031 endpoint; ignore the old localhost placeholder."""
        url = str(self.value("FNK0031_URL", "") or "").strip()
        if url:
            return url.rstrip("/")
        legacy_url = str(self.value("ROBOT_URL", "") or "").strip()
        if legacy_url and (urlparse(legacy_url).hostname or "").lower() not in {"localhost", "127.0.0.1", "::1"}:
            return legacy_url.rstrip("/")
        return ""

    def _robot_token(self) -> str:
        return str(self.value("FNK0031_TOKEN") or self.value("ROBOT_TOKEN", "") or "")

    def _robot_configured(self) -> bool:
        return bool(self.value("BODY_PLUGIN_ROBOT_ENABLED", False)) and bool(self._robot_url())

    def fetch_robot_sensors(self) -> dict | None:
        """GET {FNK0031_URL}/sensors — the robot's current state + scene."""
        url = self._robot_url()
        token = self._robot_token()
        timeout = float(self.value("FNK0031_TIMEOUT", self.value("ROBOT_TIMEOUT", 5.0)) or 5.0)
        try:
            sensors = _http_get(f"{url}/sensors", token=token, timeout=timeout)
            if isinstance(sensors, dict):
                self._robot_last_ok = time.time()
                self._robot_last_error = ""
                return sensors
            self._robot_last_error = "robot /sensors returned a non-object payload"
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            self._robot_last_error = f"robot unreachable: {exc}"
            LOG.warning("Robot sensor poll failed: %s", exc)
        return None

    def publish_robot(self, sensors: dict) -> None:
        """Store robot telemetry and forward it to the Brain bridge queue."""
        now = time.time()
        position = sensors.get("position") or [0.0, 0.0, 0.0]
        body_entry = {
            "entity_id": "robot.body.pose",
            "source": "robot", "kind": "body",
            "subject": "body.pose",
            "value": f"({position[0]:.1f},{position[1]:.1f}) heading {sensors.get('orientation', 0):.2f}rad",
            "unit": "m", "confidence": 1.0, "observed_at": now,
            "provenance": {
                "position": position,
                "orientation": sensors.get("orientation"),
                "carrying": sensors.get("carrying"),
                "battery": sensors.get("battery"),
                "capabilities": sensors.get("capabilities") or {},
                "affordances": sensors.get("affordances") or {},
            },
        }
        self.latest[body_entry["entity_id"]] = body_entry
        self._bridge_put(body_entry)
        for obj in (sensors.get("objects") or [])[:24]:
            oid = str(obj.get("id") or obj.get("label") or "object")
            entry = {
                "entity_id": f"robot.object.{oid}",
                "source": "robot", "kind": str(obj.get("kind") or "object"),
                "subject": f"object.{oid}",
                "value": f"{obj.get('label') or oid} at ({obj.get('x', 0):.1f},{obj.get('y', 0):.1f})",
                "unit": "m", "confidence": 1.0, "observed_at": now,
                "provenance": {"id": oid, "mass": obj.get("mass"), "size": obj.get("size"), "props": obj.get("props")},
            }
            self.latest[entry["entity_id"]] = entry
            self._bridge_put(entry)

    def publish_worldmodel_perception(self) -> None:
        """Forward the Body-owned perception boundary to the Brain bridge."""
        wm = self._worldmodel
        if wm is None:
            return
        try:
            perception = wm.status_summary().get("perception") or {}
            if not perception.get("available"):
                return
            body = perception.get("body") or {}
            entry = {
                "entity_id": "world_model.body_state",
                "source": "world_model",
                "kind": "embodied_perception",
                "subject": "body.world_model",
                "value": {
                    "contract": "body_perception_frame.v2",
                    "frame_id": (perception.get("sensor_projections") or {}).get("frame", {}).get("frame_id"),
                    "timestamp": float(perception.get("timestamp") or time.time()),
                    "capabilities": body.get("capabilities") or {},
                    "affordances": perception.get("affordances") or {},
                    "objects": perception.get("objects") or [],
                    "modalities": perception.get("modalities") or {},
                    "sensor_projections": perception.get("sensor_projections") or {},
                    "perception_frame": perception.get("perception_frame") or {},
                    "scene_interpreter": perception.get("scene_interpreter") or {},
                    "position": body.get("position"),
                    "orientation": body.get("orientation"),
                    "text": perception.get("text") or "",
                },
                "unit": "",
                "confidence": 1.0,
                "observed_at": float(perception.get("timestamp") or time.time()),
                "provenance": {
                    "source": perception.get("source") or "world_model",
                    "ground_truth_available": bool(perception.get("ground_truth_available")),
                    "capabilities": body.get("capabilities") or {},
                    "affordances": perception.get("affordances") or {},
                    "quality": (perception.get("sensor_projections") or {}).get("quality") or {},
                },
            }
            self.latest[entry["entity_id"]] = entry
            self._bridge_put(entry)
        except Exception:
            LOG.debug("World-model perception bridge update failed", exc_info=True)

    def publish_runtime_status(self) -> None:
        """Publish a small, timestamped Body health snapshot over the Brain bridge."""
        now = time.time()
        worldmodel = self._worldmodel
        worldmodel_status = {"enabled": bool(self.value("BODY_WORLDMODEL_ENABLED", False)), "running": False}
        if worldmodel is not None:
            try:
                summary = worldmodel.status_summary()
                worldmodel_status.update({
                    "enabled": bool(summary.get("enabled")),
                    "running": bool(summary.get("running")),
                    "mode": summary.get("mode"),
                    "steps": summary.get("steps", 0),
                    "source": (
                        summary.get("source", {}).get("source", "unknown")
                        if isinstance(summary.get("source"), dict)
                        else summary.get("source")
                    ),
                })
            except Exception as exc:
                worldmodel_status["error"] = str(exc)[:180]
        camera = self.camera_settings().get("capture") or {}
        robot = self.robot_status()
        plugins = [
            {"id": item.get("id"), "enabled": bool(item.get("enabled"))}
            for item in self.plugins()
        ]
        value = {
            "runtime": "ready",
            "timestamp": now,
            "bridge_connected": self._bridge_connected.is_set(),
            "camera": {
                "status": camera.get("status", "unknown"),
                "available": bool(camera.get("available")),
                "observed_fps": camera.get("observed_fps"),
                "width": camera.get("width"),
                "height": camera.get("height"),
                "frame_age_s": camera.get("frame_age_s"),
                "last_error": str(camera.get("last_error") or "")[:180],
            },
            "robot": {
                "enabled": robot["enabled"],
                "connected": robot["last_ok_age_s"] is not None and robot["last_ok_age_s"] < 15,
                "last_ok_age_s": robot["last_ok_age_s"],
                "last_error": str(robot["last_error"] or "")[:180],
            },
            "world_model": worldmodel_status,
            "plugins": plugins,
        }
        entry = {
            "entity_id": "body.runtime.status",
            "source": "body_runtime",
            "kind": "runtime_status",
            "subject": "body.runtime",
            "value": value,
            "unit": "",
            "confidence": 1.0,
            "observed_at": now,
            "provenance": {"contract": "pandorabox.body_runtime_status.v1"},
        }
        self.latest[entry["entity_id"]] = entry
        self._bridge_put(entry)

    def _bridge_put(self, entry: dict) -> None:
        if self._ros2_bridge is not None:
            self._ros2_bridge.publish(entry)
        message = {"type": "observation", "observation": entry}
        entity_id = str(entry.get("entity_id") or entry.get("subject") or "observation")
        if not self._bridge_connected.is_set():
            with self._bridge_lock:
                self._bridge_latest[entity_id] = message
            return
        try:
            self.queue.put_nowait(message)
        except Exception:
            with self._bridge_lock:
                self._bridge_latest[entity_id] = message
            LOG.debug("Body bridge queue full; coalescing %s", entity_id)

    def _bridge_put_message(self, message: dict) -> None:
        try:
            self.queue.put_nowait(message)
        except Exception:
            LOG.warning("Body bridge queue is full; dropping outbound message")

    def execute_command(self, command: dict) -> dict:
        """Execute one Brain-approved command through the Body world model."""
        command_id = str(command.get("command_id") or "")
        expires_at = float(command.get("expires_at") or 0.0)
        if not command_id:
            return {"type": "command_result", "status": "failed", "error": "missing command_id"}
        if expires_at and expires_at <= time.time():
            result = {"type": "command_result", "command_id": command_id,
                      "status": "expired", "error": "command expired before Body delivery"}
            self._bridge_put_message(result)
            return result
        if str(command.get("status") or "") != "approved":
            result = {"type": "command_result", "command_id": command_id,
                      "status": "rejected", "error": "Body accepts approved commands only"}
            self._bridge_put_message(result)
            return result
        try:
            from body_runtime_host.worldmodel.types import Action
            action = Action(
                type=str(command.get("action") or "wait"),
                target=command.get("target"),
                params=dict((command.get("payload") or {}).get("params") or {}),
            )
            wm = self.worldmodel
            if wm is None:
                raise RuntimeError("world model unavailable")
            execution = wm.execute_external(action)
            outcome = dict(execution.get("outcome") or {})
            status = "executed" if str(outcome.get("kind")) in {"success", "neutral"} else "failed"
            result = {"type": "command_result", "command_id": command_id,
                      "status": status, "outcome": outcome, "execution": execution}
        except Exception as exc:
            LOG.exception("Approved Body command failed: %s", command_id)
            result = {"type": "command_result", "command_id": command_id,
                      "status": "failed", "error": str(exc)[:240]}
        self._bridge_put_message(result)
        # Also expose the outcome to the Body's own observation stream.
        self.latest[f"body_action.{command_id}"] = {
            "entity_id": f"body_action.{command_id}", "source": "body_action",
            "kind": "actuation_feedback", "subject": f"{command.get('target')}.{command.get('action')}",
            "value": result.get("status"), "unit": "", "confidence": 1.0,
            "observed_at": time.time(), "provenance": {"command_id": command_id, "outcome": result.get("outcome", {})},
        }
        return result

    def robot_status(self) -> dict:
        return {
            "enabled": bool(self.value("BODY_PLUGIN_ROBOT_ENABLED", False)),
            "url": self._robot_url(),
            "token_set": bool(self._robot_token()),
            "last_ok": self._robot_last_ok,
            "last_ok_age_s": round(time.time() - self._robot_last_ok, 1) if self._robot_last_ok else None,
            "last_error": self._robot_last_error,
            "role": "primary sensorimetry channel",
        }

    def robot_sim_status(self) -> dict:
        with self._robot_sim_lock:
            server = self._robot_sim
            if server is None:
                return {"running": False, "url": "", "platform": "fnk0031_simulator"}
            return {
                "running": True,
                "url": f"http://127.0.0.1:{server.port}",
                "port": server.port,
                "platform": "fnk0031_simulator",
                "capabilities": server.capabilities(),
            }

    def start_robot_sim(self, payload: dict | None = None) -> dict:
        with self._robot_sim_lock:
            if self._robot_sim is not None:
                return {"ok": True, **self.robot_sim_status(), "already_running": True}
            from body_runtime_host.robot_sim import RobotSimServer
            requested = (payload or {}).get("port")
            requested_port = int(self.value("FNK0031_SIM_PORT", 9101) if requested is None else requested)
            server = RobotSimServer(host="127.0.0.1", port=requested_port)
            server.start()
            self._robot_sim = server
            return {"ok": True, **self.robot_sim_status()}

    def stop_robot_sim(self) -> dict:
        with self._robot_sim_lock:
            server = self._robot_sim
            self._robot_sim = None
        if server is not None:
            server.stop()
        return {"ok": True, "running": False, "stopped": server is not None}

    def use_robot_sim(self) -> dict:
        started = self.start_robot_sim()
        url = str(started.get("url") or "")
        result = self.update_fnk0031_settings({
            "url": url,
            "platform": "fnk0031_simulator",
            "poll_interval": 1,
            "timeout": 3,
            "snn_enabled": bool(self.value("FNK0031_SNN_ENABLED", False)),
            "actuation_enabled": True,
        })
        enabled = self.set_plugin_enabled("fnk0031_wifi", True)
        return {"ok": bool(result.get("ok") and enabled.get("persisted")), "simulator": started, "settings": result, "plugin": enabled}

    # ── poll loop (robot first, HA auxiliary) ──────────────────────────────

    def poll_loop(self) -> None:
        while not self.stop_event.is_set():
            interval = 5
            if self._robot_configured():
                interval = max(1, min(300, int(self.value("FNK0031_POLL_INTERVAL", self.value("ROBOT_POLL_INTERVAL", 5)) or 5)))
                sensors = self.fetch_robot_sensors()
                if sensors is not None:
                    self.publish_robot(sensors)
                    LOG.info("Robot: %d objects, body at %s",
                             len(sensors.get("objects") or []), sensors.get("position"))
            ha_enabled = bool(self.value("BODY_PLUGIN_HOME_ASSISTANT_ENABLED", self.value("HOME_ASSISTANT_ENABLED", False)))
            if ha_enabled:
                try:
                    entities = self.discover()
                    self.save_discovery(entities)
                    for item in entities:
                        self.publish(item)
                    LOG.info("Home Assistant: %d selected entities (auxiliary)", len(entities))
                except (HTTPError, URLError, TimeoutError, OSError) as exc:
                    LOG.warning("Home Assistant poll failed: %s", exc)
                except Exception:
                    LOG.exception("Home Assistant poll failed")
            if bool(self.value("BODY_WORLDMODEL_ENABLED", False)):
                self.publish_worldmodel_perception()
            self.publish_fnk0031_usb_status()
            self.publish_runtime_status()
            self.stop_event.wait(interval)

    # ── Brain bridge (websocket) ────────────────────────────────────────────

    def bridge_loop(self) -> None:
        try:
            import websockets
        except ImportError:
            LOG.warning("Brain bridge disabled: install body_requirements.txt")
            return
        asyncio.run(self._bridge_session(websockets))

    async def _bridge_session(self, websockets) -> None:
        while not self.stop_event.is_set():
            url = str(self.value("BODY_BRIDGE_URL", "") or "").strip()
            token = str(self.value("BODY_BRIDGE_TOKEN", "") or "").strip()
            if not bool(self.value("BODY_BRIDGE_ENABLED", False)) or not url or not token:
                await asyncio.sleep(2)
                continue
            try:
                headers = {"Authorization": f"Bearer {token}"}
                kwargs = {"ping_interval": 20, "ping_timeout": 10, "close_timeout": 2}
                if url.startswith("wss://") and not bool(self.value("BODY_BRIDGE_VERIFY_TLS", True)):
                    kwargs["ssl"] = ssl._create_unverified_context()
                try:
                    socket = websockets.connect(url, additional_headers=headers, **kwargs)
                except TypeError:
                    socket = websockets.connect(url, extra_headers=headers, **kwargs)
                async with socket as ws:
                    await ws.send(json.dumps({"type": "hello", "device_id": self.value("BODY_BRIDGE_DEVICE_ID", "body-local"), "protocol": 1}))
                    self._bridge_connected.set()
                    with self._bridge_lock:
                        pending = list(self._bridge_latest.values())
                        self._bridge_latest.clear()
                    for message in pending:
                        try:
                            self.queue.put_nowait(message)
                        except Exception:
                            break
                    LOG.info("Body bridge connected to %s", url)

                    async def send_loop():
                        while not self.stop_event.is_set():
                            try:
                                message = await asyncio.to_thread(self.queue.get, True, 1)
                                await ws.send(json.dumps(message, ensure_ascii=False))
                            except Empty:
                                continue

                    async def receive_loop():
                        while not self.stop_event.is_set():
                            raw = await ws.recv()
                            message = json.loads(raw) if isinstance(raw, str) else raw
                            if isinstance(message, dict) and message.get("type") == "command":
                                self.execute_command(dict(message.get("command") or {}))

                    sender = asyncio.create_task(send_loop())
                    receiver = asyncio.create_task(receive_loop())
                    done, pending = await asyncio.wait(
                        {sender, receiver}, return_when=asyncio.FIRST_COMPLETED
                    )
                    for task in pending:
                        task.cancel()
                    await asyncio.gather(*done, return_exceptions=True)
                    self._bridge_connected.clear()
            except Exception as exc:
                self._bridge_connected.clear()
                LOG.warning("Body bridge disconnected: %s", exc)
            await asyncio.sleep(max(1, float(self.value("BODY_BRIDGE_RECONNECT_SECONDS", 3))))

    # ── world model (owned by the Body) ────────────────────────────────────

    @property
    def worldmodel(self):
        """The Body's embodied world model (lazy, owned by this process).

        The sensor source is resolved from config: robot > sim robot >
        HA fallback > null.  Re-resolve after a config change with
        ``reload_worldmodel_source()``.
        """
        if self._worldmodel is None:
            with self._worldmodel_lock:
                if self._worldmodel is None:
                    try:
                        from .worldmodel import EmbodiedWorldModel
                        src = self._resolve_worldmodel_source()
                        # Body LLM settings live with the Body process, while
                        # the world-model config remains the model's own data.
                        body_llm_config = {
                            key: self.value(key, value) for key, value in self.config.items()
                            if str(key).startswith("BODY_LLM_")
                        }
                        self._worldmodel = EmbodiedWorldModel(
                            body=None,
                            data_dir=str(ROOT / "data" / "body" / "worldmodel"),
                            config=body_llm_config,
                            source=src,
                        )
                        LOG.info("World model ready (source=%s)", getattr(src, "name", "?"))
                    except Exception as exc:
                        LOG.warning("World model unavailable: %s", exc)
        return self._worldmodel

    def reload_worldmodel_source(self) -> dict:
        """Re-resolve the sensor source (after a config change) and restart."""
        wm = self.worldmodel
        if wm is None:
            return {"ok": False, "error": "world model unavailable"}
        try:
            src = self._resolve_worldmodel_source()
            wm.stop()
            wm.source = src
            return {"ok": True, "source": src.name, "status": wm.status_summary()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _resolve_worldmodel_source(self):
        """Resolve the source selected by the Body's world-model config.

        ``data/body/worldmodel/config.json`` is authoritative for the
        simulator/bridge mode.  Previously the Body plugin priority could
        silently replace ``mode=sim`` with an unavailable robot endpoint.
        """
        from .worldmodel import SimRobotSource, resolve_source

        model_config_path = ROOT / "data" / "body" / "worldmodel" / "config.json"
        model_config: dict = {}
        try:
            payload = json.loads(model_config_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                model_config = payload
        except Exception:
            pass
        mode = str(model_config.get("mode") or "sim").strip().lower()
        usb_robot_selected = (
            bool(self.value("BODY_PLUGIN_ROBOT_ENABLED", False))
            and str(self.value("FNK0031_PLATFORM", "") or "").strip().lower() == "usb_serial"
        )
        if mode == "sim" and not usb_robot_selected:
            try:
                return SimRobotSource(
                    camera_interval=float(self.value("BODY_CAMERA_INTERVAL", 0.5) or 0.5),
                    mmwave_enabled=bool(self.value("BODY_PLUGIN_MMWAVE_RADAR_ENABLED", True)),
                    camera_width=int(self.value("BODY_CAMERA_WIDTH", 640) or 640),
                    camera_height=int(self.value("BODY_CAMERA_HEIGHT", 480) or 480),
                    camera_profile=str(self.value("BODY_CAMERA_PROFILE", "low_body_front") or "low_body_front"),
                    camera_provider=self._camera_provider,
                )
            except TypeError:
                # Keep compatibility with lightweight test doubles and older
                # Body plugin implementations that accept no constructor args.
                return SimRobotSource()
        if mode == "bridge":
            return None
        return resolve_source(self.config, self.latest)

    def plugins(self) -> list[dict]:
        return [
            {
                "id": "pc_camera",
                "label": "PC camera",
                "enabled": bool(self.value("BODY_CAMERA_STARTUP_ENABLED", False)),
                "role": "local webcam capture for Body perception",
                "settings_url": "/body/camera",
                "capture": self.camera_settings().get("capture"),
            },
            {
                "id": "fnk0031_wifi",
                "label": "FNK0031 Wi-Fi robot",
                "enabled": bool(self.value("BODY_PLUGIN_ROBOT_ENABLED", False)),
                "url": str(self.value("FNK0031_URL") or self.value("ROBOT_URL", "") or ""),
                "last_ok_age_s": round(time.time() - self._robot_last_ok, 1) if self._robot_last_ok else None,
                "last_error": self._robot_last_error,
                "role": "six-leg sensorimetry channel (Arduino/ESP bridge)",
                "platform": str(self.value("FNK0031_PLATFORM", "ventuno_q_gateway") or "ventuno_q_gateway"),
            },
            {
                "id": "fnk0050_wifi",
                "label": "FNK0050 Wi-Fi robot",
                "enabled": bool(self.value("BODY_PLUGIN_FNK0050_ENABLED", False)),
                "url": str(self.value("FNK0050_URL", "") or ""),
                "snn_enabled": bool(self.value("FNK0050_SNN_ENABLED", False)),
                "last_ok_age_s": round(time.time() - self._robot_last_ok, 1) if self._robot_last_ok else None,
                "last_error": self._robot_last_error,
                "role": "development quadruped channel (SNN locomotion experiments)",
            },
            {
                "id": "sim_robot",
                "enabled": bool(self.value("BODY_PLUGIN_SIM_ROBOT_ENABLED", False)),
                "role": "simulated robot sandbox (dev/test/demo)",
            },
            {
                "id": "home_assistant",
                "enabled": bool(self.value("BODY_PLUGIN_HOME_ASSISTANT_ENABLED", self.value("HOME_ASSISTANT_ENABLED", False))),
                "role": "auxiliary presence cues (not a sensorimetry channel)",
            },
            {
                "id": "mmwave_radar",
                "label": "mmWave radar",
                "enabled": bool(self.value("BODY_PLUGIN_MMWAVE_RADAR_ENABLED", False)),
                "url": str(self.value("MMWAVE_RADAR_URL", "") or ""),
                "role": "vendor-neutral metric targets and relative motion",
                "protocol": str(self.value("MMWAVE_RADAR_PROTOCOL", "http_json") or "http_json"),
            },
            {
                "id": "world_model",
                "enabled": bool(self.value("BODY_WORLDMODEL_ENABLED", False)),
                "role": "embodied perception, physical memory and prediction",
            },
        ]

    # ── lifecycle ───────────────────────────────────────────────────────────

    def run(self) -> None:
        LOG.info("Standalone Body host started with %s", CONFIG_PATH)
        self._start_http_endpoint()
        if self.http_server is None:
            LOG.error("Body host did not start; refusing to run a second sensor/plugin loop")
            return
        if bool(self.value("BODY_CAMERA_STARTUP_ENABLED", False)):
            self._configure_local_camera(start=True)
        if bool(self.value("BODY_ROS2_ENABLED", False)):
            ros_status = self._start_ros2_bridge()
            if ros_status.get("available"):
                LOG.info("ROS 2 observation bridge enabled (%s -> %s)", ros_status.get("input_topic"), ros_status.get("publish_topic"))
            else:
                LOG.warning("ROS 2 bridge enabled but unavailable: %s", ros_status.get("last_error"))
        threads = [threading.Thread(target=self.poll_loop, name="body-sensors", daemon=True)]
        # Keep the bridge loop alive even when disabled so the UI can enable it
        # without requiring a second process restart.
        threads.append(threading.Thread(target=self.bridge_loop, name="body-brain-bridge", daemon=True))
        for thread in threads:
            thread.start()
        if bool(self.value("BODY_WORLDMODEL_ENABLED", False)):
            wm = self.worldmodel
            if wm is not None:
                # Body startup exposes the world-model plugin but does not
                # start a simulation episode. The operator starts it through
                # the Body UI or POST /worldmodel/run.
                LOG.info("World model ready but paused (steps=%d)", wm.status_summary().get("steps"))
            else:
                LOG.warning("BODY_WORLDMODEL_ENABLED set but the world model could not be built (numpy/torch missing?)")
        while not self.stop_event.wait(1):
            pass

        wm = self._worldmodel
        if wm is not None:
            try:
                wm.stop()
            except Exception:
                LOG.exception("World model shutdown failed")
        if self.http_server is not None:
            self.http_server.shutdown()
            self.http_server.server_close()
        with self._local_camera_lock:
            if self._local_camera is not None:
                self._local_camera.stop()
        self._stop_ros2_bridge()
        self.stop_robot_sim()

    # ── HTTP endpoints ──────────────────────────────────────────────────────

    def _start_http_endpoint(self) -> None:
        host = str(self.value("BODY_HOST", "127.0.0.1") or "127.0.0.1")
        port = max(1, min(65535, int(self.value("BODY_PORT", 8766) or 8766)))
        owner = self
        from .body_gui import BODY_GUI_HTML

        class Handler(BaseHTTPRequestHandler):
            def _write_response(self, data: bytes) -> None:
                """Ignore a browser closing a polling request mid-response."""
                try:
                    self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    LOG.debug("Body HTTP client disconnected before response completed")

            def _send_html(self, html: str, status: int = 200, check_version: bool = True) -> None:
                version = hashlib.sha256(html.encode("utf-8")).hexdigest()[:16]
                version_script = (
                    f"<script>window.BODY_UI_VERSION='{version}';"
                    "(function(){async function check(){try{const r=await fetch('/ui-version',{cache:'no-store'});"
                    "if(!r.ok)return;const d=await r.json();if(d.version!==window.BODY_UI_VERSION){"
                    "const k='body-ui-reloaded-'+d.version;if(sessionStorage.getItem(k))return;"
                    "sessionStorage.setItem(k,'1');location.reload()}}catch(e){}}"
                    "setInterval(check,20000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)check()})})();</script>"
                )
                if check_version:
                    html = html.replace("</body></html>", version_script + "</body></html>", 1)
                data = html.encode("utf-8")
                try:
                    self.send_response(status)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self._write_response(data)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    LOG.debug("Body HTTP client disconnected before HTML response completed")

            def _send(self, payload, status: int = 200) -> None:
                data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
                try:
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self._write_response(data)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    LOG.debug("Body HTTP client disconnected before JSON response completed")

            def _read_body(self) -> dict:
                length = int(self.headers.get("Content-Length") or 0)
                if length <= 0:
                    return {}
                try:
                    return json.loads(self.rfile.read(length).decode("utf-8"))
                except Exception:
                    return {}

            def do_GET(self):  # noqa: N802
                path = self.path.split("?", 1)[0].rstrip("/") or "/"
                if path in {"", "/", "/body", "/worldmodel", "/camera", "/llm", "/robot", "/ros2", "/runtime"}:
                    self._send_html(BODY_GUI_HTML)
                elif path == "/quest":
                    quest_page = ROOT / "body_runtime_host" / "quest_vr.html"
                    self._send_html(quest_page.read_text(encoding="utf-8"), check_version=False)
                elif path == "/quest-hud-preview":
                    preview_page = ROOT / "body_runtime_host" / "quest_hud_preview.html"
                    self._send_html(preview_page.read_text(encoding="utf-8"), check_version=False)
                elif path == "/quest-hud-preview.js":
                    preview_script = ROOT / "body_runtime_host" / "quest-hud-preview.bundle.js"
                    try:
                        data = preview_script.read_bytes()
                        self.send_response(200)
                        self.send_header("Content-Type", "text/javascript; charset=utf-8")
                        self.send_header("Cache-Control", "no-store")
                        self.send_header("Content-Length", str(len(data)))
                        self.end_headers()
                        self._write_response(data)
                    except FileNotFoundError:
                        self._send({"error": "Quest HUD preview is not installed"}, 404)
                elif path == "/quest-vr.js":
                    bundle = ROOT / "body_runtime_host" / "quest-vr.bundle.js"
                    try:
                        data = bundle.read_bytes()
                        self.send_response(200)
                        self.send_header("Content-Type", "text/javascript; charset=utf-8")
                        self.send_header("Cache-Control", "no-store")
                        self.send_header("Content-Length", str(len(data)))
                        self.end_headers()
                        self._write_response(data)
                    except FileNotFoundError:
                        self._send({"error": "Quest VR renderer bundle is not installed"}, 404)
                elif path == "/ui-version":
                    version = hashlib.sha256(BODY_GUI_HTML.encode("utf-8")).hexdigest()[:16]
                    self._send({"version": version})
                elif path == "/health":
                    wm = owner._worldmodel
                    self._send({
                        "status": "ready",
                        "runtime": "independent",
                        "observations": len(owner.latest),
                        "bridge_enabled": bool(owner.value("BODY_BRIDGE_ENABLED", False)),
                        "config_path": str(CONFIG_PATH),
                        "robot": owner.robot_status(),
                        "ros2": owner.ros2_settings(),
                        "plugins": owner.plugins(),
                        "worldmodel": (
                            {"available": True, **wm.status_summary()}
                            if wm is not None
                            else {"available": False, "note": "not initialized (BODY_WORLDMODEL_ENABLED or first /worldmodel/* call)"}
                        ),
                    })
                elif path in {"/ros2/status", "/ros2/settings"}:
                    self._send(owner.ros2_settings())
                elif path == "/workflows/catalog":
                    self._send(owner.workflow_manager.catalog())
                elif path == "/workflows/templates/mobile-manipulation":
                    self._send(owner.workflow_manager.mobile_manipulation_demo())
                elif path == "/workflows":
                    self._send(owner.workflow_manager.list())
                elif path.startswith("/workflows/"):
                    parts = path.strip("/").split("/")
                    workflow_id = parts[1] if len(parts) > 1 else ""
                    try:
                        if len(parts) == 3 and parts[2] == "executions":
                            self._send(owner.workflow_manager.executions(workflow_id))
                        elif len(parts) == 2:
                            self._send(owner.workflow_manager.get(workflow_id))
                        else:
                            self._send({"error": "not found"}, 404)
                    except KeyError:
                        self._send({"error": "workflow not found"}, 404)
                elif path == "/plugins":
                    self._send({"plugins": owner.plugins()})
                elif path == "/brain-bridge":
                    self._send(owner.brain_bridge_settings())
                elif path == "/plugins/home_assistant/settings":
                    self._send(owner.home_assistant_settings())
                elif path == "/plugins/fnk0050_wifi/settings":
                    self._send(owner.fnk0050_settings())
                elif path == "/plugins/fnk0031_wifi/settings":
                    self._send(owner.fnk0031_settings())
                elif path == "/plugins/fnk0031_wifi/usb/status":
                    self._send(owner.fnk0031_usb_status())
                elif path == "/plugins/fnk0031_wifi/modules":
                    self._send(owner.fnk0031_modules())
                elif path == "/plugins/fnk0031_wifi/modules/status":
                    self._send(owner.fnk0031_module_status())
                elif path == "/plugins/fnk0031_wifi/diagnostic":
                    try:
                        self._send(json.loads(owner._fnk_diagnostic_path.read_text(encoding="utf-8")))
                    except (OSError, ValueError):
                        self._send({"status": "not_run", "schema": "fnk0031.hardware_diagnostic.v1"})
                elif path == "/plugins/fnk0031_wifi/controller":
                    self._send(owner.fnk0031_controller_status())
                elif path == "/plugins/fnk0031_wifi/experiment":
                    self._send(owner.fnk0031_experiment_status())
                elif path == "/robot-sim/status":
                    self._send(owner.robot_sim_status())
                elif path == "/deployment/status":
                    self._send({
                        "ok": True,
                        "contract": "pandorabox.body_bundle.v1",
                        "secrets_excluded": True,
                        "learned_model_optional": True,
                    })
                elif path == "/runtime/status":
                    try:
                        self._send(owner._repository_updater.status())
                    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
                        self._send({"available": False, "error": str(exc)}, 503)
                elif path == "/runtime/network":
                    self._send(owner.runtime_network_settings())
                elif path == "/worldmodel/scene-interpreter":
                    wm = owner.worldmodel
                    self._send(wm.scene_interpreter.status() if wm is not None else {"status": "unavailable"})
                elif path == "/body/llm":
                    self._send(owner.body_llm_settings())
                elif path == "/body/camera":
                    self._send(owner.camera_settings())
                elif path == "/body/camera/frame":
                    self._send(owner.camera_frame())
                elif path == "/body/camera/test-vlm":
                    self._send(owner.body_vlm_test_status())
                elif path == "/body/llm/models":
                    self._send(owner.body_llm_models())
                elif path == "/observations":
                    self._send({"observations": sorted(
                        owner.latest.values(),
                        key=lambda item: float(item.get("observed_at") or 0),
                        reverse=True,
                    )})
                elif path == "/config":
                    self._send({"config": {k: v for k, v in owner.config.items() if "TOKEN" not in k and "SECRET" not in k}})
                elif path == "/worldmodel/status":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                    else:
                        self._send(wm.status_summary())
                elif path == "/worldmodel/perception":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                    else:
                        self._send(wm.status_summary().get("perception") or {"available": False})
                elif path == "/worldmodel/map":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"available": False, "error": "world model unavailable"}, 503)
                    else:
                        self._send(wm.route_memory.snapshot())
                elif path == "/worldmodel/spatial-map":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"available": False, "error": "world model unavailable"}, 503)
                    else:
                        query = parse_qs(urlparse(self.path).query)
                        try:
                            limit = max(0, min(100_000, int((query.get("limit") or [5_000])[0])))
                        except (TypeError, ValueError):
                            limit = 5_000
                        self._send({
                            "available": True,
                            **wm.spatial_map.snapshot(limit=limit),
                            "last_update": dict(wm._last_spatial_map_update),
                        })
                elif path == "/worldmodel/semantic-splats":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"available": False, "error": "world model unavailable"}, 503)
                    else:
                        perception = (wm.status_summary().get("perception") or {})
                        self._send(perception.get("semantic_splats") or {
                            "contract": "body_semantic_splats.v1",
                            "status": "waiting_for_perception",
                            "groups": [],
                            "safety_authoritative": False,
                        })
                elif path == "/worldmodel/map/route":
                    wm = owner.worldmodel
                    query = parse_qs(urlparse(self.path).query)
                    target = str((query.get("target") or [""])[0]).strip()
                    if wm is None:
                        self._send({"available": False, "error": "world model unavailable"}, 503)
                    elif target == "start":
                        self._send(wm.route_memory.route_to_start())
                    else:
                        self._send(wm.route_memory.route_to(target))
                elif path == "/worldmodel/anchors":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                    else:
                        self._send(wm.anchors_payload())
                elif path == "/worldmodel/episodes":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                    else:
                        self._send(wm.recent_episodes(limit=12))
                elif path == "/worldmodel/context":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                    else:
                        self._send({"context": wm.context_for_brain()})
                elif path == "/worldmodel/evaluation":
                    self._send(owner.worldmodel_evaluation_status())
                elif path == "/worldmodel/sensorimotor-test":
                    self._send(owner.vlm_sensorimotor_test_status())
                elif path == "/worldmodel/capability-gate":
                    self._send(owner.worldmodel_capability_gate())
                elif path == "/worldmodel/plans/validate":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                        return
                    self._send(wm.plan_runtime.validate(self._read_body()))
                elif path == "/worldmodel/plans":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                    else:
                        self._send(wm.plan_payload())
                elif path == "/worldmodel/snapshot":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                    else:
                        wm.ensure_snapshot()
                        self._send(wm.plan_payload().get("latest_snapshot") or {"available": False})
                elif path == "/worldmodel/config":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                    else:
                        self._send(wm.config())
                else:
                    self._send({"error": "not found"}, 404)

            def do_POST(self):  # noqa: N802
                path = self.path.split("?", 1)[0].rstrip("/")
                if path == "/workflows":
                    try:
                        self._send({"ok": True, "workflow": owner.workflow_manager.save(self._read_body())})
                    except (ValueError, OSError) as exc:
                        self._send({"ok": False, "error": str(exc)}, 400)
                elif path.startswith("/workflows/") and path.endswith("/execute"):
                    workflow_id = path[len("/workflows/"):-len("/execute")].strip("/")
                    try:
                        self._send(owner.workflow_manager.execute(workflow_id))
                    except KeyError:
                        self._send({"error": "workflow not found"}, 404)
                    except (ValueError, OSError) as exc:
                        self._send({"status": "failed", "error": str(exc)}, 400)
                elif path.startswith("/workflows/") and path.endswith("/analyze"):
                    workflow_id = path[len("/workflows/"):-len("/analyze")].strip("/")
                    self._send(owner.analyze_workflow_execution(workflow_id))
                elif path == "/body/llm/embedding-check":
                    self._send(owner.test_body_embeddings(str(self._read_body().get("label") or "")))
                elif path == "/brain-bridge":
                    try:
                        self._send({"ok": True, "settings": owner.update_brain_bridge_settings(self._read_body())})
                    except (ValueError, OSError) as exc:
                        self._send({"ok": False, "error": str(exc)}, 400)
                elif path.startswith("/plugins/"):
                    plugin_id = path.rsplit("/", 1)[-1]
                    body = self._read_body()
                    if path == "/plugins/home_assistant/settings":
                        self._send(owner.update_home_assistant_settings(body))
                    elif path == "/plugins/fnk0050_wifi/settings":
                        self._send(owner.update_fnk0050_settings(body))
                    elif path == "/plugins/fnk0031_wifi/settings":
                        self._send(owner.update_fnk0031_settings(body))
                    elif path == "/plugins/fnk0031_wifi/modules":
                        self._send(owner.update_fnk0031_module(body))
                    elif path == "/plugins/fnk0031_wifi/diagnostic":
                        self._send(owner.fnk0031_diagnostic())
                    elif path == "/plugins/fnk0031_wifi/controller/step":
                        self._send(owner.fnk0031_controller_step())
                    elif path == "/plugins/fnk0031_wifi/experiment/start":
                        self._send(owner.start_fnk0031_experiment())
                    elif path == "/plugins/home_assistant/discover":
                        try:
                            entities = owner.discover()
                            owner.save_discovery(entities)
                            self._send({"ok": True, "status": "ok", "count": len(entities), "entities": entities})
                        except Exception as exc:
                            self._send({"ok": False, "message": str(exc), "entities": []}, 502)
                    else:
                        try:
                            self._send(owner.set_plugin_enabled(plugin_id, bool(body.get("enabled", False))))
                        except ValueError as exc:
                            self._send({"error": str(exc)}, 400)
                elif path == "/body/llm":
                    self._send(owner.update_body_llm_settings(self._read_body()))
                elif path == "/ros2/settings":
                    try:
                        self._send(owner.update_ros2_settings(self._read_body()))
                    except (OSError, ValueError) as exc:
                        self._send({"ok": False, "error": str(exc)}, 400)
                elif path == "/body/camera":
                    try:
                        self._send(owner.update_camera_settings(self._read_body()))
                    except (TypeError, ValueError) as exc:
                        self._send({"ok": False, "error": str(exc)}, 400)
                elif path == "/body/camera/capture":
                    body = self._read_body()
                    self._send(owner.set_camera_capture(_payload_bool(body.get("enabled"))))
                elif path == "/body/camera/test-vlm":
                    self._send(owner.test_body_vlm())
                elif path == "/body/camera/test-vlm/start":
                    mode = str(self._read_body().get("mode", "single") or "single")
                    self._send(owner.start_body_vlm_test(mode=mode), 202)
                elif path == "/body/llm/restart":
                    try:
                        is_loopback = ipaddress.ip_address(self.client_address[0].split("%", 1)[0]).is_loopback
                    except ValueError:
                        is_loopback = False
                    if not is_loopback:
                        self._send({"ok": False, "status": "forbidden", "error": "GenieX restart is restricted to local Body UI requests."}, 403)
                        return
                    result = owner.restart_geniex()
                    self._send(result, 200 if result.get("ok") else 409)
                elif path == "/deployment/check":
                    self._send(owner.deployment_check(self._read_body()))
                elif path == "/deployment/push":
                    self._send(owner.deployment_push(self._read_body()))
                elif path == "/deployment/activate":
                    self._send(owner.deployment_activate(self._read_body()))
                elif path == "/deployment/restart":
                    self._send(owner.deployment_restart(self._read_body()))
                elif path in {"/runtime/check", "/runtime/pull"}:
                    try:
                        result = owner._repository_updater.check() if path.endswith("/check") else owner._repository_updater.pull()
                        self._send(result, 200 if result.get("ok") else 409)
                    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
                        self._send({"ok": False, "error": str(exc)}, 502)
                elif path == "/runtime/network":
                    try:
                        self._send(owner.update_runtime_network_settings(self._read_body()))
                    except (OSError, ValueError) as exc:
                        self._send({"ok": False, "error": str(exc)}, 400)
                elif path == "/robot-sim/start":
                    self._send(owner.start_robot_sim(self._read_body()))
                elif path == "/robot-sim/stop":
                    self._send(owner.stop_robot_sim())
                elif path == "/robot-sim/use":
                    self._send(owner.use_robot_sim())
                elif path == "/worldmodel/step":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                        return
                    self._send(wm.step())
                elif path == "/worldmodel/run":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                        return
                    command = self._read_body()
                    running = bool(command.get("running", False))
                    if running:
                        wm.start(shuffle=bool(command.get("shuffle", False)))
                    else:
                        wm.stop()
                    self._send(wm.status_summary())
                elif path == "/worldmodel/reset":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                        return
                    body = self._read_body()
                    self._send(wm.reset(clear_memory=bool(body.get("clear_memory", False))))
                elif path == "/worldmodel/evaluation/run":
                    self._send(owner.start_worldmodel_evaluation(self._read_body()))
                elif path == "/worldmodel/sensorimotor-test/run":
                    self._send(owner.start_vlm_sensorimotor_test(self._read_body()), 202)
                elif path == "/worldmodel/perception/video-upload":
                    self._send(owner.upload_video_replay(self._read_body()))
                elif path == "/worldmodel/perception/video-replay":
                    self._send(owner.run_video_lidar_replay(self._read_body()))
                elif path == "/worldmodel/config":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                        return
                    body = self._read_body()
                    values = body.get("values") if isinstance(body.get("values"), dict) else body
                    self._send(wm.update_config(values or {}))
                elif path == "/worldmodel/reload":
                    self._send(owner.reload_worldmodel_source())
                elif path == "/worldmodel/plans/validate":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                        return
                    self._send(wm.plan_runtime.validate(self._read_body()))
                elif path == "/worldmodel/plans":
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                        return
                    self._send(wm.submit_plan(self._read_body()))
                elif path.startswith("/worldmodel/plans/") and path.endswith("/cancel"):
                    wm = owner.worldmodel
                    if wm is None:
                        self._send({"error": "world model unavailable"}, 503)
                        return
                    plan_id = path[len("/worldmodel/plans/"):-len("/cancel")].strip("/")
                    payload = self._read_body()
                    self._send(wm.cancel_plan(plan_id, str(payload.get("reason") or "cancelled by operator")))
                else:
                    self._send({"error": "not found"}, 404)

            def do_DELETE(self):  # noqa: N802
                path = self.path.split("?", 1)[0].rstrip("/")
                if path.startswith("/workflows/"):
                    workflow_id = path[len("/workflows/"):].strip("/")
                    removed = owner.workflow_manager.delete(workflow_id)
                    self._send({"ok": removed}, 200 if removed else 404)
                else:
                    self._send({"error": "not found"}, 404)

            def log_message(self, format, *args):
                LOG.debug("Body HTTP: " + format, *args)

        try:
            self.http_server = ThreadingHTTPServer((host, port), Handler)
            threading.Thread(target=self.http_server.serve_forever, name="body-http", daemon=True).start()
            LOG.info("Body endpoint listening on http://%s:%d/", host, port)
        except OSError as exc:
            LOG.warning("Body endpoint unavailable on %s:%d: %s", host, port, exc)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    _load_dotenv()
    host = BodyHost()
    signal.signal(signal.SIGINT, lambda *_: host.stop_event.set())
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, lambda *_: host.stop_event.set())
    host.run()
    LOG.info("Standalone Body host stopped")
