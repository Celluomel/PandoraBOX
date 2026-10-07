"""Deterministic, explicitly simulated autonomy scenario for workflow testing."""
from __future__ import annotations

import heapq
import math
import time
from typing import Any


SCENARIO_ID = "autonomy-room-v1"
FRAME_ID = "map"
GRID = 0.25


def sensor_suite(config: dict[str, Any]) -> dict[str, Any]:
    now = time.time()
    if config.get("inject_stale_data"):
        now -= 10
    return {
        "kind": "sim_sensor_bundle", "scenario_id": SCENARIO_ID,
        "source": "simulation", "simulated": True, "actuation": False,
        "frame_id": FRAME_ID, "timestamp": now,
        "sensors": {
            "camera": {"timestamp": now, "objects": [
                {"id": "goal-cup", "label": "cup", "position": [4.5, 0.0], "confidence": 0.94},
                {"id": "table-1", "label": "table", "position": [2.5, 0.0], "confidence": 0.91},
            ]},
            "lidar": {"timestamp": now, "frame_id": FRAME_ID, "obstacles": [
                {"id": "table-1", "kind": "static", "position": [2.5, 0.0], "radius_m": 0.48},
            ], "detections": [
                {"id": "goal-cup", "position": [4.5, 0.0], "range_m": 4.0, "confidence": 0.9},
            ], "returns": 240, "confidence": 0.98},
            "mmwave": {"timestamp": now, "frame_id": FRAME_ID, "targets": [
                {"id": "person-1", "kind": "dynamic", "position": [2.5, 1.2], "velocity_mps": [0.0, -0.15], "confidence": 0.86},
            ]},
            "imu": {"timestamp": now, "frame_id": FRAME_ID, "roll_deg": 0.4, "pitch_deg": -0.2, "yaw_deg": 0.0, "confidence": 0.99},
            "odometry": {"timestamp": now, "frame_id": FRAME_ID, "position": [0.5, 0.0], "heading_deg": 0.0, "linear_speed_mps": 0.0, "confidence": 0.97},
        },
    }


def localize(bundle: dict[str, Any]) -> dict[str, Any]:
    _require_sim_bundle(bundle)
    sensors = bundle["sensors"]
    stamps = [float(sensors[name]["timestamp"]) for name in ("imu", "odometry", "lidar", "mmwave")]
    skew = max(stamps) - min(stamps)
    if skew > 0.1:
        raise ValueError(f"sensor time skew too high ({skew:.3f}s > 0.100s)")
    odom = sensors["odometry"]
    return {"kind": "sim_localization", "scenario_id": bundle["scenario_id"], "frame_id": bundle["frame_id"],
            "pose": odom["position"], "heading_deg": odom["heading_deg"],
            "confidence": round(min(odom["confidence"], sensors["imu"]["confidence"]), 3),
            "sensor_time_skew_s": round(skew, 4), "simulated": True, "actuation": False}


def fuse_scene(bundle: dict[str, Any]) -> dict[str, Any]:
    _require_sim_bundle(bundle)
    sensors = bundle["sensors"]
    camera_objects = sensors["camera"]["objects"]
    ranged = {item["id"]: item for item in sensors["lidar"]["obstacles"] + sensors["lidar"].get("detections", [])}
    semantic_objects = []
    for item in camera_objects:
        match = ranged.get(item["id"])
        semantic_objects.append({**item, "range_confirmed": match is not None,
                                 "kind": match.get("kind", "goal") if match else "goal",
                                 "association_confidence": round(min(item["confidence"], sensors["lidar"]["confidence"]), 3) if match else item["confidence"]})
    dynamic = sensors["mmwave"]["targets"]
    obstacles = [dict(item) for item in sensors["lidar"]["obstacles"]]
    obstacles.extend({**item, "radius_m": 0.32} for item in dynamic)
    target = next((item for item in semantic_objects if item["id"] == "goal-cup"), None)
    if target is None:
        raise ValueError("camera did not identify the configured goal")
    return {"kind": "sim_fused_scene", "scenario_id": bundle["scenario_id"], "frame_id": bundle["frame_id"],
            "objects": semantic_objects, "obstacles": obstacles, "dynamic_targets": dynamic,
            "goal": {"id": target["id"], "position": target["position"],
                     "range_confirmed": target["range_confirmed"],
                     "confidence": target["association_confidence"]},
            "sensor_sources": ["camera", "lidar", "mmwave", "imu", "odometry"],
            "timestamp": bundle["timestamp"], "simulated": True, "actuation": False}


def plan_route(scene: dict[str, Any], localization: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    if scene.get("kind") != "sim_fused_scene" or localization.get("kind") != "sim_localization":
        raise ValueError("planner requires fused scene and localization inputs")
    start = localization["pose"][:2]
    goal = scene["goal"]["position"][:2]
    if config.get("inject_blocked_route"):
        obstacles = list(scene["obstacles"]) + [
            {"id": f"wall-{index}", "position": [2.5, y], "radius_m": 0.48}
            for index, y in enumerate((-1.5, -0.5, 0.5, 1.5))
        ]
    else:
        obstacles = scene["obstacles"]
    start_cell = _cell(start)
    goal_cell = _cell(goal)
    path = _astar(start_cell, goal_cell, obstacles)
    if not path:
        return {"kind": "sim_nav_plan", "status": "blocked", "reason": "no_collision_free_route",
                "path": [], "simulated": True, "actuation": False}
    points = [[round(x * GRID, 2), round(y * GRID, 2)] for x, y in path]
    return {"kind": "sim_nav_plan", "status": "planned", "frame_id": scene["frame_id"],
            "start": [round(value, 2) for value in start], "goal": [round(value, 2) for value in goal],
            "path": points, "waypoint_count": len(points), "length_m": round(_path_length(points), 2),
            "planner": "Body deterministic A* (metric grid)", "obstacle_avoidance": True,
            "replanned_for_dynamic_target": bool(scene.get("dynamic_targets")),
            "behavior_tree": "NavigateToPose: plan -> follow -> on obstacle clear costmap / wait / replan",
            "simulated": True, "actuation": False}


def safety_check(scene: dict[str, Any], localization: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    if plan.get("status") != "planned":
        return {"kind": "sim_safety_decision", "state": "blocked", "reason": plan.get("reason", "no_plan"),
                "simulated": True, "actuation": False}
    now = time.time()
    age = now - float(scene.get("timestamp", 0))
    fresh = 0 <= age <= 2.0
    confidence = float(localization.get("confidence", 0))
    goal_confirmed = bool(scene.get("goal", {}).get("range_confirmed"))
    goal_confidence = float(scene.get("goal", {}).get("confidence", 0))
    valid = fresh and confidence >= 0.8 and bool(plan.get("path")) and goal_confirmed and goal_confidence >= 0.8
    return {"kind": "sim_safety_decision", "state": "clear" if valid else "blocked",
            "checks": {"simulated_input_provenance": scene.get("simulated") is True,
                       "sensor_data_fresh_under_2s": fresh, "localization_confidence_ge_0_8": confidence >= 0.8,
                       "goal_range_confirmed": goal_confirmed, "goal_association_confidence_ge_0_8": goal_confidence >= 0.8,
                       "route_exists": bool(plan.get("path"))},
            "sensor_age_s": round(age, 3), "warning": "Simulation-only gate; not evidence for physical motion or a certified safety system.",
            "simulated": True, "actuation": False}


def fnk_command_intents(nav: dict[str, Any]) -> dict[str, Any]:
    if nav.get("kind") != "sim_nav_result" or nav.get("status") != "succeeded":
        raise ValueError("FNK intent adapter requires a successful simulated navigation result")
    points = nav.get("path") or []
    intents = []
    for start, end in zip(points, points[1:]):
        dx, dy = float(end[0]) - float(start[0]), float(end[1]) - float(start[1])
        intents.append({"api": "robot.Crawl(x, y, angle)", "map_delta_m": [round(dx, 3), round(dy, 3)],
                        "heading_deg": round(math.degrees(math.atan2(dy, dx)), 1),
                        "status": "simulated_intent_only"})
    return {"kind": "sim_fnk_command_intents", "transport": "USB / stock FNHR framed protocol (not opened in simulation)",
            "controller_owner": "FNK0031 firmware / FNHR", "motor_owner": "FNK0031 (18 servos)",
            "commands": intents, "command_count": len(intents),
            "calibration_required": True,
            "warning": "Map deltas are not FNHR units. Real adapter must calibrate command scale, gait timing, stop behavior and feedback before actuation.",
            "simulated": True, "actuation": False}


def mission_result(scene: dict[str, Any], plan: dict[str, Any], nav: dict[str, Any], safety: dict[str, Any], fnk: dict[str, Any]) -> dict[str, Any]:
    reached = safety.get("state") == "clear" and plan.get("status") == "planned" and nav.get("status") == "succeeded"
    return {"kind": "sim_mission_report", "scenario_id": scene["scenario_id"],
            "status": "goal_reached" if reached else "safely_stopped",
            "goal_id": scene["goal"]["id"], "goal_position": scene["goal"]["position"],
            "route_waypoints": plan.get("waypoint_count", 0), "route_length_m": plan.get("length_m"),
            "fnk_command_intents": fnk.get("command_count", 0),
            "recovery_policy": ["pause on dynamic obstacle", "re-evaluate sensor freshness", "replan", "safe-stop after bounded retries"],
            "nav_action": nav.get("status"), "simulated": True, "actuation": False,
            "physical_autonomy_claim": False,
            "architecture": "Body plans and supervises; FNK0031/FNHR owns gait generation and servos over USB."}


def _require_sim_bundle(bundle: dict[str, Any]) -> None:
    if bundle.get("kind") != "sim_sensor_bundle" or bundle.get("simulated") is not True:
        raise ValueError("node requires explicitly simulated sensor-suite input")
    if bundle.get("scenario_id") != SCENARIO_ID:
        raise ValueError("unknown simulation scenario")
    required = {"camera", "lidar", "mmwave", "imu", "odometry"}
    if not required.issubset(bundle.get("sensors", {})):
        raise ValueError("sensor suite is incomplete")


def _cell(point: list[float]) -> tuple[int, int]:
    return round(float(point[0]) / GRID), round(float(point[1]) / GRID)


def _astar(start: tuple[int, int], goal: tuple[int, int], obstacles: list[dict[str, Any]]) -> list[tuple[int, int]]:
    def blocked(cell):
        x, y = cell[0] * GRID, cell[1] * GRID
        return not (0 <= x <= 5.5 and -2 <= y <= 2) or any(
            math.hypot(x - float(item["position"][0]), y - float(item["position"][1]))
            < float(item.get("radius_m", 0.3)) + 0.3 for item in obstacles
        )
    queue = [(0.0, start)]
    parents = {}
    costs = {start: 0.0}
    while queue:
        _priority, current = heapq.heappop(queue)
        if current == goal:
            path = [current]
            while current in parents:
                current = parents[current]
                path.append(current)
            return list(reversed(path))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            neighbor = (current[0] + dx, current[1] + dy)
            if blocked(neighbor):
                continue
            step = math.hypot(dx, dy)
            cost = costs[current] + step
            if cost < costs.get(neighbor, float("inf")):
                costs[neighbor] = cost
                parents[neighbor] = current
                heuristic = math.hypot(goal[0] - neighbor[0], goal[1] - neighbor[1])
                heapq.heappush(queue, (cost + heuristic, neighbor))
    return []


def _path_length(points: list[list[float]]) -> float:
    return sum(math.dist(left, right) for left, right in zip(points, points[1:]))
