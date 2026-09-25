"""Tests for the grounded Body-to-Brain awareness summary."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class BodyAwarenessContextTest(unittest.TestCase):
    def test_context_describes_current_embodied_state_before_learning(self):
        from body_runtime_host.worldmodel.core import EmbodiedWorldModel
        from body_runtime_host.worldmodel.sources import SimRobotSource

        with tempfile.TemporaryDirectory() as temp_dir:
            model = EmbodiedWorldModel(data_dir=temp_dir, source=SimRobotSource())
            context = model.context_for_brain()

        self.assertIn("CURRENT EMBODIED STATE", context)
        self.assertIn("Current Body pose: unavailable", context)
        self.assertIn("Sensor source: simulated robot sandbox", context)
        self.assertIn("Do not infer an unobserved body state", context)

