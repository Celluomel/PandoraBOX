from types import SimpleNamespace

import cognition.epistemic_efficacy_model as efficacy_module
import cognition.internal_cognitive_state as internal_state_module
import cognition.recursive_deliberation as deliberation_module
import cognition.reflection_controller as reflection_module
import pytest


class _Workspace:
    def __init__(self):
        self.state = SimpleNamespace(focus="prior focus", context={})

    def get_state(self):
        return self.state

    def set_hypotheses(self, *_args, **_kwargs):
        pass

    def update_state(self, _source, **fields):
        for key, value in fields.items():
            setattr(self.state, key, value)


class _EfficacyModel:
    def __init__(self):
        self.observed = []
        self.predictions = []

    def observe_if_pending(self, pressure):
        self.observed.append(pressure)

    def record_prediction_if_winner(self, name, topic, pressure):
        self.predictions.append((name, topic, pressure))


class _Competition:
    def __init__(self):
        self.received_models = []

    def compete(self, **kwargs):
        self.received_models.append(kwargs.get("efficacy_model"))
        candidate = {
            "id": "resolve-uncertainty",
            "name": "resolve_uncertainty",
            "topic": "resolve_uncertainty",
            "type": "goal",
            "score": 1.0,
        }
        return {"competition": {"all_candidates": [candidate]}}


@pytest.mark.parametrize("internal_state_fails", [False, True])
def test_default_adaptive_depth_keeps_epistemic_efficacy_in_deliberation(
    monkeypatch, internal_state_fails
):
    workspace = _Workspace()
    organism = SimpleNamespace(workspace=workspace)
    efficacy = _EfficacyModel()
    competition = _Competition()
    internal_state = SimpleNamespace(history=[], update=lambda _pressure: None)
    monkeypatch.setattr(deliberation_module, "_gather_live_goals", lambda _org: [{
        "id": "resolve-uncertainty",
        "name": "resolve_uncertainty",
        "topic": "resolve_uncertainty",
        "priority": 1.0,
        "energy": 1.0,
        "urgency": 1.0,
        "quality_score": 1.0,
    }])
    monkeypatch.setattr(deliberation_module, "_gather_live_percepts", lambda _org: [])
    monkeypatch.setattr(deliberation_module, "_gather_live_symbols", lambda _org: [])
    monkeypatch.setattr(deliberation_module, "_gather_live_tensions", lambda _org: {})
    monkeypatch.setattr(deliberation_module, "_gather_live_pressure", lambda _org: {"epistemic": 0.6})
    monkeypatch.setattr(deliberation_module, "_get_competition_instance", lambda _gw: competition)
    monkeypatch.setattr(deliberation_module, "_profile_candidate", lambda *_args: {"novelty": 0.0})
    monkeypatch.setattr(deliberation_module, "_compute_utility", lambda raw, _max, _profile: raw)
    def get_internal_state(_org):
        if internal_state_fails:
            raise RuntimeError("simulated state accessor failure")
        return internal_state

    monkeypatch.setattr(internal_state_module, "get_internal_cognitive_state", get_internal_state)
    monkeypatch.setattr(efficacy_module, "get_epistemic_efficacy_model", lambda _org: efficacy)
    monkeypatch.setattr(
        reflection_module,
        "get_reflection_controller",
        lambda: SimpleNamespace(allowed_depth=lambda _error: 1),
    )

    result = deliberation_module.deliberate(organism, "test the default path")

    assert result is not None
    assert competition.received_models == [efficacy]
    assert efficacy.observed == [0.6]
    assert efficacy.predictions == [("resolve_uncertainty", "resolve_uncertainty", 0.6)]
