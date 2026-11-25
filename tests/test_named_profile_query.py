from cognition.profile_flow import (
    is_explicit_named_profile_query,
    render_explicit_profile_facts,
)


def test_explicit_profile_read_queries_are_routed_but_profile_writes_are_not():
    assert is_explicit_named_profile_query(
        "Selon mon profil utilisateur enregistré, quelle préférence ai-je ?"
    )
    assert is_explicit_named_profile_query(
        "According to my stored profile, what preferences are recorded?"
    )
    assert is_explicit_named_profile_query(
        "What preferences are recorded in my profile?"
    )
    assert not is_explicit_named_profile_query(
        "Please add my preference for concise answers to my profile."
    )
    assert not is_explicit_named_profile_query("How are you doing?")


def test_profile_answer_uses_only_supplied_provenance_backed_facts():
    rendered = render_explicit_profile_facts(
        [
            {"category": "preference", "value": "concise updates in French"},
            {"category": "interest", "value": "robotics"},
        ],
        "Quelle préférence est enregistrée dans mon profil ?",
    )

    assert rendered["status"] == "rendered_from_provenance_backed_profile"
    assert rendered["fact_count"] == 1
    assert rendered["categories"] == ["preference"]
    assert "concise updates in French" in rendered["answer"]
    assert "robotics" not in rendered["answer"]


def test_empty_profile_answer_does_not_fall_back_to_behavioral_inference():
    rendered = render_explicit_profile_facts(
        [], "What preference is stored in my profile?"
    )

    assert rendered["status"] == "empty"
    assert rendered["fact_count"] == 0
    assert "no provenance-backed explicit fact" in rendered["answer"]
