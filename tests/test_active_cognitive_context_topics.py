from unittest.mock import Mock, patch

from cognition.active_cognitive_context import ActiveCognitiveContext
from cognition.semantic_extractor import SemanticExtractor


def test_cag_does_not_turn_question_ngrams_or_assistant_prose_into_topics():
    context = ActiveCognitiveContext(organism=None, llm=None)

    context.update_from_turn(
        "Quelles émotions fonctionnelles sont actives en toi maintenant ?",
        "La curiosité et la chaleur sont actives.",
    )

    assert context.snapshot()["topics"] == []
    assert "Extracted conversation concepts" not in context.get_prompt_fragment()


def test_cag_accepts_only_extractor_concepts_present_in_incoming_evidence():
    context = ActiveCognitiveContext(organism=None, llm=None)
    user_text = "Quelles émotions fonctionnelles sont actives en toi maintenant ?"

    context.update_semantic_topics(
        ["émotions fonctionnelles", "hallucinated mechanism"],
        topic="émotions fonctionnelles",
        evidence_text=user_text,
        source_role="user_topic",
    )

    snapshot = context.snapshot()["topics"]
    assert [item["topic"] for item in snapshot] == ["émotions fonctionnelles"]
    assert snapshot[0]["source_role"] == "user_topic"
    assert "user_topic" in context.get_prompt_fragment()


def test_cag_rejects_concepts_without_a_valid_conversation_source():
    context = ActiveCognitiveContext(organism=None, llm=None)
    context.update_semantic_topics(
        ["robot locomotion"],
        topic="robot locomotion",
        evidence_text="robot locomotion",
        source_role="assistant_claim",
    )

    assert context.snapshot()["topics"] == []


def test_semantic_extractor_forwards_grounded_topics_with_turn_source_to_cag():
    runtime_state = Mock()
    runtime_state.acc = Mock()
    extractor = SemanticExtractor(semantic_memory=Mock())
    extractor._parse = Mock(return_value=(
        ["émotions fonctionnelles"], [], "émotions fonctionnelles", 0.4,
    ))
    user_text = "Quelles émotions fonctionnelles sont actives en toi maintenant ?"

    with patch("core.state.state", runtime_state):
        extractor._extract(
            user_text, "La curiosité est active.", None, None, "user_topic",
        )

    runtime_state.acc.update_semantic_topics.assert_called_once_with(
        ["émotions fonctionnelles"],
        topic="émotions fonctionnelles",
        evidence_text=user_text,
        source_role="user_topic",
    )
