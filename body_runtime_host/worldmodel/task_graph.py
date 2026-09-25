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
from .local_planner import LocalRoutePlanner
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
    details: Dict[str, Any] = None


class TaskGraphExecutor:
    """Derive the next safe primitive action from a generic plan step."""

    def decide(self, plan: BodyPlan, snapshot: BodySnapshot, body: BodyState) -> TaskDecision:
        if plan.current_step_index >= len(plan.steps):
            return TaskDecision(None, reason="all plan steps are satisfied", satisfied=True)
        step = plan.steps[plan.current_step_index]
        if self._satisfied(step, snapshot, body):
            return TaskDecision(None, step.step_id, "postcondition observed", satisfied=True)
        if step.verb == "explore":
            return self._explore_decision(step, snapshot, body)
        if step.verb == "navigate":
            return self._route_decision(step.step_id, step.target, snapshot, body, arguments=step.arguments)
        release_target = self._release_destination(step) if step.verb == "release" else step.target
        if step.verb in {"grab", "release"} and not self._predicate({"type": "near", "target": release_target, "operation": step.verb}, snapshot, body):
            reach_kind = "grab" if step.verb == "grab" else "release"
            reason = "align_for_grasp" if reach_kind == "grab" else "align_for_release"
            return self._route_decision(step.step_id, release_target, snapshot, body, reason, step.arguments)
        if step.verb in {"grab", "release", "push", "wait"}:
            return TaskDecision(
                Action(type=step.verb, target=release_target, params={"plan_controlled": True, **step.arguments}),
                step.step_id,
                "execute planned primitive",
            )
        return TaskDecision(None, step.step_id, f"unsupported plan verb: {step.verb}")

    def _explore_decision(self, step: PlanStep, snapshot: BodySnapshot, body: BodyState) -> TaskDecision:
        """Visit bounded scene anchors before allowing the next plan step."""
        arguments = dict(step.arguments or {})
        targets = [str(value) for value in arguments.get("targets") or [] if str(value)]
        if not targets:
            targets = [
                str(item.get("id")) for item in snapshot.objects
                if item.get("id") and item.get("position") is not None
                and str(item.get("kind") or "").lower() not in {"object", "item", "target"}
            ]
        index = max(0, min(int(arguments.get("target_index", 0) or 0), len(targets)))
        while index < len(targets):
            target = targets[index]
            if self._predicate({"type": "near", "target": target}, snapshot, body):
                index += 1
                continue
            updated = {**arguments, "targets": targets, "target_index": index}
            decision = self._route_decision(step.step_id, target, snapshot, body, "explore_scene", updated)
            decision.details = {**(decision.details or {}), "step_arguments": updated, "explore_target": target, "explore_index": index}
            return decision
        updated = {**arguments, "targets": targets, "target_index": len(targets)}
        return TaskDecision(None, step.step_id, "scene exploration complete", satisfied=True, details={"step_arguments": updated, "explore_count": len(targets)})

    def _route_decision(self, step_id: str, target: str, snapshot: BodySnapshot, body: BodyState, align_reason: str = "", arguments: Optional[Dict[str, Any]] = None) -> TaskDecision:
        route_reach = None
        if align_reason == "align_for_release":
            route_reach = float(body.capabilities.get("placement_reach", body.capabilities.get("reach", 1.0)))
        route = self.local_planner.route(target, snapshot, body, reach=route_reach)
        self.last_route = route.as_dict()
        if route.blocked:
            return TaskDecision(None, step_id, "recover_from_blockage", details=self.last_route)
        return TaskDecision(self._navigation_action(route, snapshot, body, arguments), step_id, align_reason or route.reason, details=self.last_route)

    def recovery_action(self, plan: BodyPlan, snapshot: BodySnapshot, body: BodyState) -> TaskDecision:
        """Take one reversible clearance action before re-evaluating a step."""
        if plan.current_step_index >= len(plan.steps):
            return TaskDecision(None, reason="no remaining step")
        step = plan.steps[plan.current_step_index]
        target = self._object(step.target, snapshot)
        # Recovery is still a Body action, so it must obey the same geometry
        # as ordinary navigation.  The old unconditional retreat could move
        # directly into a wall or furniture and turn one blockage into a
        # collision loop.
        if self._translation_clear(snapshot, body, -1.0):
            return TaskDecision(Action(type="backward", target=step.target, params={"plan_controlled": True}), step.step_id, "recover clearance by increasing separation")
        desired = None
        if target:
            desired = math.atan2(
                float((target.get("position") or [0.0, 0.0])[1]) - float(body.position[1]),
                float((target.get("position") or [0.0, 0.0])[0]) - float(body.position[0]),
            )
        delta = ((desired - float(body.orientation) + math.pi) % (2 * math.pi) - math.pi) if desired is not None else 0.0
        preferred = "turn_left" if delta >= 0 else "turn_right"
        alternate = "turn_right" if preferred == "turn_left" else "turn_left"
        for action in (preferred, alternate):
            turn = math.radians(90.0 if action == "turn_left" else -90.0)
            heading = (float(body.orientation) + turn + math.pi) % (2 * math.pi) - math.pi
            if self._translation_clear(snapshot, body, 1.0, heading=heading):
                return TaskDecision(Action(type=action, target=step.target, params={"plan_controlled": True}), step.step_id, "recover by changing heading before replanning")
        return TaskDecision(Action(type="wait", target=step.target, params={"plan_controlled": True}), step.step_id, "recover by waiting for a clear observation")

    @staticmethod
    def _translation_clear(snapshot: BodySnapshot, body: BodyState, distance: float, heading: Optional[float] = None) -> bool:
        """Check one grid translation using the current Body snapshot."""
        angle = float(body.orientation if heading is None else heading)
        x = float(body.position[0]) + math.cos(angle) * distance
        y = float(body.position[1]) + math.sin(angle) * distance
        width = float(body.capabilities.get("world_width", 12.0))
        height = float(body.capabilities.get("world_height", 12.0))
        if x < 0.0 or y < 0.0 or x >= width or y >= height:
            return False
        for item in snapshot.objects:
            if str(item.get("kind")) not in {"obstacle", "chair", "table", "surface", "wall", "mobile_obstacle"}:
                continue
            position = item.get("position") or [0.0, 0.0]
            if math.hypot(float(position[0]) - x, float(position[1]) - y) < 0.6:
                return False
        return True

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
            destination = str(step.arguments.get("surface") or step.arguments.get("destination") or step.target)
            held = str(step.arguments.get("held") or "")
            if held and destination:
                return {"type": "on_surface", "target": held, "surface": destination}
            return {"type": "empty_gripper"}
        return {"type": "action_completed"}

    @staticmethod
    def _release_destination(step: PlanStep) -> str:
        """Resolve the receiving surface, keeping older plans compatible."""
        return str(step.arguments.get("surface") or step.arguments.get("destination") or step.target)

    def _predicate(self, predicate: Dict[str, Any], snapshot: BodySnapshot, body: BodyState) -> bool:
        if not isinstance(predicate, dict):
            # A malformed persisted/LLM predicate must fail closed, not stop
            # the Body loop with an AttributeError.
            return False
        kind = str(predicate.get("type") or "").lower()
        if kind in {"near", "at_location"}:
            target = self._object(str(predicate.get("target") or ""), snapshot)
            default_reach = body.capabilities.get("reach", 1.0)
            if predicate.get("operation") == "release":
                default_reach = body.capabilities.get("placement_reach", min(float(default_reach), 1.2))
            reach = float(predicate.get("distance", default_reach))
            return bool(target and _distance(snapshot.pose, target) <= reach)
        if kind in {"holding", "held"}:
            return str(body.posture.get("holding") or "") == str(predicate.get("target") or "")
        if kind == "released":
            return str(body.posture.get("holding") or "") != str(predicate.get("target") or "")
        if kind == "empty_gripper":
            return not body.posture.get("holding")
        if kind in {"on_surface", "goal_reached"}:
            target = self._object(str(predicate.get("target") or ""), snapshot)
            surface = self._object(str(predicate.get("surface") or predicate.get("goal") or "goal"), snapshot)
            radius = float(predicate.get("distance", 1.0))
            return bool(target and surface and _distance({"x": float(target["position"][0]), "y": float(target["position"][1])}, surface) <= radius)
        if kind == "clear_path":
            return self._clear_path(str(predicate.get("target") or ""), snapshot, body)
        if kind == "action_completed":
            return False
        return False

    @staticmethod
    def _object(target: str, snapshot: BodySnapshot) -> Optional[Dict[str, Any]]:
        return next((item for item in snapshot.objects if str(item.get("id")) == target), None)

    def _clear_path(self, target_id: str, snapshot: BodySnapshot, body: BodyState) -> bool:
        target = self._object(target_id, snapshot)
        if target is None:
            return False
        tx, ty = (target.get("position") or [0.0, 0.0])[:2]
        bx, by = float(body.position[0]), float(body.position[1])
        length = math.hypot(tx - bx, ty - by)
        if length < 1e-6:
            return True
        for item in snapshot.objects:
            if str(item.get("id")) == target_id or str(item.get("kind")) in {"goal", "target"}:
                continue
            if str(item.get("kind")) not in {"obstacle", "chair", "table", "surface", "wall", "mobile_obstacle"}:
                continue
            ox, oy = (item.get("position") or [0.0, 0.0])[:2]
            projection = max(0.0, min(1.0, ((ox - bx) * (tx - bx) + (oy - by) * (ty - by)) / (length * length)))
            nearest_x, nearest_y = bx + projection * (tx - bx), by + projection * (ty - by)
            clearance = max(0.45, float(item.get("size", 0.5)) * 0.5 + 0.25)
            if math.hypot(ox - nearest_x, oy - nearest_y) < clearance:
                return False
        return True

    def _navigation_action(self, route: Any, snapshot: BodySnapshot, body: BodyState, arguments: Optional[Dict[str, Any]] = None) -> Action:
        waypoint = route.next_cell
        if waypoint is None:
            return Action(type="wait", target=route.target)
        desired = math.atan2(float(waypoint[1]) - snapshot.pose["y"], float(waypoint[0]) - snapshot.pose["x"])
        delta = (desired - float(body.orientation) + math.pi) % (2 * math.pi) - math.pi
        if abs(delta) > 0.35:
            return Action(type="turn_left" if delta > 0 else "turn_right", target=route.target, params={**(arguments or {}), "waypoint": list(waypoint), "plan_controlled": True})
        return Action(type="forward", target=route.target, params={**(arguments or {}), "waypoint": list(waypoint), "plan_controlled": True})
    def __init__(self) -> None:
        self.local_planner = LocalRoutePlanner()
        self.last_route: Dict[str, Any] = {}
