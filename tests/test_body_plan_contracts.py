"""Phase-0 embodied plan contracts: validation and restart-safe persistence."""
from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from body_runtime_host.worldmodel.contracts import ActionResult, BodyPlan, BodySnapshot, PlanStep
from body_runtime_host.worldmodel.plan_runtime import BodyPlanRuntime
from body_runtime_host.worldmodel.task_graph import TaskGraphExecutor
from body_runtime_host.worldmodel.local_planner import LocalRoutePlanner
from body_runtime_host.worldmodel.types import BodyState
from body_runtime_host.worldmodel.types import Action
from body_runtime_host.worldmodel.sim_world import SimulatedRoom


def snapshot() -> BodySnapshot:
    return BodySnapshot(
        source="simulated_room",
        frame="world",
        pose={"x": 1.0, "y": 1.0, "yaw": 0.0},
        objects=[{"id": "cup"}, {"id": "table"}],
        capabilities=["navigate", "grab", "release"],
        reliability=1.0,
    )


def plan(**overrides):
    value = {
        "objective": "place the cup on the table",
        "required_capabilities": ["navigate", "grab", "release"],
        "expires_at": time.time() + 60,
        "steps": [
            {"step_id": "approach", "verb": "navigate", "target": "cup"},
            {"step_id": "grasp", "verb": "grab", "target": "cup"},
            {"step_id": "place", "verb": "release", "target": "table"},
        ],
    }
    value.update(overrides)
    return value


class BodyPlanContractTests(unittest.TestCase):
    def test_compiler_repairs_release_target_to_receiving_surface(self):
        from cognition.body_plan_compiler import compile_body_plan

        body_snapshot = {
            "snapshot_id": "snap-1",
            "objects": [
                {"id": "cup", "kind": "target"},
                {"id": "table", "kind": "table"},
                {"id": "chair", "kind": "chair"},
            ],
        }
        payload = {
            "objective": "move the cup to the table then the chair",
            "required_capabilities": ["navigate", "grab", "release"],
            "steps": [
                {"step_id": "to-table", "verb": "navigate", "target": "table"},
                {"step_id": "grab-1", "verb": "grab", "target": "cup"},
                {"step_id": "release-1", "verb": "release", "target": "cup"},
                {"step_id": "to-chair", "verb": "navigate", "target": "chair"},
                {"step_id": "grab-2", "verb": "grab", "target": "cup"},
                {"step_id": "release-2", "verb": "release", "target": "cup"},
            ],
        }
        result = compile_body_plan("move the cup to the table then the chair", body_snapshot, lambda *_args, **_kwargs: json.dumps(payload))
        self.assertTrue(result["accepted"], result)
        releases = [step for step in result["steps"] if step["verb"] == "release"]
        self.assertEqual([step["target"] for step in releases], ["table", "chair"])
        self.assertEqual([step["arguments"]["held"] for step in releases], ["cup", "cup"])

    def test_rejects_unknown_target_and_missing_capability(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = BodyPlanRuntime(Path(tmp))
            runtime.record_snapshot(snapshot())
            result = runtime.submit(plan(required_capabilities=["navigate", "fly"], steps=[
                {"step_id": "x", "verb": "navigate", "target": "moon"},
            ]))
            self.assertFalse(result["accepted"])
            self.assertTrue(any("missing capabilities" in error for error in result["errors"]))
            self.assertTrue(any("unknown target" in error for error in result["errors"]))

    def test_intrinsic_observation_capabilities_do_not_require_hardware(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = BodyPlanRuntime(Path(tmp))
            runtime.record_snapshot(snapshot())
            result = runtime.submit(plan(
                required_capabilities=["navigate", "wait", "inspect", "avoid"],
                steps=[{"step_id": "route", "verb": "navigate", "target": "table"}],
            ))
            self.assertTrue(result["accepted"], result)

    def test_plan_restores_and_enforces_single_active_lease(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            runtime = BodyPlanRuntime(path)
            runtime.record_snapshot(snapshot())
            accepted = runtime.submit(plan(plan_id="plan-cup"))
            self.assertTrue(accepted["accepted"])
            self.assertEqual(runtime.payload()["active_plan"]["state"], "ready")

            restored = BodyPlanRuntime(path)
            restored.record_snapshot(snapshot())
            self.assertEqual(restored.payload()["active_plan"]["plan_id"], "plan-cup")
            competing = restored.submit(plan(plan_id="plan-other"))
            self.assertFalse(competing["accepted"])
            self.assertIn("lease", competing["errors"][0])

    def test_cancel_releases_active_plan_and_keeps_audit_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            runtime = BodyPlanRuntime(path)
            runtime.record_snapshot(snapshot())
            self.assertTrue(runtime.submit(plan(plan_id="plan-cup"))["accepted"])
            self.assertTrue(runtime.cancel("plan-cup")["ok"])
            self.assertIsNone(runtime.payload()["active_plan"])
            records = (path / "plans.jsonl").read_text(encoding="utf-8")
            self.assertIn('"accepted"', records)
            self.assertIn('"cancelled"', records)

    def test_action_result_requires_current_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            runtime = BodyPlanRuntime(path)
            current = snapshot()
            runtime.record_snapshot(current)
            result = ActionResult(
                plan_id="plan", step_id="step", action_id="action", status="success",
                outcome="moved", snapshot_id=current.snapshot_id,
            )
            self.assertTrue(runtime.record_action(result)["ok"])
            stale = ActionResult(
                plan_id="plan", step_id="step", action_id="stale", status="success",
                outcome="moved", snapshot_id="snap-stale",
            )
            self.assertFalse(runtime.record_action(stale)["ok"])
            self.assertIn('"action_result"', (path / "actions.jsonl").read_text(encoding="utf-8"))

    def test_task_graph_uses_geometry_and_observed_postconditions(self):
        current = snapshot()
        current.objects[0]["position"] = [4.0, 1.0, 0.0]
        plan_value = BodyPlan(
            objective="approach and grasp cup",
            steps=[
                PlanStep(step_id="approach", verb="navigate", target="cup"),
                PlanStep(step_id="grasp", verb="grab", target="cup"),
            ],
        )
        executor = TaskGraphExecutor()
        body = BodyState(position=[1.0, 1.0, 0.0], orientation=0.0, posture={"holding": ""})
        decision = executor.decide(plan_value, current, body)
        self.assertEqual(decision.action.type, "forward")
        current.pose["x"] = 4.0
        body.position[0] = 4.0
        self.assertTrue(executor.decide(plan_value, current, body).satisfied)
        plan_value.current_step_index = 1
        body.posture["holding"] = "cup"
        self.assertTrue(executor.decide(plan_value, current, body).satisfied)

    def test_task_graph_checks_surface_path_and_expiry(self):
        current = snapshot()
        current.objects = [
            {"id": "cup", "kind": "target", "position": [4.0, 1.0, 0.0], "size": 0.4},
            {"id": "table", "kind": "table", "position": [4.2, 1.0, 0.0], "size": 1.0},
            {"id": "pillar", "kind": "obstacle", "position": [2.5, 1.0, 0.0], "size": 0.8},
        ]
        body = BodyState(position=[1.0, 1.0, 0.0], posture={"holding": ""})
        executor = TaskGraphExecutor()
        self.assertTrue(executor._predicate({"type": "on_surface", "target": "cup", "surface": "table"}, current, body))
        self.assertFalse(executor._predicate({"type": "clear_path", "target": "cup"}, current, body))
        with tempfile.TemporaryDirectory() as tmp:
            runtime = BodyPlanRuntime(Path(tmp))
            runtime.record_snapshot(current)
            self.assertTrue(runtime.submit(plan(expires_at=time.time() + 0.01))["accepted"])
            time.sleep(0.02)
            self.assertEqual(runtime.expire_if_needed()["plan"]["state"], "expired")
            self.assertIsNone(runtime.active_plan())

    def test_task_graph_releases_held_object_on_destination_surface(self):
        current = snapshot()
        current.objects = [
            {"id": "parcel", "kind": "object", "position": [4.0, 1.0, 0.0], "size": 0.4},
            {"id": "chair", "kind": "chair", "position": [4.0, 1.0, 0.0], "size": 0.8},
        ]
        current.pose = {"x": 4.0, "y": 1.0, "yaw": 0.0}
        body = BodyState(position=[4.0, 1.0, 0.0], posture={"holding": "parcel"})
        plan_value = BodyPlan(objective="place parcel on chair", steps=[
            PlanStep(step_id="release", verb="release", target="chair"),
        ])
        decision = TaskGraphExecutor().decide(plan_value, current, body)
        self.assertEqual(decision.action.type, "release")
        self.assertEqual(decision.action.target, "chair")

    def test_local_planner_routes_around_inflated_obstacle(self):
        current = snapshot()
        current.objects = [
            {"id": "cup", "kind": "target", "position": [8.0, 1.0, 0.0], "size": 0.4},
            {"id": "pillar", "kind": "obstacle", "position": [4.0, 1.0, 0.0], "size": 1.0},
        ]
        body = BodyState(position=[1.0, 1.0, 0.0], capabilities={"reach": 1.0, "world_width": 12, "world_height": 12})
        route = LocalRoutePlanner().route("cup", current, body)
        self.assertFalse(route.blocked)
        self.assertGreater(len(route.cells), 2)
        self.assertNotIn((4, 1), route.cells)
        self.assertLessEqual(abs(route.cells[-1][0] - 8) + abs(route.cells[-1][1] - 1), 1)

    def test_local_planner_replans_and_aligns_before_grasp(self):
        current = snapshot()
        current.objects = [{"id": "parcel", "kind": "object", "position": [5.0, 1.0, 0.0], "size": 0.4}]
        body = BodyState(position=[1.0, 1.0, 0.0], orientation=0.0, posture={"holding": ""}, capabilities={"reach": 1.0, "world_width": 12, "world_height": 12})
        planner = LocalRoutePlanner()
        self.assertFalse(planner.route("parcel", current, body).replanned)
        current.objects.append({"id": "moving", "kind": "mobile_obstacle", "position": [3.0, 1.0, 0.0], "size": 0.8})
        self.assertTrue(planner.route("parcel", current, body).replanned)
        plan_value = BodyPlan(objective="grasp parcel", steps=[PlanStep(step_id="grasp", verb="grab", target="parcel")])
        decision = TaskGraphExecutor().decide(plan_value, current, body)
        self.assertEqual(decision.reason, "align_for_grasp")
        self.assertIn(decision.action.type, {"forward", "turn_left", "turn_right"})

    def test_plan_controlled_simulation_uses_arbitrary_object_and_surface(self):
        room = SimulatedRoom()
        room.objects["parcel"] = {"id": "parcel", "label": "parcel", "kind": "object", "x": 2.0, "y": 2.0, "mass": 0.4, "size": 0.4}
        room.objects["dock"] = {"id": "dock", "label": "dock", "kind": "surface", "x": 5.0, "y": 5.0, "mass": 25.0, "size": 1.0}
        room.px, room.py = room.objects["parcel"]["x"], room.objects["parcel"]["y"]
        _, outcome = room.step(Action(type="grab", target="parcel", params={"plan_controlled": True}))
        self.assertEqual(outcome.kind, "success")
        room.px, room.py = room.objects["dock"]["x"], room.objects["dock"]["y"]
        _, outcome = room.step(Action(type="release", target="dock", params={"plan_controlled": True}))
        self.assertEqual(outcome.kind, "success")
        self.assertEqual(room.carrying, None)
        self.assertEqual((room.objects["parcel"]["x"], room.objects["parcel"]["y"]), (room.objects["dock"]["x"], room.objects["dock"]["y"]))

    def test_plan_controlled_simulation_accepts_chair_as_destination(self):
        room = SimulatedRoom()
        room.objects["parcel"] = {"id": "parcel", "label": "parcel", "kind": "object", "x": 2.0, "y": 2.0, "mass": 0.4, "size": 0.4}
        room.objects["chair"] = {"id": "chair", "label": "chair", "kind": "chair", "x": 5.0, "y": 5.0, "mass": 12.0, "size": 0.8}
        room.px, room.py = 5.0, 5.0
        room.carrying = "parcel"
        _, outcome = room.step(Action(type="release", target="chair", params={"plan_controlled": True}))
        self.assertEqual(outcome.kind, "success")
        self.assertIsNone(room.carrying)
        self.assertEqual((room.objects["parcel"]["x"], room.objects["parcel"]["y"]), (5.0, 5.0))
