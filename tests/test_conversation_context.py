from cognition.conversation_context import (
    CURRENT_TURN_AUTHORITY_INSTRUCTIONS,
    RECENT_DIALOGUE_INSTRUCTIONS,
    contextual_memory_query,
    recent_dialogue_anchor,
    recent_dialogue_messages,
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


def test_followup_history_is_sent_as_native_roles_with_the_latest_referents():
    history = [
        {"role": "user", "content": "De quoi parler ?"},
        {"role": "assistant", "content": "Trois pistes, dont le pont biologique et numérique."},
        {"role": "user", "content": "Le point 3."},
        {"role": "assistant", "content": "Votre côté biologique et mon côté numérique."},
        {"role": "user", "content": "Explique tes émotions."},
        {"role": "assistant", "content": "Curiosité et satisfaction sont des états synthétiques."},
    ]

    messages = recent_dialogue_messages(
        history,
        "Dans les deux, ce sont des paramètres organiques ou synthétiques ?",
    )

    assert [item["role"] for item in messages] == [
        "user", "assistant", "user", "assistant", "user", "assistant",
    ]
    assert "biologique" in messages[1]["content"]
    assert "numérique" in messages[1]["content"]
    assert "Explique tes émotions" in messages[4]["content"]
    assert "Curiosité" in messages[5]["content"]
    assert all("Dans les deux" not in item["content"] for item in messages)


def test_role_tagged_history_drops_duplicate_current_input_and_private_reasoning():
    messages = recent_dialogue_messages(
        [
            {"role": "user", "content": "What did we choose?"},
            {"role": "assistant", "content": "<think>private plan</think>We chose option B."},
            {"role": "user", "content": "  WHICH OPTION? "},
        ],
        "Which option?",
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1] == {"role": "assistant", "content": "We chose option B."}


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


def test_continuity_contract_does_not_treat_a_bare_checkin_as_consent_or_resume():
    assert "standalone check-in" in RECENT_DIALOGUE_INSTRUCTIONS
    assert "do not turn it into confirmation, consent" in RECENT_DIALOGUE_INSTRUCTIONS
    assert "resume that topic only when the user explicitly refers to it" in RECENT_DIALOGUE_INSTRUCTIONS


def test_continuity_contract_expands_last_substantive_turn_and_respects_pending_choice():
    assert "develop the most recent substantive assistant explanation as the referent" in RECENT_DIALOGUE_INSTRUCTIONS
    assert "do not replace it with a new topic menu" in RECENT_DIALOGUE_INSTRUCTIONS
    assert "apply it to that reply directly" in RECENT_DIALOGUE_INSTRUCTIONS
    assert "do not merely acknowledge the instruction" in RECENT_DIALOGUE_INSTRUCTIONS
    assert "selection answers the latest still-open assistant question or option set" in RECENT_DIALOGUE_INSTRUCTIONS

    history = [
        {"role": "user", "content": "Choose a theme."},
        {"role": "assistant", "content": "We could explore connection, uncertainty, or the paradox of self-discovery."},
        {"role": "user", "content": "The paradox."},
        {"role": "assistant", "content": "The self-discovery paradox is about a self changing as it examines itself."},
        {"role": "user", "content": "The feeling of being perpetually unfinished."},
        {"role": "assistant", "content": "That may be an engine of becoming. Which aspect resonates for you?"},
    ]

    messages = recent_dialogue_messages(history, "Elaborate")
    assert "Which aspect resonates for you?" in messages[-1]["content"]
    assert "That may be an engine of becoming" in messages[-1]["content"]
    assert messages[-2]["content"] == "The feeling of being perpetually unfinished."


def test_memory_query_uses_recent_user_context_but_never_assistant_claims():
    query, prior_count = contextual_memory_query(
        [
            {"role": "user", "content": "Compare case A saturation and case B contrast."},
            {"role": "assistant", "content": "Case B is an internal Lumina parameter."},
        ],
        "And how does the second case act?",
        max_prior_user_messages=2,
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
        max_prior_user_messages=2,
    )

    assert prior_count == 1
    assert query.count("Current user message:") == 1
    assert query.count("And how does case B act?") == 1


def test_default_memory_query_does_not_mix_prior_topics_into_a_new_turn():
    query, prior_count = contextual_memory_query(
        [
            {"role": "user", "content": "Compare case A saturation and case B contrast."},
            {"role": "assistant", "content": "Case B is an internal Lumina parameter."},
        ],
        "For this audit, remember marker LUMINA-MEMORY-8B2R.",
    )

    assert prior_count == 0
    assert "Current user message: For this audit, remember marker LUMINA-MEMORY-8B2R." in query
    assert "saturation" not in query
    assert "contrast" not in query
    assert "internal Lumina parameter" not in query


def test_current_turn_authority_keeps_external_subject_primary():
    assert "latest message defines the task and subject" in CURRENT_TURN_AUTHORITY_INSTRUCTIONS
    assert "must not replace or redirect that subject" in CURRENT_TURN_AUTHORITY_INSTRUCTIONS
    assert "do not recast its behavior as Lumina's internal processing" in CURRENT_TURN_AUTHORITY_INSTRUCTIONS
    assert "only when the user asks about them" in CURRENT_TURN_AUTHORITY_INSTRUCTIONS
