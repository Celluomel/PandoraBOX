import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cognition.curiosity_engine import CuriosityEngine
from cognition.semantic_extractor import SemanticExtractor


class _Memory:
    def upsert_concept(self, *_args, **_kwargs):
        return 1

    def record_observation(self, *_args, **_kwargs):
        return True

    def upsert_relation(self, *_args, **_kwargs):
        return True


def test_grounded_user_topic_is_the_only_semantic_path_to_curiosity():
    curiosity = Mock()
    organism = SimpleNamespace(curiosity=curiosity)
    extractor = SemanticExtractor(
        _Memory(),
        llm_fn=lambda _prompt: json.dumps({
            "turn_kind": "topic",
            "concepts": [{
                "name": "robot locomotion",
                "evidence": "robot locomotion",
            }],
            "relations": [],
            "dominant_topic": "robot locomotion",
            "cognitive_load": 0.2,
        }),
        organism=organism,
    )
    runtime_state = SimpleNamespace(acc=None)

    with patch("core.state.state", runtime_state):
        receipt = extractor._extract(
            "Je m'intéresse à robot locomotion.",
            "We can inspect that capability.",
            None,
            None,
            "user_topic",
            "turn-semantic-1",
        )

    curiosity.stimulate.assert_called_once_with(
        "robot locomotion", amount=0.15, source="user_semantic",
    )
    assert receipt["turn_id"] == "turn-semantic-1"
    assert receipt["curiosity_status"] == "stimulated"
    assert receipt["curiosity_topic_selected"] is True


def test_peer_topic_does_not_stimulate_human_curiosity():
    curiosity = Mock()
    extractor = SemanticExtractor(
        _Memory(),
        llm_fn=lambda _prompt: json.dumps({
            "turn_kind": "topic",
            "concepts": [{"name": "robot locomotion", "evidence": "robot locomotion"}],
            "relations": [],
            "dominant_topic": "robot locomotion",
            "cognitive_load": 0.2,
        }),
        organism=SimpleNamespace(curiosity=curiosity),
    )

    with patch("core.state.state", SimpleNamespace(acc=None)):
        receipt = extractor._extract(
            "Shared robot locomotion.", "Peer response.", None, None,
            "peer_topic", "turn-peer-1",
        )

    curiosity.stimulate.assert_not_called()
    assert receipt["curiosity_status"] == "skipped_peer_source"
    assert receipt["curiosity_topic_selected"] is True


def test_user_semantic_curiosity_uses_grounding_not_word_filter(tmp_path: Path):
    engine = CuriosityEngine(str(tmp_path / "curiosity.json"))
    behavior_gate = SimpleNamespace(may_generate_curiosity=lambda: False)
    runtime_state = SimpleNamespace(
        persona=SimpleNamespace(
            _organism=SimpleNamespace(behavior_gate=behavior_gate),
        ),
    )

    with (
        patch("core.state.state", runtime_state),
        patch("cognition.curiosity_engine.get_topic_filter") as topic_filter,
    ):
        topic_filter.return_value.is_valid.return_value = False
        engine.stimulate(
            "robot locomotion", amount=0.15, source="user_semantic",
        )

    assert engine.top_interests(1)[0][0] == "robot locomotion"
    topic_filter.assert_not_called()


def test_single_grounded_concept_resolves_missing_or_mismatched_dominant_topic():
    one_concept = SemanticExtractor(
        _Memory(),
        llm_fn=lambda _prompt: json.dumps({
            "turn_kind": "topic",
            "concepts": [{"name": "nomic embeddings", "evidence": "Nomic embeddings"}],
            "relations": [],
            "dominant_topic": "embedding model",
            "cognitive_load": 0.2,
        }),
    )
    concepts, _, topic, _, kind = one_concept._parse(
        "Explain Nomic embeddings.", "",
    )
    assert concepts == ["nomic embeddings"]
    assert topic == "nomic embeddings"
    assert kind == "topic"

    ambiguous = SemanticExtractor(
        _Memory(),
        llm_fn=lambda _prompt: json.dumps({
            "turn_kind": "topic",
            "concepts": [
                {"name": "nomic embeddings", "evidence": "Nomic embeddings"},
                {"name": "goal scoring", "evidence": "goal scoring"},
            ],
            "relations": [],
            "dominant_topic": "unrelated topic",
            "cognitive_load": 0.2,
        }),
    )
    concepts, _, topic, _, kind = ambiguous._parse(
        "Explain Nomic embeddings and goal scoring.", "",
    )
    assert len(concepts) == 2
    assert topic == ""
    assert kind == "topic"


def test_retrieval_turn_does_not_persist_or_promote_concepts():
    memory = Mock()
    curiosity = Mock()
    runtime_state = SimpleNamespace(acc=Mock())
    provider_turn_ids = []

    def classify_retrieval(_prompt):
        from core.turn_execution_context import current_turn_id
        provider_turn_ids.append(current_turn_id.get())
        return json.dumps({
            "turn_kind": "retrieval",
            "concepts": [{
                "name": "dernier objectif cognitif",
                "evidence": "dernier objectif cognitif",
            }],
            "relations": [],
            "dominant_topic": "dernier objectif cognitif",
            "cognitive_load": 0.2,
        })

    extractor = SemanticExtractor(
        memory,
        llm_fn=classify_retrieval,
        organism=SimpleNamespace(curiosity=curiosity),
    )

    with patch("core.state.state", runtime_state):
        receipt = extractor._extract(
            "Rappelle-moi le dernier objectif cognitif.",
            "It was the audit objective.", None, None, "user_topic",
            "turn-retrieval-1",
        )

    memory.upsert_concept.assert_not_called()
    memory.record_observation.assert_not_called()
    memory.upsert_relation.assert_not_called()
    runtime_state.acc.update_semantic_topics.assert_not_called()
    curiosity.stimulate.assert_not_called()
    assert receipt["turn_kind"] == "retrieval"
    assert receipt["learning_status"] == "skipped_non_topic_turn"
    assert receipt["persistence_status"] == "not_needed"
    assert provider_turn_ids == ["turn-retrieval-1"]


def test_trusted_upstream_act_skips_redundant_semantic_llm_and_learning():
    for turn_kind in ("retrieval", "social", "other"):
        memory = Mock()
        curiosity = Mock()
        llm_fn = Mock(side_effect=AssertionError("unexpected semantic LLM call"))
        extractor = SemanticExtractor(
            memory,
            llm_fn=llm_fn,
            organism=SimpleNamespace(curiosity=curiosity),
        )

        with patch("core.state.state", SimpleNamespace(acc=Mock())):
            receipt = extractor._extract(
                "How are you?", "I am doing well.", None, None,
                "user_topic", f"turn-{turn_kind}-hint", None, turn_kind,
            )

        llm_fn.assert_not_called()
        memory.upsert_concept.assert_not_called()
        memory.record_observation.assert_not_called()
        memory.upsert_relation.assert_not_called()
        curiosity.stimulate.assert_not_called()
        assert receipt["status"] == "completed"
        assert receipt["classification_source"] == "upstream_turn_contract"
        assert receipt["turn_kind"] == turn_kind
        assert receipt["learning_status"] == "skipped_non_topic_turn"
