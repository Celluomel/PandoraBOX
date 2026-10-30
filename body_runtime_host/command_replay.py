"""Durable, fail-closed deduplication of approved Body command identifiers.

This ledger prevents re-execution after a Body process restart. It is not a
substitute for authenticated delivery, authorization, or a physical e-stop.
"""
from __future__ import annotations

import json
import math
import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path


class CommandReplayLedger:
    def __init__(self, path: str | Path, retention_seconds: float = 86400.0):
        self.path = Path(path)
        self.retention_seconds = float(retention_seconds)
        self._lock = threading.RLock()

    @contextmanager
    def _process_lock(self):
        """Serialize independent Body processes around read/modify/replace."""
        lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as lock_file:
            if os.name == "nt":
                import msvcrt
                lock_file.seek(0, os.SEEK_END)
                if lock_file.tell() == 0:
                    lock_file.write(b"\0")
                    lock_file.flush()
                lock_file.seek(0)
                deadline = time.monotonic() + 15.0
                while True:
                    try:
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                        break
                    except OSError:
                        if time.monotonic() >= deadline:
                            raise
                        time.sleep(0.02)
                try:
                    yield
                finally:
                    lock_file.seek(0)
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def reserve(self, command_id: str, expires_at: float, *, now: float | None = None) -> tuple[bool, str]:
        """Reserve before execution; fail closed on malformed data or disk errors."""
        now = time.time() if now is None else float(now)
        command_id = str(command_id or "")
        if not command_id or len(command_id) > 256:
            return False, "invalid command_id"
        if not (math.isfinite(now) and math.isfinite(expires_at) and now < expires_at <= now + self.retention_seconds):
            return False, "missing, expired, or invalid command expiry"
        with self._lock:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self._process_lock():
                    records = {}
                    if self.path.exists():
                        loaded = json.loads(self.path.read_text(encoding="utf-8"))
                        if not isinstance(loaded, dict):
                            return False, "invalid command replay ledger"
                        for key, value in loaded.items():
                            expiry = float(value)
                            if not str(key) or not math.isfinite(expiry):
                                return False, "invalid command replay ledger"
                            if expiry > now:
                                records[str(key)] = expiry
                    if command_id in records:
                        return False, "duplicate approved command_id"
                    # Retain IDs beyond command expiry so a forged renewed
                    # expiry cannot make a previous command executable again.
                    records[command_id] = now + self.retention_seconds
                    temporary = self.path.with_suffix(self.path.suffix + ".tmp")
                    try:
                        with temporary.open("w", encoding="utf-8", newline="\n") as output:
                            output.write(json.dumps(records, sort_keys=True))
                            output.flush()
                            os.fsync(output.fileno())
                        os.replace(temporary, self.path)
                        if os.name != "nt":
                            directory_fd = os.open(self.path.parent, os.O_RDONLY)
                            try:
                                os.fsync(directory_fd)
                            finally:
                                os.close(directory_fd)
                    finally:
                        temporary.unlink(missing_ok=True)
                return True, ""
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                return False, "command replay ledger unavailable"
