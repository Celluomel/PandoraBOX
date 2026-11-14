import threading
from dataclasses import asdict
from unittest.mock import patch

from cognition.cognitive_audit_engine import (
    AuditState, CognitiveAuditEngine, DevelopmentProposal, SignalSnapshot,
)


def _engine(samples=None):
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
    )), snapshot_log=list(samples or []))
    engine._lock = threading.Lock()
    engine._trial_evaluation_in_progress = False
    return engine


def test_mature_trial_starts_only_one_evaluation_thread():
    engine = _engine([
        {"slow_cycle": 50, "belief_confidence_mean": 0.45,
         "signal_status": {"belief_confidence_mean": "measured"}},
        {"slow_cycle": 60, "belief_confidence_mean": 0.46,
         "signal_status": {"belief_confidence_mean": "measured"}},
    ])
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


def test_mature_trial_waits_for_two_measured_post_proposal_snapshots():
    engine = _engine([{
        "slow_cycle": 50,
        "belief_confidence_mean": 0.46,
        "signal_status": {"belief_confidence_mean": "measured"},
    }])
    started = []

    class FakeThread:
        def __init__(self, **kwargs):
            self.name = kwargs.get("name")

        def start(self):
            started.append(self.name)

    with patch("cognition.cognitive_audit_engine.threading.Thread", FakeThread):
        engine.tick(70)

    assert "cae-evaluate" not in started
    assert engine._trial_evaluation_in_progress is False


def test_trial_verdict_uses_mean_of_two_post_proposal_samples(tmp_path):
    engine = _engine([
        {"slow_cycle": 50, "belief_confidence_mean": 0.46,
         "signal_status": {"belief_confidence_mean": "measured"}},
        {"slow_cycle": 60, "belief_confidence_mean": 0.48,
         "signal_status": {"belief_confidence_mean": "measured"}},
    ])
    engine._state.committed_params = {}
    engine._state.trial_log = []
    engine._state.consecutive_under = {}
    engine._read_signals = lambda cycle: SignalSnapshot(
        slow_cycle=cycle,
        timestamp=1.0,
        signal_status={"belief_confidence_mean": "measured"},
        signal_sample_count={"belief_confidence_mean": 40},
        belief_confidence_mean=0.65,
    )
    engine._save = lambda: None
    trial = DevelopmentProposal(**engine._state.active_trial)

    engine._evaluate_trial(trial, slow_cycle=70)

    assert trial.signal_sample_count_at_eval == 3
    assert trial.signal_at_eval == (0.48 + 0.65) / 2
    assert trial.outcome == "confirmed"
    assert engine._state.trial_log[0]["signal_sample_count_at_eval"] == 3


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
