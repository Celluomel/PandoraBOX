"""Portable FNK0031 robot-side protocol helpers.

The firmware transport can be HTTP, serial-over-IP or another gateway, but
the Body always consumes this normalized JSON shape.
"""
from __future__ import annotations

import time
from typing import Any, Dict

PROTOCOL_VERSION = "fnk0031.body.v1"


def normalize_sensors(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("FNK0031 sensors payload must be an object")
    position = payload.get("position")
    if position is None:
        position = [payload.get("x", 0.0), payload.get("y", 0.0), payload.get("z", 0.0)]
    if not isinstance(position, (list, tuple)) or len(position) < 2:
        raise ValueError("FNK0031 sensors position must contain x and y")
    try:
        position = [float(position[0]), float(position[1]), float(position[2] if len(position) > 2 else 0.0)]
        orientation = float(payload.get("orientation", payload.get("yaw", 0.0)) or 0.0)
    except (TypeError, ValueError) as exc:
        raise ValueError("FNK0031 pose values must be numeric") from exc
    objects = payload.get("objects") or []
    if not isinstance(objects, list):
        raise ValueError("FNK0031 objects must be an array")
    return {
        **payload,
        "protocol_version": str(payload.get("protocol_version") or PROTOCOL_VERSION),
        "timestamp": float(payload.get("timestamp") or time.time()),
        "position": position,
        "orientation": orientation,
        "objects": [item for item in objects if isinstance(item, dict)],
        "capabilities": dict(payload.get("capabilities") or {}),
        "imu": dict(payload.get("imu") or payload.get("imu_data") or {}),
        "coordinate_frame": str(payload.get("coordinate_frame") or "local_map"),
        "position_source": str(payload.get("position_source") or "odometry"),
    }


def normalize_command(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("FNK0031 command must be an object")
    command = str(payload.get("type") or "").strip().lower()
    if not command:
        raise ValueError("FNK0031 command type is required")
    params = payload.get("params") or {}
    if not isinstance(params, dict):
        raise ValueError("FNK0031 command params must be an object")
    return {"protocol_version": PROTOCOL_VERSION, **payload, "type": command, "params": params}
