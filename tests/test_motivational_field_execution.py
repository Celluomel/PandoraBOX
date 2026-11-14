from types import SimpleNamespace
import threading

from cognition.autonomous_curiosity_resolver import AutonomousCuriosityResolver
from cognition.motivational_field import FieldState, MotivationalField, MotivationalNeed


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
    field._integrate_drives = lambda _cycle: {"status": "completed", "drive_count": 8}
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

    assert first["drive_update"] == "completed"
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


def test_motivational_field_save_is_atomic_and_serialized(tmp_path):
    field = MotivationalField.__new__(MotivationalField)
    field._path = tmp_path / "motivational_field.json"
    field._lock = threading.Lock()
    field._save_lock = threading.Lock()
    field._state = FieldState()
    field.drive_vector = {"epistemic": 0.5}
    failures = []

    def writer(value):
        for _ in range(20):
            with field._lock:
                field.drive_vector = {"epistemic": value}
                field._state.drive_vector = dict(field.drive_vector)
            if not field._save():
                failures.append(value)

    workers = [threading.Thread(target=writer, args=(value,)) for value in (0.2, 0.8)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    persisted = __import__("json").loads(field._path.read_text(encoding="utf-8"))
    assert failures == []
    assert persisted["drive_vector"]["epistemic"] in {0.2, 0.8}
    assert list(tmp_path.glob("*.tmp")) == []


def _skill_stagnation_field(skill):
    field = MotivationalField.__new__(MotivationalField)
    field._lock = threading.Lock()
    field._state = FieldState()
    field._organism = SimpleNamespace(skill_registry=SimpleNamespace(_skills={
        skill.domain: skill,
    }))
    return field


def test_unverified_skill_exposures_do_not_create_stagnation_need():
    skill = SimpleNamespace(
        domain="quantum_mechanics_analogy", practice_count=12,
        verified_practices=0, depth=1,
    )
    field = _skill_stagnation_field(skill)

    assert field._detect_skill_stagnation(1) == []  # baseline
    assert field._detect_skill_stagnation(31) == []
    assert field._state.skill_verified_practice_snapshot == {
        "quantum_mechanics_analogy": 0,
    }


def test_verified_skill_can_create_stagnation_need_after_baseline():
    skill = SimpleNamespace(
        domain="technical_reasoning", practice_count=12,
        verified_practices=2, depth=1,
    )
    field = _skill_stagnation_field(skill)

    assert field._detect_skill_stagnation(1) == []  # baseline
    needs = field._detect_skill_stagnation(31)

    assert len(needs) == 1
    assert needs[0].need_type == "skill_stagnation"
    assert needs[0].target == "technical_reasoning"
