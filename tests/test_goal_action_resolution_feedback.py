import json
import tempfile
import unittest
from types import ModuleType
from pathlib import Path
from types import SimpleNamespace

# Import the executor without triggering cognition.__init__'s optional FAISS
# native loader; this suite exercises planner/receipt behavior only.
ROOT = Path(__file__).resolve().parents[1]
cognition_package = ModuleType("cognition")
cognition_package.__path__ = [str(ROOT / "cognition")]
import sys
sys.modules.setdefault("cognition", cognition_package)

from cognition.goal_action_executor import (
    GoalActionExecutor,
    _generation_completion_problem,
    _retain_generated_text,
    _usable_model_text,
)


class GoalActionResolutionFeedbackTests(unittest.TestCase):
    def test_generated_text_is_never_silently_truncated(self):
        complete = "A hypothesis that is longer than the old 180-character cutoff " + "x" * 150

        self.assertEqual(_retain_generated_text(complete, max_chars=800), complete)
        self.assertIsNone(_retain_generated_text(complete + "x" * 700, max_chars=800))

    def test_empty_or_error_model_text_is_not_usable_cognitive_output(self):
        self.assertFalse(_usable_model_text(""))
        self.assertFalse(_usable_model_text("Error: provider offline"))
        self.assertFalse(_usable_model_text("too short"))
        self.assertTrue(_usable_model_text("A complete hypothesis grounded in evidence."))

    def test_cognitive_llm_action_requires_verified_provider_completion(self):
        self.assertEqual(
            _generation_completion_problem({"status": "truncated", "completion_verified": False}),
            "provider_output_truncated",
        )
        self.assertEqual(
            _generation_completion_problem({"status": "ok", "completion_verified": False}),
            "provider_completion_unverified",
        )
        self.assertEqual(
            _generation_completion_problem({"status": "ok", "completion_verified": True}),
            "",
        )

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
