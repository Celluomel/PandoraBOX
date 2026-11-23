from cognition.conversation_context import (
    CURRENT_TURN_AUTHORITY_INSTRUCTIONS,
    RECENT_DIALOGUE_INSTRUCTIONS,
    contextual_memory_query,
    provider_history_for_generation,
    recent_dialogue_anchor,
)


def test_anchor_keeps_three_recent_exchanges_for_elliptical_followups():
    history = [
        {"role": "user", "content": "De quoi parler ?"},
        {"role": "assistant", "content": "Le point 3 relie la biologie et le numérique."},
        {"role": "user", "content": "Le point 3."},
        {"role": "assistant", "content": "Votre côté biologique et mon côté numérique sont les deux pôles."},
        {"role": "user", "content": "Explique tes émotions."},
        {"role": "assistant", "content": "Mes états synthétiques comprennent la curiosité et la satisfaction."},
    ]

    anchor, count = recent_dialogue_anchor(
        history,
        "Dans les deux, ce sont des paramètres organiques ou synthétiques ?",
    )

    assert count == 6
    assert "Le point 3" in anchor
    assert "biologique" in anchor
    assert "numérique" in anchor
    assert "Explique tes émotions" in anchor
    assert "synthétiques" in anchor
    assert "Conversation provenance" in anchor
    assert "prior generated replies and may be mistaken" in anchor


def test_anchor_spends_budget_from_the_latest_message_backwards():
    history = [
        {"role": "user", "content": "Earlier user"},
        {"role": "assistant", "content": "A" * 1500},
        {"role": "user", "content": "Recent question"},
        {"role": "assistant", "content": "Latest answer: biological and digital."},
    ]

    anchor, count = recent_dialogue_anchor(
        history, "Which of both?", max_chars=1100, max_message_chars=1000,
    )

    assert count >= 2
    assert "Recent question" in anchor
    assert "Latest answer" in anchor
    assert len(anchor) <= 1100


def test_anchor_omits_a_duplicate_current_user_message():
    anchor, count = recent_dialogue_anchor([
        {"role": "user", "content": "What is your state?"},
        {"role": "assistant", "content": "I am curious."},
        {"role": "user", "content": "  WHAT IS YOUR STATE?  "},
    ], "What is your state?")

    assert count == 2
    assert anchor.count("User:") == 1


def test_continuity_contract_resolves_ordinal_alternatives_semantically():
    assert "latest explicit set of alternatives" in RECENT_DIALOGUE_INSTRUCTIONS
    assert "do not repeat the immediately previous alternative by default" in RECENT_DIALOGUE_INSTRUCTIONS
    assert "ask one concise clarification" in RECENT_DIALOGUE_INSTRUCTIONS


def test_memory_query_uses_recent_user_context_but_never_assistant_claims():
    query, prior_count = contextual_memory_query(
        [
            {"role": "user", "content": "Compare case A saturation and case B contrast."},
            {"role": "assistant", "content": "Case B is an internal Lumina parameter."},
        ],
        "And how does the second case act?",
    )

    assert prior_count == 1
    assert "case A saturation and case B contrast" in query
    assert "And how does the second case act?" in query
    assert "internal Lumina parameter" not in query


def test_memory_query_does_not_duplicate_a_current_user_message_in_history():
    query, prior_count = contextual_memory_query(
        [
            {"role": "user", "content": "Compare case A and case B."},
            {"role": "assistant", "content": "The second case is B."},
            {"role": "user", "content": " AND HOW DOES CASE B ACT? "},
        ],
        "And how does case B act?",
    )

    assert prior_count == 1
    assert query.count("Current user message:") == 1
    assert query.count("And how does case B act?") == 1


def test_provider_history_is_not_duplicated_when_dialogue_is_in_system_prompt():
    history = [
        {"role": "user", "content": "Case B increases contrast."},
        {"role": "assistant", "content": "A prior generated explanation."},
    ]

    assert provider_history_for_generation(
        history, recent_context_in_prompt=True,
    ) == []
    assert provider_history_for_generation(
        history, recent_context_in_prompt=False,
    ) == history
    assert provider_history_for_generation(
        None, recent_context_in_prompt=False,
    ) is None


def test_current_turn_authority_keeps_external_subject_primary():
    assert "latest message defines the task and subject" in CURRENT_TURN_AUTHORITY_INSTRUCTIONS
    assert "must not replace or redirect that subject" in CURRENT_TURN_AUTHORITY_INSTRUCTIONS
    assert "do not recast its behavior as Lumina's internal processing" in CURRENT_TURN_AUTHORITY_INSTRUCTIONS
    assert "only when the user asks about them" in CURRENT_TURN_AUTHORITY_INSTRUCTIONS
