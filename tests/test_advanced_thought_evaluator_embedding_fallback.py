from unittest.mock import patch

import numpy as np

from cognition.advanced_thought_evaluator import AdvancedThoughtEvaluator


class _SpaceEmbedder:
    def __init__(self, space_id):
        self.space_id = space_id

    def encode_with_metadata(self, texts):
        return np.asarray([[1.0, 0.0] for _ in texts]), self.space_id


def test_advanced_evaluator_does_not_use_word_overlap_for_uncalibrated_fallback():
    evaluator = AdvancedThoughtEvaluator()
    embedder = _SpaceEmbedder("sentence-transformers:all-MiniLM-L6-v2")
    with patch("utils.shared_embedder.get_embedder", return_value=embedder):
        result = evaluator._compute_goal_similarity(
            ["robot odometry"], [{"name": "robot odometry"}],
        )

    assert result == 0.0


def test_advanced_evaluator_uses_cosine_for_calibrated_nomic():
    evaluator = AdvancedThoughtEvaluator()
    embedder = _SpaceEmbedder(
        "api:http://localhost:1234/v1:text-embedding-nomic-embed-text-v1.5"
    )
    with patch("utils.shared_embedder.get_embedder", return_value=embedder):
        result = evaluator._compute_goal_similarity(
            ["robot odometry"], [{"name": "mechanical walking"}],
        )

    assert result == 1.0


def test_advanced_evaluator_returns_goal_id_with_calibrated_match():
    evaluator = AdvancedThoughtEvaluator()
    embedder = _SpaceEmbedder(
        "api:http://localhost:1234/v1:text-embedding-nomic-embed-text-v1.5"
    )
    with patch("utils.shared_embedder.get_embedder", return_value=embedder):
        result = evaluator._compute_goal_match(
            ["cognitive execution flow"],
            [{"id": "goal-cognitive-flow", "name": "systemic process"}],
        )

    assert result == {"goal_id": "goal-cognitive-flow", "similarity": 1.0}


def test_advanced_evaluator_does_not_emit_goal_id_from_uncalibrated_space():
    evaluator = AdvancedThoughtEvaluator()
    embedder = _SpaceEmbedder("sentence-transformers:all-MiniLM-L6-v2")
    with patch("utils.shared_embedder.get_embedder", return_value=embedder):
        result = evaluator._compute_goal_match(
            ["cognitive execution flow"],
            [{"id": "goal-cognitive-flow", "name": "systemic process"}],
        )

    assert result == {"goal_id": None, "similarity": 0.0}


def test_advanced_evaluator_uses_schema_signal_and_structured_topic_only():
    evaluator = AdvancedThoughtEvaluator()

    for prose in (
        "A resolved tension, with no uncertainty or opportunity in the wording.",
        "Une phrase neutre, sans termes anglais déclencheurs.",
        "没有触发词的普通记录。",
    ):
        thought = {
            "content": prose,
            "thought_type": "tension_awareness",
            "topic": "cognitive_execution_flow",
            "priority": 0.8,
        }
        assert evaluator._classify_thought_advanced(thought) == ("tension", 1.0)
        assert evaluator._extract_concepts(thought) == ["cognitive execution flow"]

    keyword_rich = {
        "content": "wonder conflict explore contradiction",
        "thought_type": "reflection",
    }
    assert evaluator._classify_thought_advanced(keyword_rich) == ("general", 0.0)
    assert evaluator._extract_concepts(keyword_rich) == []
    assert evaluator._compute_actionability("general", ["matching goal"], 1.0) == 0.0


def test_friction_comes_only_from_numeric_producer_field():
    evaluator = AdvancedThoughtEvaluator()

    assert evaluator._detect_conceptual_friction({
        "content": "but however contradiction despite",
    }) == 0.0
    assert evaluator._detect_conceptual_friction({
        "conceptual_friction": 0.7,
        "content": "neutral prose",
    }) == 0.7


def test_non_actionable_thought_is_updated_in_place_and_not_reprocessed(tmp_path):
    from core.data.access import DataAccess

    dal = DataAccess(str(tmp_path))
    assert dal.add_thought({
        "id": "adv-eval-neutral-1",
        "content": "I wonder whether contradiction may create an opportunity.",
        "source": "internal",
        "thought_type": "reflection",
        "priority": 0.4,
        "topic": "",
    })

    evaluator = AdvancedThoughtEvaluator(str(tmp_path))
    assert evaluator.evaluate_recent_thoughts() == []
    stored = dal.get_thoughts(skip_expired=False, limit=20)
    matches = [row for row in stored if row["id"] == "adv-eval-neutral-1"]
    assert len(matches) == 1
    assert matches[0]["evaluated"] is True
    assert evaluator.evaluate_recent_thoughts() == []
    stored_again = dal.get_thoughts(skip_expired=False, limit=20)
    assert sum(row["id"] == "adv-eval-neutral-1" for row in stored_again) == 1


def test_typed_thought_uses_nomic_and_persists_one_actionable_result(tmp_path):
    from core.data.access import DataAccess

    dal = DataAccess(str(tmp_path))
    assert dal.add_thought({
        "id": "adv-eval-tension-1",
        "content": "A neutral sentence in any language can carry this signal.",
        "source": "internal_loop",
        "thought_type": "tension_awareness",
        "priority": 0.84,
        "topic": "cognitive_execution_flow",
        "conceptual_friction": 0.2,
    })
    evaluator = AdvancedThoughtEvaluator(str(tmp_path))
    evaluator._load_active_goals = lambda: [{
        "id": "goal-cognitive-execution-flow",
        "name": "cognitive execution flow",
    }]

    embedder = _SpaceEmbedder(
        "api:http://localhost:1234/v1:text-embedding-nomic-embed-text-v1.5"
    )
    with patch("utils.shared_embedder.get_embedder", return_value=embedder):
        suggestions = evaluator.evaluate_recent_thoughts()

    assert len(suggestions) == 1
    result = suggestions[0]
    assert result["type"] == "tension_cognitive_execution_flow"
    assert result["concept"] == "cognitive execution flow"
    assert result["related_goal_id"] == "goal-cognitive-execution-flow"
    assert result["evaluation"]["goal_similarity"] == 1.0
    saved = dal.get_thoughts(skip_expired=False, limit=20)
    assert sum(row["id"] == "adv-eval-tension-1" for row in saved) == 1
    assert next(row for row in saved if row["id"] == "adv-eval-tension-1")["evaluated"] is True


def test_semantic_match_cannot_promote_untyped_thought_to_goal(tmp_path):
    from core.data.access import DataAccess

    dal = DataAccess(str(tmp_path))
    assert dal.add_thought({
        "id": "adv-eval-untyped-1",
        "content": "wonder conflict explore contradiction",
        "source": "internal",
        "thought_type": "reflection",
        "priority": 0.95,
        "topic": "cognitive_execution_flow",
    })
    evaluator = AdvancedThoughtEvaluator(str(tmp_path))
    evaluator._load_active_goals = lambda: [{"name": "cognitive execution flow"}]
    embedder = _SpaceEmbedder(
        "api:http://localhost:1234/v1:text-embedding-nomic-embed-text-v1.5"
    )
    with patch("utils.shared_embedder.get_embedder", return_value=embedder):
        assert evaluator.evaluate_recent_thoughts() == []

    saved = dal.get_thoughts(skip_expired=False, limit=20)
    row = next(row for row in saved if row["id"] == "adv-eval-untyped-1")
    assert row["evaluated"] is True
    assert sum(item["id"] == "adv-eval-untyped-1" for item in saved) == 1
