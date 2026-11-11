from types import SimpleNamespace
import threading

from cognition.autonomous_curiosity_resolver import AutonomousCuriosityResolver
from cognition.motivational_field import MotivationalField, MotivationalNeed


class _GoalEngine:
    def __init__(self, accept=True):
        self._goals = {}
        self.accept = accept
        self.add_calls = []

    def add_goal(self, goal):
        self.add_calls.append(goal)
        if not self.accept:
            return False
        self._goals[goal.id] = goal
        return True


def test_internal_need_is_not_marked_acted_when_goal_engine_rejects_it():
    goal_engine = _GoalEngine(accept=False)
    field = MotivationalField.__new__(MotivationalField)
    field._ai = SimpleNamespace(goal_engine=goal_engine)
    field._organism = SimpleNamespace()
    need = MotivationalNeed(
        need_type="concept_accumulation",
        description="resolve a repeated question",
        target="causal reasoning",
        urgency=0.7,
        cycle=20,
    )

    assert field._act_on_need(need, 20) is False
    assert need.acted_on is False
    assert len(goal_engine.add_calls) == 1
    assert goal_engine._goals == {}


def test_curiosity_resolver_only_reports_goal_promotion_after_commit():
    goal_engine = _GoalEngine(accept=False)
    resolver = AutonomousCuriosityResolver.__new__(AutonomousCuriosityResolver)

    assert resolver._create_goal(goal_engine, "a coherent curiosity topic", 0.8, 20) is False
    assert goal_engine._goals == {}


def test_motivational_field_reports_async_scan_and_prevents_overlap(monkeypatch):
    field = MotivationalField.__new__(MotivationalField)
    field._scan_state_lock = threading.Lock()
    field._need_scan_state = {
        "status": "idle", "cycle": 0, "need_count": 0,
        "acted_count": 0, "unacted_count": 0,
    }
    receipts = []
    field._organism = SimpleNamespace(
        _loop=SimpleNamespace(record_async_cycle_stage=lambda *args, **kwargs: receipts.append((args, kwargs)))
    )
    field._integrate_drives = lambda _cycle: None
    field._scan_needs = lambda _cycle: {
        "status": "completed", "need_count": 2,
        "acted_count": 1, "unacted_count": 1,
    }

    workers = []

    class _DeferredThread:
        def __init__(self, *, target, args, **_kwargs):
            self.target = target
            self.args = args

        def start(self):
            workers.append(self)

    monkeypatch.setattr("cognition.motivational_field.threading.Thread", _DeferredThread)
    first = field.tick(20)
    overlapping = field.tick(40)

    assert first["need_scan"] == "scheduled"
    assert overlapping["need_scan"] == "skipped_overlap"
    assert len(workers) == 1
    workers[0].target(*workers[0].args)
    status = field.need_scan_status()
    assert status["status"] == "completed"
    assert status["cycle"] == 20
    assert status["need_count"] == 2
    assert status["acted_count"] == 1
    assert status["unacted_count"] == 1
    assert isinstance(status["duration_ms"], float)
    assert receipts[0][0] == (20, "motivational_field.need_scan", "completed")
    assert receipts[0][1]["metrics"]["acted_count"] == 1
