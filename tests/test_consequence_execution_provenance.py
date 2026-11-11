import tempfile
import unittest

from cognition.causal_ledger import CausalLedger
from cognition.consequence_tracker import ConsequenceTracker


class ConsequenceExecutionProvenanceTests(unittest.TestCase):
    def test_prediction_outcome_and_updates_share_exact_execution_chain(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = CausalLedger(folder)
            tracker = ConsequenceTracker(persona_dir=folder, ledger=ledger)

            prediction = tracker.predict(
                goal_id="goal-audit",
                goal_topic="audit causal chain",
                action_type="self_question",
                cycle_id=27,
                execution_id="act-audit-27-1",
            )
            result = tracker.resolve(
                prediction,
                {
                    "goal_id": "goal-audit",
                    "action": "self_question",
                    "success": True,
                    "result": "usable answer produced",
                },
            )

            self.assertTrue(result["resolved"])
            self.assertEqual(result["cycle_id"], 27)
            self.assertEqual(result["execution_id"], "act-audit-27-1")
            events = ledger.recent(20)
            related = [
                event for event in events
                if (event.get("refs") or {}).get("execution_id") == "act-audit-27-1"
            ]

            self.assertEqual(
                {event["kind"] for event in related},
                {"prediction", "outcome", "error", "update"},
            )
            self.assertTrue(all(event["cycle_id"] == 27 for event in related))
            outcome = next(event for event in related if event["kind"] == "outcome")
            error = next(event for event in related if event["kind"] == "error")
            update = next(event for event in related if event["kind"] == "update")
            chain = ledger.chain(update["event_id"])
            self.assertEqual(
                [event["kind"] for event in chain],
                ["prediction", "outcome", "error", "update"],
            )
            self.assertEqual(outcome["parent_event_ids"], [prediction["prediction_event_id"]])
            self.assertEqual(error["parent_event_ids"], [outcome["event_id"]])
            self.assertEqual(update["parent_event_ids"], [error["event_id"]])


if __name__ == "__main__":
    unittest.main()
