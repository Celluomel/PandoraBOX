"""Bounded, privacy-safe execution telemetry for cognitive modules."""

from __future__ import annotations

import math
import threading
import time
import traceback
from typing import Any


def summarize_output(value: Any, *, side_effect_only: bool = False) -> dict[str, Any]:
    """Describe result shape and numeric validity without retaining prose."""
    result: dict[str, Any] = {"type": type(value).__name__}
    if value is None or isinstance(value, (bool, int, float)):
        if isinstance(value, bool):
            result["value"] = value
        elif isinstance(value, (int, float)):
            try:
                result["finite"] = math.isfinite(float(value))
            except (OverflowError, TypeError, ValueError):
                result["finite"] = False
            if result["finite"]:
                result["value"] = value
        result["quality"] = (
            "side_effect_only" if value is None and side_effect_only else
            "empty" if value is None else
            "invalid_numeric" if result.get("finite") is False else
            "present"
        )
        return result
    if isinstance(value, str):
        result["length"] = len(value)
        result["quality"] = "empty" if not value.strip() else "present_redacted"
        return result
    if isinstance(value, dict):
        result["keys"] = sorted(str(key)[:64] for key in list(value)[:24])
        result["item_count"] = len(value)
        numeric = {}
        non_finite = []
        for key, item in list(value.items())[:64]:
            if isinstance(item, (int, float)) and not isinstance(item, bool):
                try:
                    finite = math.isfinite(float(item))
                except (OverflowError, TypeError, ValueError):
                    finite = False
                numeric[str(key)[:64]] = {"finite": finite}
                if not finite:
                    non_finite.append(str(key)[:64])
        if numeric:
            result["numeric_fields"] = numeric
        if non_finite:
            result["non_finite_fields"] = non_finite
        result["quality"] = (
            "empty" if not value else
            "invalid_numeric" if non_finite else
            "present"
        )
        return result
    if isinstance(value, (list, tuple, set)):
        items = list(value)
        result["item_count"] = len(items)
        result["sample_types"] = sorted({type(item).__name__ for item in items[:16]})
        result["quality"] = "empty" if not items else "present"
        return result
    fields = getattr(value, "__dataclass_fields__", None)
    if isinstance(fields, dict):
        result["fields"] = sorted(str(name)[:64] for name in fields)[:32]
        result["quality"] = "present"
    else:
        result["quality"] = "shape_only"
    return result


def _state_for_output(output: dict[str, Any] | None) -> str:
    """Separate successful execution from outputs that are not inspectable."""
    quality = str((output or {}).get("quality", "unknown"))
    if quality == "invalid_numeric":
        return "degraded"
    if quality in {"empty", "shape_only", "unknown"}:
        return "output_unverified"
    return "healthy"


class ModuleTickLog:
    """Thread-safe last-value/counter log; never stores module output text."""

    def __init__(self):
        self._lock = threading.RLock()
        self._modules: dict[str, dict[str, Any]] = {}

    def register(self, name: str, *, initialized: bool, cadence: str = "conditional") -> None:
        with self._lock:
            item = self._modules.setdefault(name, {
                "tick_count": 0,
                "skip_count": 0,
                "last_skip_at": None,
                "last_skip_status": None,
                "last_skip_metrics": None,
                "error_count": 0,
                "last_tick_at": None,
                "last_success_at": None,
                "last_duration_ms": None,
                "last_status": "not_observed",
                "last_error_type": None,
                "last_error": None,
                "last_output": None,
                "observed_methods": [],
            })
            item["initialized"] = bool(initialized)
            item["cadence"] = cadence
            item["state"] = (
                "unavailable" if not initialized else
                _state_for_output(item.get("last_output"))
                if item["last_status"] == "completed" else
                "error" if item["last_status"] == "failed" else
                "skipped_by_policy" if item.get("skip_count", 0) else
                "initialized_unobserved"
            )

    def record(self, name: str, method: str, *, started_at: float,
               duration_ms: float, output: Any = None, error: BaseException | None = None,
               side_effect_only: bool = False) -> None:
        now = time.time()
        with self._lock:
            item = self._modules.setdefault(name, {
                "initialized": True,
                "cadence": "conditional",
                "tick_count": 0,
                "skip_count": 0,
                "last_skip_at": None,
                "last_skip_status": None,
                "last_skip_metrics": None,
                "error_count": 0,
                "last_tick_at": None,
                "last_success_at": None,
                "last_duration_ms": None,
                "last_status": "not_observed",
                "last_error_type": None,
                "last_error": None,
                "last_output": None,
                "observed_methods": [],
            })
            item["tick_count"] += 1
            item["last_tick_at"] = now
            item["last_duration_ms"] = round(max(0.0, duration_ms), 3)
            if method not in item["observed_methods"]:
                item["observed_methods"] = (item["observed_methods"] + [method])[-12:]
            if error is None:
                item["last_status"] = "completed"
                item["last_success_at"] = now
                item["last_output"] = summarize_output(output, side_effect_only=side_effect_only)
                item["state"] = _state_for_output(item["last_output"])
            else:
                item["error_count"] += 1
                item["last_status"] = "failed"
                item["last_error_type"] = type(error).__name__
                frames = traceback.extract_tb(error.__traceback__) if error.__traceback__ else []
                frame = frames[-1] if frames else None
                item["last_error"] = {
                    "type": type(error).__name__,
                    "method": method,
                    "at": now,
                    "location": (
                        {"file": frame.filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1],
                         "line": frame.lineno, "function": frame.name}
                        if frame else None
                    ),
                }
                item["last_output"] = None
                item["state"] = "error"

    def record_skip(self, name: str, status: str, *,
                    metrics: dict[str, Any] | None = None) -> None:
        """Record a policy/cadence skip without counting it as an execution tick."""
        now = time.time()
        with self._lock:
            item = self._modules.get(name)
            if item is None:
                return
            item["skip_count"] = int(item.get("skip_count", 0) or 0) + 1
            item["last_skip_at"] = now
            item["last_skip_status"] = str(status)[:48]
            item["last_skip_metrics"] = {
                str(key)[:48]: value
                for key, value in (metrics or {}).items()
                if isinstance(value, (str, bool, int, float))
            }
            if int(item.get("tick_count", 0) or 0) == 0 and item.get("initialized"):
                item["state"] = "skipped_by_policy"

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {name: dict(item) for name, item in self._modules.items()}

    def analysis(self) -> dict[str, Any]:
        """Aggregate execution/output evidence without inferring semantic correctness."""
        modules = self.snapshot()
        states: dict[str, int] = {}
        output_qualities: dict[str, int] = {}
        executed = 0
        total_ticks = total_errors = 0
        total_skips = modules_with_skips = 0
        modules_with_errors = 0
        for item in modules.values():
            state = str(item.get("state", "unknown"))
            states[state] = states.get(state, 0) + 1
            ticks = int(item.get("tick_count", 0) or 0)
            total_ticks += ticks
            errors = int(item.get("error_count", 0) or 0)
            total_errors += errors
            modules_with_errors += errors > 0
            skips = int(item.get("skip_count", 0) or 0)
            total_skips += skips
            modules_with_skips += skips > 0
            executed += ticks > 0
            output = item.get("last_output")
            if isinstance(output, dict):
                quality = str(output.get("quality", "unknown"))
                output_qualities[quality] = output_qualities.get(quality, 0) + 1
        return {
            "module_count": len(modules),
            "executed_module_count": executed,
            "total_ticks": total_ticks,
            "total_errors": total_errors,
            "total_skips": total_skips,
            "modules_with_skips": modules_with_skips,
            "modules_with_errors": modules_with_errors,
            "states": states,
            "last_output_qualities": output_qualities,
            "interpretation_limit": "Shape and numeric sanity only; semantic correctness is not established.",
        }
