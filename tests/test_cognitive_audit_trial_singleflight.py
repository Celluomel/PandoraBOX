import threading
from dataclasses import asdict
from unittest.mock import patch

from cognition.cognitive_audit_engine import AuditState, CognitiveAuditEngine, DevelopmentProposal


def _engine():
    engine = CognitiveAuditEngine.__new__(CognitiveAuditEngine)
    engine._state = AuditState(active_trial=asdict(DevelopmentProposal(
        dimension="belief_confidence_mean",
        signal_at_proposal=0.3,
        signal_target=0.5,
        parameter="grounding_boost",
        prior_value=0.03,
        proposed_value=0.04,
        rationale="test trial",
        proposed_at_cycle=10,
    )))
    engine._lock = threading.Lock()
    engine._trial_evaluation_in_progress = False
    return engine


def test_mature_trial_starts_only_one_evaluation_thread():
    engine = _engine()
    started = []

    class FakeThread:
        def __init__(self, *, target, args, daemon, name):
            self.target = target
            self.args = args
            self.name = name

        def start(self):
            started.append(self)

    with patch("cognition.cognitive_audit_engine.threading.Thread", FakeThread):
        for cycle in range(70, 76):
            engine.tick(cycle)

    assert len(started) == 1
    assert started[0].name == "cae-evaluate"
    assert started[0].target == engine._evaluate_trial_once
    assert engine._trial_evaluation_in_progress is True


def test_singleflight_guard_is_released_even_if_evaluation_raises():
    engine = _engine()
    engine._trial_evaluation_in_progress = True

    def fail(_trial, _cycle):
        raise RuntimeError("simulated evaluation error")

    engine._evaluate_trial = fail

    try:
        engine._evaluate_trial_once(DevelopmentProposal(
            dimension="belief_confidence_mean",
            signal_at_proposal=0.3,
            signal_target=0.5,
            parameter="grounding_boost",
            prior_value=0.03,
            proposed_value=0.04,
            rationale="test trial",
            proposed_at_cycle=10,
        ), 70)
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected the simulated evaluation error")

    assert engine._trial_evaluation_in_progress is False
