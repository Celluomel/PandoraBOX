from types import SimpleNamespace
from unittest.mock import patch

from cognition.goal_completion import record_goal_completion
from cognition.goal_engine import Goal, GoalEngine


class _Narrative:
    def __init__(self):
        self.chapters = []

    def record_chapter(self, **chapter):
        self.chapters.append(chapter)


def test_completion_does_not_claim_or_narrate_when_engine_rejects_write():
    narrative = _Narrative()
    engine = SimpleNamespace(complete_goal=lambda *_args, **_kwargs: False)
    with patch("cognition.goal_completion.get_narrative_identity", return_value=narrative):
        result = record_goal_completion(
            {"id": "goal-1", "topic": "cognitive integrity", "origin": "autonomous"},
            goal_engine=engine,
        )

    assert result is False
    assert narrative.chapters == []


def test_completion_requires_dal_to_confirm_persistence_before_narrative():
    narrative = _Narrative()
    dal = SimpleNamespace(save_goal=lambda _goal: False)
    with patch("cognition.goal_completion.get_narrative_identity", return_value=narrative):
        result = record_goal_completion(
            {"id": "goal-2", "topic": "cognitive integrity", "origin": "autonomous"},
            dal=dal,
        )

    assert result is False
    assert narrative.chapters == []


def test_completion_narrative_follows_confirmed_engine_write():
    narrative = _Narrative()
    engine = SimpleNamespace(complete_goal=lambda *_args, **_kwargs: True)
    with patch("cognition.goal_completion.get_narrative_identity", return_value=narrative):
        result = record_goal_completion(
            {"id": "goal-3", "topic": "cognitive integrity", "origin": "autonomous"},
            goal_engine=engine,
            reason="criterion met",
        )

    assert result is True
    assert len(narrative.chapters) == 1
    assert "criterion met" in narrative.chapters[0]["description"]


def test_goal_engine_does_not_skip_lifecycle_when_completion_write_fails(tmp_path):
    engine = GoalEngine(None, persistence_file=str(tmp_path / "goals.json"))
    goal = Goal(
        id="goal-lifecycle", topic="investigate cognitive lifecycle",
        origin="autonomous", priority=0.8, energy=0.10,
        created_cycle=1, last_active=1, persistence=10,
        actions_taken=3, non_introspective_actions=1,
    )
    assert engine.add_goal(goal)

    with (
        patch("cognition.goal_completion.goal_completion_eligible", return_value=(True, "eligible")),
        patch("cognition.goal_completion.load_current_tensions", return_value={}),
        patch("cognition.goal_completion.record_goal_completion", return_value=False),
    ):
        engine.update_goals()

    assert engine.get_goal_by_id(goal.id).status == "dormant"
