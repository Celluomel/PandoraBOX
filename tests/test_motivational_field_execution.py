from types import SimpleNamespace

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
