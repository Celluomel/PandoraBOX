import json

from cognition.goal_engine import GoalEngine
from cognition.thought_goal_linker import ThoughtGoalLinker


def test_phase_two_thought_goal_creation_uses_goal_engine_and_persists_source(tmp_path):
    persistence = tmp_path / "goals.json"
    engine = GoalEngine(None, persistence_file=str(persistence))
    linker = ThoughtGoalLinker(str(tmp_path), goal_engine=engine)
    linker._load_goals = lambda: []
    linker._find_similar_goal = lambda _thought, _goals: None
    linker._merge_similar_goals = lambda _goals: []

    result = linker.process_thought_evaluation({
        "type": "reflection",
        "concepts": ["cognitive pipeline"],
        "priority": 0.72,
        "urgency": 0.6,
        "actionability": 0.9,
        "origin_thought_id": "phase2-thought-9",
    })

    assert len(result["created_goals"]) == 1
    goal_id = result["created_goals"][0]
    goal = json.loads(persistence.read_text(encoding="utf-8"))["goals"][goal_id]
    assert goal["origin"] == "thought_goal_linker"
    assert goal["source_thought_id"] == "phase2-thought-9"
    assert goal["source_thought_type"] == "reflection"
    assert goal["source_concept_method"] == "advanced_thought_evaluator"
