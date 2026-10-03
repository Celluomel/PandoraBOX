"""Remote world-model facade for the Brain.

The embodied world model is OWNED by the Body (``body_runtime_host`` process),
where the robot sensors and the world live.  The Brain never mutates it — it
reads it over the Body's HTTP endpoints:

    GET  {base}/worldmodel/status
    GET  {base}/worldmodel/anchors
    GET  {base}/worldmodel/episodes
    GET  {base}/worldmodel/context
    GET  {base}/worldmodel/config
    POST {base}/worldmodel/step | reset | config | reload

This module wraps that API in the same object surface the brain-side code
already uses (``status_summary()``, ``context_for_brain()``, ``step()``,
``reset()``, ``config()``, ``update_config()``, ``recent_episodes()``,
``anchors_payload()``), so the dashboard, the REST API and the prompt context
work only through the separately launched Body host.

Read-only by design: the only mutations the Brain may trigger are the
explicit, auditable ``step`` / ``reset`` / ``config`` operations.
"""
from __future__ import annotations

import json
import logging
import base64
import ssl
import urllib.error
import urllib.request
from urllib.parse import quote
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _request(method: str, url: str, payload: Optional[Dict[str, Any]] = None,
             timeout: float = 10.0, headers: Optional[Dict[str, str]] = None,
             ssl_context: Optional[ssl.SSLContext] = None) -> Any:
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Accept": "application/json", "Content-Type": "application/json", **(headers or {})},
    )
    opener = urllib.request.urlopen
    response = opener(req, timeout=timeout) if ssl_context is None else opener(
        req, timeout=timeout, context=ssl_context
    )
    with response as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else None


class RemoteWorldModel:
    """Brain-side, read-only view of the Body-owned world model."""

    def __init__(self, base_url: str, timeout: float = 10.0,
                 auth_username: str = "", auth_password: str = "", ca_cert: str = ""):
        self.base_url = str(base_url or "").rstrip("/")
        self.timeout = float(timeout or 10.0)
        self._headers: Dict[str, str] = {}
        if auth_username or auth_password:
            raw = f"{auth_username}:{auth_password}".encode("utf-8")
            self._headers["Authorization"] = "Basic " + base64.b64encode(raw).decode("ascii")
        self._ssl_context = ssl.create_default_context(cafile=ca_cert) if ca_cert else None
        self._last_error = ""

    def _request(self, method: str, url: str, payload: Optional[Dict[str, Any]] = None,
                 timeout: Optional[float] = None) -> Any:
        args = (method, url, payload, self.timeout if timeout is None else timeout, self._headers)
        return _request(*args) if self._ssl_context is None else _request(*args, self._ssl_context)

    # ── liveness ────────────────────────────────────────────────────────────

    def ping(self) -> bool:
        try:
            self._request("GET", f"{self.base_url}/health", timeout=2.0)
            self._last_error = ""
            return True
        except Exception as exc:
            self._last_error = str(exc)
            return False

    # ── the brain-facing surface ────────────────────────────────────────────

    def status_summary(self) -> Dict[str, Any]:
        try:
            data = self._request("GET", f"{self.base_url}/worldmodel/status")
            data["remote"] = True
            data["base_url"] = self.base_url
            return data
        except Exception as exc:
            self._last_error = str(exc)
            return {"available": False, "remote": True, "base_url": self.base_url, "error": str(exc)}

    def snapshot(self) -> Dict[str, Any]:
        """Return the latest structured Body snapshot for planning."""
        try:
            data = self._request("GET", f"{self.base_url}/worldmodel/snapshot")
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            self._last_error = str(exc)
            return {"available": False, "error": str(exc)}

    def perception(self) -> Dict[str, Any]:
        """Return the complete timestamped 2-D/3-D Body perception packet."""
        try:
            data = self._request("GET", f"{self.base_url}/worldmodel/perception")
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            self._last_error = str(exc)
            return {"available": False, "error": str(exc)}

    def interpret_camera(self) -> Dict[str, Any]:
        """Ask the Body-owned VLM to interpret its latest camera scene."""
        try:
            data = self._request(
                "POST", f"{self.base_url}/body/camera/test-vlm",
                payload={}, timeout=max(self.timeout, 90.0),
            )
            return data if isinstance(data, dict) else {"ok": False, "error": "invalid Body VLM response"}
        except Exception as exc:
            self._last_error = str(exc)
            return {"ok": False, "error": str(exc)}

    def route_map(self) -> Dict[str, Any]:
        """Return the Body-owned metric route memory and landmark flags."""
        try:
            data = self._request("GET", f"{self.base_url}/worldmodel/map")
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            self._last_error = str(exc)
            return {"available": False, "error": str(exc)}

    def remembered_route(self, target: str = "start") -> Dict[str, Any]:
        """Read a replayable route to a remembered object or the start pose."""
        try:
            encoded = quote(str(target or "start"), safe="")
            data = self._request("GET", f"{self.base_url}/worldmodel/map/route?target={encoded}")
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            self._last_error = str(exc)
            return {"available": False, "error": str(exc)}

    def context_for_brain(self) -> str:
        try:
            data = self._request("GET", f"{self.base_url}/worldmodel/context")
            return str(data.get("context") or "")
        except Exception as exc:
            self._last_error = str(exc)
            return ""

    def recent_episodes(self, limit: int = 12) -> List[Dict[str, Any]]:
        try:
            data = self._request("GET", f"{self.base_url}/worldmodel/episodes?limit={int(limit)}")
            return data if isinstance(data, list) else []
        except Exception as exc:
            self._last_error = str(exc)
            return []

    def anchors_payload(self, limit: int = 40) -> Dict[str, Any]:
        try:
            data = self._request("GET", f"{self.base_url}/worldmodel/anchors")
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            self._last_error = str(exc)
            return {"error": str(exc)}

    def config(self) -> Dict[str, Any]:
        try:
            data = self._request("GET", f"{self.base_url}/worldmodel/config")
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            self._last_error = str(exc)
            return {}

    # ── explicit, auditable operations (the only mutations the Brain may ask) ─

    def step(self) -> Dict[str, Any]:
        try:
            return self._request("POST", f"{self.base_url}/worldmodel/step")
        except Exception as exc:
            self._last_error = str(exc)
            return {"error": str(exc)}

    def run(self, running: bool = True, shuffle: bool = False) -> Dict[str, Any]:
        try:
            return self._request("POST", f"{self.base_url}/worldmodel/run",
                                 payload={"running": bool(running), "shuffle": bool(shuffle)})
        except Exception as exc:
            self._last_error = str(exc)
            return {"error": str(exc)}

    def submit_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a Brain-produced generic plan to the Body validator."""
        try:
            return self._request("POST", f"{self.base_url}/worldmodel/plans",
                                 payload=payload or {})
        except Exception as exc:
            self._last_error = str(exc)
            return {"accepted": False, "error": str(exc)}

    def plan_payload(self) -> Dict[str, Any]:
        """Read the current plan lease and latest Body planning snapshot."""
        try:
            return self._request("GET", f"{self.base_url}/worldmodel/plans")
        except Exception as exc:
            self._last_error = str(exc)
            return {"active_plan": None, "error": str(exc)}

    def capability_gate(self) -> Dict[str, Any]:
        """Read the latest Body evidence gate for Brain/chat status answers."""
        try:
            data = self._request("GET", f"{self.base_url}/worldmodel/capability-gate")
            return data if isinstance(data, dict) else {"state": "unknown"}
        except Exception as exc:
            self._last_error = str(exc)
            return {"state": "unavailable", "error": str(exc)}

    def validate_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Ask the Body whether a plan is feasible without reserving it."""
        try:
            return self._request("POST", f"{self.base_url}/worldmodel/plans/validate",
                                 payload=payload or {})
        except Exception as exc:
            self._last_error = str(exc)
            return {"feasible": False, "error": str(exc)}

    def cancel_plan(self, plan_id: str, reason: str = "cancelled by Brain") -> Dict[str, Any]:
        try:
            return self._request("POST", f"{self.base_url}/worldmodel/plans/{plan_id}/cancel",
                                 payload={"reason": reason})
        except Exception as exc:
            self._last_error = str(exc)
            return {"ok": False, "error": str(exc)}

    def reset(self, clear_memory: bool = False) -> Dict[str, Any]:
        try:
            return self._request("POST", f"{self.base_url}/worldmodel/reset",
                                 payload={"clear_memory": bool(clear_memory)})
        except Exception as exc:
            self._last_error = str(exc)
            return {"error": str(exc)}

    def update_config(self, values: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self._request("POST", f"{self.base_url}/worldmodel/config",
                                 payload={"values": values or {}})
        except Exception as exc:
            self._last_error = str(exc)
            return {"error": str(exc)}

    def reload_source(self) -> Dict[str, Any]:
        try:
            return self._request("POST", f"{self.base_url}/worldmodel/reload")
        except Exception as exc:
            self._last_error = str(exc)
            return {"error": str(exc)}

    @property
    def last_error(self) -> str:
        return self._last_error
