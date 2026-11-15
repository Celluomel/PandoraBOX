from types import SimpleNamespace

import cognition.epistemic_efficacy_model as efficacy_module
import cognition.internal_cognitive_state as internal_state_module
import cognition.recursive_deliberation as deliberation_module
import cognition.reflection_controller as reflection_module
import pytest
from cognition.epistemic_efficacy_model import EpistemicEfficacyModel
from cognition.workspace_competition import WorkspaceCompetition


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

    def observe_if_pending(self, pressure, observation_cycle_id=None):
        self.observed.append((pressure, observation_cycle_id))

    def record_competition_application(self, **receipt):
        self.application = receipt

    def record_prediction_if_winner(self, name, topic, pressure, source_cycle_id=None):
        self.predictions.append((name, topic, pressure, source_cycle_id))


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

    result = deliberation_module.deliberate(
        organism, "test the default path", cycle_id="turn-42"
    )

    assert result is not None
    assert competition.received_models == [efficacy]
    assert efficacy.observed == [(0.6, "turn-42:observe")]
    assert efficacy.application["cycle_id"] == "turn-42"
    assert efficacy.predictions == [
        ("resolve_uncertainty", "resolve_uncertainty", 0.6, "turn-42")
    ]


class _SelfConcept:
    def __init__(self):
        self._beliefs = {
            "effective_at_resolving_uncertainty": SimpleNamespace(confidence=0.5)
        }

    def record_affirmation(self, _name):
        self._beliefs["effective_at_resolving_uncertainty"].confidence += 0.1

    def record_violation(self, _name, context=None):
        self._beliefs["effective_at_resolving_uncertainty"].confidence -= 0.1


def test_prediction_receipt_links_cycles_pressures_belief_and_applied_multiplier():
    model = EpistemicEfficacyModel(_SelfConcept())
    model.record_competition_application(
        cycle_id="turn-10", candidate={
            "id": "g-1", "name": "resolve_uncertainty", "topic": "resolve_uncertainty",
            "score": 1.2, "efficacy_multiplier_applied": 1.0,
            "internal_alignment_baseline": 0.2, "internal_bias": 0.2,
        }, final_focus="resolve_uncertainty",
    )
    model.record_prediction_if_winner(
        "resolve_uncertainty", "resolve_uncertainty", 0.6, source_cycle_id="turn-10"
    )
    pending_id = model._pending.prediction_id

    assert model.observe_if_pending(0.45, observation_cycle_id="turn-11:observe") == pytest.approx(0.0)
    receipt = model.history[-1]
    assert receipt["prediction_id"] == pending_id
    assert receipt["source_cycle_id"] == "turn-10"
    assert receipt["observation_cycle_id"] == "turn-11:observe"
    assert receipt["pressure_before"] == pytest.approx(0.6)
    assert receipt["pressure_after"] == pytest.approx(0.45)
    assert receipt["confidence_before"] == pytest.approx(0.5)
    assert receipt["confidence_after"] == pytest.approx(0.6)
    assert receipt["competition_application"]["applied_to_final_focus"] is True


def test_prediction_not_created_when_multiplier_did_not_affect_selected_focus():
    model = EpistemicEfficacyModel(_SelfConcept())
    model.record_competition_application(
        cycle_id="turn-12", candidate={
            "id": "g-1", "name": "resolve_uncertainty", "topic": "resolve_uncertainty",
            "score": 1.2, "efficacy_multiplier_applied": 1.0,
        }, final_focus="other_goal",
    )

    model.record_prediction_if_winner(
        "resolve_uncertainty", "resolve_uncertainty", 0.6, source_cycle_id="turn-12"
    )

    assert model._pending is None
    assert model.last_application["applied_to_final_focus"] is False


def test_workspace_competition_exposes_actual_multiplier_application():
    class InternalState:
        def internal_alignment(self, _name, _topic, efficacy_multiplier=1.0):
            return 0.2 * efficacy_multiplier

    class Efficacy:
        def effectiveness_multiplier(self):
            return 1.4

    result = WorkspaceCompetition().compete(
        goals=[{
            "id": "resolve-1", "name": "resolve_uncertainty",
            "topic": "resolve_uncertainty", "priority": 1.0, "energy": 1.0,
            "urgency": 0.0, "quality_score": 1.0,
        }],
        thoughts=[], tensions={}, pressure={}, internal_state=InternalState(),
        efficacy_model=Efficacy(),
    )
    candidate = result["competition"]["all_candidates"][0]
    assert candidate["efficacy_multiplier_applied"] == pytest.approx(1.4)
    assert candidate["internal_alignment_baseline"] == pytest.approx(0.2)
    assert candidate["internal_bias"] == pytest.approx(0.28)
    assert candidate["score"] - candidate["score_without_efficacy"] == pytest.approx(0.08)
