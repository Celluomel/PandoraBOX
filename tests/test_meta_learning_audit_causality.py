from types import SimpleNamespace
from unittest.mock import patch

from cognition.meta_learning_audit import (
    META_WINDOW, MetaLearningAudit, ParameterEffectiveness,
)


def _audit(tmp_path, pending, snapshots):
    cae = SimpleNamespace(_state=SimpleNamespace(snapshot_log=snapshots, trial_log=[]))
    loop = SimpleNamespace(_cognitive_audit=cae)
    organism = SimpleNamespace(_loop=loop)
    audit = MetaLearningAudit(organism, ai_system=None, path=str(tmp_path / "meta.json"))
    audit._pending = pending
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


def test_matured_commit_is_not_registered_for_evaluation_twice(tmp_path):
    audit = _audit(tmp_path, [], [])
    trial = {
        "outcome": "confirmed",
        "committed": True,
        "parameter": "grounding_boost",
        "dimension": "belief_confidence_mean",
        "proposed_at_cycle": 40,
        "evaluated_at_cycle": 100,
        "signal_at_eval": 0.56,
    }
    audit._organism._loop._cognitive_audit._state.trial_log = [trial]
    audit._records.append(ParameterEffectiveness(
        parameter="grounding_boost", signal="belief_confidence_mean",
        before=0.56, after_peak=0.70, after_stable=0.68,
        verdict="effective", commit_cycle=100,
    ))

    audit._register_new_commits(slow_cycle=400)

    assert audit._pending == []


def test_save_failure_is_reported_and_preserves_existing_state_file(tmp_path):
    path = tmp_path / "meta.json"
    path.write_text('{"records": [], "pending": []}', encoding="utf-8")
    audit = _audit(tmp_path, [], [])
    audit._path = path

    with patch("cognition.meta_learning_audit.os.replace", side_effect=OSError("disk full")):
        assert audit._save() is False

    assert path.read_text(encoding="utf-8") == '{"records": [], "pending": []}'
    assert list(tmp_path.glob(".meta.json.*.tmp")) == []


def test_worker_receipt_reports_persistence_failure(tmp_path):
    audit = _audit(tmp_path, [], [])
    receipts = []
    audit._save = lambda: False
    audit._record_async_completion = lambda cycle, status, output, **kwargs: receipts.append(
        (cycle, status, output)
    )

    audit._run_guarded(50)

    assert receipts[0][1] == "failed"
    assert receipts[0][2]["reason_code"] == "state_persistence_failed"
    assert audit._worker_pending is False
