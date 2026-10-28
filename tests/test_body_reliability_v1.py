"""Regression tests for Body plan freshness and bounded recovery.

Run with: python -m unittest discover -s tests -p 'test_body_reliability_v1.py'
"""
import tempfile
import time
import unittest
from pathlib import Path

from body_runtime_host.worldmodel.contracts import BodySnapshot
from body_runtime_host.worldmodel.plan_runtime import BodyPlanRuntime


def proposal():
    return {
        "objective": "Inspect the scene",
        "steps": [{"step_id": "s1", "verb": "inspect", "target": "scene", "max_retries": 1}],
    }


def snapshot(age=0.0):
    return BodySnapshot(
        source="sim", frame="local_map", pose={},
        objects=[], capabilities=["inspect"], reliability=1.0,
        timestamp=time.time() - age,
    )


class BodyReliabilityV1Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.runtime = BodyPlanRuntime(Path(self.temp.name))

    def test_fresh_snapshot_accepted(self):
        self.runtime.record_snapshot(snapshot())
        self.assertTrue(self.runtime.validate(proposal())["feasible"])

    def test_stale_snapshot_rejected(self):
        self.runtime.record_snapshot(snapshot(age=10.0))
        self.assertFalse(self.runtime.validate(proposal())["feasible"])
        self.assertFalse(self.runtime.submit(proposal())["accepted"])

    def test_future_snapshot_rejected(self):
        self.runtime.record_snapshot(snapshot(age=-30.0))
        self.assertFalse(self.runtime.validate(proposal())["feasible"])

    def test_recovery_actions_are_bounded_even_when_no_failures_recorded(self):
        snap = snapshot()
        self.runtime.record_snapshot(snap)
        self.assertTrue(self.runtime.submit(proposal())["accepted"])
        # First failure crosses max_retries only after two failures.
        self.runtime.record_step_failure("s1", snap.snapshot_id, "blocked")
        self.runtime.record_step_failure("s1", snap.snapshot_id, "blocked")
        self.assertEqual(self.runtime.active_plan().state, "recovery")
        for attempt in range(3):
            self.assertTrue(self.runtime.record_recovery_attempt("s1", snap.snapshot_id)["ok"])
        denied = self.runtime.record_recovery_attempt("s1", snap.snapshot_id)
        self.assertFalse(denied["ok"])
        self.assertEqual(self.runtime.active_plan().state, "paused")
        # Late failure callbacks must never reactivate a paused lease.
        late = self.runtime.record_step_failure("s1", snap.snapshot_id, "late callback")
        self.assertFalse(late["ok"])
        self.assertEqual(self.runtime.active_plan().state, "paused")
        restarted = BodyPlanRuntime(Path(self.temp.name))
        self.assertEqual(restarted.active_plan().state, "paused")

    def test_verified_recovery_resumes_and_advances(self):
        snap = snapshot()
        self.runtime.record_snapshot(snap)
        self.assertTrue(self.runtime.submit(proposal())["accepted"])
        self.runtime.record_step_failure("s1", snap.snapshot_id, "blocked")
        self.runtime.record_step_failure("s1", snap.snapshot_id, "blocked")
        self.assertEqual(self.runtime.active_plan().state, "recovery")
        # Recovery cannot advance directly; it requires an explicit
        # verified transition to executing.
        self.assertFalse(self.runtime.advance("s1", snap.snapshot_id)["ok"])
        resumed = self.runtime.resume_after_recovery(
            "s1", snap.snapshot_id, "observed postcondition",
        )
        self.assertTrue(resumed["ok"])
        self.assertEqual(self.runtime.active_plan().state, "executing")
        self.assertTrue(self.runtime.advance("s1", snap.snapshot_id)["ok"])
        self.assertEqual(self.runtime.active_plan().state, "completed")
        restarted = BodyPlanRuntime(Path(self.temp.name))
        self.assertIsNone(restarted.active_plan())

    def test_paused_recovery_cannot_be_resumed(self):
        snap = snapshot()
        self.runtime.record_snapshot(snap)
        self.assertTrue(self.runtime.submit(proposal())["accepted"])
        self.runtime.record_step_failure("s1", snap.snapshot_id, "blocked")
        self.runtime.record_step_failure("s1", snap.snapshot_id, "blocked")
        for _ in range(3):
            self.assertTrue(self.runtime.record_recovery_attempt("s1", snap.snapshot_id)["ok"])
        self.assertFalse(self.runtime.record_recovery_attempt("s1", snap.snapshot_id)["ok"])
        self.assertEqual(self.runtime.active_plan().state, "paused")
        self.assertFalse(self.runtime.resume_after_recovery(
            "s1", snap.snapshot_id, "late observation",
        )["ok"])
        self.assertEqual(self.runtime.active_plan().state, "paused")

    def test_recovery_is_bounded_and_persisted(self):
        snap = snapshot()
        self.runtime.record_snapshot(snap)
        result = self.runtime.submit(proposal())
        self.assertTrue(result["accepted"])
        for attempt in range(1, 5):
            self.runtime.record_step_failure("s1", snap.snapshot_id, "failed")
        self.assertEqual(self.runtime.active_plan().state, "recovery")
        self.runtime.record_step_failure("s1", snap.snapshot_id, "failed")
        self.assertEqual(self.runtime.active_plan().state, "paused")
        # Late failure callbacks must never reactivate a paused lease.
        late = self.runtime.record_step_failure("s1", snap.snapshot_id, "late callback")
        self.assertFalse(late["ok"])
        self.assertEqual(self.runtime.active_plan().state, "paused")
        restarted = BodyPlanRuntime(Path(self.temp.name))
        self.assertEqual(restarted.active_plan().state, "paused")


if __name__ == "__main__":
    unittest.main()
