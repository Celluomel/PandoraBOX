from types import SimpleNamespace

from cognition.meta_learning_audit import META_WINDOW, MetaLearningAudit


def _audit(tmp_path, pending, snapshots):
    cae = SimpleNamespace(_state=SimpleNamespace(snapshot_log=snapshots, trial_log=[]))
    loop = SimpleNamespace(_cognitive_audit=cae)
    organism = SimpleNamespace(_loop=loop)
    audit = MetaLearningAudit(organism, ai_system=None, path=str(tmp_path / "meta.json"))
    audit._pending = pending
    audit._save = lambda: None
    return audit


def test_committed_trial_baseline_starts_at_actual_confirmation(tmp_path):
    audit = _audit(tmp_path, [], [])
    audit._organism._loop._cognitive_audit._state.trial_log = [{
        "outcome": "confirmed",
        "committed": True,
        "parameter": "grounding_boost",
        "dimension": "belief_confidence_mean",
        "proposed_at_cycle": 40,
        "evaluated_at_cycle": 100,
        "signal_at_proposal": 0.30,
        "signal_at_eval": 0.56,
    }]

    audit._register_new_commits(slow_cycle=100)

    assert audit._pending == [{
        "parameter": "grounding_boost",
        "signal": "belief_confidence_mean",
        "before": 0.56,
        "baseline_source": "commit_snapshot",
        "commit_cycle": 100,
        "eval_at": 100 + META_WINDOW,
    }]


def test_evaluation_uses_only_measured_post_commit_window(tmp_path):
    pending = [{
        "parameter": "grounding_boost",
        "signal": "belief_confidence_mean",
        "before": 0.55,
        "baseline_source": "commit_snapshot",
        "commit_cycle": 100,
        "eval_at": 220,
    }]
    snapshots = [
        {"slow_cycle": 90, "belief_confidence_mean": 0.99,
         "signal_status": {"belief_confidence_mean": "measured"}},
        {"slow_cycle": 140, "belief_confidence_mean": 0.65,
         "signal_status": {"belief_confidence_mean": "measured"}},
        {"slow_cycle": 180, "belief_confidence_mean": None,
         "signal_status": {"belief_confidence_mean": "no_observations"}},
        {"slow_cycle": 220, "belief_confidence_mean": 0.69,
         "signal_status": {"belief_confidence_mean": "measured"}},
        {"slow_cycle": 240, "belief_confidence_mean": 0.10,
         "signal_status": {"belief_confidence_mean": "measured"}},
    ]
    audit = _audit(tmp_path, pending, snapshots)

    audit._evaluate_matured(slow_cycle=220)

    assert len(audit._records) == 1
    result = audit._records[0]
    assert result.before == 0.55
    assert result.after_peak == 0.69
    assert result.after_stable == 0.67
    assert result.commit_cycle == 100
    assert result.verdict == "effective"


def test_evaluation_defers_when_post_commit_measurements_are_missing(tmp_path):
    pending = [{
        "parameter": "grounding_boost",
        "signal": "belief_confidence_mean",
        "before": 0.55,
        "baseline_source": "commit_snapshot",
        "commit_cycle": 100,
        "eval_at": 220,
    }]
    snapshots = [
        {"slow_cycle": 140, "belief_confidence_mean": None,
         "signal_status": {"belief_confidence_mean": "no_observations"}},
        {"slow_cycle": 180, "belief_confidence_mean": 0.70,
         "signal_status": {"belief_confidence_mean": "measured"}},
    ]
    audit = _audit(tmp_path, pending, snapshots)

    audit._evaluate_matured(slow_cycle=220)

    assert audit._records == []
    assert audit._pending == pending
