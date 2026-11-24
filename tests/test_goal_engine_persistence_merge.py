import json
from types import SimpleNamespace
from unittest.mock import patch

from cognition.goal_engine import Goal, GoalEngine
from cognition.goal_quality_filter import GoalQualityFilter


def test_goal_engine_write_preserves_dal_quality_and_archived_records(tmp_path):
    path = tmp_path / "goals.json"
    existing_live = Goal(
        id="live-1", topic="understand cognitive cycles", origin="manual",
        priority=0.6, energy=0.6, created_cycle=3, last_active=3,
    )
    archived = {
        "id": "archived-1", "name": "old noisy goal", "topic": "old noisy goal",
        "origin": "goal_quality_filter", "priority": 0.2, "energy": 0.1,
        "created_cycle": 1, "last_active": 1, "status": "low_quality",
        "quality_score": 0.0, "low_quality_reason": "quality gate",
    }
    live_record = {
        **existing_live.__dict__, "quality_score": 0.82,
        "quality_reasons": ["embedding alignment"],
    }
    path.write_text(json.dumps({
        "cycle_counter": 3,
        "goals": {"live-1": live_record, "archived-1": archived},
    }), encoding="utf-8")

    engine = GoalEngine(None, persistence_file=str(path))
    admitted = Goal(
        id="new-1", topic="investigate cognitive pipeline persistence",
        origin="test", priority=0.7, energy=0.7, created_cycle=4, last_active=4,
    )
    assert engine.add_goal(admitted)

    persisted = json.loads(path.read_text(encoding="utf-8"))["goals"]
    assert persisted["archived-1"]["status"] == "low_quality"
    assert persisted["archived-1"]["quality_score"] == 0.0
    assert persisted["live-1"]["quality_score"] == 0.82
    assert persisted["live-1"]["quality_reasons"] == ["embedding alignment"]
    assert "new-1" in persisted


def test_goal_engine_explicit_recycle_removes_only_the_selected_record(tmp_path):
    path = tmp_path / "goals.json"
    recyclable = Goal(
        id="old-1", topic="retired cognitive question", origin="test",
        priority=0.2, energy=0.1, created_cycle=1, last_active=1,
        status="dormant",
    )
    archived = {
        "id": "archived-1", "name": "archived record", "topic": "archived record",
        "origin": "goal_quality_filter", "priority": 0.2, "energy": 0.1,
        "created_cycle": 1, "last_active": 1, "status": "low_quality",
        "quality_score": 0.0,
    }
    path.write_text(json.dumps({
        "cycle_counter": 1,
        "goals": {"old-1": recyclable.__dict__, "archived-1": archived},
    }), encoding="utf-8")

    engine = GoalEngine(None, persistence_file=str(path))
    engine.MAX_TOTAL_GOALS = 1
    duplicate = Goal(
        id="duplicate-1", topic="retired cognitive question", origin="test",
        priority=0.5, energy=0.5, created_cycle=2, last_active=2,
    )
    assert not engine.add_goal(duplicate)
    assert "old-1" in json.loads(path.read_text(encoding="utf-8"))["goals"]

    candidate = Goal(
        id="new-1", topic="investigate cognitive pipeline persistence",
        origin="test", priority=0.7, energy=0.7, created_cycle=2, last_active=2,
    )
    assert engine.add_goal(candidate)

    persisted = json.loads(path.read_text(encoding="utf-8"))["goals"]
    assert "old-1" not in persisted
    assert "new-1" in persisted
    assert persisted["archived-1"]["quality_score"] == 0.0


def test_archived_and_merged_history_does_not_exhaust_live_goal_capacity(tmp_path):
    path = tmp_path / "goals.json"
    history = {
        "archived-1": {
            "id": "archived-1", "name": "historical archived goal",
            "topic": "historical archived goal", "quality_score": 0.73,
            "status": "archived", "origin": "test", "priority": 0.2,
            "energy": 0.1, "created_cycle": 1, "last_active": 1,
        },
        "merged-1": {
            "id": "merged-1", "topic": "historical merged goal",
            "status": "merged", "origin": "test", "priority": 0.2,
            "energy": 0.1, "created_cycle": 1, "last_active": 1,
        },
    }
    path.write_text(json.dumps({"cycle_counter": 1, "goals": history}), encoding="utf-8")

    engine = GoalEngine(None, persistence_file=str(path))
    engine.MAX_TOTAL_GOALS = 1
    assert engine.get_metrics()["total_goals"] == 0
    assert engine.get_goal_by_id("archived-1").status == "archived"
    assert engine.get_goal_by_id("merged-1").status == "merged"

    candidate = Goal(
        id="new-1", topic="investigate current cognitive pipeline",
        origin="test", priority=0.7, energy=0.7, created_cycle=2, last_active=2,
    )
    assert engine.add_goal(candidate)

    persisted = json.loads(path.read_text(encoding="utf-8"))["goals"]
    assert persisted["archived-1"] == history["archived-1"]
    assert persisted["merged-1"] == history["merged-1"]
    assert "new-1" in persisted


def test_tick_admits_persists_and_activates_goal_with_terminal_history_present(tmp_path):
    path = tmp_path / "goals.json"
    history = {
        f"archived-{index}": {
            "id": f"archived-{index}", "topic": f"old archived goal {index}",
            "origin": "test", "priority": 0.2, "energy": 0.1,
            "created_cycle": 1, "last_active": 1, "status": "archived",
        }
        for index in range(21)
    }
    history.update({
        f"merged-{index}": {
            "id": f"merged-{index}", "topic": f"old merged goal {index}",
            "origin": "test", "priority": 0.2, "energy": 0.1,
            "created_cycle": 1, "last_active": 1, "status": "merged",
        }
        for index in range(4)
    })
    path.write_text(json.dumps({"cycle_counter": 1, "goals": history}), encoding="utf-8")

    engine = GoalEngine(
        SimpleNamespace(
            identity_system=SimpleNamespace(get_identity=lambda: {}),
            _organism=SimpleNamespace(
                semantic_memory=SimpleNamespace(recent_user_topics=lambda **_kwargs: []),
                curiosity=None,
            ),
        ),
        persistence_file=str(path),
    )
    engine.derive_motivations = lambda _identity, _pressures: [
        SimpleNamespace(name="understand_user", strength=0.8, origin="test")
    ]
    engine.get_current_pressures = lambda: {}

    with patch(
        "cognition.goal_semantics.batch_topic_quality",
        side_effect=lambda topics: {
            topic: (0.8, 0.2, True) for topic in topics
        },
    ):
        engine.tick()

    report = engine.get_last_tick_report()
    assert report["candidate_count"] == 3
    assert report["accepted_candidate_count"] == 3
    assert report["active_goal_count"] == 3
    assert report["total_goal_count"] == 3
    assert engine.get_goal_by_id("archived-0").status == "archived"

    persisted = json.loads(path.read_text(encoding="utf-8"))["goals"]
    assert persisted["archived-0"] == history["archived-0"]
    assert persisted["merged-0"] == history["merged-0"]
    live_ids = set(persisted) - set(history)
    assert len(live_ids) == 3
    assert all(persisted[goal_id]["status"] == "active" for goal_id in live_ids)


def test_quality_filter_submits_new_tension_goal_through_goal_engine(tmp_path):
    submissions = []

    class _Dal:
        def get_goals(self):
            return []

        def save_goal(self, _goal):
            raise AssertionError("new goal bypassed GoalEngine admission")

    filter_ = GoalQualityFilter(str(tmp_path))
    generated = filter_._generate_tension_goals(
        {"curiosity_drive": 0.9}, [], _Dal(),
        goal_engine=SimpleNamespace(add_goal=lambda goal: submissions.append(goal) or True),
    )

    assert len(generated) == 1
    assert len(submissions) == 1
    assert isinstance(submissions[0], Goal)
    assert submissions[0].origin == "goal_quality_filter"
    assert submissions[0].tension_source == "curiosity_drive"
    assert submissions[0].source_concept_method == (
        "cognition.tension_topics.generate_curiosity_topic"
    )
    assert generated[0]["source_concept_method"] == submissions[0].source_concept_method
    assert submissions[0].source_concept_kind in {"state_record", "unresolved"}
    assert generated[0]["source_concept_kind"] == submissions[0].source_concept_kind


def test_tension_source_receipt_survives_goal_engine_persistence(tmp_path):
    path = tmp_path / "goals.json"
    engine = GoalEngine(None, persistence_file=str(path))
    goal = Goal(
        id="provenance-1", topic="How does memory consolidation work?",
        origin="goal_quality_filter", priority=0.7, energy=0.7,
        created_cycle=3, last_active=3, tension_source="curiosity_drive",
        source_concept_method="cognition.tension_topics.generate_curiosity_topic",
        source_concept_kind="state_record",
        source_concept_ref="curiosity.json#/topics/memory consolidation",
        source_concept_sha256="a" * 64,
    )

    assert engine.add_goal(goal)
    saved = json.loads(path.read_text(encoding="utf-8"))["goals"][goal.id]
    restored = GoalEngine(None, persistence_file=str(path)).get_goal_by_id(goal.id)

    assert saved["source_concept_kind"] == "state_record"
    assert saved["source_concept_ref"] == "curiosity.json#/topics/memory consolidation"
    assert saved["source_concept_sha256"] == "a" * 64
    assert restored.source_concept_ref == goal.source_concept_ref
    assert restored.source_concept_sha256 == goal.source_concept_sha256
