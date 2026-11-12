import tempfile
import unittest
from types import SimpleNamespace

from cognition.goal_action_executor import GoalActionExecutor
from cognition.thought_stream import ThoughtStream


class GoalActionThoughtPublicationTests(unittest.TestCase):
    def test_external_thought_is_visible_and_survives_stream_persistence(self):
        with tempfile.TemporaryDirectory() as folder:
            stream = ThoughtStream(SimpleNamespace(_data_dir=folder))

            self.assertTrue(stream.add(
                "Validated self-reflection",
                source="goal_action.self_question",
                priority=0.55,
                thought_type="goal_action",
                topic="audit",
            ))
            self.assertEqual(stream.recent(1)[0].content, "Validated self-reflection")
            self.assertTrue(stream._persist_dirty)
            stream.flush()

            restored = ThoughtStream(SimpleNamespace(_data_dir=folder))
            thought = restored.recent(1)[0]
            self.assertEqual(thought.content, "Validated self-reflection")
            self.assertEqual(thought.source, "goal_action.self_question")
            self.assertEqual(thought.thought_type, "goal_action")
            self.assertEqual(thought.topic, "audit")

    def test_executor_reports_workspace_and_thoughtstream_acceptance(self):
        stream = ThoughtStream(SimpleNamespace())

        class Workspace:
            def broadcast(self, **_kwargs):
                return True

        executor = GoalActionExecutor.__new__(GoalActionExecutor)
        executor._o = SimpleNamespace(thought_stream=stream, workspace=Workspace())

        result = executor._add_thought(
            "Validated reflection", source="goal_action.self_question"
        )

        self.assertEqual(result, {
            "thought_stream_recorded": True,
            "workspace_broadcast": True,
        })
        self.assertEqual(stream.recent(1)[0].content, "Validated reflection")

    def test_publication_is_admitted_when_any_cognitive_consumer_accepts(self):
        admitted = GoalActionExecutor._publication_was_admitted
        self.assertTrue(admitted({
            "thought_stream_recorded": True,
            "workspace_broadcast": False,
        }))
        self.assertTrue(admitted({
            "thought_stream_recorded": False,
            "workspace_broadcast": True,
        }))
        self.assertFalse(admitted({
            "thought_stream_recorded": False,
            "workspace_broadcast": False,
        }))
        self.assertFalse(admitted(None))

    def test_empty_external_thought_is_rejected(self):
        stream = ThoughtStream(SimpleNamespace())
        self.assertFalse(stream.add("  "))
        self.assertFalse(stream.add("not valid priority", priority=float("nan")))
        self.assertEqual(stream.recent(), [])

    def test_goal_receipt_failure_is_reported_without_raising(self):
        class GoalEngine:
            def mark_action(self, *_args, **_kwargs):
                raise OSError("persistence unavailable")

        self.assertFalse(GoalActionExecutor._persist_goal_action_receipt(
            GoalEngine(), "goal-a", "self_question", "execution-a", 4
        ))

if __name__ == "__main__":
    unittest.main()
