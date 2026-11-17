from threading import RLock
from types import SimpleNamespace
from unittest.mock import patch

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


def test_goal_engine_counts_only_successful_persistent_admissions():
    engine = make_engine()
    engine.generate_candidates = lambda _motivations, _topics, limit: [
        SimpleNamespace(id="saved"), SimpleNamespace(id="rejected")
    ]
    engine.add_goal = lambda goal: goal.id == "saved"
    engine.tick()

    report = engine.get_last_tick_report()
    assert report["candidate_count"] == 2
    assert report["accepted_candidate_count"] == 1


def test_curiosity_topic_fallback_uses_the_same_semantic_admission_gate():
    curiosity = SimpleNamespace(
        top_topic=lambda: "après chaque",
        _lock=RLock(),
        _topics={
            "après chaque": SimpleNamespace(topic="après chaque", curiosity=0.8),
        },
    )
    semantic_memory = SimpleNamespace(recent_user_topics=lambda **_kwargs: [])
    engine = make_engine()
    engine.ai_system._organism = SimpleNamespace(
        semantic_memory=semantic_memory,
        curiosity=curiosity,
    )
    offered_topics = []
    engine.generate_candidates = lambda _motivations, topics, limit: offered_topics.extend(topics) or []

    # The quality gate's false verdict must apply to curiosity fallback topics,
    # not only to topics returned by SemanticMemory.
    with patch(
        "cognition.goal_semantics.batch_topic_quality",
        return_value={"après chaque": (0.40, 0.50, False)},
    ):
        engine.tick()

    assert "après chaque" not in offered_topics
    assert "relational understanding" in offered_topics
    report = engine.get_last_tick_report()
    assert report["topic_quality"]["curiosity"] == {
        "candidate_count": 1,
        "accepted_count": 0,
    }
    assert report["topic_quality"]["embedding_status"] == "available"


def test_curiosity_topics_are_deferred_when_semantic_quality_is_unavailable():
    curiosity = SimpleNamespace(
        top_topic=lambda: "unverified conversation fragment",
        _lock=RLock(),
        _topics={
            "unverified conversation fragment": SimpleNamespace(
                topic="unverified conversation fragment", curiosity=0.8,
            ),
        },
    )
    engine = make_engine()
    engine.ai_system._organism = SimpleNamespace(
        semantic_memory=SimpleNamespace(recent_user_topics=lambda **_kwargs: []),
        curiosity=curiosity,
    )
    offered_topics = []
    engine.generate_candidates = lambda _motivations, topics, limit: offered_topics.extend(topics) or []

    with patch("cognition.goal_semantics.batch_topic_quality", return_value=None):
        engine.tick()

    assert "unverified conversation fragment" not in offered_topics
    assert "relational understanding" in offered_topics
    report = engine.get_last_tick_report()
    assert report["topic_quality"]["curiosity"]["accepted_count"] == 0
    assert report["topic_quality"]["embedding_status"] == "deferred"
