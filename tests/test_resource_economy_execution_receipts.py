from __future__ import annotations

import json

from cognition.cognitive_resource_economy import CognitiveResourceEconomy


def test_tick_returns_resource_delta_and_verified_persistence(tmp_path):
    path = tmp_path / "resources.json"
    economy = CognitiveResourceEconomy(path=str(path))
    economy.cognitive_energy = 0.4
    economy.social_energy = 0.5
    economy.attention = 0.6

    receipt = economy.tick(elapsed_secs=10)

    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert receipt["outcome_status"] == "completed"
    assert receipt["effect_status"] == "state_updated"
    assert receipt["persisted"] is True
    assert receipt["elapsed_seconds"] == 10
    assert receipt["before"]["cognitive_energy"] == 0.4
    assert receipt["after"]["cognitive_energy"] > 0.4
    assert receipt["delta"]["attention"] == 0
    assert abs(persisted["cognitive_energy"] - receipt["after"]["cognitive_energy"]) < 1e-6
    assert abs(persisted["social_energy"] - receipt["after"]["social_energy"]) < 1e-6
    assert abs(persisted["attention"] - receipt["after"]["attention"]) < 1e-6


def test_tick_reports_state_change_when_persistence_fails(tmp_path, monkeypatch):
    path = tmp_path / "resources.json"
    economy = CognitiveResourceEconomy(path=str(path))
    economy.cognitive_energy = 0.4

    def fail_replace(_target):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(type(path), "replace", lambda self, target: fail_replace(target))
    receipt = economy.tick(elapsed_secs=10)

    assert receipt["outcome_status"] == "persistence_failed"
    assert receipt["effect_status"] == "state_updated"
    assert receipt["persisted"] is False
    assert receipt["after"]["cognitive_energy"] > receipt["before"]["cognitive_energy"]
