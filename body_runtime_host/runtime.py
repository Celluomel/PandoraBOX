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
import json
import logging
import os
import signal
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Empty, Queue
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

LOG = logging.getLogger("lumina.body")
ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "body" / "config.json"


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


class BodyHost:
    def __init__(self) -> None:
        self.stop_event = threading.Event()
        self.config = self._load_config()
        self.latest: dict[str, dict] = {}
        self.queue: Queue[dict] = Queue(maxsize=256)
        self.bridge_thread: threading.Thread | None = None
        self.http_server: ThreadingHTTPServer | None = None
        self._worldmodel = None
        self._worldmodel_lock = threading.Lock()
        self._robot_last_ok: float | None = None
        self._robot_last_error = ""

    # ── config ──────────────────────────────────────────────────────────────

    def _load_config(self) -> dict:
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
        for key in ("HOME_ASSISTANT_TOKEN", "BODY_BRIDGE_TOKEN", "ROBOT_TOKEN"):
            if safe.get(key) and not str(safe[key]).startswith("@env:"):
                safe[key] = f"@env:{key}"
        CONFIG_PATH.write_text(json.dumps(safe, indent=2, ensure_ascii=False), encoding="utf-8")

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

    def set_plugin_enabled(self, plugin_id: str, enabled: bool) -> dict:
        fields = {
            "home_assistant": "BODY_PLUGIN_HOME_ASSISTANT_ENABLED",
            "robot": "BODY_PLUGIN_ROBOT_ENABLED",
            "sim_robot": "BODY_PLUGIN_SIM_ROBOT_ENABLED",
            "world_model": "BODY_WORLDMODEL_ENABLED",
        }
        field = fields.get(plugin_id)
        if not field:
            raise ValueError(f"unknown Body plugin: {plugin_id}")
        self.config[field] = bool(enabled)
        self.save_config()
        if plugin_id == "world_model":
            wm = self.worldmodel if enabled else self._worldmodel
            if wm is not None:
                if enabled:
                    wm.start()
                else:
                    wm.stop()
        elif self._worldmodel is not None:
            self.reload_worldmodel_source()
        return {"ok": True, "plugin": plugin_id, "enabled": bool(enabled), "plugins": self.plugins()}

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

    def _robot_configured(self) -> bool:
        return bool(self.value("BODY_PLUGIN_ROBOT_ENABLED", False)) and bool(str(self.value("ROBOT_URL", "") or "").strip())

    def fetch_robot_sensors(self) -> dict | None:
        """GET {ROBOT_URL}/sensors — the robot's current state + scene."""
        url = str(self.value("ROBOT_URL", "") or "").rstrip("/")
        token = str(self.value("ROBOT_TOKEN", "") or "")
        timeout = float(self.value("ROBOT_TIMEOUT", 5.0) or 5.0)
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

    def _bridge_put(self, entry: dict) -> None:
        message = {"type": "observation", "observation": entry}
        try:
            self.queue.put_nowait(message)
        except Exception:
            LOG.warning("Body bridge queue is full; dropping observation")

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
            "url": str(self.value("ROBOT_URL", "") or ""),
            "token_set": bool(str(self.value("ROBOT_TOKEN", "") or "")),
            "last_ok": self._robot_last_ok,
            "last_ok_age_s": round(time.time() - self._robot_last_ok, 1) if self._robot_last_ok else None,
            "last_error": self._robot_last_error,
            "role": "primary sensorimetry channel",
        }

    # ── poll loop (robot first, HA auxiliary) ──────────────────────────────

    def poll_loop(self) -> None:
        while not self.stop_event.is_set():
            interval = 5
            if self._robot_configured():
                interval = max(1, min(300, int(self.value("ROBOT_POLL_INTERVAL", 5) or 5)))
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
            except Exception as exc:
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
                        self._worldmodel = EmbodiedWorldModel(
                            body=None,
                            data_dir=str(ROOT / "data" / "body" / "worldmodel"),
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
            if bool(self.value("BODY_WORLDMODEL_ENABLED", False)) and wm.config().get("enabled"):
                wm.start()
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
        if mode == "sim":
            return SimRobotSource()
        if mode == "bridge":
            return None
        return resolve_source(self.config, self.latest)

    def plugins(self) -> list[dict]:
        return [
            {
                "id": "robot",
                "enabled": bool(self.value("BODY_PLUGIN_ROBOT_ENABLED", False)),
                "url": str(self.value("ROBOT_URL", "") or ""),
                "last_ok_age_s": round(time.time() - self._robot_last_ok, 1) if self._robot_last_ok else None,
                "last_error": self._robot_last_error,
                "role": "primary sensorimetry channel (plugged robot sensors)",
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
        threads = [threading.Thread(target=self.poll_loop, name="body-sensors", daemon=True)]
        if bool(self.value("BODY_BRIDGE_ENABLED", False)):
            threads.append(threading.Thread(target=self.bridge_loop, name="body-brain-bridge", daemon=True))
        for thread in threads:
            thread.start()
        if bool(self.value("BODY_WORLDMODEL_ENABLED", False)):
            wm = self.worldmodel
            if wm is not None:
                # The Body plugin toggle is the runtime authority.  The
                # model-local flag remains persisted for direct world-model
                # use, but must not silently prevent the enabled Body plugin
                # from starting after a restart.
                wm.start()
                LOG.info("World model loop started (steps=%d)", wm.status_summary().get("steps"))
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

    # ── HTTP endpoints ──────────────────────────────────────────────────────

    def _start_http_endpoint(self) -> None:
        host = str(self.value("BODY_HOST", "127.0.0.1") or "127.0.0.1")
        port = max(1, min(65535, int(self.value("BODY_PORT", 8766) or 8766)))
        owner = self
        from .body_gui import BODY_GUI_HTML

        class Handler(BaseHTTPRequestHandler):
            def _send_html(self, html: str, status: int = 200) -> None:
                data = html.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _send(self, payload, status: int = 200) -> None:
                data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

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
                if path in {"", "/", "/body", "/worldmodel"}:
                    self._send_html(BODY_GUI_HTML)
                elif path == "/health":
                    wm = owner._worldmodel
                    self._send({
                        "status": "ready",
                        "runtime": "independent",
                        "observations": len(owner.latest),
                        "bridge_enabled": bool(owner.value("BODY_BRIDGE_ENABLED", False)),
                        "robot": owner.robot_status(),
                        "plugins": owner.plugins(),
                        "worldmodel": (
                            {"available": True, **wm.status_summary()}
                            if wm is not None
                            else {"available": False, "note": "not initialized (BODY_WORLDMODEL_ENABLED or first /worldmodel/* call)"}
                        ),
                    })
                elif path == "/plugins":
                    self._send({"plugins": owner.plugins()})
                elif path == "/plugins/home_assistant/settings":
                    self._send(owner.home_assistant_settings())
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
                if path.startswith("/plugins/"):
                    plugin_id = path.rsplit("/", 1)[-1]
                    body = self._read_body()
                    if path == "/plugins/home_assistant/settings":
                        self._send(owner.update_home_assistant_settings(body))
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
