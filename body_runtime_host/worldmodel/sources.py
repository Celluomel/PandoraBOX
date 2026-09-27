"""Sensor sources — how the Body gets observations, body state, and executes actions.

The world model does not care *where* the sensors come from.  A source is any
object implementing:

    name        -> str
    observe()   -> Observation          (scene + text + body-relative data)
    body_state()-> BodyState            (position, heading, capabilities)
    execute(action: Action) -> (Observation, Outcome)
    status()    -> dict                 (for the dashboard / brain)

Sources (priority order, see ``resolve_source``):

    1. RobotHttpSource   — a real robot exposing the Lumina robot protocol
                           (GET /sensors, POST /command).  This is the MAIN
                           sensorimetry channel: the body is plugged into
                           robot sensors, not into a smart home.
    2. SimRobotSource    — a simulated robot (the SimulatedRoom sandbox),
                           used for tests, demos and development without a
                           physical robot.
    3. HA fallback       — coarse observations from Home Assistant presence
                           sensors (auxiliary only; never the main channel).
    4. NullSource        — no sensors attached: the loop stays alive but
                           learns nothing (honest empty state).
"""
from __future__ import annotations

import json
import logging
import math
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .sim_world import SimulatedRoom
from .spatial import LocalMapReference, geo_fix
from .types import Action, BodyState, Observation, Outcome, SceneObject

logger = logging.getLogger(__name__)

DEFAULT_CAPABILITIES = {
    "reach": 1.8,
    "speed": 1.0,
    "strength": 20.0,
    "gripper": 1.0,
}


def _http_json(method: str, url: str, payload: Optional[Dict[str, Any]] = None,
               token: str = "", timeout: float = 5.0) -> Any:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else None


class NullSource:
    """No sensors attached.  Keeps the world model loop alive and honest."""

    name = "null"

    def __init__(self, note: str = "no sensor source attached"):
        self.note = note
        self.last_error = ""

    def observe(self) -> Observation:
        return Observation(subject="scene", text=self.note, source=self.name, kind="none")

    def body_state(self) -> BodyState:
        return BodyState(position=[0.0, 0.0, 0.0], capabilities=dict(DEFAULT_CAPABILITIES))

    def execute(self, action: Action) -> Tuple[Observation, Outcome]:
        self.last_error = f"{action.type} not executable (no actuators)"
        return self.observe(), Outcome(kind="neutral", reward=0.0, description=self.last_error)

    def execute_authorized(self, action: Action) -> Tuple[Observation, Outcome]:
        return self.execute(action)

    def status(self) -> Dict[str, Any]:
        return {"source": self.name, "note": self.note, "last_error": self.last_error}


class SimRobotSource:
    """A simulated robot: the SimulatedRoom sandbox as sensor + actuator.

    Used for tests, demos and offline development.  It speaks the *exact*
    same interface as a real robot source, so switching between them is a
    config change, not a code change.
    """

    name = "sim_robot"

    def __init__(
        self,
        room: Optional[SimulatedRoom] = None,
        camera_interval: float = 0.5,
        simulation_dt_s: float = 1.0,
    ):
        self.room = room or SimulatedRoom(simulation_dt_s=simulation_dt_s)
        self.last_error = ""
        self.camera_interval = max(0.05, float(camera_interval or 0.5))
        self._last_camera_at = 0.0
        self._last_camera: Dict[str, Any] = {}
        self._last_pose: Optional[Tuple[float, float]] = None
        self._last_mobile_pose: Optional[Tuple[float, float]] = None
        self._last_heading: Optional[float] = None
        self._last_room_step: Optional[int] = None
        self._last_pose_at = 0.0
        self._last_motion_speed = 0.0
        self._last_angular_speed = 0.0
        self._last_relative_speed = 0.0
        self._last_closing_speed = 0.0
        self._last_effective_camera_interval = self.camera_interval

    def _effective_camera_interval(self, now: float) -> float:
        """Sample faster when the simulated Body itself is moving faster.

        The camera cadence follows measured odometry, rather than a fixed
        object list or a guessed action name.  A safety margin can further
        increase sampling without changing the physical controller.
        """
        state = self.room.body_state()
        position = (float(state.position[0]), float(state.position[1]))
        heading = float(state.orientation)
        mobile = self.room.objects.get("mobile_obstacle")
        mobile_position = (
            (float(mobile["x"]), float(mobile["y"])) if isinstance(mobile, dict) else None
        )
        step_delta = (
            int(self.room.steps) - int(self._last_room_step)
            if self._last_room_step is not None else 0
        )
        # Simulation actions have a stable physical duration of one world
        # step. Use that unit rather than wall-clock HTTP latency.
        elapsed = float(step_delta) if step_delta > 0 else 0.0
        angular_speed = 0.0
        if elapsed > 0.0:
            body_velocity = (
                (position[0] - self._last_pose[0]) / elapsed,
                (position[1] - self._last_pose[1]) / elapsed,
            )
            self._last_motion_speed = math.hypot(*body_velocity)
            if self._last_heading is not None:
                heading_delta = math.atan2(
                    math.sin(heading - self._last_heading),
                    math.cos(heading - self._last_heading),
                )
                angular_speed = abs(heading_delta) / elapsed
            if self._last_mobile_pose is not None and mobile_position is not None:
                mobile_velocity = (
                    (mobile_position[0] - self._last_mobile_pose[0]) / elapsed,
                    (mobile_position[1] - self._last_mobile_pose[1]) / elapsed,
                )
                relative_velocity = (
                    body_velocity[0] - mobile_velocity[0],
                    body_velocity[1] - mobile_velocity[1],
                )
                self._last_relative_speed = math.hypot(*relative_velocity)
                separation = (mobile_position[0] - position[0], mobile_position[1] - position[1])
                length = math.hypot(*separation)
                self._last_closing_speed = max(
                    0.0,
                    -(relative_velocity[0] * separation[0] + relative_velocity[1] * separation[1]) / length,
                ) if length > 1e-3 else 0.0
        self._last_pose = position
        self._last_mobile_pose = mobile_position
        self._last_heading = heading
        self._last_room_step = int(self.room.steps)
        self._last_pose_at = now
        reference = max(0.1, float(state.capabilities.get("speed", 1.0) or 1.0))
        effective_speed = max(self._last_motion_speed, self._last_relative_speed, self._last_closing_speed, angular_speed)
        self._last_angular_speed = angular_speed
        interval = self.camera_interval / (1.0 + min(2.0, effective_speed / reference))
        status = self.room.status()
        distance = status.get("mobile_obstacle_distance")
        clearance = float(state.capabilities.get("mobile_obstacle_clearance", 1.3) or 1.3)
        margin = float(state.capabilities.get("mobile_obstacle_planning_margin", 0.0) or 0.0)
        if distance is not None and margin > 0.0:
            gap = max(0.0, float(distance) - clearance)
            risk = max(0.0, min(1.0, (margin - gap) / margin))
            if risk >= 0.5:
                interval = min(interval, self.camera_interval * 0.35)
        self._last_effective_camera_interval = max(0.05, min(self.camera_interval, interval))
        return self._last_effective_camera_interval

    def observe(self) -> Observation:
        now = time.time()
        interval = self._effective_camera_interval(now)
        capture = not self._last_camera or now - self._last_camera_at >= interval
        observation = self.room.observe(include_camera=capture)
        if capture and observation.modalities.get("camera"):
            self._last_camera = dict(observation.modalities["camera"])
            self._last_camera["captured_at"] = now
            self._last_camera["motion_speed"] = round(self._last_motion_speed, 4)
            self._last_camera["angular_speed_rad_s"] = round(self._last_angular_speed, 4)
            self._last_camera["heading_deg"] = round(math.degrees(float(self.room.body_state().orientation)), 3)
            self._last_camera["capture_interval_s"] = round(interval, 3)
            self._last_camera_at = now
        elif self._last_camera:
            observation.modalities["camera"] = dict(self._last_camera)
            observation.modalities["camera"]["stale_age_s"] = round(max(0.0, now - self._last_camera_at), 3)
        return observation

    def body_state(self) -> BodyState:
        return self.room.body_state()

    def execute(self, action: Action) -> Tuple[Observation, Outcome]:
        if action.type == "reset":
            self.room.reset()
            return self.observe(), Outcome(kind="success", reward=0.0, description="sim robot reset")
        return self.room.step(action)

    def execute_authorized(self, action: Action) -> Tuple[Observation, Outcome]:
        return self.execute(action)

    def reset(self) -> None:
        self.room.reset()
        self._last_camera = {}
        self._last_camera_at = 0.0
        self._last_pose = None
        self._last_mobile_pose = None
        self._last_heading = None
        self._last_room_step = None
        self._last_pose_at = 0.0
        self._last_motion_speed = 0.0
        self._last_angular_speed = 0.0
        self._last_relative_speed = 0.0
        self._last_closing_speed = 0.0
        self._last_effective_camera_interval = self.camera_interval

    def status(self) -> Dict[str, Any]:
        # An action may have completed since the last sensor poll. Refresh
        # motion telemetry before publishing status so a final turn is not
        # invisible until the next world-model step.
        self._effective_camera_interval(time.time())
        st = dict(self.room.status())
        st["source"] = self.name
        st["last_error"] = self.last_error
        st["motion_speed"] = round(self._last_motion_speed, 4)
        st["angular_speed_rad_s"] = round(self._last_angular_speed, 4)
        st["angular_speed_deg_s"] = round(math.degrees(self._last_angular_speed), 3)
        st["heading_deg"] = round(math.degrees(float(self.room.body_state().orientation)), 3)
        st["relative_speed"] = round(self._last_relative_speed, 4)
        st["closing_speed"] = round(self._last_closing_speed, 4)
        st["camera_interval_s"] = round(self._last_effective_camera_interval, 3)
        st["simulation_time_s"] = round(float(self.room.simulation_time_s), 3)
        st["simulation_dt_s"] = float(self.room.simulation_dt_s)
        return st


class RobotHttpSource:
    """A real robot over the Lumina robot protocol (HTTP + JSON).

    The robot exposes (the robot side is what you plug into Lumina):

        GET  {ROBOT_URL}/sensors
        -> {
             "position": [x, y, z],
             "orientation": 0.78,            # radians
             "capabilities": {"reach": 1.8, "strength": 20, "gripper": 1},
             "objects": [{"id","label","kind","x","y","z"?,"mass","size","props"?}],
             "carrying": null,
             "battery": 0.8,
             "timestamp": 1713000000.0
           }

        POST {ROBOT_URL}/command
             {"type": "forward", "target": null, "params": {...}}
        -> {
             "outcome": "success" | "failure" | "danger" | "neutral",
             "reward": 0.0,
             "description": "moved forward"
           }

        GET  {ROBOT_URL}/health   (optional, for ping)

    Security: ``ROBOT_TOKEN`` (optional) is sent as a Bearer token.  The
    endpoint may be hosted by the Linux side of an Arduino VENTUNO Q. In our
    FNK0031 deployment the VENTUNO Q is the network/AI gateway, while the
    FNK0031 board remains the servo and motor controller behind it. The
    gateway must forward the validated command to the FNK0031 board and keep
    the FNK0031 local stop path available.
    """

    name = "robot"

    def __init__(
        self,
        url: str,
        token: str = "",
        timeout: float = 5.0,
        capabilities: Optional[Dict[str, float]] = None,
        actuation_enabled: bool = False,
    ):
        self.url = str(url or "").rstrip("/")
        self.token = str(token or "")
        self.timeout = float(timeout or 5.0)
        self.capabilities = dict(capabilities or DEFAULT_CAPABILITIES)
        self.actuation_enabled = bool(actuation_enabled)
        self.last_error = ""
        self.last_ok: Optional[float] = None
        self.last_latency_ms: Optional[float] = None
        self._last_obs: Optional[Observation] = None
        self._last_body: Optional[BodyState] = None
        self._spatial = LocalMapReference()

    # ── protocol ────────────────────────────────────────────────────────────

    def ping(self) -> bool:
        try:
            _http_json("GET", f"{self.url}/health", token=self.token, timeout=self.timeout)
            self.last_error = ""
            return True
        except Exception:
            # /health is optional — a /sensors probe is the real liveness test
            try:
                self._raw_sensors()
                self.last_error = ""
                return True
            except Exception as exc:
                self.last_error = f"robot unreachable: {exc}"
                return False

    def _raw_sensors(self) -> Dict[str, Any]:
        t0 = time.time()
        try:
            payload = _http_json(
                "GET", f"{self.url}/sensors",
                token=self.token, timeout=self.timeout,
            )
        finally:
            self.last_latency_ms = round((time.time() - t0) * 1000.0, 1)
        if not isinstance(payload, dict):
            raise ValueError("robot /sensors returned a non-object payload")
        return payload

    def _scene_from_payload(self, payload: Dict[str, Any]) -> List[SceneObject]:
        out: List[SceneObject] = []
        for raw in payload.get("objects") or []:
            if not isinstance(raw, dict):
                continue
            raw_geo = raw.get("geo") or raw.get("gps") or raw.get("gnss") or {}
            explicit_position = raw.get("position") or any(key in raw for key in ("x", "y", "z"))
            pos = raw.get("position") or [raw.get("x", 0.0), raw.get("y", 0.0), raw.get("z", 0.0)]
            if not explicit_position and geo_fix(raw_geo):
                pos = self._spatial.project(raw_geo) or [0.0, 0.0, 0.0]
            try:
                pos = [float(pos[0]), float(pos[1]), float(pos[2])] if len(pos) >= 3 else [float(pos[0]), float(pos[1]), 0.0]
            except Exception:
                pos = [0.0, 0.0, 0.0]
            out.append(SceneObject(
                id=str(raw.get("id") or raw.get("label") or f"obj{len(out)}"),
                label=str(raw.get("label") or raw.get("id") or "object"),
                kind=str(raw.get("kind") or "object"),
                position=pos,
                size=float(raw.get("size", 1.0) or 1.0),
                mass=float(raw.get("mass", 1.0) or 1.0),
                props={k: v for k, v in (raw.get("props") or {}).items()},
                coordinate_frame=str(raw.get("coordinate_frame") or raw.get("frame") or payload.get("coordinate_frame") or ("local_map" if geo_fix(raw_geo) else "local_map")),
                position_source=str(raw.get("position_source") or raw.get("location_source") or ("gnss_projected" if geo_fix(raw_geo) and not explicit_position else "perception")),
                position_accuracy_m=(float(raw["position_accuracy_m"]) if raw.get("position_accuracy_m") is not None else None),
                geo=dict(raw_geo),
            ))
        return out

    # ── source protocol ─────────────────────────────────────────────────────

    def observe(self) -> Observation:
        try:
            payload = self._raw_sensors()
            body_geo = payload.get("geo") or payload.get("gps") or payload.get("gnss") or {}
            explicit_position = payload.get("position") is not None
            pos = payload.get("position") or [0.0, 0.0, 0.0]
            position_source = str(payload.get("position_source") or payload.get("location_source") or "odometry")
            if not explicit_position and geo_fix(body_geo):
                pos = self._spatial.project(body_geo) or [0.0, 0.0, 0.0]
                position_source = "gnss_projected"
            pos = [float(pos[0]), float(pos[1]), float(pos[2])] if len(pos) >= 3 else [float(pos[0]), float(pos[1]), 0.0]
            # Anchor the local map on the robot fix before projecting object
            # fixes; an object must never become the map origin by accident.
            scene = self._scene_from_payload(payload)
            if payload.get("capabilities"):
                for k, v in payload["capabilities"].items():
                    try:
                        self.capabilities[str(k)] = float(v)
                    except Exception:
                        pass
            carrying = payload.get("carrying")
            text_parts = [
                f"Robot body at ({pos[0]:.1f},{pos[1]:.1f}) heading {math.degrees(float(payload.get('orientation', 0.0))):.0f}deg."
            ]
            if carrying:
                text_parts.append(f"Carrying {carrying}.")
            if scene:
                text_parts.append("Scene: " + ", ".join(f"{o.label} ({o.kind})" for o in scene) + ".")
            else:
                text_parts.append("Scene: empty.")
            battery = payload.get("battery")
            if battery is not None:
                text_parts.append(f"Battery {float(battery):.0%}.")
            obs = Observation(
                subject="scene",
                value=None,
                source=self.name,
                kind="scene",
                confidence=float(payload.get("confidence", 1.0)),
                timestamp=float(payload.get("timestamp") or time.time()),
                scene=scene,
                text=" ".join(text_parts),
                modalities=dict(
                    payload.get("modalities")
                    or payload.get("perception")
                    or {
                        key: payload[key]
                        for key in ("camera", "vision", "lidar", "point_cloud")
                        if key in payload
                    }
                ),
            )
            body = BodyState(
                position=pos,
                orientation=float(payload.get("orientation", 0.0)),
                posture={"carrying": carrying, "battery": battery,
                         "imu": payload.get("imu") or payload.get("imu_data") or {},
                         "snn": payload.get("snn") or {}},
                capabilities=dict(self.capabilities),
                timestamp=obs.timestamp,
                coordinate_frame=str(payload.get("coordinate_frame") or payload.get("frame") or "local_map"),
                position_source=position_source,
                position_accuracy_m=(float(payload["position_accuracy_m"]) if payload.get("position_accuracy_m") is not None else None),
                geo=dict(body_geo),
            )
            self.last_error = ""
            self.last_ok = time.time()
            self._last_obs, self._last_body = obs, body
            return obs
        except Exception as exc:
            self.last_error = str(exc)
            logger.warning("[robot] sensors poll failed: %s", exc)
            # Serve the last good frame (stale) rather than crashing the loop.
            if self._last_obs is not None:
                return self._last_obs
            return NullSource("robot unreachable").observe()

    def body_state(self) -> BodyState:
        if self._last_body is None:
            self.observe()
        return self._last_body or BodyState(capabilities=dict(self.capabilities))

    def execute(self, action: Action) -> Tuple[Observation, Outcome]:
        # The autonomous world-model loop must never actuate a physical robot.
        # Only the explicit Body command path may call execute_authorized().
        return self.observe(), Outcome(
            kind="neutral", reward=0.0,
            description="physical actuation requires an approved Body command",
        )

    def execute_authorized(self, action: Action) -> Tuple[Observation, Outcome]:
        if not self.actuation_enabled:
            return self.observe(), Outcome(
                kind="neutral", reward=0.0,
                description="physical actuation disabled in Body configuration",
            )
        try:
            result = _http_json(
                "POST", f"{self.url}/command",
                payload={"type": action.type, "target": action.target, "params": action.params},
                token=self.token, timeout=self.timeout,
            ) or {}
            outcome = Outcome(
                kind=str(result.get("outcome") or "neutral"),
                reward=float(result.get("reward", 0.0)),
                description=str(result.get("description") or ""),
            )
            self.last_error = ""
            return self.observe(), outcome
        except Exception as exc:
            self.last_error = f"command failed: {exc}"
            logger.warning("[robot] command %s failed: %s", action.type, exc)
            return self.observe(), Outcome(kind="failure", reward=-0.1, description=self.last_error)

    def status(self) -> Dict[str, Any]:
        age = round(time.time() - self.last_ok, 1) if self.last_ok else None
        return {
            "source": self.name,
            "url": self.url,
            "token_set": bool(self.token),
            "actuation_enabled": self.actuation_enabled,
            "last_ok_age_s": age,
            "last_latency_ms": self.last_latency_ms,
            "last_error": self.last_error,
        }


class FNK0050WifiSource(RobotHttpSource):
    """Development adapter for an FNK0050 Wi-Fi robot.

    The hardware remains optional. Its firmware can expose the same compact
    JSON contract as the Body robot adapter while keeping FNK0050 telemetry
    distinct for locomotion and spiking-neural-network experiments.
    """

    name = "fnk0050_wifi"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(
            url=str(config.get("FNK0050_URL", "") or ""),
            token=str(config.get("FNK0050_TOKEN", "") or ""),
            timeout=float(config.get("FNK0050_TIMEOUT", 5.0) or 5.0),
            capabilities=config.get("FNK0050_CAPABILITIES") or DEFAULT_CAPABILITIES,
            actuation_enabled=bool(config.get("FNK0050_ACTUATION_ENABLED", False)),
        )


class FNK0031WifiSource(RobotHttpSource):
    """FNK0031 six-leg development profile.

    The Mega 2560 remains a motor/sensor endpoint. The Body host owns the
    higher-rate SNN/CPG loop and sends validated motion commands through the
    same transport, which also works with an ESP Wi-Fi bridge.
    """

    name = "fnk0031_wifi"

    def __init__(self, config: Dict[str, Any]):
        url = str(config.get("FNK0031_URL") or config.get("ROBOT_URL", "") or "")
        token = str(config.get("FNK0031_TOKEN") or config.get("ROBOT_TOKEN", "") or "")
        super().__init__(
            url=url,
            token=token,
            timeout=float(config.get("FNK0031_TIMEOUT", config.get("ROBOT_TIMEOUT", 5.0)) or 5.0),
            capabilities={"reach": 0.7, "speed": 0.6, "strength": 2.0, "gripper": 0.0, "legs": 6},
            actuation_enabled=bool(config.get("FNK0031_ACTUATION_ENABLED", config.get("BODY_ACTUATION_ENABLED", False))),
        )
        self.snn_enabled = bool(config.get("FNK0031_SNN_ENABLED", False))
        self.snn_controller = None
        if self.snn_enabled:
            try:
                from body_runtime_host.locomotion import FNK0031LocomotionController
                self.snn_controller = FNK0031LocomotionController(
                    Path("data/body/locomotion/fnk0031_hardware.npz")
                )
            except Exception as exc:
                self.last_error = f"SNN controller unavailable: {exc}"
                logger.warning("[fnk0031] SNN controller unavailable: %s", exc)

    def execute_authorized(self, action: Action) -> Tuple[Observation, Outcome]:
        # The SNN creates a bounded gait command; this method remains the only
        # place where it can reach the physical adapter.
        if self.snn_controller is not None and action.type in {"forward", "backward", "turn_left", "turn_right"}:
            imu = (self._last_body.posture.get("imu") if self._last_body else None)
            learned = self.snn_controller.step(imu=imu, gait=action.type, simulate=False)
            action = Action(type=action.type, target=action.target,
                            params={**action.params, "gait": action.type, "snn": learned})
        return super().execute_authorized(action)


class HAFallbackSource:
    """Coarse observations from Home Assistant presence sensors (auxiliary).

    This is deliberately a *fallback*: a smart-home presence feed carries no
    scene geometry, no objects, no actuation — it is not a sensorimetry
    channel, only a weak environmental cue.
    """

    name = "home_assistant"

    def __init__(self, latest: Dict[str, Dict[str, Any]]):
        # ``latest`` is the BodyHost's observation store (entity_id -> item)
        self.latest = latest
        self.last_error = ""

    def observe(self) -> Observation:
        items = list(self.latest.values())

        def _val(item, key, default=None):
            if isinstance(item, dict):
                return item.get(key, default)
            return getattr(item, key, default)

        items.sort(key=lambda i: _val(i, "observed_at", 0) or 0, reverse=True)
        lines = []
        for i in items[:10]:
            label = _val(i, "label") or _val(i, "subject") or _val(i, "entity_id") or "unknown"
            value = _val(i, "signal") or _val(i, "value") or _val(i, "state")
            lines.append(f"{label}={value}")
        text = ("Home Assistant presence cues: " + "; ".join(lines) + ".") if lines \
            else "No Home Assistant observations available."
        return Observation(
            subject="presence", value=None, source="home_assistant",
            kind="presence", confidence=0.6, text=text, scene=[],
        )

    def body_state(self) -> BodyState:
        # A smart home gives no body pose — the body stays at origin with
        # conservative capabilities.  This source is for *context*, not control.
        return BodyState(position=[0.0, 0.0, 0.0], capabilities={
            "reach": 1.0, "speed": 0.0, "strength": 0.0, "gripper": 0.0,
        })

    def execute(self, action: Action) -> Tuple[Observation, Outcome]:
        return self.observe(), Outcome(
            kind="neutral", reward=0.0,
            description=f"HA fallback has no actuators; '{action.type}' not executed",
        )

    def execute_authorized(self, action: Action) -> Tuple[Observation, Outcome]:
        return self.execute(action)

    def status(self) -> Dict[str, Any]:
        return {
            "source": self.name,
            "observations": len(self.latest),
            "last_error": self.last_error,
            "note": "auxiliary context only (no scene, no actuators)",
        }


# ── resolution ───────────────────────────────────────────────────────────────


def resolve_source(config: Dict[str, Any], latest: Optional[Dict[str, Dict[str, Any]]] = None) -> Any:
    """Pick the active sensor source from Body config.

    Priority: robot → sim robot → HA fallback → null.
    """
    config = config or {}
    # 1) FNK0050 development channel (explicitly preferred when enabled).
    if bool(config.get("BODY_PLUGIN_FNK0050_ENABLED", False)):
        url = str(config.get("FNK0050_URL", "") or "").strip()
        if url:
            return FNK0050WifiSource(config)
        logger.warning("[body] FNK0050 plugin enabled but FNK0050_URL is empty — falling through")
    # 2) FNK0031 six-leg development channel.
    if bool(config.get("BODY_PLUGIN_ROBOT_ENABLED", False)):
        url = str(config.get("FNK0031_URL") or config.get("ROBOT_URL", "") or "").strip()
        if url:
            return FNK0031WifiSource(config)
        logger.warning("[body] FNK0031 plugin enabled but FNK0031_URL/ROBOT_URL is empty — falling through")
    # 3) simulated robot (development / tests / demos)
    if bool(config.get("BODY_PLUGIN_SIM_ROBOT_ENABLED", False)):
        return SimRobotSource(camera_interval=float(config.get("BODY_CAMERA_INTERVAL", 0.5) or 0.5))
    # 4) HA fallback (auxiliary context)
    if latest is not None and bool(config.get("BODY_PLUGIN_HOME_ASSISTANT_ENABLED",
                                             config.get("HOME_ASSISTANT_ENABLED", False))):
        return HAFallbackSource(latest)
    # 5) nothing attached
    return NullSource("no sensor source enabled (set FNK0050_URL, ROBOT_URL, or BODY_PLUGIN_SIM_ROBOT_ENABLED)")
