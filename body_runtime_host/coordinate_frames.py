"""Coordinate conventions shared by the Body map and robot preview."""
from __future__ import annotations

import math


def compass_heading_degrees(heading_radians: float) -> float:
    """Convert world heading (east=0, counter-clockwise) to compass degrees."""
    return (90.0 - math.degrees(float(heading_radians))) % 360.0


def north_up_svg_rotation_degrees(heading_radians: float) -> float:
    """Rotation for drawings whose unrotated front points toward screen north."""
    return 90.0 - math.degrees(float(heading_radians))
