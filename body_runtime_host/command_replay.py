"""Durable, fail-closed deduplication of approved Body command identifiers.

This ledger prevents re-execution after a Body process restart. It is not a
substitute for authenticated delivery, authorization, or a physical e-stop.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path


class CommandReplayLedger:
    def __init__(self, path: str | Path, retention_seconds: float = 86400.0):
        self.path = Path(path)
        self.retention_seconds = float(retention_seconds)
        self._lock = threading.RLock()

    def reserve(self, command_id: str, expires_at: float, *, now: float | None = None) -> tuple[bool, str]:
        """Reserve before execution; fail closed on malformed data or disk errors."""
        now = time.time() if now is None else float(now)
        command_id = str(command_id or "")
        if not command_id or len(command_id) > 256:
            return False, "invalid command_id"
        if not (now < expires_at <= now + self.retention_seconds):
            return False, "missing, expired, or invalid command expiry"
        with self._lock:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                records = {}
                if self.path.exists():
                    loaded = json.loads(self.path.read_text(encoding="utf-8"))
                    if not isinstance(loaded, dict):
                        return False, "invalid command replay ledger"
                    records = {str(k): float(v) for k, v in loaded.items() if float(v) > now}
                if command_id in records:
                    return False, "duplicate approved command_id"
                # Keep the ID reserved for the full retention period, not
                # merely until command expiry. A replay with a forged later
                # expiry must not be accepted after the original expires.
                records[command_id] = now + self.retention_seconds
                temporary = self.path.with_suffix(self.path.suffix + ".tmp")
                try:
                    temporary.write_text(json.dumps(records, sort_keys=True), encoding="utf-8")
                    temporary.replace(self.path)
                finally:
                    temporary.unlink(missing_ok=True)
                return True, ""
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                return False, "command replay ledger unavailable"
