"""Repeatable, local evaluation of the generic Body task stack."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List

from .contracts import BodyPlan, PlanStep
from .core import EmbodiedWorldModel
from .sim_world import SimulatedRoom
from .task_graph import TaskGraphExecutor
from .types import Action


@dataclass
class TrialResult:
    success: bool
    steps: int
    collisions: int
    replans: int
    recoveries: int
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


def run_shuffled_trials(trials: int = 25, max_steps: int = 180) -> Dict[str, Any]:
    """Exercise routing, manipulation and recovery on fresh shuffled scenes."""
    results: List[TrialResult] = []
    for _ in range(max(1, min(250, int(trials)))):
        room = SimulatedRoom()
        room.reset_episode(shuffle=True)
        # Rename only the fixture entities. The evaluator and executor retain
        # no dependency on their original demonstration names.
        parcel = room.objects.pop("cup")
        parcel.update({"id": "parcel", "label": "parcel", "kind": "object"})
        room.objects["parcel"] = parcel
        dock = room.objects.pop("table")
        dock.update({"id": "dock", "label": "dock", "kind": "surface"})
        room.objects["dock"] = dock
        plan, executor = _generic_plan(), TaskGraphExecutor()
        replans = recoveries = 0
        reason = "step_budget_exhausted"
        for step_number in range(max_steps):
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
                recovery = executor.recovery_action(plan, snapshot, body)
                action = recovery.action or Action(type="wait")
                recoveries += 1
            _, outcome = room.step(action)
            if outcome.kind in {"failure", "danger"}:
                recovery = executor.recovery_action(plan, snapshot, room.body_state())
                if recovery.action:
                    room.step(recovery.action)
                    recoveries += 1
        results.append(TrialResult(
            success=reason == "completed",
            steps=room.steps,
            collisions=room.collision_count,
            replans=replans,
            recoveries=recoveries,
            reason=reason,
        ))
    successful = [item for item in results if item.success]
    return {
        "trials": len(results),
        "successes": len(successful),
        "success_rate": round(len(successful) / max(1, len(results)), 4),
        "avg_steps": round(sum(item.steps for item in results) / max(1, len(results)), 2),
        "collisions": sum(item.collisions for item in results),
        "replans": sum(item.replans for item in results),
        "recoveries": sum(item.recoveries for item in results),
        "results": [item.as_dict() for item in results],
    }
