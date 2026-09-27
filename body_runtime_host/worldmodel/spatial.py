"""Sensor-agnostic spatial reference for the Body world frame.

Indoor robots normally have no useful GNSS signal.  The Body therefore keeps
its planning coordinates in a local metric frame, while accepting an optional
geographic fix to anchor that frame when GNSS is available.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional, Sequence

EARTH_RADIUS_M = 6_378_137.0


def geo_fix(value: Any) -> Dict[str, float]:
    if not isinstance(value, dict):
        return {}
    latitude = value.get("latitude", value.get("lat"))
    longitude = value.get("longitude", value.get("lon", value.get("lng")))
    if latitude is None or longitude is None:
        return {}
    try:
        fix = {"latitude": float(latitude), "longitude": float(longitude)}
        if value.get("altitude", value.get("alt")) is not None:
            fix["altitude"] = float(value.get("altitude", value.get("alt")))
        return fix
    except (TypeError, ValueError):
        return {}


class LocalMapReference:
    """Project geographic fixes into a stable east/north local frame."""

    def __init__(self) -> None:
        self.origin: Dict[str, float] = {}

    def project(self, value: Any) -> Optional[list[float]]:
        fix = geo_fix(value)
        if not fix:
            return None
        if not self.origin:
            self.origin = dict(fix)
            return [0.0, 0.0, float(fix.get("altitude", 0.0) - self.origin.get("altitude", 0.0))]
        lat0 = math.radians(self.origin["latitude"])
        east = math.radians(fix["longitude"] - self.origin["longitude"]) * EARTH_RADIUS_M * math.cos(lat0)
        north = math.radians(fix["latitude"] - self.origin["latitude"]) * EARTH_RADIUS_M
        altitude = float(fix.get("altitude", self.origin.get("altitude", 0.0)) - self.origin.get("altitude", 0.0))
        return [east, north, altitude]

    def metadata(self, source: str = "odometry", accuracy: Any = None) -> Dict[str, Any]:
        try:
            accuracy_value = float(accuracy) if accuracy is not None else None
        except (TypeError, ValueError):
            accuracy_value = None
        return {
            "coordinate_frame": "local_map",
            "position_source": source,
            "position_accuracy_m": accuracy_value,
            "geo_origin": dict(self.origin),
        }
