import json
from unittest.mock import patch

import numpy as np

from cognition.goal_engine import GoalEngine
from cognition.thought_goal_linker import ThoughtGoalLinker


class _SpaceEmbedder:
    def __init__(self, space_id):
        self.space_id = space_id

    def encode_with_metadata(self, texts):
        return np.asarray([[1.0, 0.0] for _ in texts]), self.space_id


def test_untyped_numeric_suggestion_cannot_create_durable_goal(tmp_path):
    persistence = tmp_path / "goals.json"
    engine = GoalEngine(None, persistence_file=str(persistence))
    linker = ThoughtGoalLinker(str(tmp_path), goal_engine=engine)
    linker._load_goals = lambda: []
    linker._find_similar_goal = lambda _thought, _goals: None
    linker._merge_similar_goals = lambda _goals: []

    result = linker.process_thought_evaluation({
        "type": "reflection",
        "concepts": ["cognitive pipeline"],
        "priority": 0.72,
        "urgency": 0.6,
        "actionability": 0.9,
        "origin_thought_id": "phase2-thought-9",
    })

    assert result["created_goals"] == []
    assert not persistence.exists()


def test_typed_evaluator_suggestion_uses_goal_engine_and_persists_source(tmp_path):
    persistence = tmp_path / "goals.json"
    engine = GoalEngine(None, persistence_file=str(persistence))
    linker = ThoughtGoalLinker(str(tmp_path), goal_engine=engine)
    linker._load_goals = lambda: []
    linker._find_similar_goal = lambda _thought, _goals: None
    linker._merge_similar_goals = lambda _goals: []

    result = linker.process_thought_evaluation({
        "type": "uncertainty_cognitive pipeline",
        "cognitive_signal": "uncertainty",
        "source": "advanced_thought_evaluator",
        "concepts": ["cognitive pipeline"],
        "priority": 0.72,
        "urgency": 0.6,
        "actionability": 0.9,
        "origin_thought_id": "phase2-thought-9",
    })

    assert len(result["created_goals"]) == 1
    goal_id = result["created_goals"][0]
    goal = json.loads(persistence.read_text(encoding="utf-8"))["goals"][goal_id]
    assert goal["origin"] == "thought_goal_linker"
    assert goal["source_thought_id"] == "phase2-thought-9"
    assert goal["source_thought_type"] == "uncertainty"
    assert goal["source_concept_method"] == "advanced_thought_evaluator"
    assert goal["source_concept_kind"] == "evaluated_internal_thought"
    assert goal["source_concept_ref"] == "thought:phase2-thought-9"


def test_linker_uses_semantic_match_receipt_to_persist_causal_goal_link(tmp_path):
    persistence = tmp_path / "goals.json"
    from core.data.access import DataAccess

    dal = DataAccess(str(tmp_path))
    assert dal.save_goal({
        "id": "goal-existing-1",
        "name": "a deliberately different surface label",
        "topic": "cognitive process",
        "status": "active",
        "priority": 0.6,
        "source_turn_id": "turn-existing",
        "source_concept_kind": "user_explicit_goal",
        "source_concept_method": "GoalEngine.create_user_requested_goal",
        "source_concept_ref": "turn:turn-existing",
    })
    engine = GoalEngine(None, persistence_file=str(persistence))
    linker = ThoughtGoalLinker(str(tmp_path), goal_engine=engine)

    result = linker.process_thought_evaluation({
        "type": "tension_cognitive_execution_flow",
        "cognitive_signal": "tension",
        "source": "advanced_thought_evaluator",
        "concepts": ["cognitive execution flow"],
        "related_goal_id": "goal-existing-1",
        "evaluation": {
            "goal_similarity": 0.82,
            "related_goal_id": "goal-existing-1",
        },
        "priority": 0.84,
        "urgency": 0.8,
        "actionability": 0.69,
        "origin_thought_id": "typed-thought-42",
    }, goal_engine=engine)

    assert result["linked_goals"] == ["goal-existing-1"]
    saved = dal.get_goal_by_id("goal-existing-1")
    assert saved["priority"] == 0.84
    assert saved["origin_thoughts"][-1]["thought_id"] == "typed-thought-42"


def test_linker_does_not_infer_a_goal_match_from_surface_words():
    linker = ThoughtGoalLinker()
    goal = {"id": "goal-same-words", "name": "cognitive execution flow", "status": "active"}

    assert linker._find_similar_goal({
        "concepts": ["cognitive execution flow"],
        "evaluation": {"goal_similarity": 1.0},
    }, [goal]) is None


def test_linker_rejects_conflicting_goal_ids_in_match_receipt():
    linker = ThoughtGoalLinker()
    goal = {"id": "goal-a", "name": "A", "status": "active"}
    assert linker._find_similar_goal({
        "cognitive_signal": "tension",
        "related_goal_id": "goal-a",
        "evaluation": {"related_goal_id": "goal-b", "goal_similarity": 0.95},
    }, [goal]) is None


def test_goal_merge_similarity_requires_calibrated_nomic_space():
    linker = ThoughtGoalLinker()
    first = {"name": "matching goal description"}
    second = {"name": "matching goal description"}

    with patch("utils.shared_embedder.get_embedder", return_value=_SpaceEmbedder(
        "sentence-transformers:all-MiniLM-L6-v2"
    )):
        assert linker._compute_goal_similarity(first, second) == 0.0

    with patch("utils.shared_embedder.get_embedder", return_value=_SpaceEmbedder(
        "api:http://localhost:1234/v1:text-embedding-nomic-embed-text-v1.5"
    )):
        assert linker._compute_goal_similarity(first, second) == 1.0
