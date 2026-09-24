"""Generic, snapshot-grounded TaskGraph execution for Body plans.

The executor deliberately understands only physical predicates and action
capabilities.  It does not contain a scenario script: a plan supplies the
ordered objective, while the Body proves progress from its current snapshot.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .contracts import BodyPlan, BodySnapshot, PlanStep
from .types import Action, BodyState


def _distance(a: Dict[str, float], b: Dict[str, Any]) -> float:
    pos = b.get("position") or [0.0, 0.0, 0.0]
    return math.hypot(float(a.get("x", 0.0)) - float(pos[0]), float(a.get("y", 0.0)) - float(pos[1]))


@dataclass
class TaskDecision:
    action: Optional[Action]
    step_id: str = ""
    reason: str = ""
    satisfied: bool = False


class TaskGraphExecutor:
    """Derive the next safe primitive action from a generic plan step."""

    def decide(self, plan: BodyPlan, snapshot: BodySnapshot, body: BodyState) -> TaskDecision:
        if plan.current_step_index >= len(plan.steps):
            return TaskDecision(None, reason="all plan steps are satisfied", satisfied=True)
        step = plan.steps[plan.current_step_index]
        if self._satisfied(step, snapshot, body):
            return TaskDecision(None, step.step_id, "postcondition observed", satisfied=True)
        if step.verb == "navigate":
            return TaskDecision(self._navigation_action(step.target, snapshot, body), step.step_id, "route toward planned target")
        if step.verb in {"grab", "release", "push", "wait"}:
            return TaskDecision(Action(type=step.verb, target=step.target), step.step_id, "execute planned primitive")
        return TaskDecision(None, step.step_id, f"unsupported plan verb: {step.verb}")

    def _satisfied(self, step: PlanStep, snapshot: BodySnapshot, body: BodyState) -> bool:
        predicates = step.postconditions or [self._default_postcondition(step)]
        return all(self._predicate(predicate, snapshot, body) for predicate in predicates)

    @staticmethod
    def _default_postcondition(step: PlanStep) -> Dict[str, Any]:
        if step.verb == "navigate":
            return {"type": "near", "target": step.target}
        if step.verb == "grab":
            return {"type": "holding", "target": step.target}
        if step.verb == "release":
            return {"type": "empty_gripper"}
        return {"type": "action_completed"}

    def _predicate(self, predicate: Dict[str, Any], snapshot: BodySnapshot, body: BodyState) -> bool:
        kind = str(predicate.get("type") or "").lower()
        if kind == "near":
            target = self._object(str(predicate.get("target") or ""), snapshot)
            reach = float(predicate.get("distance", body.capabilities.get("reach", 1.0)))
            return bool(target and _distance(snapshot.pose, target) <= reach)
        if kind == "holding":
            return str(body.posture.get("holding") or "") == str(predicate.get("target") or "")
        if kind == "empty_gripper":
            return not body.posture.get("holding")
        if kind == "action_completed":
            return False
        return False

    @staticmethod
    def _object(target: str, snapshot: BodySnapshot) -> Optional[Dict[str, Any]]:
        return next((item for item in snapshot.objects if str(item.get("id")) == target), None)

    def _navigation_action(self, target_id: str, snapshot: BodySnapshot, body: BodyState) -> Action:
        target = self._object(target_id, snapshot)
        if target is None:
            return Action(type="wait", target=target_id)
        pos = target.get("position") or [0.0, 0.0, 0.0]
        desired = math.atan2(float(pos[1]) - snapshot.pose["y"], float(pos[0]) - snapshot.pose["x"])
        delta = (desired - float(body.orientation) + math.pi) % (2 * math.pi) - math.pi
        if abs(delta) > 0.35:
            return Action(type="turn_left" if delta > 0 else "turn_right", target=target_id)
        return Action(type="forward", target=target_id)
