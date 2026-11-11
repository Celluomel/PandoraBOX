import ast
import json
from pathlib import Path
from types import SimpleNamespace

from cognition.goal_engine import GoalEngine
from cognition.goal_action_executor import GoalActionExecutor
from cognition.simple_thought_evaluator import SimpleThoughtEvaluator
from cognition.thought_stream import Thought
from cognition.workspace_competition import WorkspaceCompetition
from core.data.access import DataAccess


def test_selected_thought_proposal_is_persisted_with_source_evidence(tmp_path):
    persistence_file = tmp_path / "goals.json"
    engine = GoalEngine(SimpleNamespace(), persistence_file=str(persistence_file))
    proposal = {
        "type": "tension",
        "goal_type": "test_hypothesis",
        "concept": "cognitive_execution_flow",
        "priority": 0.82,
        "origin_thought": "thought-42",
        "origin_thought_source": "cognitive_loop",
        "origin_thought_type": "tension_awareness",
        "origin_thought_timestamp": "2026-11-11T20:00:00Z",
        "concept_source": "structured_topic",
        "hypothesis": "If the selected goal is routed directly, action selection will preserve focus.",
    }

    result = engine.commit_selected_thought_proposal(proposal, cycle=12)

    assert result["created"] is True
    assert result["verified"] is True
    assert result["source_thought_id"] == "thought-42"
    persisted = json.loads(persistence_file.read_text(encoding="utf-8"))
    goal = persisted["goals"][result["id"]]
    assert goal["topic"] == "cognitive execution flow"
    assert goal["source_thought_id"] == "thought-42"
    assert goal["source_thought_source"] == "cognitive_loop"
    assert goal["source_thought_type"] == "tension_awareness"
    assert goal["source_thought_timestamp"] == "2026-11-11T20:00:00Z"
    assert goal["source_concept_method"] == "structured_topic"
    assert goal["desired_effect"] == proposal["hypothesis"]


def test_rejected_proposal_does_not_become_a_persisted_goal(tmp_path):
    persistence_file = tmp_path / "goals.json"
    engine = GoalEngine(SimpleNamespace(), persistence_file=str(persistence_file))

    result = engine.commit_selected_thought_proposal(
        {"concept": "module", "origin_thought": "noise-1"}, cycle=2
    )

    assert result["created"] is False
    assert result["verified"] is False
    assert not persistence_file.exists()


def test_high_priority_tension_defers_llm_synthesis_until_selected(tmp_path):
    evaluator = SimpleThoughtEvaluator(tmp_path)
    evaluator._classify_thought = lambda _text, _thought: "tension"
    evaluator._extract_concept = lambda _text: "cognitive execution flow"
    evaluator._compute_priority = lambda _text, _kind: 0.8
    evaluator._compute_actionability = lambda _text, _kind: 0.8
    evaluator._identify_friction = lambda _text, _kind: "execution evidence"
    evaluator._determine_goal_type = lambda _kind: "resolve_tension"
    evaluator._generate_hypothesis = lambda *_args: (_ for _ in ()).throw(
        AssertionError("hypothesis synthesis must not run during bulk scoring")
    )

    result = evaluator._evaluate_thought({"content": "a contradiction needs analysis"})

    assert result["hypothesis_pending"] is True
    assert result["goal_type"] == "test_hypothesis"


def test_thought_evaluator_prefers_existing_structured_topic():
    evaluator = SimpleThoughtEvaluator(Path("."))
    evaluator._compute_priority = lambda *_args: 0.7
    evaluator._compute_actionability = lambda *_args: 0.6
    evaluator._identify_friction = lambda *_args: "test"
    evaluator._determine_goal_type = lambda *_args: "learn"

    result = evaluator._evaluate_thought({
        "content": "I wonder why this generic generated sentence exists",
        "topic": "cognitive_execution_flow",
    })

    assert result["concept"] == "cognitive execution flow"
    assert result["concept_source"] == "structured_topic"


def test_structured_thought_reaches_persisted_workspace_goal_end_to_end(tmp_path):
    """Prove topic/provenance survive the real store, evaluator, and goal consumer."""
    persona_dir = tmp_path / "persona"
    persona_dir.mkdir()
    dal = DataAccess(str(persona_dir))
    source = Thought(
        content="A recurring contradiction needs a concrete test.",
        source="cognitive_loop",
        priority=0.91,
        thought_type="tension_awareness",
        timestamp=1794427200.0,
        topic="cognitive_execution_flow",
    )
    assert dal.add_thought({"id": "thought-e2e-1", **source.to_dict()}) is True

    evaluator = SimpleThoughtEvaluator(persona_dir)
    evaluator._classify_thought = lambda *_args: "tension"
    evaluator._compute_priority = lambda *_args: 0.82
    evaluator._compute_actionability = lambda *_args: 0.8
    evaluator._identify_friction = lambda *_args: "unresolved execution evidence"
    evaluator._determine_goal_type = lambda *_args: "resolve_tension"
    evaluator._inject_followup_thoughts = lambda *_args: None

    proposals = evaluator.evaluate_recent_thoughts()
    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal["concept"] == "cognitive execution flow"
    assert proposal["concept_source"] == "structured_topic"
    assert proposal["origin_thought"] == "thought-e2e-1"

    proposal_candidate = {
        "id": f"goal-proposal:{proposal['origin_thought']}",
        "source": "simple_thought_evaluator",
        "thought_type": "goal_proposal",
        "topic": proposal["concept"],
        "content": proposal["concept"],
        "priority": proposal["priority"],
        "actionability": proposal["actionability"],
        "_goal_proposal": proposal,
    }
    competition = WorkspaceCompetition(str(persona_dir)).compete(
        goals=[],
        thoughts=[proposal_candidate],
        tensions={},
        pressure={"curiosity_drive": 0.5, "total": 0.0},
        context={},
    )
    selected = competition["winner"]["source_data"].get("_goal_proposal")
    assert competition["winner"]["id"] == proposal_candidate["id"]
    assert selected == proposal

    goals_file = persona_dir / "goals.json"
    engine = GoalEngine(SimpleNamespace(), persistence_file=str(goals_file))
    committed = engine.commit_selected_thought_proposal(selected, cycle=21)
    assert committed["created"] is True
    assert committed["verified"] is True

    workspace_candidates = engine.get_goal_thoughts()
    assert any(
        item["goal_id"] == committed["id"]
        and item["topic"] == "cognitive execution flow"
        and item["source"] == "goal_engine"
        for item in workspace_candidates
    )


def test_authoritative_non_goal_decision_does_not_fall_back_to_old_goal():
    class _GoalEngine:
        def get_active_goals(self, min_activation):
            return [SimpleNamespace(id="older-goal", topic="old focus")]

    executor = GoalActionExecutor.__new__(GoalActionExecutor)
    executor._get_goal_engine = lambda: _GoalEngine()
    executor._select_eligible_goal = lambda _active: (_ for _ in ()).throw(
        AssertionError("must not select an unrelated fallback goal")
    )

    result = executor.run_tick(selection_is_authoritative=True)

    assert result is None


def test_internal_loop_uses_one_proposal_evaluation_path_and_authoritative_winner():
    source_path = Path(__file__).resolve().parents[1] / "core" / "internal_loop.py"
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    internal_loop = next(
        node for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "InternalThoughtLoop"
    )
    slow_cycle = next(
        node for node in internal_loop.body
        if isinstance(node, ast.FunctionDef) and node.name == "_slow_cycle_impl"
    )

    evaluator_calls = [
        node for node in ast.walk(slow_cycle)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "evaluate_thoughts_and_create_goals"
    ]
    executor_calls = [
        node for node in ast.walk(slow_cycle)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run_tick"
        and any(
            keyword.arg == "selection_is_authoritative"
            for keyword in node.keywords
        )
    ]

    assert evaluator_calls == [], "Phase1 owns proposal evaluation; no second independent loop may consume thoughts"
    assert len(executor_calls) == 1, "the executor must receive arbitration authority explicitly"
