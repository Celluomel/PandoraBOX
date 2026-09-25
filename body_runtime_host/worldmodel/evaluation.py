"""Repeatable, local evaluation of the generic Body task stack."""
from __future__ import annotations

import json
import inspect
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .contracts import BodyPlan, PlanStep
from .core import EmbodiedWorldModel
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
    disturbed: bool = False
    reason: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


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


def _run_trial(
    seed: int,
    max_steps: int,
    *,
    allow_recovery: bool,
    inject_disturbance: bool,
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
    reason = "step_budget_exhausted"
    disturbance_step = max(6, min(18, max_steps // 4))
    for step_number in range(max_steps):
        if inject_disturbance and step_number == disturbance_step:
            disturbed = _displace_surface(room, "dock", seed + 17)
        obs, body = room.observe(), room.body_state()
        snapshot = EmbodiedWorldModel._make_plan_snapshot(obs, body)
        decision = executor.decide(plan, snapshot, body)
        if decision.satisfied:
            plan.current_step_index += 1
            if plan.current_step_index >= len(plan.steps):
                reason = "completed"
                break
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
        _, outcome = room.step(action)
        if allow_recovery and outcome.kind in {"failure", "danger"}:
            recovery = executor.recovery_action(plan, snapshot, room.body_state())
            if recovery.action:
                room.step(recovery.action)
                recoveries += 1
    return TrialResult(
        seed=int(seed),
        success=reason == "completed",
        steps=room.steps,
        collisions=room.collision_count,
        replans=replans,
        recoveries=recoveries,
        disturbed=disturbed,
        reason=reason,
    )


def _aggregate(results: List[TrialResult]) -> Dict[str, Any]:
    successful = [item for item in results if item.success]
    disturbed = [item for item in results if item.disturbed]
    return {
        "trials": len(results),
        "successes": len(successful),
        "success_rate": round(len(successful) / max(1, len(results)), 4),
        "avg_steps": round(sum(item.steps for item in results) / max(1, len(results)), 2),
        "collisions": sum(item.collisions for item in results),
        "replans": sum(item.replans for item in results),
        "recoveries": sum(item.recoveries for item in results),
        "disturbed_trials": len(disturbed),
        "results": [item.as_dict() for item in results],
    }


def run_shuffled_trials(
    trials: int = 100,
    max_steps: int = 180,
    *,
    seeds: List[int] | None = None,
    report_path: str | Path | None = None,
) -> Dict[str, Any]:
    """Exercise routing, manipulation and recovery on reproducible scenes."""
    count = max(1, min(250, int(trials)))
    trial_seeds = list(seeds or range(count))[:count]
    if len(trial_seeds) < count:
        trial_seeds.extend(range(len(trial_seeds), count))
    deterministic_shuffling = "seed" in inspect.signature(SimulatedRoom.reset_episode).parameters
    results = [_run_trial(seed, max_steps, allow_recovery=True, inject_disturbance=True) for seed in trial_seeds]
    baseline_results = [_run_trial(seed, max_steps, allow_recovery=False, inject_disturbance=True) for seed in trial_seeds]
    adaptive = _aggregate(results)
    baseline = _aggregate(baseline_results)
    report = {
        "schema": "pandorabox.embodied_evaluation.v1",
        "suite": "generic_shuffled_scene_with_disturbance",
        "controller": "task_graph_local_planner",
        "deterministic_shuffling": deterministic_shuffling,
        "recorded_at": time.time(),
        **adaptive,
        "baseline_without_recovery": baseline,
    }
    if report_path:
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(report, ensure_ascii=False) + "\n")
    return report
