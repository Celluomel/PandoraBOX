import tempfile
import unittest

from cognition.causal_ledger import CausalLedger
from cognition.consequence_tracker import ConsequenceTracker
from cognition.goal_engine import Goal, GoalEngine


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
                goal_source_turn_id="turn-user-origin",
                goal_source_thought_id="thought-origin",
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
            self.assertTrue(all(
                event["refs"]["goal_source_turn_id"] == "turn-user-origin"
                and event["refs"]["goal_source_thought_id"] == "thought-origin"
                for event in related
            ))
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

    def test_goal_action_counter_is_persisted_with_execution_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            engine = GoalEngine(None, persistence_file=f"{folder}/goals.json")
            goal = Goal(
                id="goal-origin",
                topic="audit action receipts",
                origin="user_requested_development",
                priority=0.7,
                energy=0.7,
                created_cycle=3,
                last_active=3,
                source_turn_id="turn-request-3",
                success_criteria="A verified action receipt is stored",
            )
            engine._goals[goal.id] = goal
            engine._cycle_counter = 9

            persisted = engine.mark_action(
                goal.id,
                "web_search",
                execution_id="act-cycle-9-2",
                cycle_id=9,
            )

            self.assertTrue(persisted)
            self.assertEqual(goal.actions_taken, 1)
            self.assertEqual(goal.non_introspective_actions, 1)
            self.assertEqual(goal.last_action_execution_id, "act-cycle-9-2")
            self.assertEqual(goal.last_action_cycle_id, 9)
            self.assertEqual(goal.last_action_source_turn_id, "turn-request-3")
            reloaded = GoalEngine(None, persistence_file=f"{folder}/goals.json")
            self.assertEqual(reloaded._goals[goal.id].last_action_execution_id, "act-cycle-9-2")
            self.assertEqual(reloaded._goals[goal.id].last_action_source_turn_id, "turn-request-3")

            engine._save_goals = lambda: False
            self.assertFalse(engine.mark_action(
                goal.id, "web_search", execution_id="act-save-failure", cycle_id=10
            ))
            self.assertEqual(goal.actions_taken, 1)
            self.assertEqual(goal.last_action_execution_id, "act-cycle-9-2")


if __name__ == "__main__":
    unittest.main()
