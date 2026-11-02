"""Shared, robot-agnostic interpretation of Body hardware capability reports."""
from __future__ import annotations

import time
from typing import Any, Iterable


def latest_observations(observations: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for item in observations:
        if not isinstance(item, dict):
            continue
        subject = str(item.get("subject") or "")
        try:
            observed_at = float(item.get("observed_at") or 0.0)
        except (TypeError, ValueError, OverflowError):
            observed_at = 0.0
        previous = latest.get(subject)
        try:
            previous_at = float(previous.get("observed_at") or 0.0) if previous else -1.0
        except (TypeError, ValueError, OverflowError):
            previous_at = 0.0
        if previous is None or observed_at >= previous_at:
            latest[subject] = item
    return latest


def robot_inventory_observation(observations: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    """Return generic Body inventory, adapting the legacy FNK status if needed."""
    latest = latest_observations(observations)
    item = latest.get("robot.capability_inventory")
    if isinstance(item, dict) and isinstance(item.get("value"), dict):
        return item
    legacy = latest.get("fnk0031.usb_status")
    legacy_value = legacy.get("value") if isinstance(legacy, dict) else None
    if not isinstance(legacy_value, dict):
        return None
    installed = legacy_value.get("servo_motors_installed")
    connected = legacy_value.get("connected")
    authorized = legacy_value.get("actuation_enabled")
    adapted = {
        "contract": "body_robot_capability_inventory.v1",
        "robot_id": "fnk0031",
        "robot_model": legacy_value.get("robot_model") or "FNK0031",
        "simulated": False,
        "inventory_source": legacy_value.get("servo_inventory_source", "legacy_fnk_status"),
        "capabilities": {"locomotion": {
            "installed": installed,
            "operational": connected,
            "authorized": authorized,
            "available": installed is True and connected is True and authorized is True,
            "supported_actions": legacy_value.get("supported_actions") or [],
        }},
    }
    provenance = legacy.get("provenance") if isinstance(legacy.get("provenance"), dict) else {}
    return {
        **legacy,
        "subject": "robot.capability_inventory",
        "value": adapted,
        "provenance": {**provenance, "adapter": "legacy_fnk_status"},
    }


def robot_capability_report(
    observations: Iterable[dict[str, Any]], capability: str, *, now: float | None = None,
    max_age: float = 15.0,
) -> dict[str, Any]:
    """Resolve readiness from the generic Body inventory, with an FNK adapter fallback.

    A capability is usable only when Body explicitly reports hardware installed,
    operational, authorized, fresh, and non-simulated. Missing fields stay unknown.
    """
    current = time.time() if now is None else float(now)
    item = robot_inventory_observation(observations)
    value = item.get("value") if isinstance(item, dict) else None
    source = str(item.get("source") or "robot.capability_inventory") if isinstance(item, dict) else None
    try:
        observed_at = float(item.get("observed_at") or 0.0) if isinstance(item, dict) else 0.0
    except (TypeError, ValueError, OverflowError):
        observed_at = 0.0
    age = max(0.0, current - observed_at) if observed_at else None
    fresh = age is not None and age <= max_age
    provenance = item.get("provenance") if isinstance(item, dict) and isinstance(item.get("provenance"), dict) else {}
    source_text = " ".join(str(part or "").lower() for part in (
        item.get("source") if isinstance(item, dict) else "",
        value.get("source") if isinstance(value, dict) else "",
        provenance.get("source"),
        provenance.get("adapter"),
    ))
    simulated = bool(
        value.get("simulated", False)
        or value.get("simulated_only", False)
        or provenance.get("simulated", False)
        or any(marker in source_text for marker in ("simulation", "simulated", "sim_robot", "virtual_lidar"))
    ) if isinstance(value, dict) else False
    capabilities = value.get("capabilities") if isinstance(value, dict) else None
    record = capabilities.get(capability) if isinstance(capabilities, dict) else None
    record = record if isinstance(record, dict) else {}
    ready = (
        fresh and not simulated and record.get("installed") is True
        and record.get("operational") is True and record.get("authorized") is True
        and record.get("available") is True
    )
    return {
        "ready": ready,
        "known": bool(record),
        "fresh": fresh,
        "age_seconds": age,
        "simulated": simulated,
        "source": source if isinstance(value, dict) else None,
        "robot_id": value.get("robot_id") if isinstance(value, dict) else None,
        "robot_model": value.get("robot_model") if isinstance(value, dict) else None,
        "inventory_source": value.get("inventory_source") if isinstance(value, dict) else None,
        "record": record,
    }
