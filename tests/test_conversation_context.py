from cognition.conversation_context import recent_dialogue_anchor


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
