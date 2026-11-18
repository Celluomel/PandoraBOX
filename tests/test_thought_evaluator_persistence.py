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
    assert len(second_proposals) == 1
    assert second_proposals[0]["status"] == "pending"
    assert second_proposals[0]["proposal_id"] == proposals[0]["proposal_id"]
    second_evaluation.assert_not_called()


def test_losing_goal_proposal_survives_and_retries_without_re_evaluation(tmp_path):
    stream = ThoughtStream(SimpleNamespace(_data_dir=tmp_path))
    stream.add(
        "A recurring contradiction in the cognitive harness needs review.",
        source="audit-test",
        priority=0.8,
        thought_type="tension",
        topic="cognitive harness audit",
    )
    thought_id = stream.recent_dicts(1)[0]["id"]
    evaluator = SimpleThoughtEvaluator(tmp_path, thought_stream=stream)
    evaluate = patch.object(evaluator, "_evaluate_thought", return_value=_goal_evaluation())

    with evaluate as evaluate_mock, patch.object(evaluator, "_inject_followup_thoughts"):
        first = evaluator.evaluate_recent_thoughts()
        second = evaluator.evaluate_recent_thoughts()

    assert len(first) == len(second) == 1
    assert first[0]["proposal_id"] == second[0]["proposal_id"]
    assert second[0]["status"] == "pending"
    assert evaluate_mock.call_count == 1
    stored = next(
        item for item in DataAccess(str(tmp_path)).get_thoughts(skip_expired=False)
        if item["id"] == thought_id
    )
    assert stored["evaluation"]["goal_proposal"]["status"] == "pending"

    assert evaluator.record_proposal_disposition(
        second[0], "committed", cycle=14, reason="goal_readback_verified"
    ) == 1
    assert evaluator.evaluate_recent_thoughts() == []
    resolved = next(
        item for item in DataAccess(str(tmp_path)).get_thoughts(skip_expired=False)
        if item["id"] == thought_id
    )
    assert resolved["evaluation"]["goal_proposal"]["status"] == "committed"
    assert resolved["evaluation"]["goal_proposal"]["resolved_cycle"] == 14
    evaluate_mock.assert_called_once()


def test_quality_gate_rejection_closes_pending_proposal(tmp_path):
    stream = ThoughtStream(SimpleNamespace(_data_dir=tmp_path))
    stream.add(
        "An unresolved contradiction in the cognitive harness.",
        source="audit-test",
        priority=0.8,
        thought_type="tension",
        topic="cognitive harness quality",
    )
    thought_id = stream.recent_dicts(1)[0]["id"]
    evaluator = SimpleThoughtEvaluator(tmp_path, thought_stream=stream)
    with patch.object(evaluator, "_evaluate_thought", return_value=_goal_evaluation()), \
         patch.object(evaluator, "_inject_followup_thoughts"):
        proposal = evaluator.evaluate_recent_thoughts()[0]

    assert evaluator.record_proposal_rejection(thought_id, "low_quality_topic") is True
    assert evaluator.evaluate_recent_thoughts() == []
    stored = next(
        item for item in DataAccess(str(tmp_path)).get_thoughts(skip_expired=False)
        if item["id"] == thought_id
    )
    assert stored["evaluation"]["goal_proposal"]["status"] == "rejected"
    assert stored["evaluation"]["goal_proposal"]["reason_code"] == "low_quality_topic"
    assert proposal["proposal_id"]


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


def test_memory_recall_provenance_does_not_itself_create_an_opportunity(tmp_path):
    evaluator = SimpleThoughtEvaluator(tmp_path)

    neutral = evaluator._classify_thought(
        "retrieved context: the project stored a prior measurement",
        {"source": "goal_action.memory_recall"},
    )
    tension = evaluator._classify_thought(
        "retrieved context describes an unresolved contradiction",
        {"source": "goal_action.memory_recall"},
    )
    opportunity = evaluator._classify_thought(
        "retrieved context says we could explore a new experiment",
        {"source": "goal_action.memory_recall"},
    )

    assert neutral == "mundane"
    assert tension == "tension"
    assert opportunity == "opportunity"


def test_generated_evaluator_thoughts_cannot_create_recursive_goal_intent(tmp_path):
    evaluator = SimpleThoughtEvaluator(tmp_path)

    for source in (
        "thought_evaluator.followup",
        "thought_evaluator.stagnation_guard",
    ):
        assert evaluator._classify_thought(
            "What remains unresolved and could be explored?", {"source": source}
        ) == "mundane"


def test_negative_evaluation_is_persisted_and_not_reprocessed(tmp_path):
    stream = ThoughtStream(SimpleNamespace(_data_dir=tmp_path))
    stream.add(
        "A simple observation of a blue cup.",
        source="ordinary_note",
        priority=0.2,
        thought_type="reflection",
    )
    thought_id = stream.recent_dicts(1)[0]["id"]
    evaluator = SimpleThoughtEvaluator(tmp_path, thought_stream=stream)

    with patch.object(evaluator, "_inject_followup_thoughts"):
        assert evaluator.evaluate_recent_thoughts() == []

    marked = next(item for item in stream.recent_dicts(10) if item["id"] == thought_id)
    assert marked["evaluated"] is True
    assert marked["evaluation"] == {
        "type": "mundane",
        "should_create_goal": False,
        "reason_code": "no_goal_signal",
    }

    with patch.object(evaluator, "_evaluate_thought") as second_evaluation:
        assert evaluator.evaluate_recent_thoughts() == []
    second_evaluation.assert_not_called()


def test_stagnation_guard_emits_at_most_one_recent_seed(tmp_path):
    evaluator = SimpleThoughtEvaluator(tmp_path)

    assert evaluator.evaluate_recent_thoughts() == []
    assert evaluator.evaluate_recent_thoughts() == []

    seeds = [
        thought for thought in DataAccess(str(tmp_path)).get_thoughts(skip_expired=False)
        if thought.get("source") == "thought_evaluator.stagnation_guard"
    ]
    assert len(seeds) == 1

