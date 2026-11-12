import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from cognition.goal_action_executor import GoalActionExecutor


class GoalActionResolutionFeedbackTests(unittest.TestCase):
    def test_generated_insight_text_cannot_change_evaluator_weights(self):
        with tempfile.TemporaryDirectory() as folder:
            data_dir = Path(folder)
            sma = SimpleNamespace(_tension_priority=0.65, propose_change=lambda *_a: True)
            executor = GoalActionExecutor.__new__(GoalActionExecutor)
            executor._o = SimpleNamespace(
                ai_system=SimpleNamespace(liberty_self_mod=sma),
                _data_dir=data_dir,
            )

            result = executor._record_resolution_outcome(
                SimpleNamespace(origin="test_hypothesis"),
                "This could perhaps be a concrete and useful insight.",
            )

            self.assertFalse(result)
            self.assertEqual(sma._tension_priority, 0.65)
            self.assertFalse((data_dir / "evaluator_weights.json").exists())


if __name__ == "__main__":
    unittest.main()
