"""Brain-side registry for observations and permissioned Body commands.

The actual sensor/plugin/world-model host runs separately in
``body_runtime_host``. This Brain-side adapter receives its observations and
approved command results over the authenticated WebSocket bridge; it never
starts a second Body or a local world-model fallback.
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
import json
import uuid
from pathlib import Path
from queue import Full, Queue
from threading import RLock
import time
from typing import Any, Dict, Optional
from secret_store import SECRET_FIELDS, config_reference, resolve, store


@dataclass
class BodyObservation:
    source: str
    kind: str
    subject: str
    value: Any
    unit: str = ""
    confidence: float = 1.0
    observed_at: float = field(default_factory=time.time)
    provenance: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["age_seconds"] = round(max(0.0, time.time() - self.observed_at), 3)
        return result


@dataclass
class BodyCommand:
    target: str
    action: str
    command_id: str = field(default_factory=lambda: f"bodycmd_{uuid.uuid4().hex[:12]}")
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 120.0)
    status: str = "queued"
    requires_confirmation: bool = True
    origin: str = "brain"
    approved_at: Optional[float] = None
    rejected_at: Optional[float] = None
    executed_at: Optional[float] = None
    outcome: Dict[str, Any] = field(default_factory=dict)
    error: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BodyRuntime:
    """Passive Brain-side state, observation, and command adapter."""

    def __init__(self, organism: Any = None, max_events: int = 256):
        self.organism = organism
        self._config_path = Path("data/body/config.json")
        self._config = self._load_config()
        self._lock = RLock()
        self._plugins: Dict[str, Dict[str, Any]] = {}
        self.register_plugin(
            "home_assistant",
            "Home Assistant",
            "BODY_PLUGIN_HOME_ASSISTANT_ENABLED",
            "Read-only environmental sensors and presence",
        )
        self.register_plugin(
            "fnk0031_wifi",
            "FNK0031 Wi-Fi robot",
            "BODY_PLUGIN_ROBOT_ENABLED",
            "Network robot adapter for the FNK0031/Mega 2560 body",
        )
        self.register_plugin(
            "sim_robot",
            "Simulated robot",
            "BODY_PLUGIN_SIM_ROBOT_ENABLED",
            "Safe local robot and world-model test body",
        )
        self.register_plugin(
            "world_model",
            "Embodied world model",
            "BODY_WORLDMODEL_ENABLED",
            "Body-owned perception, memory, dynamics and policy",
        )
        self._latest: Dict[str, BodyObservation] = {}
        self._events = deque(maxlen=max_events)
        self._commands = deque(maxlen=64)
        self._bridge_commands: Queue[Dict[str, Any]] = Queue(maxsize=64)
        self._bridge_devices: set[str] = set()
        # The Body's embodied world model (lazy — built on first access).
        # Owned by the Body; the Brain only reads its context.
        self._worldmodel = None

    _CONFIG_FIELDS = {
        "BODY_RUNTIME_ENABLED", "BODY_PLUGIN_HOME_ASSISTANT_ENABLED",
        "BODY_HOST", "BODY_PORT",
        "BODY_PLUGIN_ROBOT_ENABLED", "ROBOT_URL", "ROBOT_TOKEN",
        "ROBOT_TIMEOUT", "ROBOT_POLL_INTERVAL",
        "BODY_PLUGIN_SIM_ROBOT_ENABLED", "BODY_WORLDMODEL_ENABLED",
        "HOME_ASSISTANT_ENABLED", "HOME_ASSISTANT_PRESENCE_ENABLED",
        "HOME_ASSISTANT_URL", "HOME_ASSISTANT_TOKEN",
        "HOME_ASSISTANT_VERIFY_SSL", "HOME_ASSISTANT_POLL_INTERVAL",
        "HOME_ASSISTANT_ALLOWED_DOMAINS", "HOME_ASSISTANT_SELECTED_ENTITIES",
        "HOME_ASSISTANT_DISCOVERED_ENTITIES", "HOME_ASSISTANT_ENTITY_TAGS",
        "BODY_BRIDGE_ENABLED", "BODY_BRIDGE_URL", "BODY_BRIDGE_TOKEN",
        "BODY_BRIDGE_DEVICE_ID", "BODY_BRIDGE_VERIFY_TLS", "BODY_BRIDGE_RECONNECT_SECONDS",
        "BODY_COMMAND_TTL_SECONDS", "BODY_ACTUATION_ENABLED",
    }

    def _load_config(self) -> Dict[str, Any]:
        try:
            if self._config_path.exists():
                payload = json.loads(self._config_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    for key in SECRET_FIELDS:
                        if key in payload:
                            payload[key] = resolve(key, payload[key])
                    return payload
                return {}
        except Exception:
            pass
        migrated: Dict[str, Any] = {}
        try:
            from managers.settings_manager import config
            for key in self._CONFIG_FIELDS:
                if hasattr(config, key):
                    migrated[key] = getattr(config, key)
        except Exception:
            pass
        self._write_config(migrated)
        return migrated

    def _write_config(self, payload: Dict[str, Any]) -> None:
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            safe = dict(payload)
            for key in SECRET_FIELDS:
                if safe.get(key):
                    store(key, safe[key])
                safe[key] = config_reference(key, safe.get(key))
            self._config_path.write_text(json.dumps(safe, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def config_value(self, key: str, fallback: Any = None) -> Any:
        with self._lock:
            return self._config.get(key, fallback)

    def update_config(self, values: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            for key, value in values.items():
                if key in self._CONFIG_FIELDS:
                    self._config[key] = value
            self._write_config(self._config)
        return dict(self._config)

    def config_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._config)

    def register_plugin(self, plugin_id: str, label: str, toggle_field: str, description: str) -> None:
        """Allow body adapters to announce themselves without changing brain UI."""
        with self._lock:
            self._plugins[plugin_id] = {
                "id": plugin_id,
                "label": label,
                "toggle_field": toggle_field,
                "description": description,
                "available": True,
            }

    def plugins(self) -> list[Dict[str, Any]]:
        with self._lock:
            plugins = list(self._plugins.values())
        for plugin in plugins:
            field = plugin["toggle_field"]
            fallback = self.config_value(
                "HOME_ASSISTANT_ENABLED", False
            ) if plugin["id"] == "home_assistant" else False
            plugin["enabled"] = bool(self.config_value(field, fallback))
            # Do not call status() here: status() includes plugin snapshots and
            # would recurse forever as soon as the Body toggle is enabled.
            running = bool(self._bridge_devices)
            plugin["runtime"] = "active" if plugin["enabled"] and running else "disabled"
        return plugins

    # ── Embodied world model (owned by the Body) ────────────────────────────

    @property
    def worldmodel(self):
        """The Body's embodied world model (lazy).

        The model is OWNED by the Body.  Preferred source: the independent
        Body host process (``body_runtime_host``), read over HTTP. The Brain
        never creates a fallback model: starting the Body is an explicit,
        separate operator action.
        """
        if self._worldmodel is None:
            self._worldmodel = self._build_worldmodel()
        return self._worldmodel

    def _build_worldmodel(self):
        host = str(self.config_value("BODY_HOST", "127.0.0.1") or "127.0.0.1")
        port = self.config_value("BODY_PORT", 8766) or 8766
        base = f"http://{host}:{port}"
        # 1) Body host (owner of the world model) — remote, read-only facade
        try:
            from .remote import RemoteWorldModel
            client = RemoteWorldModel(base)
            if client.ping():
                import logging
                logging.getLogger(__name__).info("World model: attached to Body host at %s", base)
                return client
        except Exception:
            pass
        import logging
        logging.getLogger(__name__).info(
            "World model unavailable: standalone Body host is not reachable at %s", base
        )
        return None

    def publish_observation(self, observation: BodyObservation | None = None, forward: bool = True, **kwargs: Any) -> BodyObservation:
        """Record a Body observation received from a local or remote adapter."""
        item = observation or BodyObservation(**kwargs)
        key = f"{item.source}:{item.subject}"
        with self._lock:
            self._latest[key] = item
            self._events.append(item)
        return item

    def enqueue_command(self, target: str, action: str, payload: Optional[Dict[str, Any]] = None,
                        requires_confirmation: bool = True, origin: str = "brain",
                        ttl_seconds: Optional[float] = None) -> BodyCommand:
        ttl = float(ttl_seconds if ttl_seconds is not None else self.config_value(
            "BODY_COMMAND_TTL_SECONDS", 120.0
        ) or 120.0)
        command = BodyCommand(
            target=target,
            action=action,
            payload=dict(payload or {}),
            expires_at=time.time() + max(1.0, ttl),
            requires_confirmation=bool(requires_confirmation),
            origin=str(origin or "brain"),
        )
        with self._lock:
            self._expire_commands_locked()
            self._commands.append(command)
        return command

    def _expire_commands_locked(self) -> None:
        now = time.time()
        for command in self._commands:
            if command.status in {"queued", "approved"} and command.expires_at <= now:
                command.status = "expired"
                command.error = "command approval or delivery window expired"

    def snapshot_commands(self, include_terminal: bool = False) -> list[Dict[str, Any]]:
        with self._lock:
            self._expire_commands_locked()
            commands = list(self._commands)
        if not include_terminal:
            commands = [item for item in commands if item.status in {"queued", "approved", "executing"}]
        return [item.as_dict() for item in reversed(commands)]

    def approve_command(self, command_id: str) -> Dict[str, Any]:
        with self._lock:
            self._expire_commands_locked()
            command = next((item for item in self._commands if item.command_id == command_id), None)
            if command is None:
                return {"ok": False, "error": "command not found"}
            if command.status != "queued":
                return {"ok": False, "error": f"command is {command.status}", "command": command.as_dict()}
            command.status = "approved"
            command.approved_at = time.time()
            message = {"type": "command", "command": command.as_dict()}
        try:
            self._bridge_commands.put_nowait(message)
        except Full:
            with self._lock:
                command.status = "queued"
                command.approved_at = None
            return {"ok": False, "error": "Body bridge command queue is full", "command": command.as_dict()}
        return {"ok": True, "command": command.as_dict(), "delivery": "queued"}

    def reject_command(self, command_id: str, reason: str = "rejected by operator") -> Dict[str, Any]:
        with self._lock:
            self._expire_commands_locked()
            command = next((item for item in self._commands if item.command_id == command_id), None)
            if command is None:
                return {"ok": False, "error": "command not found"}
            if command.status != "queued":
                return {"ok": False, "error": f"command is {command.status}", "command": command.as_dict()}
            command.status = "rejected"
            command.rejected_at = time.time()
            command.error = str(reason or "rejected by operator")[:240]
            return {"ok": True, "command": command.as_dict()}

    def next_bridge_command(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        try:
            return self._bridge_commands.get(timeout=max(0.0, timeout))
        except Exception:
            return None

    def register_bridge_device(self, device_id: str) -> None:
        with self._lock:
            self._bridge_devices.add(str(device_id or "body"))

    def unregister_bridge_device(self, device_id: str) -> None:
        with self._lock:
            self._bridge_devices.discard(str(device_id or "body"))

    def record_command_outcome(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        command_id = str(payload.get("command_id") or "")
        with self._lock:
            command = next((item for item in self._commands if item.command_id == command_id), None)
            if command is None:
                return {"ok": False, "error": "command not found"}
            command.executed_at = time.time()
            command.outcome = dict(payload.get("outcome") or {})
            command.error = str(payload.get("error") or "")[:240]
            kind = str(command.outcome.get("kind") or payload.get("status") or "failure").lower()
            command.status = "executed" if kind in {"success", "neutral"} else "failed"
            result = command.as_dict()
        # Feed the physical outcome back through the normal perception path.
        self.publish_observation(
            source="body_action",
            kind="actuation_feedback",
            subject=f"{command.target}.{command.action}",
            value=result["status"],
            confidence=1.0 if result["status"] == "executed" else 0.8,
            provenance={"command_id": command_id, "outcome": result["outcome"]},
        )
        # Action outcomes are perceptions too: route them through the same
        # connector used by sensors so learning and workspace competition see
        # success/failure without coupling the Body to the chat turn.
        if self.organism is not None:
            try:
                from cognition.universal_connector import get_universal_connector, Percept
                get_universal_connector(self.organism).perceive(Percept(
                    modality="body_action",
                    source="body_runtime",
                    payload={
                        "command_id": command_id,
                        "target": command.target,
                        "action": command.action,
                        "status": result["status"],
                        "outcome": result["outcome"],
                    },
                    confidence=1.0 if result["status"] == "executed" else 0.8,
                    salience=0.8,
                    provenance={"command_id": command_id, "origin": command.origin},
                ))
            except Exception:
                import logging
                logging.getLogger(__name__).debug("Body action feedback connector route failed", exc_info=True)
        return {"ok": True, "command": result}

    def snapshot(self, max_age: Optional[float] = None) -> list[Dict[str, Any]]:
        now = time.time()
        with self._lock:
            observations = list(self._latest.values())
        if max_age is not None:
            observations = [item for item in observations if now - item.observed_at <= max_age]
        return [item.as_dict() for item in sorted(observations, key=lambda item: item.observed_at, reverse=True)]

    def recent_events(self, limit: int = 20) -> list[Dict[str, Any]]:
        with self._lock:
            return [item.as_dict() for item in list(self._events)[-max(1, limit):]]

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "available": True,
                "running": bool(self._bridge_devices),
                "mode": "remote-connected" if self._bridge_devices else "remote-disconnected",
                "heartbeat": max((item.observed_at for item in self._latest.values()), default=None),
                "observation_count": len(self._latest),
                "event_count": len(self._events),
                "commands": self.snapshot_commands(include_terminal=True),
                "pending_commands": len(self._commands),
                "last_observation": max((item.observed_at for item in self._latest.values()), default=None),
                "plugins": {
                    item["id"]: item["enabled"] for item in self.plugins()
                },
                "brain_bridge": {
                    "enabled": bool(self.config_value("BODY_BRIDGE_ENABLED", False)),
                    "connected": bool(self._bridge_devices),
                    "url": str(self.config_value("BODY_BRIDGE_URL", "") or ""),
                },
                # World model is reported only if already built (no forced
                # torch import on every /status poll).
                "worldmodel": (
                    {"available": True, **self._worldmodel.status_summary()}
                    if self._worldmodel is not None
                    else {"available": False, "note": "not yet initialized"}
                ),
            }

    def context_for_brain(self, max_age: float = 120.0, exclude_sources: Optional[set[str]] = None) -> str:
        if not bool(self.config_value("BODY_RUNTIME_ENABLED", True)):
            return ""
        observations = self.snapshot(max_age=max_age)
        if exclude_sources:
            observations = [item for item in observations if item.get("source") not in exclude_sources]
        # The Body may receive a permitted discovery list from a plugin, while
        # the user-facing selection is narrower. Keep unselected HA entities
        # out of the brain prompt even when the connector refreshed them.
        selected = {
            item.strip()
            for item in str(self.config_value("HOME_ASSISTANT_SELECTED_ENTITIES", "") or "").split(",")
            if item.strip()
        }
        if selected:
            observations = [
                item for item in observations
                if item.get("source") != "home_assistant"
                or str((item.get("provenance") or {}).get("entity_id", "")) in selected
            ]
        if not observations:
            observations = []
        lines: list[str] = []
        if observations:
            lines = [
                "BODY RUNTIME OBSERVATIONS (local, timestamped sensor evidence):",
                "Use these observations only when relevant; preserve exact values and timestamps.",
            ]
            for item in observations:
                value = item["value"]
                unit = f" {item['unit']}" if item.get("unit") else ""
                stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(item["observed_at"]))
                lines.append(f"- {item['subject']}: {value}{unit} (source {item['source']}, observed {stamp})")
        # The Body's learned world knowledge (anchors + task state).  Only
        # included if the world model was already built — this is the single
        # channel through which the Body's physical knowledge informs the
        # Brain, and it is read-only by design.  It is included even when
        # there are no live sensor observations (e.g. the simulated body).
        try:
            wm = self._worldmodel
            if wm is not None:
                wm_ctx = wm.context_for_brain()
                if wm_ctx:
                    if lines:
                        lines.append("")
                    lines.extend(wm_ctx.split("\n"))
        except Exception:
            pass
        return "\n".join(lines)

def get_body_runtime(organism: Any = None) -> BodyRuntime:
    """Return the Brain-side passive adapter; the Body host starts separately."""
    if organism is not None:
        existing = getattr(organism, "_body_runtime", None)
        if existing is not None:
            return existing
    runtime = BodyRuntime(organism=organism)
    if organism is not None:
        try:
            organism._body_runtime = runtime
        except Exception:
            pass
    return runtime
