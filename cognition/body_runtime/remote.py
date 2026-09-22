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
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _request(method: str, url: str, payload: Optional[Dict[str, Any]] = None,
             timeout: float = 10.0) -> Any:
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else None


class RemoteWorldModel:
    """Brain-side, read-only view of the Body-owned world model."""

    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = str(base_url or "").rstrip("/")
        self.timeout = float(timeout or 10.0)
        self._last_error = ""

    # ── liveness ────────────────────────────────────────────────────────────

    def ping(self) -> bool:
        try:
            _request("GET", f"{self.base_url}/health", timeout=2.0)
            self._last_error = ""
            return True
        except Exception as exc:
            self._last_error = str(exc)
            return False

    # ── the brain-facing surface ────────────────────────────────────────────

    def status_summary(self) -> Dict[str, Any]:
        try:
            data = _request("GET", f"{self.base_url}/worldmodel/status", timeout=self.timeout)
            data["remote"] = True
            data["base_url"] = self.base_url
            return data
        except Exception as exc:
            self._last_error = str(exc)
            return {"available": False, "remote": True, "base_url": self.base_url, "error": str(exc)}

    def context_for_brain(self) -> str:
        try:
            data = _request("GET", f"{self.base_url}/worldmodel/context", timeout=self.timeout)
            return str(data.get("context") or "")
        except Exception as exc:
            self._last_error = str(exc)
            return ""

    def recent_episodes(self, limit: int = 12) -> List[Dict[str, Any]]:
        try:
            data = _request("GET", f"{self.base_url}/worldmodel/episodes?limit={int(limit)}", timeout=self.timeout)
            return data if isinstance(data, list) else []
        except Exception as exc:
            self._last_error = str(exc)
            return []

    def anchors_payload(self, limit: int = 40) -> Dict[str, Any]:
        try:
            data = _request("GET", f"{self.base_url}/worldmodel/anchors", timeout=self.timeout)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            self._last_error = str(exc)
            return {"error": str(exc)}

    def config(self) -> Dict[str, Any]:
        try:
            data = _request("GET", f"{self.base_url}/worldmodel/config", timeout=self.timeout)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            self._last_error = str(exc)
            return {}

    # ── explicit, auditable operations (the only mutations the Brain may ask) ─

    def step(self) -> Dict[str, Any]:
        try:
            return _request("POST", f"{self.base_url}/worldmodel/step", timeout=self.timeout)
        except Exception as exc:
            self._last_error = str(exc)
            return {"error": str(exc)}

    def reset(self, clear_memory: bool = False) -> Dict[str, Any]:
        try:
            return _request("POST", f"{self.base_url}/worldmodel/reset",
                            payload={"clear_memory": bool(clear_memory)}, timeout=self.timeout)
        except Exception as exc:
            self._last_error = str(exc)
            return {"error": str(exc)}

    def update_config(self, values: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return _request("POST", f"{self.base_url}/worldmodel/config",
                            payload={"values": values or {}}, timeout=self.timeout)
        except Exception as exc:
            self._last_error = str(exc)
            return {"error": str(exc)}

    def reload_source(self) -> Dict[str, Any]:
        try:
            return _request("POST", f"{self.base_url}/worldmodel/reload", timeout=self.timeout)
        except Exception as exc:
            self._last_error = str(exc)
            return {"error": str(exc)}

    @property
    def last_error(self) -> str:
        return self._last_error
