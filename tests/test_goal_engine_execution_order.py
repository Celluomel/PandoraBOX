"""Regression coverage for GoalEngine's position in the slow-cycle pipeline."""

import ast
import time
from pathlib import Path

from cognition.goal_engine import Goal, GoalEngine


def test_goal_engine_runs_once_after_current_cycle_pressure_is_published():
    source_path = Path(__file__).resolve().parents[1] / "core" / "internal_loop.py"
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    internal_loop = next(
        node for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "InternalThoughtLoop"
    )
    slow_cycle = next(
        node for node in internal_loop.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_slow_cycle_impl"
    )

    goal_ticks = [
        node for node in ast.walk(slow_cycle)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "tick"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "_ge"
    ]
    pressure_publications = [
        node for node in ast.walk(slow_cycle)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "o"
            and target.attr == "_v32_decision_pressure"
            for target in node.targets
        )
    ]

    assert len(goal_ticks) == 1, "GoalEngine must not consume the same cycle twice"
    assert len(pressure_publications) == 1
    assert goal_ticks[0].lineno > pressure_publications[0].lineno, (
        "GoalEngine must run after the current cycle's pressure result is stored"
    )


def test_startup_migration_retires_interaction_echo_social_goals():
    engine = GoalEngine.__new__(GoalEngine)
    engine._goals = {
        "echo": Goal(
            id="echo", topic="Still thinking about: [curiosity] during interaction: test",
            origin="goal_quality_filter", priority=0.6, energy=0.5,
            created_cycle=1, last_active=1, tension_source="social_drive",
        ),
        "explicit": Goal(
            id="explicit", topic="Understand how memory retrieval affects audit continuity",
            origin="goal_quality_filter", priority=0.6, energy=0.5,
            created_cycle=1, last_active=1, tension_source="social_drive",
        ),
        "other-origin": Goal(
            id="other-origin", topic="Still thinking about: [curiosity] during interaction: test",
            origin="thought_evaluation", priority=0.6, energy=0.5,
            created_cycle=1, last_active=1, tension_source="social_drive",
        ),
    }
    engine._recently_abandoned = {}
    saves = []
    engine._save_goals = lambda: saves.append(True) or True

    retired = engine._retire_interaction_echo_goals()

    assert retired == 1
    assert engine._goals["echo"].status == "abandoned"
    assert engine._goals["explicit"].status == "active"
    assert engine._goals["other-origin"].status == "active"
    assert saves == [True]
    assert engine._recently_abandoned[engine._goals["echo"].topic.casefold()] <= time.time()
