import unittest

from cognition.factual_self_report_context import history_without_assistant_claims


class FactualSelfReportContextTests(unittest.TestCase):
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
