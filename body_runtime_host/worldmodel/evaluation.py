"""Repeatable, local evaluation of the generic Body task stack."""
from __future__ import annotations

import json
import heapq
import inspect
import logging
import math
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .contracts import BodyPlan, BodySnapshot, PlanStep
from .core import EmbodiedWorldModel
from .dynamics import LatentWorldDynamics
from .sim_world import BODY_RADIUS_M, CONTACT_MARGIN_M, SimulatedRoom
from .task_graph import TaskGraphExecutor
from .local_planner import LocalRoutePlanner
from .types import Action
from .plan_runtime import BodyPlanRuntime
from .perception import sensor_projections
from .scene_interpreter import BodySceneInterpreter
from .virtual_camera import render_camera

logger = logging.getLogger(__name__)


@dataclass
class TrialResult:
    seed: int
    success: bool
    steps: int
    collisions: int
    replans: int
    recoveries: int
    near_misses: int = 0
    detour_steps: int = 0
    productive_steps: int = 0
    rotation_steps: int = 0
    wait_steps: int = 0
    distance_travelled: float = 0.0
    final_distance: float = 0.0
    decision_time_ms: float = 0.0
    max_decision_time_ms: float = 0.0
    detour_distance: float = 0.0
    detour_action_counts: Dict[str, int] = field(default_factory=dict)
    action_counts: Dict[str, int] = field(default_factory=dict)
    decision_reasons: Dict[str, int] = field(default_factory=dict)
    disturbed: bool = False
    disturbance_kind: str = ""
    final_step: str = ""
    reason: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def _evaluation_state(room: SimulatedRoom) -> Any:
    """Encode a variable-size scene as a permutation-invariant object set.

    The learner must not depend on object order or on a five-object fixture.
    Each object contributes the same compact feature vector; pooling mean,
    maximum, minimum and spread keeps the dynamics input fixed-size without
    truncating newly discovered objects.
    """
    import numpy as np

    body = room.body_state()
    width = max(1.0, float(body.capabilities.get("world_width", room.width)))
    height = max(1.0, float(body.capabilities.get("world_height", room.height)))
    object_features = []
    body_x, body_y = float(body.position[0]), float(body.position[1])
    for item in room.objects.values():
        kind = str(item.get("kind", "object"))
        kind_signal = (sum(ord(char) for char in kind) % 997) / 997.0
        object_features.append([
            (float(item.get("x", 0.0)) - body_x) / width,
            (float(item.get("y", 0.0)) - body_y) / height,
            float(item.get("size", 0.0)) / max(width, height),
            min(1.0, float(item.get("mass", 0.0)) / 1000.0),
            kind_signal,
            1.0 if kind == "mobile_obstacle" else 0.0,
        ])
    object_array = np.asarray(object_features or [[0.0] * 6], dtype="float32")
    pooled = np.concatenate([
        object_array.mean(axis=0),
        object_array.max(axis=0),
        object_array.min(axis=0),
        object_array.std(axis=0),
    ])
    goal = body.capabilities.get("goal") or [0.0, 0.0]
    goal_distance = math.hypot(float(goal[0]) - body_x, float(goal[1]) - body_y)
    mobile_velocity = body.capabilities.get("mobile_obstacle_velocity") or [0.0, 0.0]
    values = [
        body_x / width,
        body_y / height,
        math.sin(float(body.orientation)),
        math.cos(float(body.orientation)),
        1.0 if body.posture.get("holding") else 0.0,
        float(body.capabilities.get("mobile_obstacle_speed", 0.0)),
        min(1.0, len(room.objects) / 32.0),
        goal_distance / math.hypot(width, height),
        float(mobile_velocity[0]) / width,
        float(mobile_velocity[1]) / height,
    ]
    values.extend(pooled.tolist())
    return np.asarray(values, dtype="float32")


class _EvaluationLearner:
    """Small in-run learner for the shuffled-scene protocol."""

    def __init__(self) -> None:
        self.model = LatentWorldDynamics(in_dim=34, latent_dim=16, hidden_dim=32, lr=2e-3, seed=19)
        self.transitions = 0
        self.updates = 0
        self.losses: list[float] = []
        self.policy_switches = 0

    def observe(self, before: Any, action: Action, after: Any, reward: float, success: bool) -> None:
        if not self.model.available:
            return
        self.model.remember(before, action, after, reward, success)
        self.transitions += 1
        if self.transitions % 8:
            return
        result = self.model.train_step(batch=32, epochs=1)
        if result:
            self.updates += 1
            self.losses.append(float(result.get("loss", 0.0)))

    def snapshot(self) -> Dict[str, Any]:
        window = self.losses[-10:]
        return {
            "transitions": self.transitions,
            "updates": self.updates,
            "loss": round(sum(window) / len(window), 6) if window else None,
            "available": bool(self.model.available),
            "training_steps": self.model.training_steps,
            "policy_switches": self.policy_switches,
        }

    def select_navigation_action(
        self,
        state: Any,
        planned: Action,
        snapshot: Any,
        body: Any,
    ) -> tuple[Action, Optional[Dict[str, Any]]]:
        """Use learned counterfactuals without bypassing route safety.

        The task graph still determines the target and the current phase. The
        learner may only choose a safe locomotion primitive for that phase;
        grasp/release order and blocked-route recovery stay deterministic.
        """
        if not self.model.available or self.model.training_steps < 25:
            return planned, None
        if planned.type not in {"forward", "backward", "turn_left", "turn_right", "wait", "sprint", "retreat"}:
            return planned, None

        hazard_near = any(
            str(item.get("kind")) == "mobile_obstacle"
            and math.hypot(
                float((item.get("position") or [0.0, 0.0])[0]) - float(body.position[0]),
                float((item.get("position") or [0.0, 0.0])[1]) - float(body.position[1]),
            ) <= 1.5
            for item in snapshot.objects
        )
        # The learned evaluator can pause for a nearby dynamic hazard, but it
        # cannot replace a validated route with a different turn or direction.
        movement = (planned.type, "wait") if hazard_near else (planned.type,)
        safe: list[Action] = []

        for action_type in movement:
            if action_type in {"turn_left", "turn_right", "wait"}:
                safe.append(Action(type=action_type, target=planned.target, params=dict(planned.params or {})))
                continue
            distance = 1.0 if action_type == "forward" else -1.0
            heading = float(body.orientation) if distance > 0 else float(body.orientation) + math.pi
            if TaskGraphExecutor._translation_clear(snapshot, body, abs(distance), heading=heading):
                safe.append(Action(type=action_type, target=planned.target, params=dict(planned.params or {})))
        if len(safe) < 2:
            return planned, None

        latent_state = self.model.encode(state)
        evaluations = [
            self.model.counterfactual(latent_state, action, horizon=6)
            for action in safe
        ]
        by_type = {str(item["action"]): item for item in evaluations}
        baseline = by_type.get(planned.type)
        if baseline is None:
            return planned, None
        best = max(evaluations, key=lambda item: float(item.get("mean_value", 0.0)))
        margin = float(best.get("mean_value", 0.0)) - float(baseline.get("mean_value", 0.0))
        if str(best.get("action")) == planned.type or margin < 0.05:
            return planned, None

        def dynamic_risk(action_type: str) -> float:
            """Estimate closing risk without replacing the geometric planner."""
            mobile = next(
                (item for item in snapshot.objects if str(item.get("kind")) == "mobile_obstacle"),
                None,
            )
            if mobile is None or action_type not in {"forward", "backward", "sprint", "retreat", "wait"}:
                return 0.0
            mobile_position = list(mobile.get("position") or [0.0, 0.0])
            predicted = body.capabilities.get("mobile_obstacle_predicted_position") or mobile_position
            body_x, body_y = float(body.position[0]), float(body.position[1])
            distance = 2.0 if action_type in {"sprint", "retreat"} else 1.0
            direction = 1.0 if action_type in {"forward", "sprint"} else -1.0
            minimum = max(
                0.8,
                float(body.capabilities.get("mobile_obstacle_clearance", 1.3))
                + max(0.0, float(body.capabilities.get("mobile_obstacle_planning_margin", 0.0))),
            )
            closest = float("inf")
            for index in range(1, int(distance) + 1):
                candidate_x = body_x + direction * math.cos(float(body.orientation)) * index
                candidate_y = body_y + direction * math.sin(float(body.orientation)) * index
                closest = min(
                    closest,
                    math.hypot(float(mobile_position[0]) - candidate_x, float(mobile_position[1]) - candidate_y),
                    math.hypot(float(predicted[0]) - candidate_x, float(predicted[1]) - candidate_y),
                )
            return max(0.0, minimum - closest)

        selected_type = str(best.get("action"))
        if dynamic_risk(selected_type) > dynamic_risk(planned.type) + 1e-6:
            return planned, None

        self.policy_switches += 1
        selected = Action(type=selected_type, target=planned.target, params={
            **(planned.params or {}),
            "learned_selection": True,
        })
        return selected, {
            "planned": planned.type,
            "selected": selected.type,
            "margin": round(margin, 5),
            "training_steps": self.model.training_steps,
        }


def _generic_plan(parcel_id: str = "parcel", dock_id: str = "dock") -> BodyPlan:
    return BodyPlan(
        objective="move an object through a surface to a goal",
        required_capabilities=["navigate", "grab", "release"],
        expires_at=time.time() + 3600,
        steps=[
            PlanStep("approach_object", "navigate", parcel_id),
            PlanStep("grasp_object", "grab", parcel_id),
            PlanStep("approach_surface", "navigate", dock_id),
            PlanStep("place_on_surface", "release", dock_id, postconditions=[{"type": "on_surface", "target": parcel_id, "surface": dock_id}]),
            PlanStep("regrasp_object", "grab", parcel_id),
            PlanStep("approach_goal", "navigate", "goal"),
            PlanStep("place_at_goal", "release", "goal", postconditions=[{"type": "goal_reached", "target": parcel_id, "goal": "goal"}]),
        ],
    )


def _add_scene_variation(room: SimulatedRoom, seed: int) -> None:
    """Add deterministic, non-task objects to vary scene complexity."""
    import random

    rng = random.Random(int(seed) + 701)
    occupied = [(float(room.px), float(room.py)), tuple(map(float, room.shelf))]
    occupied.extend((float(item.get("x", 0.0)), float(item.get("y", 0.0))) for item in room.objects.values())
    candidates = [
        (float(x), float(y))
        for x in range(1, room.width - 1)
        for y in range(1, room.height - 1)
        if all(math.hypot(x - ox, y - oy) >= 1.5 for ox, oy in occupied)
    ]
    rng.shuffle(candidates)
    for index, position in enumerate(candidates[:int(seed) % 4]):
        room.objects[f"scene_obstacle_{index}"] = {
            "id": f"scene_obstacle_{index}",
            "label": "scene obstacle",
            "kind": "obstacle",
            "x": position[0], "y": position[1],
            "mass": 999.0, "size": 0.5 + (index % 2) * 0.3,
        }


def _fractionalize_scene(room: SimulatedRoom) -> None:
    """Move the deterministic scene off grid centers while preserving roles."""
    # A fixed sub-cell transform makes metric-vs-grid comparisons paired and
    # reproducible.  The displacement is small enough to preserve the legal
    # shuffled layout and large enough to exercise continuous clearance.
    dx, dy = 0.23, -0.17
    room.shelf = (
        max(0.8, min(float(room.width) - 1.2, float(room.shelf[0]) + dx)),
        max(0.8, min(float(room.height) - 1.2, float(room.shelf[1]) + dy)),
    )
    for item in room.objects.values():
        item["x"] = max(0.8, min(float(room.width) - 1.2, float(item["x"]) + dx))
        item["y"] = max(0.8, min(float(room.height) - 1.2, float(item["y"]) + dy))


def collect_body_llm_grounding(
    samples: int,
    config: Dict[str, Any],
    *,
    seeds: Optional[List[int]] = None,
    visual_blind: bool = True,
) -> Dict[str, Any]:
    """Collect real Body-LLM grounding evidence on reproducible scenes.

    This is deliberately separate from the motion benchmark: an unavailable
    or slow LLM must not alter navigation results. Geometry remains sourced
    from the simulator packet and the interpreter only returns semantic
    context after its grounding gate.
    """
    requested = max(0, min(100, int(samples or 0)))
    if requested == 0:
        return {"status": "not_requested", "samples": 0}
    interpreter = BodySceneInterpreter(dict(config or {}))
    try:
        if not bool(config.get("BODY_LLM_ENABLED")) or not str(config.get("BODY_LLM_MODEL") or "").strip():
            return {"status": "disabled", "samples": 0, "reason": "Body LLM is not configured"}
        precisions: list[float] = []
        accepted = rejected = errors = 0
        diagnostics: list[Dict[str, Any]] = []
        for index, seed in enumerate((seeds or list(range(requested)))[:requested]):
            room = SimulatedRoom()
            room.reset_episode(shuffle=True, seed=int(seed))
            _add_scene_variation(room, int(seed))
            _fractionalize_scene(room)
            observation = room.observe()
            body = room.body_state()
            objects = [item.as_dict() if hasattr(item, "as_dict") else dict(item) for item in observation.scene]
            projections = sensor_projections(body, observation.scene, modalities=observation.modalities)
            # Keep the rendered camera frame alongside the compact projections.
            # The projections are useful for geometry checks, but a vision LLM
            # must receive the actual pixels to validate visual grounding.
            raw_camera = observation.modalities.get("camera") if isinstance(observation.modalities, dict) else None
            camera_profiles = ("low_body_front", "level_body_front", "high_body_front")
            camera_profile = camera_profiles[int(seed) % len(camera_profiles)]
            variant_fov = (92.0, 100.0, 108.0)[int(seed) % 3]
            variant_camera = render_camera(
                body, observation.scene, width=640, height=480,
                fov_deg=variant_fov, frame_id=f"grounding-eval-{int(seed)}-{index}",
                profile=camera_profile,
            )
            if isinstance(variant_camera, dict) and variant_camera.get("image_base64"):
                projections["camera"] = dict(variant_camera)
                projections["camera"]["frame_id"] = f"grounding-eval-{int(seed)}-{index}"
                projections["camera"]["validation"] = "deterministic_scene_fixture"
            packet = {
                "frame_id": f"grounding-eval-{int(seed)}-{index}",
                "timestamp": float(observation.timestamp),
                "pose": {"position": list(body.position), "yaw": float(body.orientation)},
                "objects": objects,
                "capabilities": dict(body.capabilities),
                "modalities": projections,
                # Retain fusion for post-call scoring and Body grounding, but
                # let the interpreter strip it from the visual-blind prompt.
                "sensor_fusion": projections.get("fusion"),
                "visual_blind": bool(visual_blind),
            }
            result = interpreter._interpret(packet)
            if result.get("status") != "interpreted":
                errors += 1
                diagnostics.append({
                    "seed": int(seed),
                    "frame_id": packet["frame_id"],
                    "status": "error",
                    "reason": str(result.get("error") or "unknown_interpreter_error")[:240],
                })
                continue
            grounding = ((result.get("semantic_scene") or {}).get("grounding") or {})
            precision = float(grounding.get("reference_precision", 0.0) or 0.0)
            precisions.append(precision)
            invented = int(grounding.get("invented_object_references", 0) or 0)
            fusion = ((result.get("semantic_scene") or {}).get("sensor_fusion") or {})
            object_positions = {
                str(item.get("id")): [round(float(value), 1) for value in list(item.get("position") or [])[:2]]
                for item in objects if isinstance(item, dict)
            }
            obstacle = object_positions.get("obstacle") or []
            body_position = list(body.position or [])
            obstacle_distance = (
                ((float(obstacle[0]) - float(body_position[0])) ** 2
                 + (float(obstacle[1]) - float(body_position[1])) ** 2) ** 0.5
                if len(obstacle) >= 2 and len(body_position) >= 2 else None
            )
            if grounding.get("accepted_for_context"):
                accepted += 1
                decision = "accepted"
            else:
                rejected += 1
                decision = "rejected_below_grounding_threshold"
            diagnostics.append({
                "seed": int(seed),
                "frame_id": packet["frame_id"],
                "status": decision,
                "reference_precision": round(precision, 3),
                "threshold": interpreter._grounding_threshold(),
                "referenced": int(grounding.get("primary_object_references", 0) or 0)
                + int(grounding.get("described_object_references", 0) or 0),
                "valid_references": int(grounding.get("valid_primary_object_references", 0) or 0)
                + int(grounding.get("valid_described_object_references", 0) or 0),
                "invented_object_references": invented,
                "sensor_fusion_matched": int(fusion.get("matched", 0) or 0),
                "sensor_fusion_returns": int(fusion.get("lidar_returns", 0) or 0),
                "obstacle_distance_m": round(obstacle_distance, 3) if obstacle_distance is not None else None,
                "obstacle_condition": "near" if obstacle_distance is not None and obstacle_distance <= 6.0 else "far",
                "camera_profile": camera_profile,
                "position_signature": ";".join(
                    f"{key}:{value[0]:.1f},{value[1]:.1f}"
                    for key, value in sorted(object_positions.items())
                ),
            })
        count = len(precisions)
        threshold = interpreter._grounding_threshold()
        invented_total = sum(int(item.get("invented_object_references", 0) or 0) for item in diagnostics)
        invented_scenes = sum(1 for item in diagnostics if int(item.get("invented_object_references", 0) or 0) > 0)

        def grouped_precision(condition: str) -> Dict[str, Any]:
            values = [
                float(item.get("reference_precision", 0.0) or 0.0)
                for item in diagnostics
                if item.get("status") != "error" and item.get("obstacle_condition") == condition
            ]
            return {
                "samples": len(values),
                "average_precision": round(sum(values) / len(values), 3) if values else None,
                "minimum_precision": round(min(values), 3) if values else None,
            }

        successful_diagnostics = [item for item in diagnostics if item.get("status") != "error"]
        position_values = [float(item.get("reference_precision", 0.0) or 0.0) for item in successful_diagnostics]

        def grouped_camera(profile: str) -> Dict[str, Any]:
            values = [
                float(item.get("reference_precision", 0.0) or 0.0)
                for item in successful_diagnostics if item.get("camera_profile") == profile
            ]
            return {
                "samples": len(values),
                "average_precision": round(sum(values) / len(values), 3) if values else None,
                "minimum_precision": round(min(values), 3) if values else None,
            }
        return {
            "status": "completed",
            "requested": requested,
            "samples": count,
            "accepted": accepted,
            "rejected": rejected,
            "errors": errors,
            "average_reference_precision": round(sum(precisions) / count, 3) if count else None,
            "minimum_reference_precision": round(min(precisions), 3) if precisions else None,
            "threshold": threshold,
            "accepted_rate": round(accepted / count, 3) if count else 0.0,
            "invented_object_references": invented_total,
            "scenes_with_invented_objects": invented_scenes,
            "stability": {
                "position_samples": len(position_values),
                "position_average_precision": round(sum(position_values) / len(position_values), 3) if position_values else None,
                "position_minimum_precision": round(min(position_values), 3) if position_values else None,
                "obstacle_near": grouped_precision("near"),
                "obstacle_far": grouped_precision("far"),
                "unique_position_signatures": len({item.get("position_signature") for item in successful_diagnostics}),
                "camera_profiles": {
                    profile: grouped_camera(profile)
                    for profile in ("low_body_front", "level_body_front", "high_body_front")
                },
            },
            "diagnostics": diagnostics,
            "geometry_authoritative": True,
            "same_fractional_scene_protocol": True,
        }
    finally:
        interpreter.close()


def _sensor_route(body: Any, lidar: Dict[str, Any], goal: tuple[int, int], room: SimulatedRoom,
                  mmwave: Optional[Dict[str, Any]] = None) -> list[tuple[int, int]]:
    """Plan a coarse route from the current scan, without reading scene objects."""
    x0, y0 = float(body.position[0]), float(body.position[1])
    yaw = float(body.orientation)
    occupied: set[tuple[int, int]] = set()
    for point in (lidar.get("points") or []):
        try:
            px, py = float(point["x"]), float(point["y"])
        except (KeyError, TypeError, ValueError):
            continue
        if lidar.get("frame") == "body":
            wx = x0 + math.cos(yaw) * px - math.sin(yaw) * py
            wy = y0 + math.sin(yaw) * px + math.cos(yaw) * py
        else:
            wx, wy = px, py
        cell = (int(round(wx)), int(round(wy)))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                candidate = (cell[0] + dx, cell[1] + dy)
                # Inflate measured surfaces by the Body footprint and margin,
                # rather than blocking an entire 3x3 neighbourhood per return.
                if math.hypot(candidate[0] - wx, candidate[1] - wy) <= 0.7:
                    occupied.add(candidate)
    for target in (mmwave or {}).get("targets") or []:
        if not isinstance(target, dict):
            continue
        try:
            position = target.get("position_m") or []
            velocity = target.get("velocity_mps") or []
            px, py = float(position[0]) + float(velocity[0]), float(position[1]) + float(velocity[1])
        except (IndexError, TypeError, ValueError):
            continue
        if math.hypot(float(velocity[0]), float(velocity[1])) < 0.05:
            continue
        for x in range(int(math.floor(px - 1.0)), int(math.ceil(px + 1.0)) + 1):
            for y in range(int(math.floor(py - 1.0)), int(math.ceil(py + 1.0)) + 1):
                if math.hypot(x - px, y - py) <= 0.9:
                    occupied.add((x, y))

    start = (int(round(x0)), int(round(y0)))
    if start == goal:
        return [start]
    frontier: list[tuple[float, tuple[int, int]]] = [(0.0, start)]
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    cost = {start: 0.0}
    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            break
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            neighbor = (current[0] + dx, current[1] + dy)
            if not (1 <= neighbor[0] <= room.width - 2 and 1 <= neighbor[1] <= room.height - 2):
                continue
            if neighbor in occupied and neighbor != goal:
                continue
            next_cost = cost[current] + 1.0
            if next_cost >= cost.get(neighbor, float("inf")):
                continue
            cost[neighbor] = next_cost
            came_from[neighbor] = current
            heuristic = abs(goal[0] - neighbor[0]) + abs(goal[1] - neighbor[1])
            heapq.heappush(frontier, (next_cost + heuristic, neighbor))
    if goal not in came_from:
        return []
    route = []
    current: tuple[int, int] | None = goal
    while current is not None:
        route.append(current)
        current = came_from[current]
    return list(reversed(route))


def run_vlm_sensorimotor_scenario(
    config: Dict[str, Any], *, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    seed: int = 31, max_actions: int = 32, compare_modalities: bool = True,
    roi_compare: bool = False,
    interpreter: Optional[BodySceneInterpreter] = None,
) -> Dict[str, Any]:
    """Run a simulation-only camera + LiDAR + VLM closed-loop navigation check."""
    from .types import Action

    owns_interpreter = interpreter is None
    interpreter = interpreter or BodySceneInterpreter(dict(config or {}))
    room = None
    timeline: list[Dict[str, Any]] = []
    snapshots: list[Dict[str, Any]] = []
    scenario_id = ""
    goal: Optional[tuple[int, int]] = None
    task_target_label = "purple cube"
    task_description = "Approach the purple cube and stop at a LiDAR-safe distance without touching it."
    try:
        if not config.get("BODY_LLM_ENABLED") or not str(config.get("BODY_LLM_MODEL") or "").strip():
            return {"status": "failed", "error": "Configure and enable the Body VLM before running this scenario."}
        room = SimulatedRoom()
        room.reset_episode(shuffle=False, seed=int(seed))
        layouts = (
            ((5.0, 4.0), (8.0, 1.0), (7.0, 8.0)),
            ((6.0, 5.0), (3.0, 9.0), (9.0, 9.0)),
            ((5.0, 5.0), (8.0, 1.0), (10.0, 10.0)),
        )
        target_xy, chair_xy, mobile_xy = layouts[(int(seed) - 31) % len(layouts)]
        room.objects = {
            "target": {"id": "target", "label": "purple cube", "kind": "obstacle",
                       "x": target_xy[0], "y": target_xy[1], "mass": 999.0, "size": 1.0},
            "chair": {"id": "chair", "label": "chair", "kind": "chair",
                      "x": chair_xy[0], "y": chair_xy[1], "mass": 6.0, "size": 0.8},
            "mobile_obstacle": {"id": "mobile_obstacle", "label": "moving obstacle",
                                "kind": "mobile_obstacle", "x": mobile_xy[0], "y": mobile_xy[1],
                                "mass": 999.0, "size": 0.7,
                                "props": {"velocity_x": -0.15, "velocity_y": 0.08}},
        }
        scenario_id = f"vlm-nav-{int(seed)}-{time.time_ns()}"

        def capture_frame(stage: str) -> tuple[Any, Any, Dict[str, Any], Dict[str, Any]]:
            observation = room.observe()
            body = room.body_state()
            timestamp = float(observation.timestamp)
            frame_id = f"{scenario_id}-{stage}-{room.steps}"
            camera = dict(observation.modalities.get("camera") or {})
            lidar = dict(observation.modalities.get("lidar") or {})
            camera.update({"frame_id": frame_id, "timestamp": timestamp})
            lidar.update({"frame_id": frame_id, "timestamp": timestamp,
                          "coordinate_frame": "body", "unit": "m", "native": False})
            radar = dict(observation.modalities.get("mmwave_radar") or {})
            radar.update({"frame_id": frame_id, "timestamp": timestamp, "coordinate_frame": "local_map"})
            observation.modalities["camera"] = camera
            observation.modalities["lidar"] = lidar
            observation.modalities["mmwave_radar"] = radar
            projections = sensor_projections(body, observation.scene, modalities=observation.modalities)
            packet = {
                "contract": "body_perception_frame.v2", "source": "simulated_room",
                "timestamp": timestamp, "frame_id": frame_id,
                "body": {"position": list(body.position), "orientation": float(body.orientation),
                         "coordinate_frame": "world", "position_source": "simulator_odometry"},
                # This list is for offline grounding scores only; visual_blind
                # strips it and all sensor object IDs from the VLM prompt.
                "objects": [item.as_dict() for item in observation.scene],
                "modalities": observation.modalities,
                "sensor_fusion": projections.get("fusion"),
                "motion": {"speed": float(body.capabilities.get("speed", 0.0)),
                           "relative_speed": 0.0,
                           "moving": room.steps > 0, "perception_risk": 0.0},
                "navigation": {"task": task_description, "mode": "scan_grounded_simulation"},
                "visual_blind": True,
            }
            return observation, body, lidar, packet

        def interpret_frame(stage: str, frame: tuple[Any, Any, Dict[str, Any], Dict[str, Any]],
                            *, include_sensor_context: bool, mmwave_roi: bool = False) -> Dict[str, Any]:
            observation, body, lidar, packet = frame
            camera = observation.modalities["camera"]
            radar = observation.modalities.get("mmwave_radar") or {}
            frame_id = str(packet["frame_id"])
            timestamp = float(packet["timestamp"])
            result = interpreter.interpret_now(
                packet, visual_options={"include_sensor_context": include_sensor_context, "bypass_cache": True,
                                        "mmwave_roi": mmwave_roi, "max_rois": 2},
            )
            semantic = result.get("semantic_scene") or {}
            raw_interpretation = result.get("interpretation") or {}
            interpretation = BodySceneInterpreter._normalize_interpretation_schema(raw_interpretation)
            descriptions = interpretation.get("object_descriptions") if isinstance(interpretation, dict) else []
            described_labels = [
                str(item.get("label") or item.get("name") or item.get("description") or "").strip()
                for item in descriptions if isinstance(item, dict)
            ] if isinstance(descriptions, list) else []
            scene_summary = (
                interpretation.get("scene_summary") or interpretation.get("summary")
                or interpretation.get("description")
            ) if isinstance(interpretation, dict) else None
            if not scene_summary and described_labels:
                scene_summary = "Objects described: " + "; ".join(label for label in described_labels[:5] if label)
            if not scene_summary:
                returned_keys = ", ".join(str(key) for key in interpretation) if isinstance(interpretation, dict) else "no JSON fields"
                scene_summary = f"No scene summary or object descriptions returned (keys: {returned_keys or 'none'})."
            snapshots.append({
                "stage": stage, "frame_id": frame_id, "timestamp": timestamp,
                "pose_m": [round(float(body.position[0]), 3), round(float(body.position[1]), 3)],
                "heading_deg": round(math.degrees(float(body.orientation)), 1),
                "camera_image": camera.get("image_base64"),
                "camera_mime_type": camera.get("mime_type", "image/png"),
                "camera_source": camera.get("source"), "lidar_source": lidar.get("source"),
                "lidar_returns": len(lidar.get("points") or []),
                "vlm_input_modalities": ["camera", "lidar", "mmwave_radar", "pose"] if include_sensor_context else ["camera"],
                "sensor_packet": {
                    "contract": "body_perception_frame.v2", "frame_id": frame_id,
                    "timestamp": timestamp,
                    "pose": {"position_m": list(body.position), "yaw_rad": float(body.orientation)},
                    "camera": {"source": camera.get("source"), "width": camera.get("width"),
                               "height": camera.get("height"), "image_attached": bool(camera.get("image_base64"))},
                    "lidar": {"source": lidar.get("source"), "coordinate_frame": lidar.get("frame"),
                              "returns": len(lidar.get("points") or []),
                    "points_sent_to_vlm": ([
                                  {key: point[key] for key in ("x", "y", "z", "range", "intensity") if key in point}
                                  for point in (lidar.get("points") or [])[:24]
                              ] if include_sensor_context else [])},
                    "mmwave": {"source": radar.get("source"), "frame_id": frame_id,
                               "timestamp": timestamp, "coordinate_frame": radar.get("frame"),
                               "targets_sent_to_vlm": len(radar.get("targets") or []) if include_sensor_context else 0,
                               "targets": ([{
                                   key: target[key] for key in (
                                       "target_id", "position_m", "velocity_mps", "radial_speed_mps", "confidence"
                                   ) if key in target
                               } for target in (radar.get("targets") or [])[:12]] if include_sensor_context else [])},
                },
                "vlm_status": result.get("status"), "vlm_mode": result.get("interpretation_mode"),
                "vlm_latency_ms": result.get("latency_ms"),
                "scene_summary": scene_summary,
                "vlm_interpretation": interpretation,
                "vlm_raw_output": raw_interpretation if isinstance(raw_interpretation, dict) else {},
                "visual_input": result.get("visual_input"),
                "vlm_input_preview": (result.get("visual_input") or {}).get("preview_base64"),
                "grounding": semantic.get("grounding"), "error": result.get("error"),
            })
            if result.get("status") != "interpreted":
                raise RuntimeError(f"VLM {stage} frame failed: {result.get('error') or result.get('status')}")
            return result

        def publish(stage: str, **values: Any) -> None:
            if progress_callback:
                progress_callback({"scenario": scenario_id, "stage": stage, "step": room.steps, **values})

        paired_frame = capture_frame("same-scene")
        paired_frame_id = paired_frame[3]["frame_id"]
        camera_vlm = {}
        camera_snapshot = None
        if compare_modalities:
            publish("CAMERA-ONLY CONTROL", frame_id=paired_frame_id, sensor_stage="camera only")
            camera_vlm = interpret_frame("camera_only", paired_frame, include_sensor_context=False)
            camera_snapshot = snapshots[-1]
        publish("CAMERA + SYNCHRONIZED SENSORS", frame_id=paired_frame_id,
                sensor_stage="same image + synchronized LiDAR, mmWave and pose")
        lidar_vlm = interpret_frame("camera_plus_sensors", paired_frame, include_sensor_context=True)
        paired_snapshot = snapshots[-1]
        roi_vlm = None
        if roi_compare:
            publish("SAME-FRAME mmWAVE ROI A/B", frame_id=paired_frame_id,
                    sensor_stage="same global image + up to 2 radar-guided crops")
            try:
                roi_vlm = interpret_frame("mmwave_roi", paired_frame, include_sensor_context=True, mmwave_roi=True)
                roi_snapshot = snapshots[-1]
                camera_meta = paired_frame[0].modalities.get("camera") or {}
                fov = math.radians(float((camera_meta.get("calibration") or {}).get("fov_deg")
                                     or camera_meta.get("fov_deg") or 100.0))
                target = room.objects.get("target") or {}
                dx, dy = float(target.get("x", 0)) - room.px, float(target.get("y", 0)) - room.py
                bearing = math.atan2(dy, dx) - float(paired_frame[1].orientation)
                bearing = math.atan2(math.sin(bearing), math.cos(bearing))
                image_width = int(camera_meta.get("width") or 640)
                target_x = image_width * (0.5 + (bearing / (fov / 2.0)) * 0.46)
                target_size = max(5, min(74, int(110 * float(target.get("size") or 0.5)
                                              / max(math.hypot(dx, dy), 0.8))))
                boxes = (roi_snapshot.get("visual_input") or {}).get("mmwave_rois") or []
                roi_snapshot["roi_evaluation"] = {
                    "same_frame_as_full_image": roi_snapshot["frame_id"] == paired_snapshot["frame_id"],
                    "crop_count": len(boxes),
                    "task_target_covered": any(
                        box["x"] <= target_x + target_size and box["x"] + box["width"] >= target_x - target_size
                        for box in boxes
                    ),
                    "target_visible_in_camera_fov": abs(bearing) <= fov / 2.0,
                }
            except Exception as exc:
                roi_snapshot = {"stage": "mmwave_roi", "frame_id": paired_frame_id,
                                "error": str(exc)[:240], "roi_evaluation": {"crop_count": 0}}
            paired_snapshot["roi_ab_comparison"] = {
                "same_frame_id": paired_snapshot.get("frame_id") == paired_frame_id,
                "full_image_latency_ms": paired_snapshot.get("vlm_latency_ms"),
                "roi_latency_ms": roi_snapshot.get("vlm_latency_ms"),
                "full_image_grounding_accepted": (paired_snapshot.get("grounding") or {}).get("accepted_for_context"),
                "roi_grounding_accepted": (roi_snapshot.get("grounding") or {}).get("accepted_for_context"),
                "roi_count": (roi_snapshot.get("roi_evaluation") or {}).get("crop_count", 0),
                "task_target_covered": (roi_snapshot.get("roi_evaluation") or {}).get("task_target_covered", False),
                "roi_error": roi_snapshot.get("error"),
            }
        navigation_vlm = roi_vlm if roi_compare else lidar_vlm
        semantic_scene = (navigation_vlm or {}).get("semantic_scene") or {}
        grounding = semantic_scene.get("grounding") or {}
        if (grounding.get("accepted_for_context") is not True
                or grounding.get("frame_id") != paired_frame_id
                or semantic_scene.get("frame_id") != paired_frame_id):
            reason = ("mmWave ROI VLM grounding was not accepted for this synchronized frame"
                      if roi_compare else "multimodal VLM grounding was not accepted for this synchronized frame")
            publish("stopped", reason=reason, movement_started=False)
            return {
                "status": "incomplete", "scenario_id": scenario_id,
                "execution": "simulation_only", "physical_actuation": False,
                "sensor_contract": "body_perception_frame.v2",
                "sensor_source": "virtual_camera_lidar_mmwave",
                "vlm_model": str(config.get("BODY_LLM_MODEL") or ""),
                "vlm_calls": len(snapshots), "vlm_multimodal": True,
                "task": task_description,
                "autonomy": {"status": "safety_stop", "reason": reason,
                             "movement_started": False, "target_selected_by": None},
                "modality_comparison": {
                    "same_frame_id": camera_snapshot["frame_id"] == paired_snapshot["frame_id"] if camera_snapshot else None,
                    "same_timestamp": camera_snapshot["timestamp"] == paired_snapshot["timestamp"] if camera_snapshot else None,
                    "camera_only_latency_ms": camera_vlm.get("latency_ms"),
                    "camera_plus_sensors_latency_ms": lidar_vlm.get("latency_ms"),
                    "camera_only_summary": camera_snapshot.get("scene_summary") if camera_snapshot else None,
                    "camera_plus_sensors_summary": paired_snapshot.get("scene_summary"),
                    "camera_only_grounding": camera_snapshot.get("grounding") if camera_snapshot else None,
                    "camera_plus_sensors_grounding": grounding,
                    "navigation_vlm_variant": "mmwave_roi" if roi_compare else "full_frame",
                    "roi_grounding": (roi_vlm.get("semantic_scene") or {}).get("grounding") if roi_vlm else None,
                    "movement_uses_vlm_output": False,
                    "movement_uses": "stopped before motion: rejected or stale VLM grounding",
                },
                "goal_reached": False, "final_position_m": [round(room.px, 3), round(room.py, 3)],
                "distance_to_goal_m": None, "collisions": room.collision_count,
                "near_misses": room.near_miss_count, "actions": 0,
                "timeline": [], "snapshots": snapshots,
                "safety": "No movement without accepted same-frame VLM grounding.",
            }

        semantic_entities = [
            entity for entity in (semantic_scene.get("entities") or [])
            if isinstance(entity, dict) and entity.get("id") and entity.get("description")
            and entity.get("semantic_label")
        ]
        target_candidates = {
            str(entity["id"]): {
                "id": str(entity["id"]), "label": str(entity["semantic_label"]),
                "kind": str(entity.get("role") or "object"),
            }
            for entity in semantic_entities
        }
        target_matches = interpreter._semantic_reference_resolver([task_target_label], target_candidates)
        target_id = target_matches.get(" ".join(task_target_label.lower().split()))
        target_entity = next((entity for entity in semantic_entities if str(entity["id"]) == target_id), None)
        if target_entity is None:
            resolution = interpreter.status().get("embedding", {}).get("last_resolution") or {}
            reason = "task target did not match a VLM-described, sensor-grounded entity"
            publish("stopped", reason=reason, movement_started=False)
            return {
                "status": "incomplete", "scenario_id": scenario_id,
                "execution": "simulation_only", "physical_actuation": False,
                "sensor_contract": "body_perception_frame.v2",
                "sensor_source": "virtual_camera_lidar_mmwave",
                "vlm_model": str(config.get("BODY_LLM_MODEL") or ""),
                "vlm_calls": len(snapshots), "vlm_multimodal": True,
                "task": task_description,
                "autonomy": {"status": "safety_stop", "reason": reason,
                             "movement_started": False, "target_query": task_target_label,
                             "target_resolution": resolution},
                "modality_comparison": {
                    "same_frame_id": camera_snapshot["frame_id"] == paired_snapshot["frame_id"] if camera_snapshot else None,
                    "same_timestamp": camera_snapshot["timestamp"] == paired_snapshot["timestamp"] if camera_snapshot else None,
                    "camera_only_latency_ms": camera_vlm.get("latency_ms"),
                    "camera_plus_sensors_latency_ms": lidar_vlm.get("latency_ms"),
                    "camera_only_summary": camera_snapshot.get("scene_summary") if camera_snapshot else None,
                    "camera_plus_sensors_summary": paired_snapshot.get("scene_summary"),
                    "camera_only_grounding": camera_snapshot.get("grounding") if camera_snapshot else None,
                    "camera_plus_sensors_grounding": grounding,
                    "navigation_vlm_variant": "mmwave_roi" if roi_compare else "full_frame",
                    "roi_grounding": (roi_vlm.get("semantic_scene") or {}).get("grounding") if roi_vlm else None,
                    "movement_uses_vlm_output": False,
                    "movement_uses": "stopped before motion: task target not grounded",
                },
                "goal_reached": False, "final_position_m": [round(room.px, 3), round(room.py, 3)],
                "distance_to_goal_m": None, "collisions": room.collision_count,
                "near_misses": room.near_miss_count, "actions": 0,
                "timeline": [], "snapshots": snapshots,
                "safety": "No movement unless the requested target resolves to a grounded VLM entity.",
            }

        target_position = target_entity.get("position") or []
        if len(target_position) < 2 or not all(math.isfinite(float(value)) for value in target_position[:2]):
            raise RuntimeError("Grounded task target has no finite metric position")
        target_position_m = (float(target_position[0]), float(target_position[1]))
        target_size = max(0.0, float(target_entity.get("size") or 0.0))
        target_radius = max(0.12, target_size * 0.3)
        safe_clearance_m = BODY_RADIUS_M + target_radius + CONTACT_MARGIN_M
        lidar_standoff_m = target_size * 0.55 + 0.7 + 0.1
        standoff_cells = max(1, int(math.ceil(max(safe_clearance_m, lidar_standoff_m))))
        initial_observation, initial_body, initial_lidar, _initial_packet = paired_frame
        candidate_goals = [
            (round(target_position_m[0] + dx * standoff_cells),
             round(target_position_m[1] + dy * standoff_cells))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        ]
        initial_radar = initial_observation.modalities.get("mmwave_radar")
        safe_routes = [
            (_sensor_route(initial_body, initial_lidar, candidate, room, initial_radar), candidate)
            for candidate in candidate_goals
            if 1 <= candidate[0] <= room.width - 2 and 1 <= candidate[1] <= room.height - 2
        ]
        safe_routes = [(route, candidate) for route, candidate in safe_routes if len(route) >= 2]
        if not safe_routes:
            raise RuntimeError("No LiDAR-safe standoff route to the grounded target")
        _initial_route, goal = min(safe_routes, key=lambda item: (len(item[0]), item[1]))
        resolution = interpreter.status().get("embedding", {}).get("last_resolution") or {}
        publish("moving", action="starting", target_id=target_id,
                reason="VLM-grounded task target; local LiDAR planner validates every waypoint")

        action_limit = max(1, min(64, int(max_actions)))
        for _action_index in range(action_limit):
            observation = room.observe()
            body = room.body_state()
            lidar = dict(observation.modalities.get("lidar") or {})
            route = _sensor_route(body, lidar, goal, room, observation.modalities.get("mmwave_radar"))
            distance_to_goal = math.hypot(goal[0] - float(body.position[0]), goal[1] - float(body.position[1]))
            if distance_to_goal <= 0.65:
                break
            if len(route) < 2:
                timeline.append({"step": room.steps, "action": "stop", "reason": "no_lidar_safe_route"})
                break
            next_cell = route[1]
            desired = math.atan2(next_cell[1] - float(body.position[1]), next_cell[0] - float(body.position[0]))
            delta = math.atan2(math.sin(desired - float(body.orientation)), math.cos(desired - float(body.orientation)))
            if abs(delta) > math.pi / 4:
                action = Action(type="turn_left" if delta > 0 else "turn_right")
                reason = "turn toward the VLM-grounded target along the current LiDAR-safe route"
            else:
                action = Action(type="forward", params={"continuous_physics": True, "speed": 1.0})
                reason = "advance toward the VLM-grounded target; replan from a fresh LiDAR scan next step"
            if action.type == "forward" and not (lidar.get("points") or []):
                timeline.append({"step": room.steps, "action": "stop", "reason": "empty_lidar_scan"})
                break
            before = (float(room.px), float(room.py))
            _next_observation, outcome = room.step(action)
            after = (float(room.px), float(room.py))
            entry = {
                "step": room.steps, "action": action.type, "reason": reason,
                "position_before_m": [round(before[0], 3), round(before[1], 3)],
                "position_after_m": [round(after[0], 3), round(after[1], 3)],
                "outcome": outcome.kind, "description": str(outcome.description)[:180],
                "collisions": room.collision_count, "near_misses": room.near_miss_count,
                "route_cells": len(route),
            }
            timeline.append(entry)
            publish("moving", action=action.type, reason=reason,
                    position_m=entry["position_after_m"], route_cells=len(route),
                    collisions=room.collision_count)
            if outcome.kind == "danger" or room.collision_count:
                break

        final_distance = math.hypot(goal[0] - room.px, goal[1] - room.py)
        target_clearance = math.hypot(target_position_m[0] - room.px, target_position_m[1] - room.py)
        reached = final_distance <= 0.65 and target_clearance >= safe_clearance_m
        status = "completed" if reached and room.collision_count == 0 and room.near_miss_count == 0 else "incomplete"
        publish("completed", distance_to_goal_m=round(final_distance, 3),
                collisions=room.collision_count, moved=room.steps > 0)
        return {
            "status": status, "scenario_id": scenario_id,
            "execution": "simulation_only", "physical_actuation": False,
            "sensor_contract": "body_perception_frame.v2",
            "sensor_source": "virtual_camera_lidar_mmwave",
            "vlm_model": str(config.get("BODY_LLM_MODEL") or ""),
            "vlm_calls": len(snapshots),
            "vlm_multimodal": lidar_vlm.get("interpretation_mode") == "sensor_packet",
            "task": task_description,
            "autonomy": {
                "status": "completed" if reached and status == "completed" else "incomplete",
                "movement_started": bool(timeline),
                "target_selected_by": "accepted VLM description + local semantic embedding",
                "target_query": task_target_label,
                "target_id": target_id,
                "target_semantic_label": target_entity.get("semantic_label"),
                "target_position_m": [round(target_position_m[0], 3), round(target_position_m[1], 3)],
                "standoff_goal_m": list(goal),
                "target_clearance_m": round(target_clearance, 3),
                "minimum_clearance_m": round(safe_clearance_m, 3),
                "target_resolution": resolution,
                "grounding_frame_id": grounding.get("frame_id"),
            },
            "modality_comparison": {
                "same_frame_id": camera_snapshot["frame_id"] == paired_snapshot["frame_id"] if camera_snapshot else None,
                "same_timestamp": camera_snapshot["timestamp"] == paired_snapshot["timestamp"] if camera_snapshot else None,
                "camera_only_latency_ms": camera_vlm.get("latency_ms"),
                "camera_plus_sensors_latency_ms": lidar_vlm.get("latency_ms"),
                "camera_only_summary": camera_snapshot.get("scene_summary") if camera_snapshot else None,
                "camera_plus_sensors_summary": paired_snapshot.get("scene_summary"),
                "camera_only_grounding": camera_snapshot.get("grounding") if camera_snapshot else None,
                "camera_plus_sensors_grounding": paired_snapshot.get("grounding"),
                "navigation_vlm_variant": "mmwave_roi" if roi_compare else "full_frame",
                "roi_grounding": (roi_vlm.get("semantic_scene") or {}).get("grounding") if roi_vlm else None,
                "movement_uses_vlm_output": True,
                "movement_uses": ("mmWave ROI-grounded target; fresh LiDAR scans gate every route segment"
                                   if roi_compare else "accepted VLM-grounded target; fresh LiDAR scans gate every route segment"),
            },
            "goal_m": list(goal), "target_position_m": [round(target_position_m[0], 3), round(target_position_m[1], 3)],
            "final_position_m": [round(room.px, 3), round(room.py, 3)],
            "distance_to_goal_m": round(final_distance, 3), "goal_reached": reached,
            "collisions": room.collision_count, "near_misses": room.near_miss_count,
            "actions": len(timeline), "timeline": timeline, "snapshots": snapshots,
            "vlm_confirmation": {
                "status": navigation_vlm.get("status"), "latency_ms": navigation_vlm.get("latency_ms"),
                "scene_summary": (roi_snapshot or paired_snapshot).get("scene_summary") if roi_compare else snapshots[-1].get("scene_summary"),
                "grounding": ((roi_snapshot or paired_snapshot).get("grounding") if roi_compare
                              else snapshots[-1].get("grounding")),
                "target_selected": target_id,
            },
            "safety": "VLM must ground the task target in the paired frame. Every route segment and standoff is LiDAR-validated; no actuator command is sent.",
        }
    except Exception as exc:
        logger.exception("VLM sensorimotor scenario failed")
        failure = {
            "status": "failed", "error": str(exc)[:300],
            "scenario_id": scenario_id, "execution": "simulation_only",
            "physical_actuation": False, "sensor_contract": "body_perception_frame.v2",
            "goal_m": list(goal or []), "timeline": timeline, "snapshots": snapshots,
        }
        if room is not None:
            failure.update({
                "final_position_m": [round(room.px, 3), round(room.py, 3)],
                "collisions": room.collision_count, "actions": len(timeline),
            })
        return failure
    finally:
        if owns_interpreter:
            interpreter.close()


def run_vlm_sensorimotor_suite(
    config: Dict[str, Any], *, scene_count: int = 3,
    roi_compare: bool = False,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """Run reproducible, paired camera/LiDAR/mmWave scenes through the VLM."""
    count = max(1, min(5, int(scene_count)))
    results = []
    snapshots = []
    timeline = []
    interpreter = BodySceneInterpreter(dict(config or {}))
    try:
        for index in range(count):
            seed = 31 + index

            def report_progress(update: Dict[str, Any], *, scene_index: int = index) -> None:
                if progress_callback:
                    progress_callback({**update, "scene_index": scene_index + 1, "scene_count": count})

            result = run_vlm_sensorimotor_scenario(
                config, progress_callback=report_progress, seed=seed,
                compare_modalities=index == 0 and not roi_compare,
                roi_compare=roi_compare, interpreter=interpreter,
            )
            results.append(result)
            for snapshot in result.get("snapshots") or []:
                snapshots.append({**snapshot, "scene_index": index + 1, "seed": seed})
            timeline.extend({**action, "scene_index": index + 1, "seed": seed}
                            for action in result.get("timeline") or [])
    finally:
        interpreter.close()

    successes = sum(result.get("status") == "completed" for result in results)
    grounding = [
        snapshot.get("grounding") or {}
        for result in results for snapshot in (result.get("snapshots") or [])
        if snapshot.get("vlm_mode") == "sensor_packet"
    ]
    latencies = [
        float(snapshot["vlm_latency_ms"])
        for result in results for snapshot in (result.get("snapshots") or [])
        if snapshot.get("vlm_latency_ms") is not None
    ]
    total_calls = sum(int(result.get("vlm_calls") or 0) for result in results)
    collisions = sum(int(result.get("collisions") or 0) for result in results)
    near_misses = sum(int(result.get("near_misses") or 0) for result in results)
    last = results[-1] if results else {}
    suite_status = "completed" if successes == count else ("failed" if not successes else "incomplete")
    scene_reports = [{
        "scene_index": index + 1, "seed": 31 + index, "status": result.get("status"),
        "goal_reached": result.get("goal_reached", False),
        "target_id": (result.get("autonomy") or {}).get("target_id"),
        "target_label": (result.get("autonomy") or {}).get("target_semantic_label"),
        "target_resolution": (result.get("autonomy") or {}).get("target_resolution"),
        "target_clearance_m": (result.get("autonomy") or {}).get("target_clearance_m"),
        "minimum_clearance_m": (result.get("autonomy") or {}).get("minimum_clearance_m"),
        "actions": result.get("actions", 0), "collisions": result.get("collisions", 0),
        "near_misses": result.get("near_misses", 0),
        "vlm_calls": result.get("vlm_calls", 0),
        "vlm_latency_ms": [snapshot.get("vlm_latency_ms") for snapshot in result.get("snapshots") or []],
        "roi_ab_comparison": next((snapshot.get("roi_ab_comparison") for snapshot in result.get("snapshots") or []
                                    if snapshot.get("roi_ab_comparison")), None),
        "error": result.get("error"),
    } for index, result in enumerate(results)]
    roi_comparisons = [item["roi_ab_comparison"] for item in scene_reports if item.get("roi_ab_comparison")]
    full_latencies = [float(item["full_image_latency_ms"]) for item in roi_comparisons
                      if item.get("full_image_latency_ms") is not None]
    roi_latencies = [float(item["roi_latency_ms"]) for item in roi_comparisons
                     if item.get("roi_latency_ms") is not None]
    roi_comparison_summary = None
    if roi_compare:
        covered = sum(item.get("task_target_covered") is True for item in roi_comparisons)
        roi_comparison_summary = {
            "scene_count": len(roi_comparisons),
            "same_frame_id": all(item.get("same_frame_id") is True for item in roi_comparisons),
            "full_image_latency_ms": round(sum(full_latencies) / len(full_latencies), 1) if full_latencies else None,
            "roi_latency_ms": round(sum(roi_latencies) / len(roi_latencies), 1) if roi_latencies else None,
            "roi_count": round(sum(int(item.get("roi_count") or 0) for item in roi_comparisons)
                                / len(roi_comparisons), 2) if roi_comparisons else 0,
            "task_target_covered": covered == len(roi_comparisons) and bool(roi_comparisons),
            "task_target_covered_scene_count": covered,
            "roi_coverage_rate": covered / len(roi_comparisons) if roi_comparisons else 0.0,
            "full_image_grounding_accepted_count": sum(item.get("full_image_grounding_accepted") is True
                                                        for item in roi_comparisons),
            "roi_grounding_accepted_count": sum(item.get("roi_grounding_accepted") is True
                                                 for item in roi_comparisons),
            "scenes": roi_comparisons,
        }
    return {
        "status": suite_status, "execution": "simulation_only", "physical_actuation": False,
        "sensor_contract": "body_perception_frame.v2",
        "sensor_source": "generated_camera_lidar_mmwave_from_shared_metric_scene",
        "scene_count": count, "successes": successes, "success_rate": successes / count,
        "accepted_multimodal_groundings": sum(item.get("accepted_for_context") is True for item in grounding),
        "multimodal_grounding_count": len(grounding),
        "grounding_acceptance_rate": (sum(item.get("accepted_for_context") is True for item in grounding) / len(grounding)) if grounding else 0.0,
        "invented_object_references": sum(int(item.get("invented_object_references") or 0) for item in grounding),
        "average_vlm_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else None,
        "total_vlm_latency_ms": round(sum(latencies), 1) if latencies else None,
        "vlm_calls": total_calls, "vlm_multimodal": all(result.get("vlm_multimodal") for result in results),
        "vlm_model": str(config.get("BODY_LLM_MODEL") or ""),
        "task": last.get("task"), "goal_reached": successes == count,
        "final_position_m": last.get("final_position_m"),
        "distance_to_goal_m": last.get("distance_to_goal_m"),
        "collisions": collisions, "near_misses": near_misses,
        "actions": sum(int(result.get("actions") or 0) for result in results),
        "autonomy": {
            "status": "completed" if successes == count else "incomplete",
            "movement_started": any((result.get("autonomy") or {}).get("movement_started") for result in results),
            "target_selected_by": "same-frame VLM grounding + local embeddings; LiDAR route gate; mmWave motion input",
            "scenes": scene_reports,
        },
        "modality_comparison": results[0].get("modality_comparison") if results else {},
        "roi_comparison": roi_comparison_summary,
        "scene_results": scene_reports, "snapshots": snapshots, "timeline": timeline,
        "safety": "Each camera image, LiDAR scan, mmWave frame and pose shares one scene manifest, frame id and timestamp. No actuator command is sent.",
    }


def _displace_surface(room: SimulatedRoom, surface_id: str, seed: int) -> bool:
    """Move a receiving surface to a legal free cell during a trial."""
    surface = room.objects.get(surface_id)
    if not surface:
        return False
    occupied = [
        (float(obj.get("x", 0)), float(obj.get("y", 0)))
        for object_id, obj in room.objects.items()
        if object_id != surface_id
    ]
    candidates = [
        (float(x), float(y))
        for x in range(1, room.width - 1)
        for y in range(1, room.height - 1)
        if all((x - ox) ** 2 + (y - oy) ** 2 >= 2.25 for ox, oy in occupied)
        and (x, y) != (float(room.px), float(room.py))
    ]
    if not candidates:
        return False
    position = candidates[int(seed) % len(candidates)]
    surface["x"], surface["y"] = position
    return True


def _displace_mobile_obstacle(room: SimulatedRoom, seed: int) -> bool:
    """Move the dynamic hazard without invalidating completed manipulation."""
    mobile = room.objects.get("mobile_obstacle")
    if not mobile:
        return False
    occupied = [
        (float(obj.get("x", 0)), float(obj.get("y", 0)))
        for object_id, obj in room.objects.items()
        if object_id != "mobile_obstacle" and object_id != room.carrying
    ]
    candidates = [
        (float(x), float(y))
        for x in range(1, room.width - 1)
        for y in range(1, room.height - 1)
        if all((x - ox) ** 2 + (y - oy) ** 2 >= 2.25 for ox, oy in occupied)
        and (x, y) != (float(room.px), float(room.py))
    ]
    if not candidates:
        return False
    position = candidates[int(seed) % len(candidates)]
    mobile["x"], mobile["y"] = position
    room._mobile_velocity = (0.0, 0.0)
    room._mobile_motion_phase = 0.0
    return True


def _run_trial(
    seed: int,
    max_steps: int,
    *,
    allow_recovery: bool,
    inject_disturbance: bool,
    learner: _EvaluationLearner | None = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    trial_index: int = 0,
    planner_geometry: str = "continuous",
    fractional_scene: bool = True,
) -> TrialResult:
    room = SimulatedRoom()
    try:
        room.reset_episode(shuffle=True, seed=int(seed))
    except TypeError as exc:
        if "unexpected keyword argument 'seed'" not in str(exc):
            raise
        room.reset_episode(shuffle=True)
    _add_scene_variation(room, seed)
    if fractional_scene:
        _fractionalize_scene(room)
    manipulable = [
        item for item in room.objects.values()
        if str(item.get("kind")) in {"target", "object", "item"}
        and float(item.get("mass", 0.0)) <= float(room.body_state().capabilities.get("strength", 30.0))
    ]
    surfaces = [
        item for item in room.objects.values()
        if str(item.get("kind")) in {"surface", "table", "chair"}
    ]
    if not manipulable or not surfaces:
        return TrialResult(
            seed=int(seed), success=False, steps=room.steps, collisions=room.collision_count,
        replans=0, recoveries=0, near_misses=room.near_miss_count,
            disturbed=False, final_step="role_selection", reason="missing_task_roles",
        )
    parcel = min(manipulable, key=lambda item: float(item.get("mass", 0.0)))
    dock = min(surfaces, key=lambda item: float(item.get("mass", 0.0)))
    parcel_original_id, dock_original_id = str(parcel["id"]), str(dock["id"])
    room.objects.pop(parcel_original_id)
    parcel.update({"id": "parcel", "label": "parcel", "kind": "object"})
    room.objects["parcel"] = parcel
    room.objects.pop(dock_original_id)
    dock.update({"id": "dock", "label": "dock", "kind": "surface"})
    room.objects["dock"] = dock
    plan, executor = _generic_plan(parcel_id="parcel", dock_id="dock"), TaskGraphExecutor(
        local_planner=LocalRoutePlanner(geometry_mode=planner_geometry),
    )
    replans = recoveries = 0
    detour_steps = 0
    productive_steps = 0
    rotation_steps = 0
    wait_steps = 0
    distance_travelled = 0.0
    decision_time_total = 0.0
    max_decision_time = 0.0
    detour_distance = 0.0
    detour_action_counts: Dict[str, int] = {}
    action_counts: Dict[str, int] = {}
    decision_reasons: Dict[str, int] = {}
    disturbed = False
    disturbance_kinds: list[str] = []
    reason = "step_budget_exhausted"
    disturbance_step = max(6, min(18, max_steps // 4))
    disturbance_steps = {disturbance_step, min(max_steps - 1, disturbance_step + 24)}

    def current_target_distance() -> float:
        if plan.current_step_index >= len(plan.steps):
            return 0.0
        target_id = str(plan.steps[plan.current_step_index].target or "")
        target = room.objects.get(target_id)
        if not target:
            return 0.0
        return math.hypot(float(target["x"]) - room.px, float(target["y"]) - room.py)

    def record_action(action: Action, before: tuple[float, float], before_distance: float, outcome: Any) -> None:
        nonlocal productive_steps, rotation_steps, wait_steps, distance_travelled
        moved = math.hypot(room.px - before[0], room.py - before[1])
        distance_travelled += moved
        if action.type in {"turn_left", "turn_right"}:
            rotation_steps += 1
        if action.type == "wait":
            wait_steps += 1
        after_distance = current_target_distance()
        if (
            outcome.kind in {"success", "completed"}
            or after_distance < before_distance - 0.05
            or (moved > 0.01 and action.type not in {"wait", "turn_left", "turn_right"})
        ):
            productive_steps += 1

    def inject_scene_change(step_index: int) -> None:
        nonlocal disturbed
        if not inject_disturbance or step_index not in disturbance_steps:
            return
        if plan.current_step_index < 3:
            changed = _displace_surface(room, "dock", seed + 17 + step_index)
            kind = "surface_moved_before_release"
        else:
            changed = _displace_mobile_obstacle(room, seed + 29 + step_index)
            kind = "mobile_obstacle_shifted"
        if changed:
            disturbed = True
            if kind not in disturbance_kinds:
                disturbance_kinds.append(kind)

    for step_number in range(max_steps):
        obs, body = room.observe(), room.body_state()
        snapshot = EmbodiedWorldModel._make_plan_snapshot(obs, body)
        decision_started = time.perf_counter()
        decision = executor.decide(plan, snapshot, body)
        if decision.satisfied:
            plan.current_step_index += 1
            if plan.current_step_index >= len(plan.steps):
                reason = "completed"
                break
            # Confirm the just-completed postcondition before changing the
            # scene. This models the Body's timestamped observation boundary
            # and prevents a disturbance from invalidating an action that was
            # already acknowledged by the executor.
            inject_scene_change(step_number)
            continue
        if decision.details and decision.details.get("replanned"):
            replans += 1
        reason_label = str(decision.reason or (decision.details or {}).get("reason") or "unspecified")
        decision_reasons[reason_label] = decision_reasons.get(reason_label, 0) + 1
        if any(token in reason_label for token in ("avoid", "replan", "recover", "dynamic")):
            detour_steps += 1
        action = decision.action
        if action is None:
            if allow_recovery:
                recovery = executor.recovery_action(plan, snapshot, body)
                action = recovery.action or Action(type="wait")
                recoveries += 1
            else:
                action = Action(type="wait")
        state_before = _evaluation_state(room)
        position_before = (float(room.px), float(room.py))
        target_distance_before = current_target_distance()
        learned_selection = None
        if learner is not None and action.type in {"forward", "backward", "turn_left", "turn_right", "wait", "sprint", "retreat"}:
            action, learned_selection = learner.select_navigation_action(
                state_before, action, snapshot, body,
            )
        decision_elapsed_ms = (time.perf_counter() - decision_started) * 1000.0
        decision_time_total += decision_elapsed_ms
        max_decision_time = max(max_decision_time, decision_elapsed_ms)
        _, outcome = room.step(action)
        record_action(action, position_before, target_distance_before, outcome)
        if any(token in reason_label for token in ("avoid", "replan", "recover", "dynamic")):
            detour_distance += math.hypot(room.px - position_before[0], room.py - position_before[1])
            detour_action_counts[action.type] = detour_action_counts.get(action.type, 0) + 1
        action_counts[action.type] = action_counts.get(action.type, 0) + 1
        if progress_callback is not None:
            progress_callback({
                "trial": trial_index,
                "step": step_number + 1,
                "action": action.type,
                "body": [round(room.px, 2), round(room.py, 2)],
                "mobile_obstacle": [
                    round(float(room.objects["mobile_obstacle"]["x"]), 2),
                    round(float(room.objects["mobile_obstacle"]["y"]), 2),
                ],
                "mobile_velocity": [round(float(value), 2) for value in room._mobile_velocity],
                "mobile_speed": round(float(room._mobile_current_speed), 3),
                "near_misses": room.near_miss_count,
                "learned_selection": learned_selection,
            })
        if learner is not None:
            learner.observe(
                state_before,
                action,
                _evaluation_state(room),
                float(outcome.reward),
                outcome.kind in {"success", "completed"},
            )
        if allow_recovery and outcome.kind in {"failure", "danger"}:
            recovery = executor.recovery_action(plan, snapshot, room.body_state())
            if recovery.action:
                recovery_position_before = (float(room.px), float(room.py))
                recovery_distance_before = current_target_distance()
                _, recovery_outcome = room.step(recovery.action)
                record_action(recovery.action, recovery_position_before, recovery_distance_before, recovery_outcome)
                action_counts[recovery.action.type] = action_counts.get(recovery.action.type, 0) + 1
                recoveries += 1
        inject_scene_change(step_number)
    if reason != "completed":
        current = plan.steps[plan.current_step_index] if plan.current_step_index < len(plan.steps) else None
        final_step = f"{current.verb}->{current.target}" if current else "complete"
        reason = f"{reason}:{final_step}"
    else:
        final_step = "complete"
    return TrialResult(
        seed=int(seed),
        success=reason == "completed",
        steps=room.steps,
        collisions=room.collision_count,
        replans=replans,
        recoveries=recoveries,
        near_misses=room.near_miss_count,
        detour_steps=detour_steps,
        productive_steps=productive_steps,
        rotation_steps=rotation_steps,
        wait_steps=wait_steps,
        distance_travelled=round(distance_travelled, 3),
        final_distance=round(current_target_distance(), 3),
        decision_time_ms=round(decision_time_total, 3),
        max_decision_time_ms=round(max_decision_time, 3),
        detour_distance=round(detour_distance, 3),
        detour_action_counts=detour_action_counts,
        action_counts=action_counts,
        decision_reasons=decision_reasons,
        disturbed=disturbed,
        disturbance_kind=", ".join(disturbance_kinds),
        final_step=final_step,
        reason=reason,
    )


def _aggregate(results: List[TrialResult]) -> Dict[str, Any]:
    successful = [item for item in results if item.success]
    disturbed = [item for item in results if item.disturbed]
    failures = [item for item in results if not item.success]
    failure_reasons: Dict[str, int] = {}
    action_counts: Dict[str, int] = {}
    decision_reasons: Dict[str, int] = {}
    for item in results:
        for action, count in item.action_counts.items():
            action_counts[action] = action_counts.get(action, 0) + int(count)
        for reason, count in item.decision_reasons.items():
            decision_reasons[reason] = decision_reasons.get(reason, 0) + int(count)
    for item in failures:
        reason = str(item.reason).split(":", 1)[0]
        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
    total_distance = sum(float(item.distance_travelled) for item in results)
    return {
        "trials": len(results),
        "successes": len(successful),
        "success_rate": round(len(successful) / max(1, len(results)), 4),
        "avg_steps": round(sum(item.steps for item in results) / max(1, len(results)), 2),
        "collisions": sum(item.collisions for item in results),
        "replans": sum(item.replans for item in results),
        "recoveries": sum(item.recoveries for item in results),
        "near_misses": sum(item.near_misses for item in results),
        "detour_steps": sum(item.detour_steps for item in results),
        "avg_detour_steps": round(sum(item.detour_steps for item in results) / max(1, len(results)), 2),
        "productive_steps": sum(item.productive_steps for item in results),
        "avg_productive_steps": round(sum(item.productive_steps for item in results) / max(1, len(results)), 2),
        "rotation_steps": sum(item.rotation_steps for item in results),
        "avg_rotation_steps": round(sum(item.rotation_steps for item in results) / max(1, len(results)), 2),
        "wait_steps": sum(item.wait_steps for item in results),
        "avg_wait_steps": round(sum(item.wait_steps for item in results) / max(1, len(results)), 2),
        "distance_travelled": round(total_distance, 2),
        "avg_distance_travelled": round(total_distance / max(1, len(results)), 2),
        "distance_unit": "m",
        "avg_distance_travelled_m": round(total_distance / max(1, len(results)), 2),
        "avg_distance_travelled_cm": round(total_distance / max(1, len(results)) * 100.0, 1),
        "avg_final_distance": round(sum(item.final_distance for item in results) / max(1, len(results)), 2),
        "decision_time_ms": round(sum(item.decision_time_ms for item in results), 2),
        "avg_decision_time_ms": round(sum(item.decision_time_ms for item in results) / max(1, len(results)), 3),
        "max_decision_time_ms": round(max((item.max_decision_time_ms for item in results), default=0.0), 3),
        "detour_distance": round(sum(item.detour_distance for item in results), 2),
        "avg_detour_distance": round(sum(item.detour_distance for item in results) / max(1, len(results)), 3),
        "detour_action_counts": {
            action: sum(item.detour_action_counts.get(action, 0) for item in results)
            for action in sorted({action for item in results for action in item.detour_action_counts})
        },
        "action_counts": action_counts,
        "decision_reasons": decision_reasons,
        "avg_recoveries": round(sum(item.recoveries for item in results) / max(1, len(results)), 2),
        "avg_near_misses": round(sum(item.near_misses for item in results) / max(1, len(results)), 2),
        "disturbed_trials": len(disturbed),
        "failures": len(failures),
        "failure_reasons": failure_reasons,
        "failed_trials": [
            {
                "seed": item.seed,
                "final_step": item.final_step,
                "reason": item.reason,
                "steps": item.steps,
                "replans": item.replans,
                "recoveries": item.recoveries,
                "near_misses": item.near_misses,
                "productive_steps": item.productive_steps,
                "rotation_steps": item.rotation_steps,
                "wait_steps": item.wait_steps,
                "distance_travelled": item.distance_travelled,
                "final_distance": item.final_distance,
                "detour_distance": item.detour_distance,
                "detour_action_counts": item.detour_action_counts,
                "disturbed": item.disturbed,
                "disturbance_kind": item.disturbance_kind,
            }
            for item in failures
        ],
        "results": [item.as_dict() for item in results],
    }


def _capability_gate(adaptive: Dict[str, Any], baseline: Dict[str, Any], *, trials: int) -> Dict[str, Any]:
    """Classify evaluation evidence without confusing simulation with validation.

    The gate is deliberately evidence-based and generic: it consumes metrics
    from any shuffled-scene task rather than naming a particular object or
    route.  ``PROVISIONAL`` means the simulated capability is reliable enough
    to continue testing; only a later restart/resume and hardware gate may
    promote it to ``VERIFIED``.
    """
    success_rate = float(adaptive.get("success_rate", 0.0))
    collisions = int(adaptive.get("collisions", 0))
    disturbed_trials = int(adaptive.get("disturbed_trials", 0))
    randomized = trials >= 20 and disturbed_trials > 0
    safety = collisions == 0
    reliable = success_rate >= 0.95
    baseline_steps = float(baseline.get("avg_steps", 0.0))
    adaptive_steps = float(adaptive.get("avg_steps", 0.0))
    baseline_misses = float(baseline.get("avg_near_misses", 0.0))
    adaptive_misses = float(adaptive.get("avg_near_misses", 0.0))
    efficiency = (
        baseline_steps <= 0.0
        or adaptive_steps <= baseline_steps * 1.10
    ) and (
        baseline_misses <= 0.0
        or adaptive_misses <= baseline_misses * 1.10
    )
    criteria = {
        "randomized_trials": {"passed": randomized, "observed": trials, "minimum": 20},
        "safety": {"passed": safety, "collisions": collisions, "maximum": 0},
        "task_reliability": {"passed": reliable, "success_rate": round(success_rate, 4), "minimum": 0.95},
        "efficiency_against_baseline": {
            "passed": efficiency,
            "adaptive_avg_steps": adaptive_steps,
            "baseline_avg_steps": baseline_steps,
            "adaptive_avg_near_misses": adaptive_misses,
            "baseline_avg_near_misses": baseline_misses,
            "allowed_ratio": 1.10,
        },
        "restart_resume": {"passed": False, "required": True, "note": "not exercised by this benchmark"},
        "hardware_transfer": {"passed": False, "required": True, "note": "simulation only"},
    }

    if not safety or not reliable:
        state = "REGRESSED"
    elif randomized:
        state = "PROVISIONAL"
    else:
        state = "TESTING"
    pending = [name for name, item in criteria.items() if not bool(item.get("passed"))]
    return {
        "state": state,
        "capability": "generic embodied navigation and manipulation under disturbance",
        "criteria": criteria,
        "pending_gates": pending,
        "promotion_rule": "PROVISIONAL -> VERIFIED requires restart/resume evidence and hardware validation",
        "interpretation": (
            "Safe and reliable in randomized simulation; efficiency still needs improvement."
            if state == "PROVISIONAL" and not efficiency
            else "Simulation evidence is sufficient for provisional use."
            if state == "PROVISIONAL"
            else "Evidence is insufficient for provisional promotion."
        ),
    }


def _restart_resume_probe() -> Dict[str, Any]:
    """Exercise the persisted Body plan ledger across a runtime reload.

    This is intentionally separate from the shuffled-scene score: it proves
    that an accepted, partially completed plan and its single active lease
    survive a Body ledger reload without claiming that a physical robot was
    restarted.
    """
    with tempfile.TemporaryDirectory(prefix="pandorabox-plan-probe-") as directory:
        path = Path(directory)
        first = BodyPlanRuntime(path)
        snapshot = BodySnapshot(
            source="probe", frame="world", pose={"x": 0.0, "y": 0.0, "yaw": 0.0},
            objects=[], capabilities=[], reliability=1.0,
        )
        first.record_snapshot(snapshot)
        payload = {
            "plan_id": "restart-resume-probe",
            "objective": "probe persisted plan resume",
            "source": "evaluation",
            "expires_at": time.time() + 300,
            "steps": [
                {"step_id": "observe", "verb": "observe", "target": "scene"},
                {"step_id": "wait", "verb": "wait", "target": "scene"},
            ],
        }
        accepted = first.submit(payload)
        first.begin_execution()
        advanced = first.advance("observe", snapshot.snapshot_id)
        restored = BodyPlanRuntime(path)
        restored.record_snapshot(snapshot)
        active = restored.active_plan()
        competing = restored.submit({**payload, "plan_id": "competing-plan"})
        passed = bool(
            accepted.get("accepted")
            and advanced.get("ok")
            and active is not None
            and active.plan_id == "restart-resume-probe"
            and active.current_step_index == 1
            and not competing.get("accepted")
        )
        return {
            "passed": passed,
            "plan_id": active.plan_id if active else None,
            "current_step_index": active.current_step_index if active else None,
            "next_step": active.steps[active.current_step_index].step_id if active and active.current_step_index < len(active.steps) else None,
            "single_lease_enforced": not bool(competing.get("accepted")),
            "scope": "Body plan ledger reload; not physical robot restart",
        }
def run_shuffled_trials(
    trials: int = 100,
    max_steps: int = 180,
    *,
    seeds: List[int] | None = None,
    report_path: str | Path | None = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """Exercise routing, manipulation and recovery on reproducible scenes."""
    count = max(1, min(250, int(trials)))
    trial_seeds = list(seeds or range(count))[:count]
    if len(trial_seeds) < count:
        trial_seeds.extend(range(len(trial_seeds), count))
    deterministic_shuffling = "seed" in inspect.signature(SimulatedRoom.reset_episode).parameters
    learner = _EvaluationLearner()
    results: list[TrialResult] = []
    learning_curve: list[Dict[str, Any]] = []
    for index, seed in enumerate(trial_seeds, start=1):
        results.append(_run_trial(
            seed, max_steps, allow_recovery=True, inject_disturbance=True,
            learner=learner, progress_callback=progress_callback, trial_index=index,
        ))
        if index % 10 == 0 or index == count:
            window = results[-min(10, len(results)):]
            learning_curve.append({
                "trial": index,
                "success_rate": round(sum(item.success for item in window) / len(window), 4),
                "avg_steps": round(sum(item.steps for item in window) / len(window), 2),
                "avg_near_misses": round(sum(item.near_misses for item in window) / len(window), 2),
                "model": learner.snapshot(),
            })
    baseline_results = [_run_trial(seed, max_steps, allow_recovery=False, inject_disturbance=True, planner_geometry="continuous") for seed in trial_seeds]
    legacy_results = [_run_trial(seed, max_steps, allow_recovery=True, inject_disturbance=True, planner_geometry="legacy_grid") for seed in trial_seeds]
    adaptive = _aggregate(results)
    baseline = _aggregate(baseline_results)
    legacy = _aggregate(legacy_results)
    adaptive["time_cost_vs_baseline_steps"] = round(adaptive["avg_steps"] - baseline["avg_steps"], 2)
    adaptive["detour_cost_vs_baseline_steps"] = round(adaptive["avg_detour_steps"] - baseline["avg_detour_steps"], 2)
    adaptive["detour_distance_cost_vs_baseline"] = round(adaptive["avg_detour_distance"] - baseline["avg_detour_distance"], 3)
    adaptive["decision_latency_vs_baseline_ms"] = round(adaptive["avg_decision_time_ms"] - baseline["avg_decision_time_ms"], 3)
    capability_gate = _capability_gate(adaptive, baseline, trials=count)
    restart_resume_probe = _restart_resume_probe()
    report = {
        "schema": "pandorabox.embodied_evaluation.v1",
        "suite": "generic_shuffled_scene_with_disturbance",
        "controller": "task_graph_local_planner",
        "planner_geometry": "continuous_metric",
        "scene_protocol": {
            "variable_object_count": True,
            "extra_static_obstacles": "0-3 per scene",
            "role_selection": "properties, not fixture identifiers",
            "state_encoder": "permutation_invariant_object_pooling",
            "metric_coordinates": True,
            "fractional_scene_offset_m": [0.23, -0.17],
        },
        "deterministic_shuffling": deterministic_shuffling,
        "recorded_at": time.time(),
        "learning": {
            "protocol": "online latent dynamics from sensorimotor transitions",
            "curve": learning_curve,
            "final": learner.snapshot(),
        },
        **adaptive,
        "baseline_without_recovery": baseline,
        "planner_comparison": {
            "same_seeds": True,
            "same_disturbances": True,
            "metric": {
                "successes": adaptive["successes"],
                "collisions": adaptive["collisions"],
                "avg_steps": adaptive["avg_steps"],
                "avg_distance_travelled": adaptive["avg_distance_travelled"],
                "avg_near_misses": adaptive["avg_near_misses"],
            },
            "legacy_grid": {
                "successes": legacy["successes"],
                "collisions": legacy["collisions"],
                "avg_steps": legacy["avg_steps"],
                "avg_distance_travelled": legacy["avg_distance_travelled"],
                "avg_near_misses": legacy["avg_near_misses"],
            },
            "delta_metric_minus_legacy": {
                "successes": adaptive["successes"] - legacy["successes"],
                "collisions": adaptive["collisions"] - legacy["collisions"],
                "avg_steps": round(adaptive["avg_steps"] - legacy["avg_steps"], 2),
                "avg_distance_travelled": round(adaptive["avg_distance_travelled"] - legacy["avg_distance_travelled"], 2),
                "avg_near_misses": round(adaptive["avg_near_misses"] - legacy["avg_near_misses"], 2),
            },
        },
        "capability_gate": capability_gate,
        "restart_resume_probe": restart_resume_probe,
    }
    if report_path:
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(report, ensure_ascii=False) + "\n")
    return report
