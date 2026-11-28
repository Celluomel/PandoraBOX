from cognition.narrative_synthesizer import NarrativeSynthesizer


def test_completion_flag_without_effect_receipt_does_not_create_completion_narrative():
    synthesizer = NarrativeSynthesizer()

    assert synthesizer._identify_situation({"goal_just_completed": True}) is None
    assert synthesizer.create_narrative_from_cycle({}) is None


def test_verified_completion_receipt_is_the_only_completion_evidence():
    synthesizer = NarrativeSynthesizer()
    context = {
        "goal_completion_receipt": {
            "status": "verified",
            "effect_verified": True,
            "execution_ref": "exec-42",
            "goal_name": "understand affect",
        }
    }

    assert synthesizer._identify_situation(context) == "goal_completed"
    narrative = synthesizer._fill_template(
        synthesizer._select_template("goal_completed"), context
    )
    assert "understand affect" in narrative
    assert "exec-42" in narrative
    assert "relief" not in narrative
    assert "satisfaction is" not in narrative


def test_unverified_or_unlinked_receipt_does_not_claim_goal_completion():
    synthesizer = NarrativeSynthesizer()

    for receipt in (
        {"status": "completed", "effect_verified": True, "execution_ref": "e1", "goal_name": "g"},
        {"status": "verified", "effect_verified": False, "execution_ref": "e1", "goal_name": "g"},
        {"status": "verified", "effect_verified": True, "goal_name": "g"},
    ):
        assert synthesizer._identify_situation({"goal_completion_receipt": receipt}) is None
