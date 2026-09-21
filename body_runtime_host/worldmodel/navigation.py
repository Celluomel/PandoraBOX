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
    if target is not None:
        bearing = math.atan2(target[1] - py, target[0] - px)
        delta = _angle_delta(heading, bearing)
        distance = math.hypot(target[0] - px, target[1] - py)
        if abs(delta) < math.pi / 6:
            prior["forward"] = 1.25
        elif delta > 0:
            prior["turn_left"] = 1.0
            prior["forward"] = -0.35
        else:
            prior["turn_right"] = 1.0
            prior["forward"] = -0.35
        if not carrying and distance <= float(body.capabilities.get("reach", 1.8)) * 1.25:
            prior["grab"] = 1.6
        if carrying and distance <= 1.25:
            prior["release"] = 1.8

    # A forward step is unsafe when it enters an obstacle's local footprint.
    forward = (px + math.cos(heading), py + math.sin(heading))
    nearby_obstacles = []
    for obj in objects:
        if str(getattr(obj, "kind", "")) != "obstacle":
            continue
        ox, oy = float(obj.position[0]), float(obj.position[1])
        radius = max(0.65, float(getattr(obj, "size", 1.0)) * 0.7)
        if math.hypot(ox - forward[0], oy - forward[1]) <= radius:
            nearby_obstacles.append((ox, oy))
    if nearby_obstacles:
        forbidden.add("forward")
        nearest = min(nearby_obstacles, key=lambda p: math.hypot(p[0] - px, p[1] - py))
        obstacle_bearing = math.atan2(nearest[1] - py, nearest[0] - px)
        side = _angle_delta(heading, obstacle_bearing)
        preferred = "turn_right" if side > 0 else "turn_left"
        prior[preferred] = max(prior.get(preferred, 0.0), 1.35)
        prior["forward"] = -2.0

    return {"prior": prior, "forbidden": sorted(forbidden), "target": list(target) if target else None, "obstacle_ahead": bool(nearby_obstacles)}
