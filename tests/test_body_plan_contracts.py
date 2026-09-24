"""Phase-0 embodied plan contracts: validation and restart-safe persistence."""
from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from body_runtime_host.worldmodel.contracts import ActionResult, BodySnapshot
from body_runtime_host.worldmodel.plan_runtime import BodyPlanRuntime


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
