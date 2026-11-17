import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from core.data.access import DataAccess
from cognition.simple_thought_evaluator import SimpleThoughtEvaluator
from cognition.thought_stream import ThoughtStream


def _goal_evaluation():
    return {
        "type": "opportunity",
        "concept": "memory retrieval audit",
        "priority": 0.7,
        "actionability": 0.6,
        "friction": "current evidence vs. grounded understanding",
        "goal_type": "explore_opportunity",
        "concept_source": "structured_topic",
        "should_create_goal": True,
    }


def test_evaluator_sees_unflushed_thought_and_persists_evaluation_once(tmp_path):
    stream = ThoughtStream(SimpleNamespace(_data_dir=tmp_path))
    stream.add(
        "Memory about a cognitive audit: retrieved evidence",
        source="goal_action.memory_recall",
        priority=0.6,
        thought_type="goal_action",
        topic="memory retrieval audit",
    )
    thought_id = stream.recent_dicts(1)[0]["id"]
    evaluator = SimpleThoughtEvaluator(tmp_path, thought_stream=stream)
    evaluate = patch.object(evaluator, "_evaluate_thought", return_value=_goal_evaluation())

    with evaluate as evaluate_mock, patch.object(evaluator, "_inject_followup_thoughts"):
        proposals = evaluator.evaluate_recent_thoughts()

    assert evaluate_mock.call_count == 1
    assert proposals[0]["origin_thought"] == thought_id
    marked = stream.recent_dicts(1)[0]
    assert marked["evaluated"] is True
    assert marked["evaluation"]["concept"] == "memory retrieval audit"

    # A DAL-only thought must survive the ThoughtStream's atomic file flush.
    dal = DataAccess(str(tmp_path))
    assert dal.add_thought({
        "id": "dal-only-thought",
        "content": "written by a different cognitive producer",
        "source": "audit-test",
        "priority": 0.4,
        "thought_type": "reflection",
        "evaluated": True,
        "evaluated_at": datetime.now().isoformat(),
    })
    stream.flush()

    stored = json.loads((Path(tmp_path) / "thought_stream.json").read_text(encoding="utf-8"))
    stored_ids = [item["id"] for item in stored["thoughts"]]
    assert stored_ids.count(thought_id) == 1
    assert stored_ids.count("dal-only-thought") == 1
    assert next(item for item in stored["thoughts"] if item["id"] == thought_id)["evaluated"] is True

    reloaded_stream = ThoughtStream(SimpleNamespace(_data_dir=tmp_path))
    reloaded = next(
        item for item in reloaded_stream.recent_dicts(60)
        if item["id"] == thought_id
    )
    assert reloaded["evaluated"] is True
    assert reloaded["evaluation"]["concept"] == "memory retrieval audit"

    evaluator.thought_stream = reloaded_stream
    with patch.object(evaluator, "_evaluate_thought") as second_evaluation:
        second_proposals = evaluator.evaluate_recent_thoughts()
    assert second_proposals == []
    second_evaluation.assert_not_called()


def test_dal_updates_thought_by_id_without_adding_duplicate(tmp_path):
    dal = DataAccess(str(tmp_path))
    initial = {
        "id": "stable-thought-1",
        "content": "a thought",
        "source": "test",
        "priority": 0.5,
        "thought_type": "reflection",
    }
    assert dal.add_thought(initial)
    assert dal.update_thought({
        **initial,
        "evaluated": True,
        "evaluated_at": "2026-11-17T12:00:00",
        "evaluation": {"concept": "updated"},
    })
    thoughts = dal.get_thoughts(limit=10, skip_expired=False)
    matches = [item for item in thoughts if item["id"] == initial["id"]]
    assert len(matches) == 1
    assert matches[0]["evaluated"] is True
    assert matches[0]["evaluation"]["concept"] == "updated"
