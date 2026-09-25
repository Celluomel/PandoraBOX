import unittest

from body_runtime_host.worldmodel.contracts import BodyPlan, BodySnapshot, PlanStep
from body_runtime_host.worldmodel.plan_runtime import BodyPlanRuntime


class BodyPlanFeasibilityTests(unittest.TestCase):
    def test_malformed_string_predicate_is_normalized_without_crashing(self):
        plan = BodyPlan.from_dict({
            "objective": "place cup",
            "steps": [{
                "step_id": "place",
                "verb": "release",
                "target": "chair",
                "postconditions": ["not-json-predicate"],
            }],
        })
        self.assertEqual(plan.steps[0].postconditions, [])

    def test_validate_does_not_take_plan_lease(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            runtime = BodyPlanRuntime(Path(directory))
            runtime.record_snapshot(BodySnapshot(
                source="sim_robot", frame="room", pose={"x": 1, "y": 1, "yaw": 0},
                objects=[{"id": "cup"}, {"id": "chair"}],
                capabilities=["navigate", "grab", "release"], reliability=1.0,
            ))
            plan = BodyPlan(objective="place cup on chair", steps=[
                PlanStep("move-cup", "navigate", "cup"),
                PlanStep("grab-cup", "grab", "cup"),
                PlanStep("move-chair", "navigate", "chair"),
                PlanStep("place-cup", "release", "chair"),
            ]).as_dict()
            result = runtime.validate(plan)
            self.assertTrue(result["feasible"])
            self.assertTrue(result["requires_confirmation"])
            self.assertIsNone(runtime.active_plan())

    def test_validate_reports_unknown_perceived_entity(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            runtime = BodyPlanRuntime(Path(directory))
            runtime.record_snapshot(BodySnapshot(
                source="sim_robot", frame="room", pose={"x": 1, "y": 1, "yaw": 0},
                objects=[{"id": "cup"}], capabilities=["navigate"], reliability=1.0,
            ))
            result = runtime.validate(BodyPlan(
                objective="move unknown object",
                steps=[PlanStep("move", "navigate", "lamp")],
            ).as_dict())
            self.assertFalse(result["feasible"])
            self.assertIn("unknown target", " ".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
