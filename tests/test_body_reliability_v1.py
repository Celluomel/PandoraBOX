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

    def test_recovery_is_bounded_and_persisted(self):
        snap = snapshot()
        self.runtime.record_snapshot(snap)
        result = self.runtime.submit(proposal())
        self.assertTrue(result["accepted"])
        for attempt in range(1, 4):
            self.runtime.record_step_failure("s1", snap.snapshot_id, "failed")
        self.assertEqual(self.runtime.active_plan().state, "recovery")
        self.runtime.record_step_failure("s1", snap.snapshot_id, "failed")
        self.assertEqual(self.runtime.active_plan().state, "paused")
        restarted = BodyPlanRuntime(Path(self.temp.name))
        self.assertEqual(restarted.active_plan().state, "paused")


if __name__ == "__main__":
    unittest.main()
