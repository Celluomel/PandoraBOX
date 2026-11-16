from pathlib import Path
from types import SimpleNamespace

from cognition.cognitive_restructuring_engine import CognitiveRestructuringEngine
from cognition.decision_commitment import DecisionCommitmentLayer


def test_restructuring_tick_reports_cadence_and_persisted_work(tmp_path, monkeypatch):
    engine = CognitiveRestructuringEngine(None, str(Path(tmp_path) / "restructure.json"))
    not_due = engine.tick(11)
    assert not_due["outcome_status"] == "skipped"
    assert not_due["reason_code"] == "cadence_not_due"

    signals = [
        {"source": "correction", "text": "correction signal", "strength": 0.8},
        {"source": "tension", "text": "tension signal", "strength": 0.7},
    ]
    cluster = {"label": "test", "signals": signals, "strength": 0.8}
    monkeypatch.setattr(engine, "_collect_signals", lambda: signals)
    monkeypatch.setattr(engine, "_cluster", lambda _signals: [cluster])
    monkeypatch.setattr(engine, "_make_plan", lambda _cluster, cycle: {"cycle": cycle})
    monkeypatch.setattr(engine, "_broadcast", lambda _plan: None)

    receipt = engine.tick(15)

    assert receipt == {
        "outcome_status": "completed",
        "reason_code": "plan_created",
        "cycle": 15,
        "signal_count": 2,
        "cluster_count": 1,
        "plan_created": True,
        "active_plan_exists": True,
        "persisted": True,
    }
    assert (Path(tmp_path) / "restructure.json").exists()


def test_commitment_tick_receipt_distinguishes_commit_from_checkpoint(tmp_path):
    layer = DecisionCommitmentLayer.__new__(DecisionCommitmentLayer)
    layer._o = SimpleNamespace(energy=None)
    layer._path = Path(tmp_path) / "commitments.json"
    import threading
    layer._lock = threading.Lock()
    layer._history = []
    layer._last_penalty = {}
    layer._cycle = 0

    receipt = layer.tick({"name": "curiosity_learn", "type": "thought", "score": 0.7}, 11)

    assert receipt["outcome_status"] == "committed"
    assert receipt["reason_code"] == "commitment_added"
    assert receipt["history_count"] == 1
    assert receipt["persistence_status"] == "deferred_by_checkpoint"
    assert not layer._path.exists()

