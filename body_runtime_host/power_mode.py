"""Runtime power policy for Body-owned camera and perception workloads."""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any, Callable


MODES = {"DEV", "ATTENTIVE", "IDLE"}


class PowerModeManager:
    """Small state holder; the runtime callback owns applying each policy."""

    def __init__(self, apply_mode: Callable[[str, str], dict[str, Any]], initial: str = "DEV"):
        self._apply_mode = apply_mode
        self._lock = threading.RLock()
        self._mode = "DEV"
        self._since = time.time()
        self._reason = "startup default"
        self._last_auto_raise: str | None = None
        self._watts: deque[tuple[float, str, float]] = deque()
        if initial.upper() != "DEV":
            self.set_mode(initial, "startup configuration")

    def set_mode(self, mode: str, reason: str = "operator") -> dict[str, Any]:
        mode = str(mode or "").upper()
        if mode not in MODES:
            raise ValueError("mode must be DEV, ATTENTIVE, or IDLE")
        with self._lock:
            old = self._mode
            if old != mode:
                self._apply_mode(old, mode)
                self._mode = mode
                self._since = time.time()
                self._reason = str(reason or "operator")[:120]
                self._last_auto_raise = self._reason if self._reason != "operator" else None
            return self.status()

    def auto_raise(self, reason: str) -> dict[str, Any] | None:
        with self._lock:
            if self._mode != "IDLE":
                return None
        return self.set_mode("ATTENTIVE", f"auto-raised: {reason}")

    def record_watts(self, watts: float, now: float | None = None) -> None:
        now = time.time() if now is None else float(now)
        with self._lock:
            self._watts.append((now, self._mode, float(watts)))
            cutoff = now - 60.0
            while self._watts and self._watts[0][0] < cutoff:
                self._watts.popleft()

    def status(self, intervals: dict[str, Any] | None = None, watts: float | None = None,
               energy: dict[str, Any] | None = None) -> dict[str, Any]:
        now = time.time()
        with self._lock:
            rolling = {}
            for mode in MODES:
                values = [sample for timestamp, sample_mode, sample in self._watts
                          if sample_mode == mode and timestamp >= now - 60.0]
                rolling[mode] = {
                    "mean_w": round(sum(values) / len(values), 2) if values else None,
                    "samples": len(values),
                    "window_s": 60,
                }
            result = {
                "mode": self._mode,
                "since": self._since,
                "reason": self._reason,
                "last_auto_raise": self._last_auto_raise,
                "effective_intervals_s": dict(intervals or {}),
                "rolling_60s_mean_w_by_mode": rolling,
                "board_input_w": watts,
            }
            if energy:
                result["battery_estimate"] = dict(energy)
            return result
