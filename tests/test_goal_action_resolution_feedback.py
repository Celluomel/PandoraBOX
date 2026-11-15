import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from cognition.goal_action_executor import GoalActionExecutor


class GoalActionResolutionFeedbackTests(unittest.TestCase):
    def test_terminal_plan_outcome_is_forwarded_to_tte_with_goal_provenance(self):
        recorded = []
        planner = SimpleNamespace(
            record_goal_action_outcome=lambda *args, **kwargs: None
        )
        tte = SimpleNamespace(
            record_action_receipt=lambda *args, **kwargs: recorded.append((args, kwargs))
        )
        executor = GoalActionExecutor.__new__(GoalActionExecutor)
        executor._o = SimpleNamespace(_loop=SimpleNamespace(
            _long_horizon_planner=planner,
            _tte=tte,
        ))
        goal = SimpleNamespace(id="goal-1")

        executor._record_plan_outcome(
            goal, "memory_recall", True, "recalled evidence",
            execution_id="exec-17", cycle_id=23,
        )

        assert recorded == [(("goal-1",), {
            "action": "memory_recall",
            "success": True,
            "execution_id": "exec-17",
            "cycle_id": 23,
            "result": "recalled evidence",
            "evidence_ref": "execution:exec-17",
        })]

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
