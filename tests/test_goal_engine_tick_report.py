from threading import RLock
from types import SimpleNamespace

from cognition.goal_engine import GoalEngine


def make_engine(identity_getter=None):
    engine = GoalEngine.__new__(GoalEngine)
    engine._tick_report_lock = RLock()
    engine._last_tick_report = {"status": "not_run", "tick_at": None}
    engine._last_tick_time = 0.0
    engine._retire_invalid_active_goals = lambda: None
    engine.ai_system = SimpleNamespace(
        identity_system=SimpleNamespace(get_identity=identity_getter or (lambda: {})),
        _organism=None,
    )
    engine.get_current_pressures = lambda: {}
    engine.derive_motivations = lambda _identity, _pressures: [
        SimpleNamespace(name="understand_user")
    ]
    engine._goals = {}
    engine._topic_quality_cache = {}
    engine._lock = RLock()
    engine.generate_candidates = lambda _motivations, _topics, limit: []
    engine.add_goal = lambda _goal: False
    engine.update_goals = lambda _pressures: None
    engine.get_metrics = lambda: {"active": 1, "total_goals": 2, "gei": 0.5}
    return engine


def test_goal_engine_reports_completed_tick_with_counts_only():
    engine = make_engine()
    engine.tick()

    report = engine.get_last_tick_report()
    assert report["status"] == "completed"
    assert report["motivation_count"] == 1
    assert report["candidate_count"] == 0
    assert report["active_goal_count"] == 1
    assert "topic" not in report


def test_goal_engine_reports_internal_exception_instead_of_normal_return():
    engine = make_engine(lambda: (_ for _ in ()).throw(ValueError("private detail")))
    engine.tick()

    report = engine.get_last_tick_report()
    assert report["status"] == "failed"
    assert report["error_type"] == "ValueError"
    assert "private detail" not in repr(report)


def test_goal_engine_reports_cooldown_as_skip_not_completion():
    import time

    engine = make_engine()
    engine._last_tick_time = time.time()
    engine.tick()

    report = engine.get_last_tick_report()
    assert report["status"] == "skipped_cooldown"
    assert report["cooldown_remaining_seconds"] > 0
