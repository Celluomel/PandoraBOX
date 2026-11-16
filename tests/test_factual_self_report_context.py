import unittest
import importlib.util
from pathlib import Path

_HELPER_PATH = Path(__file__).resolve().parents[1] / "cognition" / "factual_self_report_context.py"
_SPEC = importlib.util.spec_from_file_location("factual_self_report_context_test", _HELPER_PATH)
_HELPER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPER)
history_without_assistant_claims = _HELPER.history_without_assistant_claims


class FactualSelfReportContextTests(unittest.TestCase):
    def test_planner_self_report_suppresses_assistant_continuity_and_filters_history(self):
        source = (_HELPER_PATH.parents[1] / "cognition" / "persona_bridge.py").read_text(encoding="utf-8")
        self.assertIn(
            '"" if (_architecture_query or _factual_plan_query)', source,
        )
        self.assertIn('if _factual_self_report:', source)
        self.assertIn('"historical_assistant_context", "filtered"', source)

    def test_keeps_user_context_and_excludes_prior_assistant_claims(self):
        history = [
            {"role": "user", "content": "What is the active audit plan?"},
            {"role": "assistant", "content": "Confidence is 0.96."},
            {"role": "user", "content": "That confidence is not in the trace."},
            {"role": "assistant", "content": "I checked again."},
            {"role": "assistant", "content": "  "},
            {"role": "system", "content": "unexpected provider metadata"},
        ]

        filtered, counts = history_without_assistant_claims(history)

        self.assertEqual(
            filtered,
            [
                {"role": "user", "content": "What is the active audit plan?"},
                {"role": "user", "content": "That confidence is not in the trace."},
            ],
        )
        self.assertEqual(counts, {
            "retained_user_messages": 2,
            "excluded_assistant_messages": 2,
        })
        self.assertEqual(history[1]["content"], "Confidence is 0.96.")

    def test_invalid_history_fails_closed_to_empty_context(self):
        filtered, counts = history_without_assistant_claims(None)
        self.assertEqual(filtered, [])
        self.assertEqual(counts, {
            "retained_user_messages": 0,
            "excluded_assistant_messages": 0,
        })


if __name__ == "__main__":
    unittest.main()
