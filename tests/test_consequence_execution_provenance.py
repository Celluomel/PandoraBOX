import tempfile
import unittest

from cognition.causal_ledger import CausalLedger
from cognition.consequence_tracker import ACTION_MODEL, ConsequenceTracker
from cognition.goal_engine import Goal, GoalEngine
from cognition.goal_action_executor import GoalActionExecutor


class ConsequenceExecutionProvenanceTests(unittest.TestCase):
    def test_web_search_source_citations_survive_in_causal_outcome(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = CausalLedger(folder)
            tracker = ConsequenceTracker(persona_dir=folder, ledger=ledger)
            prediction = tracker.predict(
                "goal-research", "audit source grounding", "web_search",
                cycle_id=33, execution_id="act-research-33",
            )
            sources = [{
                "title": "Primary source",
                "url": "https://example.org/report",
                "source": "test_provider",
            }]

            tracker.resolve(prediction, {
                "success": True,
                "result": "interpreted research",
                "research_item_queued": True,
                "research_sources": sources,
            })

            outcome = next(
                event for event in ledger.recent(10)
                if event["kind"] == "outcome"
            )
            self.assertEqual(outcome["output_state"]["research_sources"], sources)
            self.assertEqual(
                GoalActionExecutor._research_source_reference({
                    "title": "Primary source",
                    "url": "https://example.org/report",
                    "source": "test_provider",
                }),
                sources[0],
            )
            self.assertIsNone(GoalActionExecutor._research_source_reference({
                "title": "No citation",
                "url": "file:///private/path",
            }))

    def test_deferred_prediction_is_closed_without_becoming_a_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = CausalLedger(folder)
            tracker = ConsequenceTracker(persona_dir=folder, ledger=ledger)
            prediction = tracker.predict(
                "goal-deferred", "wait for LLM capacity", "self_question",
                cycle_id=12, execution_id="act-deferred-12",
            )

            result = tracker.cancel(prediction, "LLM scheduler busy")
            report = tracker.closure_report()
            kinds = [event["kind"] for event in ledger.recent(10)]

            self.assertTrue(result["cancelled"])
            self.assertEqual(report["n_predictions"], 1)
            self.assertEqual(report["n_cancelled"], 1)
            self.assertEqual(report["n_pending"], 0)
            self.assertEqual(report["eligible_predictions"], 0)
            self.assertEqual(report["n_resolved"], 0)
            self.assertEqual(kinds, ["prediction", "deferred"])

    def test_queued_user_question_is_not_recorded_as_external_feedback(self):
        self.assertEqual(ACTION_MODEL["user_question"]["effect"], "question_queued")
        self.assertNotEqual(ACTION_MODEL["user_question"]["effect"], "external_feedback")
        with tempfile.TemporaryDirectory() as folder:
            ledger = CausalLedger(folder)
            tracker = ConsequenceTracker(persona_dir=folder, ledger=ledger)
            prediction = tracker.predict(
                "goal-social", "understand user feedback", "user_question",
                cycle_id=6, execution_id="act-question-6",
            )

            resolved = tracker.resolve(prediction, {
                "success": True,
                "result": "question queued: What is your perspective?",
            })

            self.assertEqual(resolved["observed"], 1.0)
            self.assertIsNone(resolved["attention_delta"])
            self.assertFalse(resolved["pcm_resolved"])
            outcome = next(e for e in ledger.recent(10) if e["kind"] == "outcome")
            self.assertEqual(outcome["output_state"]["outcome"], "positive")
            self.assertEqual(
                outcome["input_state"]["action"], "user_question"
            )
            self.assertFalse((ledger.persona_dir / "cognitive_attention.json").exists())

    def test_self_question_probe_requires_persisted_belief_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            tracker = ConsequenceTracker(persona_dir=folder)
            prediction = tracker.predict(
                "goal-self", "understand self model", "self_question"
            )

            self.assertEqual(tracker._observe(prediction, {
                "success": True, "result": "A long plausible reflection"
            }), 0.0)
            self.assertEqual(tracker._observe(prediction, {
                "success": True, "result": "A long plausible reflection",
                "belief_persisted": True,
            }), 1.0)

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
                parent_execution_id="act-parent-search-27",
            )
            result = tracker.resolve(
                prediction,
                {
                    "goal_id": "goal-audit",
                    "action": "self_question",
                    "success": True,
                    "result": "usable answer produced",
                    "goal_state_persisted": False,
                    "belief_persisted": True,
                    "thought_stream_recorded": True,
                    "workspace_broadcast": False,
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
                and event["refs"]["parent_execution_id"] == "act-parent-search-27"
                for event in related
            ))
            outcome = next(event for event in related if event["kind"] == "outcome")
            self.assertFalse(outcome["input_state"]["goal_state_persisted"])
            self.assertTrue(outcome["output_state"]["belief_persisted"])
            self.assertTrue(outcome["output_state"]["thought_stream_recorded"])
            self.assertFalse(outcome["output_state"]["workspace_broadcast"])
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
