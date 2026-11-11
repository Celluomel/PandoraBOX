import json
from types import SimpleNamespace

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
