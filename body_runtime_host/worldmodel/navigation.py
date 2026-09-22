"""Fast geometric navigation guard for the embodied policy.

This is deliberately local and model-independent. It uses the current scene
coordinates to bias or block obviously unsafe actions, while the learned
policy remains responsible for choosing among safe alternatives.
"""
from __future__ import annotations

import math
from collections import deque
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


def _grid_route_action(
    observation: Any,
    body: Any,
    target: tuple[float, float],
    interaction_radius: float,
) -> str | None:
    """Return the first action on a short collision-free route to ``target``.

    The old steering rule only compared the target bearing with the current
    heading. That is sufficient in open space but fails when a pillar lies on
    the direct line: after one turn the same rule can turn the Body back into
    the pillar forever. This bounded BFS is deliberately local and cheap; it
    uses the latest perception frame and is recomputed after every action.
    """
    width = body.capabilities.get("world_width")
    height = body.capabilities.get("world_height")
    if width is None or height is None:
        return None
    width, height = int(width), int(height)
    start = (int(round(float(body.position[0]))), int(round(float(body.position[1]))))
    goal = (float(target[0]), float(target[1]))
    if not (0 <= start[0] < width and 0 <= start[1] < height):
        return None

    blocked: set[tuple[int, int]] = set()
    for obj in list(getattr(observation, "scene", []) or []):
        kind = str(getattr(obj, "kind", ""))
        if kind not in {"obstacle", "mobile_obstacle", "table", "chair"}:
            continue
        # A destination surface is not traversable, but cells adjacent to it
        # remain valid goals. Other solid objects occupy their observed cell.
        ox, oy = float(obj.position[0]), float(obj.position[1])
        blocked.add((int(round(ox)), int(round(oy))))

    def is_goal(cell: tuple[int, int]) -> bool:
        return math.hypot(cell[0] - goal[0], cell[1] - goal[1]) <= interaction_radius

    # Do not treat the current cell as blocked if perception overlaps the Body.
    blocked.discard(start)
    queue = deque([start])
    parents: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    goal_cell: tuple[int, int] | None = start if is_goal(start) else None
    directions = ((1, 0), (0, 1), (-1, 0), (0, -1))
    while queue and goal_cell is None:
        cell = queue.popleft()
        for dx, dy in directions:
            nxt = (cell[0] + dx, cell[1] + dy)
            if not (0 <= nxt[0] < width and 0 <= nxt[1] < height):
                continue
            if nxt in parents or nxt in blocked:
                continue
            parents[nxt] = cell
            if is_goal(nxt):
                goal_cell = nxt
                break
            queue.append(nxt)

    if goal_cell is None or goal_cell == start:
        return None
    step = goal_cell
    while parents[step] != start:
        parent = parents[step]
        if parent is None:
            return None
        step = parent
    desired = math.atan2(step[1] - start[1], step[0] - start[0])
    if abs(_angle_delta(float(body.orientation), desired)) < 0.1:
        return "forward"
    return _turn_toward_target(float(body.orientation), (float(step[0]), float(step[1])), (float(start[0]), float(start[1])))


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

    stage = str(body.capabilities.get("task_stage", "to_target"))
    table = next((o for o in objects if str(getattr(o, "kind", "")) == "table"), None)
    target = shelf if carrying else None
    if carrying and stage == "to_table" and table is not None:
        target = (float(table.position[0]), float(table.position[1]))
    target_size = 0.0
    if target is None:
        candidates = [o for o in objects if str(getattr(o, "kind", "")) == "target"]
        if candidates:
            target_obj = min(candidates, key=lambda o: math.hypot(float(o.position[0]) - px, float(o.position[1]) - py))
            target = (float(target_obj.position[0]), float(target_obj.position[1]))
            target_size = max(0.0, float(getattr(target_obj, "size", 0.0)))

    prior: Dict[str, float] = {}
    forbidden: set[str] = set()
    mobile = next((o for o in objects if str(getattr(o, "kind", "")) == "mobile_obstacle"), None)
    recommended: str | None = None
    phase = "to_target"
    distance: float | None = None
    if target is not None:
        bearing = math.atan2(target[1] - py, target[0] - px)
        delta = _angle_delta(heading, bearing)
        distance = math.hypot(target[0] - px, target[1] - py)
        phase = stage
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
        # Keep this threshold identical to SimulatedRoom._nearest_graspable:
        # reach depends on the object's footprint. A loose generic threshold
        # caused repeated failed grabs while the target was still one step
        # away.
        grab_distance = float(body.capabilities.get("reach", 1.8)) * (1.0 + 0.25 * target_size)
        route_radius = 1.25 if carrying else grab_distance
        routed = _grid_route_action(observation, body, target, route_radius)
        if routed is not None:
            recommended = routed
            prior[routed] = max(prior.get(routed, 0.0), 3.0)
        # When the pursuer is close, spend the Body's speed advantage to
        # create separation, but only if every traversed cell is clear.
        max_speed = int(float(body.capabilities.get("max_speed", 1.0)))
        width = body.capabilities.get("world_width")
        height = body.capabilities.get("world_height")
        if recommended == "forward" and max_speed >= 2 and mobile is not None:
            mobile_distance = math.hypot(float(mobile.position[0]) - px, float(mobile.position[1]) - py)
            path_clear = True
            for step in (1, 2):
                cell = (px + math.cos(heading) * step, py + math.sin(heading) * step)
                out_of_bounds = (
                    width is not None and height is not None
                    and (cell[0] < 0 or cell[1] < 0 or cell[0] >= float(width) or cell[1] >= float(height))
                )
                if out_of_bounds or any(
                    obj is not mobile
                    and str(getattr(obj, "kind", "")) in {"obstacle", "table", "chair"}
                    and math.hypot(float(obj.position[0]) - cell[0], float(obj.position[1]) - cell[1]) < 0.6
                    for obj in objects
                ) or math.hypot(float(mobile.position[0]) - cell[0], float(mobile.position[1]) - cell[1]) < 0.6:
                    path_clear = False
                    break
            if mobile_distance <= 4.0 and path_clear:
                recommended = "sprint"
                prior["sprint"] = 3.4
        if not carrying and distance <= grab_distance:
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
        object_kind = str(getattr(obj, "kind", ""))
        # The simulator's collision model treats furniture and surfaces as
        # solid volumes too. They are valid destinations for manipulation, but
        # they are still obstacles while the Body is travelling elsewhere.
        if object_kind not in {"obstacle", "mobile_obstacle", "table", "chair"}:
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
        # A blocking surface can be the current manipulation target. If the
        # Body is already within release/grasp range, complete that operation
        # instead of turning away from the table or target.
        if recommended not in {"grab", "release"}:
            recommended = preferred

    return {
        "prior": prior,
        "forbidden": sorted(forbidden),
        "target": list(target) if target else None,
        "phase": phase,
        "distance_to_target": round(distance, 3) if distance is not None else None,
        "grasp_distance": round(grab_distance, 3) if target is not None and not carrying else None,
        "recommended": recommended,
        "obstacle_ahead": bool(nearby_obstacles),
        "boundary_ahead": boundary_ahead,
        "mobile_obstacle_distance": round(
            math.hypot(float(mobile.position[0]) - px, float(mobile.position[1]) - py), 3
        ) if mobile is not None else None,
    }
