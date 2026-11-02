"""Conservative selection of the user-designated radar return."""
from __future__ import annotations

import math
from typing import Any, Iterable


def selected_radar_target(
    targets: Iterable[Any], *, target_range_m: float = 1.8, tolerance_m: float = 0.55,
) -> dict | None:
    """Return at most the target nearest the configured range; never fall back.

    Radar IDs on the LD2450 are slot identifiers and can be reused. Selection
    is therefore based on measured position range, with confidence only as a
    tie breaker. The returned point is a radar return, not a semantic person ID.
    """
    try:
        target_range_m = float(target_range_m)
        tolerance_m = max(0.0, float(tolerance_m))
    except (TypeError, ValueError):
        target_range_m, tolerance_m = 1.8, 0.55
    if not math.isfinite(target_range_m) or not math.isfinite(tolerance_m):
        target_range_m, tolerance_m = 1.8, 0.55

    candidates: list[tuple[float, float, dict]] = []
    for target in targets or []:
        if not isinstance(target, dict):
            continue
        position = target.get("position_m") or target.get("position") or []
        try:
            if len(position) < 2:
                continue
            distance = math.hypot(float(position[0]), float(position[1]))
            confidence = float(target.get("confidence", 0.0) or 0.0)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(distance) or abs(distance - target_range_m) > tolerance_m:
            continue
        candidates.append((abs(distance - target_range_m), -confidence, target))
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][2] if candidates else None


def selected_radar_targets(
    targets: Iterable[Any], *, target_range_m: float = 1.8, tolerance_m: float = 0.55,
) -> list[dict]:
    """Return only the selected return, or an empty list when none qualifies."""
    target = selected_radar_target(
        targets, target_range_m=target_range_m, tolerance_m=tolerance_m,
    )
    return [target] if target is not None else []
