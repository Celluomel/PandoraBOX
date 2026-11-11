from types import SimpleNamespace
from unittest.mock import patch

from cognition.goal_completion import record_goal_completion


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
