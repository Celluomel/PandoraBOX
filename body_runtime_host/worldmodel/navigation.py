"""Fast geometric navigation guard for the embodied policy.

This is deliberately local and model-independent. It uses the current scene
coordinates to bias or block obviously unsafe actions, while the learned
policy remains responsible for choosing among safe alternatives.
"""
from __future__ import annotations

import math
import heapq
from collections import deque
from itertools import count
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


def _cell_clear(
    x: float,
    y: float,
    objects: list[Any],
    width: Any,
    height: Any,
) -> bool:
    if width is not None and height is not None and not (0 <= x < float(width) and 0 <= y < float(height)):
        return False
    for obj in objects:
        kind = str(getattr(obj, "kind", ""))
        if kind not in {"obstacle", "mobile_obstacle", "table", "chair"}:
            continue
        if math.hypot(float(obj.position[0]) - x, float(obj.position[1]) - y) < 0.6:
            return False
    return True


def _predict_mobile_step(
    objects: list[Any],
    position: tuple[float, float],
    moves_next: bool = True,
) -> tuple[float, float] | None:
    """Predict the next legal pursuit cell when its speed phase allows motion."""
    if not moves_next:
        return None
    mobile = next((o for o in objects if str(getattr(o, "kind", "")) == "mobile_obstacle"), None)
    if mobile is None:
        return None
    mx, my = float(mobile.position[0]), float(mobile.position[1])
    current_distance = math.hypot(mx - position[0], my - position[1])
    static = [o for o in objects if str(getattr(o, "kind", "")) in {"obstacle", "table", "chair"}]
    choices = []
    for dx, dy in ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)):
        cell = (mx + dx, my + dy)
        distance = math.hypot(cell[0] - position[0], cell[1] - position[1])
        if distance >= current_distance or math.hypot(cell[0] - position[0], cell[1] - position[1]) < 0.6:
            continue
        if any(math.hypot(float(o.position[0]) - cell[0], float(o.position[1]) - cell[1]) < 0.6 for o in static):
            continue
        choices.append((distance, cell))
    return min(choices, key=lambda item: item[0])[1] if choices else None


def _mobile_safety_radius(mobile: Any, body: Any) -> float:
    """Return the minimum body-to-mobile separation for predictive routing."""
    configured = body.capabilities.get("mobile_obstacle_clearance")
    if configured is not None:
        return max(0.8, float(configured))
    size = float(getattr(mobile, "size", 0.8) or 0.8)
    # Body footprint + obstacle footprint + a small reaction margin.
    return max(1.15, 0.6 + (size * 0.5) + 0.3)


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
    scene_objects = list(getattr(observation, "scene", []) or [])
    for obj in scene_objects:
        kind = str(getattr(obj, "kind", ""))
        if kind not in {"obstacle", "mobile_obstacle", "table", "chair"}:
            continue
        # A destination surface is not traversable, but cells adjacent to it
        # remain valid goals. Other solid objects occupy their observed cell.
        ox, oy = float(obj.position[0]), float(obj.position[1])
        blocked.add((int(round(ox)), int(round(oy))))
    predicted_mobile = _predict_mobile_step(
        scene_objects,
        (float(body.position[0]), float(body.position[1])),
        bool(body.capabilities.get("mobile_obstacle_moves_next", True)),
    )
    if predicted_mobile is not None:
        blocked.add((int(round(predicted_mobile[0])), int(round(predicted_mobile[1]))))

    mobile_obj = next((o for o in scene_objects if str(getattr(o, "kind", "")) == "mobile_obstacle"), None)
    if mobile_obj is not None:
        # Receding-horizon space-time planning: evaluate candidate Body paths
        # against the pursuer's own changing speed and pursuit step, rather
        # than treating its present location as a static wall.
        start_heading = int(round((float(body.orientation) % (2 * math.pi)) / (math.pi / 2))) % 4
        mobile_start = (
            int(round(float(mobile_obj.position[0]))),
            int(round(float(mobile_obj.position[1]))),
        )
        phase_start = float(body.capabilities.get("mobile_motion_phase", 0.5))
        first_step = int(body.capabilities.get("simulation_step", 0)) + 1
        max_speed = max(1, min(2, int(float(body.capabilities.get("max_speed", 1.0)))))
        mobile_speed = float(body.capabilities.get("mobile_obstacle_speed", 0.55))
        mobile_clearance = _mobile_safety_radius(mobile_obj, body)
        static_blocked = {
            (int(round(float(o.position[0]))), int(round(float(o.position[1]))))
            for o in scene_objects
            if str(getattr(o, "kind", "")) in {"obstacle", "table", "chair"}
        }
        actions = [("forward", 1, 0), ("backward", -1, 0), ("turn_left", 0, 1),
                   ("turn_right", 0, -1), ("wait", 0, 0)]
        if max_speed >= 2:
            actions.extend([("sprint", 2, 0), ("retreat", -2, 0)])
        queue = []
        order = count()
        start_state = (start[0], start[1], start_heading, mobile_start[0], mobile_start[1], round(phase_start, 2), 0)

        def heuristic(x: int, y: int) -> float:
            return max(0.0, math.hypot(x - goal[0], y - goal[1]) - interaction_radius) / max_speed

        heapq.heappush(queue, (heuristic(*start), 0.0, next(order), start_state, None))
        best_cost: dict[tuple, float] = {start_state: 0.0}
        expansions = 0
        while queue and expansions < 5000:
            _, cost, _, state, first_action = heapq.heappop(queue)
            x, y, heading_idx, mx, my, phase, elapsed = state
            if cost > best_cost.get(state, math.inf) + 1e-9:
                continue
            expansions += 1
            if math.hypot(x - goal[0], y - goal[1]) <= interaction_radius:
                if first_action is not None:
                    return first_action
                break
            if elapsed >= 18:
                continue
            heading_angle = heading_idx * math.pi / 2
            for action_name, distance, turn in actions:
                next_heading = (heading_idx + turn) % 4 if turn else heading_idx
                nx, ny = x, y
                sign = 1 if distance > 0 else -1
                for _ in range(abs(distance)):
                    if distance == 0:
                        break
                    dx, dy = round(math.cos(heading_angle)), round(math.sin(heading_angle))
                    cell = (nx + sign * dx, ny + sign * dy)
                    if not (0 <= cell[0] < width and 0 <= cell[1] < height) or cell in static_blocked or cell == (mx, my):
                        break
                    nx, ny = cell
                if distance and (nx, ny) == (x, y):
                    continue

                # The obstacle reacts after this Body decision, pursuing the
                # Body's pre-action location with its smoothly varying speed.
                speed = mobile_speed if elapsed == 0 else 0.55 + 0.35 * math.sin((first_step + elapsed) * 0.18)
                next_phase = phase + speed
                nmx, nmy = mx, my
                if next_phase >= 1.0:
                    next_phase -= 1.0
                    target_distance = math.hypot(mx - x, my - y)
                    choices = []
                    for odx, ody in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        cell = (mx + odx, my + ody)
                        d = math.hypot(cell[0] - x, cell[1] - y)
                        if d >= target_distance or d < 0.6 or cell in static_blocked or cell == (nx, ny):
                            continue
                        choices.append((d, cell))
                    if choices:
                        nmx, nmy = min(choices, key=lambda item: item[0])[1]
                next_phase = max(0.0, min(0.99, next_phase))
                separation = math.hypot(nmx - nx, nmy - ny)
                # Treat the predicted separation as a hard constraint. A
                # short route that enters the mobile object's reaction zone
                # is not a valid route and is the source of the old
                # advance/retreat oscillation.
                if separation < mobile_clearance:
                    continue
                risk_cost = max(0.0, (mobile_clearance + 1.0) - separation) * 1.4
                next_cost = cost + 1.0 + risk_cost
                next_elapsed = elapsed + 1
                next_state = (nx, ny, next_heading, nmx, nmy, round(next_phase, 2), next_elapsed)
                if next_cost >= best_cost.get(next_state, math.inf):
                    continue
                best_cost[next_state] = next_cost
                first = first_action or action_name
                score = next_cost + heuristic(nx, ny)
                heapq.heappush(queue, (score, next_cost, next(order), next_state, first))

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
    delta = abs(_angle_delta(float(body.orientation), desired))
    if delta > math.radians(135):
        # When the route lies behind the Body, both quarter-turns are equally
        # indirect. Choose the intermediate heading whose next cell is free;
        # otherwise a correct route can rotate into a pursuer and trigger a
        # retreat/sprint oscillation before it ever faces the route.
        turns = {
            "turn_left": float(body.orientation) + math.pi / 2,
            "turn_right": float(body.orientation) - math.pi / 2,
        }
        safe_turns = []
        for action, turn_heading in turns.items():
            next_cell = (
                int(round(float(body.position[0]) + math.cos(turn_heading))),
                int(round(float(body.position[1]) + math.sin(turn_heading))),
            )
            if next_cell not in blocked and 0 <= next_cell[0] < width and 0 <= next_cell[1] < height:
                safe_turns.append(action)
        if safe_turns:
            return safe_turns[0]
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
    mobile_predicted = _predict_mobile_step(
        objects, (px, py), bool(body.capabilities.get("mobile_obstacle_moves_next", True))
    )
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
            after_sprint = (
                px + math.cos(heading) * 2.0,
                py + math.sin(heading) * 2.0,
            )
            sprint_distance = math.hypot(target[0] - after_sprint[0], target[1] - after_sprint[1]) if target else math.inf
            sprint_makes_progress = distance is not None and sprint_distance < distance - 0.5
            interaction_radius = float(body.capabilities.get("reach", 1.8)) * (1.0 + 0.25 * target_size) if not carrying else 1.25
            sprint_skips_interaction = bool(
                distance is not None and distance > interaction_radius
                and any(
                    math.hypot(target[0] - (px + math.cos(heading) * step), target[1] - (py + math.sin(heading) * step)) <= interaction_radius
                    for step in (1, 2)
                )
            )
            path_clear = True
            for step in (1, 2):
                cell = (px + math.cos(heading) * step, py + math.sin(heading) * step)
                out_of_bounds = (
                    width is not None and height is not None
                    and (cell[0] < 0 or cell[1] < 0 or cell[0] >= float(width) or cell[1] >= float(height))
                )
                if out_of_bounds or (mobile_predicted is not None and math.hypot(mobile_predicted[0] - cell[0], mobile_predicted[1] - cell[1]) < 0.6) or any(
                    obj is not mobile
                    and str(getattr(obj, "kind", "")) in {"obstacle", "table", "chair"}
                    and math.hypot(float(obj.position[0]) - cell[0], float(obj.position[1]) - cell[1]) < 0.6
                    for obj in objects
                ) or math.hypot(float(mobile.position[0]) - cell[0], float(mobile.position[1]) - cell[1]) < 0.6:
                    path_clear = False
                    break
            if mobile_distance <= 4.0 and path_clear and sprint_makes_progress and not sprint_skips_interaction:
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
    if mobile_predicted is not None and math.hypot(mobile_predicted[0] - forward[0], mobile_predicted[1] - forward[1]) <= 0.65:
        nearby_obstacles.append(mobile_predicted)
    width = body.capabilities.get("world_width")
    height = body.capabilities.get("world_height")
    boundary_ahead = (
        width is not None and height is not None and
        (forward[0] < 0 or forward[1] < 0 or forward[0] >= float(width) or forward[1] >= float(height))
    )
    if nearby_obstacles or boundary_ahead:
        forbidden.add("forward")
        nearest = min(nearby_obstacles, key=lambda p: math.hypot(p[0] - px, p[1] - py)) if nearby_obstacles else None
        mobile_distance = math.hypot(float(mobile.position[0]) - px, float(mobile.position[1]) - py) if mobile else math.inf
        if mobile is not None and mobile_distance <= 2.2:
            mobile_dx = float(mobile.position[0]) - px
            mobile_dy = float(mobile.position[1]) - py
            forward_component = mobile_dx * math.cos(heading) + mobile_dy * math.sin(heading)
            lateral_component = abs(-mobile_dx * math.sin(heading) + mobile_dy * math.cos(heading))
            rear = (px - math.cos(heading), py - math.sin(heading))
            rear_clear = _cell_clear(rear[0], rear[1], objects, width, height)
            max_speed = float(body.capabilities.get("max_speed", 1.0))
            retreat_clear = all(
                _cell_clear(px - math.cos(heading) * step, py - math.sin(heading) * step,
                            objects, width, height)
                for step in range(1, max(1, int(max_speed)) + 1)
            )
            forward_clear = _cell_clear(forward[0], forward[1], objects, width, height)
            sprint_clear = all(
                _cell_clear(px + math.cos(heading) * step, py + math.sin(heading) * step,
                            objects, width, height)
                for step in (1, 2)
            )
            if forward_component > 0 and lateral_component <= 1.0 and max_speed >= 2 and sprint_clear:
                recommended = "sprint"
                prior["sprint"] = max(prior.get("sprint", 0.0), 3.6)
            elif forward_component > 0 and lateral_component <= 1.0 and retreat_clear and max_speed >= 2:
                recommended = "retreat"
                prior["retreat"] = max(prior.get("retreat", 0.0), 3.4)
            elif forward_component > 0 and lateral_component <= 1.0 and rear_clear:
                recommended = "backward"
                prior["backward"] = max(prior.get("backward", 0.0), 3.4)
            elif not forward_clear and not rear_clear:
                # Hold position rather than spin in a tight, occupied corridor.
                recommended = "wait"
                prior["wait"] = max(prior.get("wait", 0.0), 2.8)
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
        if recommended not in {"grab", "release", "sprint", "retreat", "backward", "wait"}:
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
        "mobile_obstacle_blocking": bool(
            mobile is not None
            and math.hypot(float(mobile.position[0]) - px, float(mobile.position[1]) - py) <= 1.25
        ),
        "mobile_obstacle_speed": round(float(body.capabilities.get("mobile_obstacle_speed", 0.0)), 3),
        "mobile_obstacle_predicted_position": list(mobile_predicted) if mobile_predicted is not None else None,
    }
