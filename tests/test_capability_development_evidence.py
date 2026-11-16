import json

from cognition.capability_development import (
    BASELINE_STEPS,
    TRIAL_STEPS,
    CapabilityDevelopmentEngine,
)


def _observation(score):
    return {"score": score, "diversity": score, "total_items": 1, "sources": []}


def test_passive_workspace_change_cannot_verify_a_capability(tmp_path):
    engine = CapabilityDevelopmentEngine(object(), path=str(tmp_path / "capability.json"))
    observations = iter(
        [_observation(0.1)] * BASELINE_STEPS
        + [_observation(0.2)] * (TRIAL_STEPS * 2)
    )
    engine._observe = lambda: next(observations)
    engine.start({"id": "proposal-1", "title": "A capability"})

    for cycle in range(1, BASELINE_STEPS + 1):
        receipt = engine.tick(cycle)
        assert receipt["outcome_status"] == "completed"
        assert receipt["persisted"] is True
    assert engine.snapshot()["experiment"]["status"] == "running"

    for cycle in range(BASELINE_STEPS + 1, BASELINE_STEPS + TRIAL_STEPS + 1):
        receipt = engine.tick(cycle)

    snapshot = engine.snapshot()
    experiment = snapshot["experiment"]
    assert experiment["status"] == "observational_only"
    assert experiment["result"]["observed_change"] == 0.1
    assert experiment["result"]["causal_attribution"] == "not_established"
    assert experiment["result"]["confirmation"] == "not_verifiable_without_intervention"
    assert experiment["trials"][-1]["intervention_status"] == "not_applied"
    assert snapshot["verified_capability"] is None

    # A terminal observational result does not keep ticking or consuming data.
    receipt = engine.tick(100)
    assert receipt["effect_status"] == "no_active_experiment"
    assert experiment["status"] == "observational_only"


def test_failed_tick_persistence_rolls_back_observation_state(tmp_path):
    engine = CapabilityDevelopmentEngine(object(), path=str(tmp_path / "capability.json"))
    engine._observe = lambda: _observation(0.3)
    engine.start({"id": "proposal-2", "title": "A capability"})
    engine._save = lambda: False

    receipt = engine.tick(1)

    assert receipt["outcome_status"] == "persistence_failed"
    assert receipt["effect_status"] == "state_update_rolled_back"
    assert receipt["persisted"] is False
    assert engine.snapshot()["experiment"]["baseline"] == []


def test_failed_start_persistence_does_not_leave_active_experiment(tmp_path):
    engine = CapabilityDevelopmentEngine(object(), path=str(tmp_path / "capability.json"))
    engine._save = lambda: False

    try:
        engine.start({"id": "proposal-3", "title": "A capability"})
    except RuntimeError as exc:
        assert "not persisted" in str(exc)
    else:
        raise AssertionError("failed persistence must not report a started experiment")

    assert engine.snapshot()["experiment"] is None


def test_legacy_passive_verified_claim_is_demoted_and_persisted(tmp_path):
    path = tmp_path / "capability.json"
    path.write_text(
        json.dumps({
            "proposal": None,
            "experiment": {
                "id": "legacy-1",
                "title": "Legacy claim",
                "status": "verified",
                "result": {"confirmation": "long_run_confirmed"},
            },
            "verified_capability": {"name": "Legacy claim", "status": "verified"},
            "history": [{"id": "legacy-history", "status": "verified", "result": {}}],
        }),
        encoding="utf-8",
    )

    engine = CapabilityDevelopmentEngine(object(), path=str(path))
    snapshot = engine.snapshot()
    persisted = json.loads(path.read_text(encoding="utf-8"))

    assert snapshot["experiment"]["status"] == "observational_only"
    assert snapshot["experiment"]["result"]["causal_attribution"] == "not_established"
    assert snapshot["verified_capability"] is None
    assert snapshot["history"][0]["status"] == "observational_only"
    assert persisted["experiment"]["status"] == "observational_only"
    assert persisted["history"][0]["result"]["confirmation"] == "not_verifiable_without_intervention"
