"""Repeatable, local evaluation of the generic Body task stack."""
from __future__ import annotations

import json
import inspect
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .contracts import BodyPlan, PlanStep
from .core import EmbodiedWorldModel
from .dynamics import LatentWorldDynamics
from .sim_world import SimulatedRoom
from .task_graph import TaskGraphExecutor
from .types import Action


@dataclass
class TrialResult:
    seed: int
    success: bool
    steps: int
    collisions: int
    replans: int
    recoveries: int
    near_misses: int = 0
    disturbed: bool = False
    disturbance_kind: str = ""
    final_step: str = ""
    reason: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def _evaluation_state(room: SimulatedRoom) -> Any:
    """Encode arbitrary scene geometry without naming a fixture or route."""
    import numpy as np

    body = room.body_state()
    width = max(1.0, float(body.capabilities.get("world_width", room.width)))
    height = max(1.0, float(body.capabilities.get("world_height", room.height)))
    values = [
        float(body.position[0]) / width,
        float(body.position[1]) / height,
        math.sin(float(body.orientation)),
        math.cos(float(body.orientation)),
        1.0 if body.posture.get("holding") else 0.0,
        float(body.capabilities.get("mobile_obstacle_speed", 0.0)),
    ]
    for item in sorted(room.objects.values(), key=lambda value: (str(value.get("kind", "")), str(value.get("id", "")))):
        kind = str(item.get("kind", "object"))
        kind_signal = (sum(ord(char) for char in kind) % 997) / 997.0
        values.extend([
            (float(item.get("x", 0.0)) - float(body.position[0])) / width,
            (float(item.get("y", 0.0)) - float(body.position[1])) / height,
            float(item.get("size", 0.0)) / max(width, height),
            min(1.0, float(item.get("mass", 0.0)) / 1000.0),
            kind_signal,
        ])
    values.extend([0.0] * max(0, 32 - len(values)))
    return np.asarray(values[:32], dtype="float32")


class _EvaluationLearner:
    """Small in-run learner for the shuffled-scene protocol."""

    def __init__(self) -> None:
        self.model = LatentWorldDynamics(in_dim=32, latent_dim=16, hidden_dim=32, lr=2e-3, seed=19)
        self.transitions = 0
        self.updates = 0
        self.losses: list[float] = []

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
        }


def _generic_plan() -> BodyPlan:
    return BodyPlan(
        objective="move an object through a surface to a goal",
        required_capabilities=["navigate", "grab", "release"],
        expires_at=time.time() + 3600,
        steps=[
            PlanStep("approach_object", "navigate", "parcel"),
            PlanStep("grasp_object", "grab", "parcel"),
            PlanStep("approach_surface", "navigate", "dock"),
            PlanStep("place_on_surface", "release", "dock", postconditions=[{"type": "on_surface", "target": "parcel", "surface": "dock"}]),
            PlanStep("regrasp_object", "grab", "parcel"),
            PlanStep("approach_goal", "navigate", "goal"),
            PlanStep("place_at_goal", "release", "goal", postconditions=[{"type": "goal_reached", "target": "parcel", "goal": "goal"}]),
        ],
    )


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
) -> TrialResult:
    room = SimulatedRoom()
    try:
        room.reset_episode(shuffle=True, seed=int(seed))
    except TypeError as exc:
        if "unexpected keyword argument 'seed'" not in str(exc):
            raise
        room.reset_episode(shuffle=True)
    parcel = room.objects.pop("cup")
    parcel.update({"id": "parcel", "label": "parcel", "kind": "object"})
    room.objects["parcel"] = parcel
    dock = room.objects.pop("table")
    dock.update({"id": "dock", "label": "dock", "kind": "surface"})
    room.objects["dock"] = dock
    plan, executor = _generic_plan(), TaskGraphExecutor()
    replans = recoveries = 0
    disturbed = False
    disturbance_kinds: list[str] = []
    reason = "step_budget_exhausted"
    disturbance_step = max(6, min(18, max_steps // 4))
    disturbance_steps = {disturbance_step, min(max_steps - 1, disturbance_step + 24)}

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
        action = decision.action
        if action is None:
            if allow_recovery:
                recovery = executor.recovery_action(plan, snapshot, body)
                action = recovery.action or Action(type="wait")
                recoveries += 1
            else:
                action = Action(type="wait")
        state_before = _evaluation_state(room)
        _, outcome = room.step(action)
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
                room.step(recovery.action)
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
    for item in failures:
        reason = str(item.reason).split(":", 1)[0]
        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
    return {
        "trials": len(results),
        "successes": len(successful),
        "success_rate": round(len(successful) / max(1, len(results)), 4),
        "avg_steps": round(sum(item.steps for item in results) / max(1, len(results)), 2),
        "collisions": sum(item.collisions for item in results),
        "replans": sum(item.replans for item in results),
        "recoveries": sum(item.recoveries for item in results),
        "near_misses": sum(item.near_misses for item in results),
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
                "disturbed": item.disturbed,
                "disturbance_kind": item.disturbance_kind,
            }
            for item in failures
        ],
        "results": [item.as_dict() for item in results],
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
    baseline_results = [_run_trial(seed, max_steps, allow_recovery=False, inject_disturbance=True) for seed in trial_seeds]
    adaptive = _aggregate(results)
    baseline = _aggregate(baseline_results)
    report = {
        "schema": "pandorabox.embodied_evaluation.v1",
        "suite": "generic_shuffled_scene_with_disturbance",
        "controller": "task_graph_local_planner",
        "deterministic_shuffling": deterministic_shuffling,
        "recorded_at": time.time(),
        "learning": {
            "protocol": "online latent dynamics from sensorimotor transitions",
            "curve": learning_curve,
            "final": learner.snapshot(),
        },
        **adaptive,
        "baseline_without_recovery": baseline,
    }
    if report_path:
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(report, ensure_ascii=False) + "\n")
    return report
