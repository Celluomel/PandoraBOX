"""Fast geometric navigation guard for the embodied policy.

This is deliberately local and model-independent. It uses the current scene
coordinates to bias or block obviously unsafe actions, while the learned
policy remains responsible for choosing among safe alternatives.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Iterable


def _angle_delta(a: float, b: float) -> float:
    return math.atan2(math.sin(b - a), math.cos(b - a))


def _turn_toward_target(heading: float, target: tuple[float, float], position: tuple[float, float]) -> str:
    """Return the quarter-turn that points most directly at ``target``.

    The simulated body turns in 90-degree increments, so choosing by the
    sign of the current bearing is not enough near a wrap-around or when the
    target is behind the body. Compare the actual post-turn headings instead.
    """
    px, py = position
    bearing = math.atan2(target[1] - py, target[0] - px)
    candidates = {
        "turn_left": heading + math.pi / 2,
        "turn_right": heading - math.pi / 2,
    }
    return min(candidates, key=lambda action: abs(_angle_delta(candidates[action], bearing)))


def navigation_guidance(observation: Any, body: Any, carrying: bool = False) -> Dict[str, Any]:
    objects = list(getattr(observation, "scene", []) or [])
    px, py = float(body.position[0]), float(body.position[1])
    heading = float(body.orientation)
    shelf = None
    text = str(getattr(observation, "text", "") or "")
    import re
    match = re.search(r"Shelf at \(([-\d.]+),\s*([-\d.]+)\)", text)
    if match:
        shelf = (float(match.group(1)), float(match.group(2)))

    target = shelf if carrying else None
    if target is None:
        candidates = [o for o in objects if str(getattr(o, "kind", "")) == "target"]
        if candidates:
            target_obj = min(candidates, key=lambda o: math.hypot(float(o.position[0]) - px, float(o.position[1]) - py))
            target = (float(target_obj.position[0]), float(target_obj.position[1]))

    prior: Dict[str, float] = {}
    forbidden: set[str] = set()
    recommended: str | None = None
    phase = "to_target"
    distance: float | None = None
    if target is not None:
        bearing = math.atan2(target[1] - py, target[0] - px)
        delta = _angle_delta(heading, bearing)
        distance = math.hypot(target[0] - px, target[1] - py)
        phase = "to_shelf" if carrying else "to_target"
        forward_position = (px + math.cos(heading), py + math.sin(heading))
        forward_distance = math.hypot(target[0] - forward_position[0], target[1] - forward_position[1])
        forward_progress = distance - forward_distance

        # A body should advance whenever its current heading makes progress.
        # This prevents the learned policy from oscillating between turns at
        # the starting point while the target remains many cells away.
        if forward_progress > 0.05:
            recommended = "forward"
            prior["forward"] = 2.4
        else:
            recommended = _turn_toward_target(heading, target, (px, py))
            prior[recommended] = 2.0
            prior["forward"] = -0.35
        if not carrying and distance <= float(body.capabilities.get("reach", 1.8)) * 1.25:
            prior["grab"] = 1.6
            recommended = "grab"
        if carrying and distance <= 1.25:
            prior["release"] = 1.8
            recommended = "release"

    # A forward step is unsafe when it enters an obstacle or leaves the known
    # world. The latter was previously invisible to the navigation guard and
    # allowed the policy to repeatedly drive into a wall at the map edge.
    forward = (px + math.cos(heading), py + math.sin(heading))
    nearby_obstacles = []
    for obj in objects:
        if str(getattr(obj, "kind", "")) != "obstacle":
            continue
        ox, oy = float(obj.position[0]), float(obj.position[1])
        radius = max(0.65, float(getattr(obj, "size", 1.0)) * 0.7)
        if math.hypot(ox - forward[0], oy - forward[1]) <= radius:
            nearby_obstacles.append((ox, oy))
    width = body.capabilities.get("world_width")
    height = body.capabilities.get("world_height")
    boundary_ahead = (
        width is not None and height is not None and
        (forward[0] < 0 or forward[1] < 0 or forward[0] >= float(width) or forward[1] >= float(height))
    )
    if nearby_obstacles or boundary_ahead:
        forbidden.add("forward")
        nearest = min(nearby_obstacles, key=lambda p: math.hypot(p[0] - px, p[1] - py)) if nearby_obstacles else None
        # Prefer the detour that remains closest to the destination after the
        # turn, rather than always turning away from the obstacle's bearing.
        if target is not None:
            preferred = min(
                ("turn_left", "turn_right"),
                key=lambda action: abs(
                    _angle_delta(
                        heading + (math.pi / 2 if action == "turn_left" else -math.pi / 2),
                        math.atan2(target[1] - py, target[0] - px),
                    )
                ),
            )
        elif nearest is not None:
            obstacle_bearing = math.atan2(nearest[1] - py, nearest[0] - px)
            side = _angle_delta(heading, obstacle_bearing)
            preferred = "turn_right" if side > 0 else "turn_left"
        else:
            preferred = _turn_toward_target(heading, target, (px, py)) if target is not None else "turn_left"
        prior[preferred] = max(prior.get(preferred, 0.0), 1.35)
        prior["forward"] = -2.0
        recommended = preferred

    return {
        "prior": prior,
        "forbidden": sorted(forbidden),
        "target": list(target) if target else None,
        "phase": phase,
        "distance_to_target": round(distance, 3) if distance is not None else None,
        "recommended": recommended,
        "obstacle_ahead": bool(nearby_obstacles),
        "boundary_ahead": boundary_ahead,
    }
