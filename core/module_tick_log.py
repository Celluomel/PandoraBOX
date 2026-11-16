"""Bounded, privacy-safe execution telemetry for cognitive modules."""

from __future__ import annotations

import math
import threading
import time
import traceback
from typing import Any


def summarize_output(value: Any) -> dict[str, Any]:
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
            "no_return_unverified" if value is None else
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
        # Tick receipts may contain compact control-flow facts. Preserve only
        # allowlisted enum/numeric fields so the audit can tell "scheduled"
        # from "deferred" without retaining prompts, prose, or arbitrary data.
        receipt_fields: dict[str, Any] = {}
        receipt_enum_fields = {
            "outcome_status", "status", "reason_code", "effect_status",
            "aspiration_planning", "goal_plan_schedule_status", "persistence_status",
        }
        receipt_numeric_fields = {
            "cycle", "goal_plans_synchronized", "goal_plans_scheduled",
            "goal_plans_pending", "pending_count", "history_count",
            "signal_count", "cluster_count",
        }
        for key in receipt_enum_fields:
            item = value.get(key)
            if isinstance(item, str) and item.isascii() and len(item) <= 64 \
                    and item.replace("_", "").replace("-", "").isalnum():
                receipt_fields[key] = item
        for key in receipt_numeric_fields:
            item = value.get(key)
            if isinstance(item, int) and not isinstance(item, bool):
                receipt_fields[key] = item
        if isinstance(value.get("aspiration_plan_exists"), bool):
            receipt_fields["aspiration_plan_exists"] = value["aspiration_plan_exists"]
        if receipt_fields:
            result["receipt_fields"] = receipt_fields
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
    """Describe observable output shape without implying semantic correctness."""
    quality = str((output or {}).get("quality", "unknown"))
    if quality == "invalid_numeric":
        return "degraded"
    if quality in {"empty", "no_return_unverified", "shape_only", "unknown"}:
        return "output_unverified"
    return "output_present_unvalidated"


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
                "method_results": {},
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
               duration_ms: float, output: Any = None, error: BaseException | None = None) -> None:
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
                "method_results": {},
            })
            item["tick_count"] += 1
            item["last_tick_at"] = now
            item["last_duration_ms"] = round(max(0.0, duration_ms), 3)
            if method not in item["observed_methods"]:
                item["observed_methods"] = (item["observed_methods"] + [method])[-12:]
            method_result = item.setdefault("method_results", {}).setdefault(method, {
                "tick_count": 0,
                "error_count": 0,
                "last_tick_at": None,
                "last_duration_ms": None,
                "last_status": "not_observed",
                "last_error_type": None,
                "last_output": None,
            })
            method_result["tick_count"] += 1
            method_result["last_tick_at"] = now
            method_result["last_duration_ms"] = round(max(0.0, duration_ms), 3)
            if error is None:
                item["last_status"] = "completed"
                item["last_success_at"] = now
                item["last_output"] = summarize_output(output)
                item["state"] = _state_for_output(item["last_output"])
                method_result["last_status"] = "completed"
                method_result["last_error_type"] = None
                method_result["last_output"] = item["last_output"]
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
                method_result["error_count"] += 1
                method_result["last_status"] = "failed"
                method_result["last_error_type"] = type(error).__name__
                method_result["last_output"] = None

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
            return {
                name: {
                    **item,
                    "observed_methods": list(item.get("observed_methods", [])),
                    "method_results": {
                        method: dict(result)
                        for method, result in item.get("method_results", {}).items()
                    },
                }
                for name, item in self._modules.items()
            }

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
