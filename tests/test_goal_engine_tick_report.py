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
            "après chaque": SimpleNamespace(
                topic="après chaque", curiosity=0.8, source="contradiction",
                source_history=["contradiction"], source_history_complete=True,
            ),
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
    def score_topics(topics):
        return {
            topic: ((0.40, 0.50, False) if topic == "après chaque"
                    else (0.70, 0.30, True))
            for topic in topics
        }

    with patch("cognition.goal_semantics.batch_topic_quality", side_effect=score_topics):
        engine.tick()

    assert "après chaque" not in offered_topics
    assert "relational understanding" in offered_topics
    report = engine.get_last_tick_report()
    assert report["topic_quality"]["curiosity"] == {
        "candidate_count": 1,
        "accepted_count": 0,
        "rejected_count": 1,
        "unscored_count": 0,
        "user_origin_suppressed_count": 0,
        "provenance_unverified_suppressed_count": 0,
    }
    assert report["topic_quality"]["embedding_status"] == "available"


def test_curiosity_topics_are_deferred_when_semantic_quality_is_unavailable():
    curiosity = SimpleNamespace(
        top_topic=lambda: "unverified conversation fragment",
        _lock=RLock(),
        _topics={
            "unverified conversation fragment": SimpleNamespace(
                topic="unverified conversation fragment", curiosity=0.8,
                source="contradiction", source_history=["contradiction"],
                source_history_complete=True,
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
    assert "relational understanding" not in offered_topics
    report = engine.get_last_tick_report()
    assert report["topic_quality"]["curiosity"]["accepted_count"] == 0
    assert report["topic_quality"]["embedding_status"] == "deferred"
    assert report["topic_quality"]["autonomous"]["unscored_count"] > 0


def test_curiosity_fallback_does_not_repromote_a_conversation_source():
    curiosity = SimpleNamespace(
        top_topic=lambda: "camera calibration",
        _lock=RLock(),
        _topics={
            "camera calibration": SimpleNamespace(
                topic="camera calibration", curiosity=0.9, source="user_semantic",
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

    with patch("cognition.goal_semantics.batch_topic_quality", return_value={}):
        engine.tick()

    assert "camera calibration" not in offered_topics
    report = engine.get_last_tick_report()
    assert report["topic_quality"]["curiosity"]["user_origin_suppressed_count"] == 1


def test_curiosity_latest_internal_stimulus_cannot_erase_user_source_lineage():
    curiosity = SimpleNamespace(
        top_topic=lambda: "camera calibration",
        _lock=RLock(),
        _topics={
            "camera calibration": SimpleNamespace(
                topic="camera calibration", curiosity=0.9,
                source="goal_exploration",
                source_history=["user_semantic", "goal_exploration"],
                source_history_complete=True,
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

    with patch("cognition.goal_semantics.batch_topic_quality", return_value={}):
        engine.tick()

    assert "camera calibration" not in offered_topics
    report = engine.get_last_tick_report()
    assert report["topic_quality"]["curiosity"]["user_origin_suppressed_count"] == 1


def test_curiosity_fallback_rejects_legacy_latest_internal_source_without_lineage():
    curiosity = SimpleNamespace(
        top_topic=lambda: "robot locomotion",
        _lock=RLock(),
        _topics={
            "robot locomotion": SimpleNamespace(
                topic="robot locomotion", curiosity=0.9,
                source="goal_exploration",
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

    with patch("cognition.goal_semantics.batch_topic_quality", return_value={}):
        engine.tick()

    assert "robot locomotion" not in offered_topics
    report = engine.get_last_tick_report()
    assert report["topic_quality"]["curiosity"]["provenance_unverified_suppressed_count"] == 1


def test_goal_engine_carries_explicit_topic_turn_provenance_into_candidates():
    semantic_memory = SimpleNamespace(
        recent_user_topic_evidence=lambda **_kwargs: [{
            "topic": "cognitive architecture",
            "turn_ids": ["turn-a", "turn-b"],
        }],
    )
    engine = make_engine()
    engine.ai_system._organism = SimpleNamespace(
        semantic_memory=semantic_memory,
        curiosity=None,
    )
    captured = {}

    def capture_candidates(_motivations, topics, limit, topic_source_turns=None):
        captured["topics"] = list(topics)
        captured["topic_source_turns"] = topic_source_turns
        return []

    engine.generate_candidates = capture_candidates
    with patch(
        "cognition.goal_semantics.batch_topic_quality",
        side_effect=lambda topics: {
            topic: (0.70, 0.30, True) for topic in topics
        },
    ):
        engine.tick()

    assert "cognitive architecture" in captured["topics"]
    assert captured["topic_source_turns"]["cognitive architecture"] == [
        "turn-a", "turn-b",
    ]


def test_semantically_admitted_topic_is_not_removed_by_word_length_or_token_rules():
    engine = make_engine()
    engine.ai_system._organism = SimpleNamespace(
        semantic_memory=SimpleNamespace(
            recent_user_topics=lambda **_kwargs: ["AI reasoning"]
        ),
        curiosity=None,
    )
    offered_topics = []
    engine.generate_candidates = lambda _motivations, topics, limit: offered_topics.extend(topics) or []

    with patch(
        "cognition.goal_semantics.batch_topic_quality",
        side_effect=lambda topics: {
            topic: (0.70, 0.30, True) for topic in topics
        },
    ):
        engine.tick()

    assert "AI reasoning" in offered_topics
    report = engine.get_last_tick_report()
    assert report["topic_quality"]["semantic_memory"]["accepted_count"] == 1
    assert report["filtered_topic_count"] >= 1
