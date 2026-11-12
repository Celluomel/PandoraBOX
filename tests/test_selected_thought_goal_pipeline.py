import ast
import json
from pathlib import Path
from types import SimpleNamespace

from cognition.goal_engine import GoalEngine
from cognition.goal_action_executor import GoalActionExecutor
from cognition.cognitive_preprocessor import CognitivePreProcessor
from cognition.simple_thought_evaluator import SimpleThoughtEvaluator
from cognition.thought_stream import Thought
from cognition.workspace_competition import WorkspaceCompetition
from core.phase1_integration import Phase1Orchestrator
from core.data.access import DataAccess
from core.internal_loop import InternalThoughtLoop


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


def test_unadmissible_proposal_is_removed_before_workspace_competition(tmp_path):
    engine = GoalEngine(SimpleNamespace(), persistence_file=str(tmp_path / "goals.json"))
    engine.thought_proposal_rejection_reason = lambda topic: (
        "low_quality_topic" if topic == "notice pull toward" else None
    )
    phase1 = Phase1Orchestrator.__new__(Phase1Orchestrator)
    phase1.goal_engine = engine
    proposals = [
        {"concept": "notice_pull_toward", "origin_thought": "noise"},
        {"concept": "grounded perception", "origin_thought": "useful"},
    ]

    admitted, rejected = phase1._admit_goal_proposals(proposals)

    assert admitted == [proposals[1]]
    assert rejected == [{
        "topic_ref": "notice pull toward",
        "reason": "low_quality_topic",
        "origin_thought_ref": "noise",
    }]


def test_goal_proposal_gate_matches_quality_and_lexical_admission(tmp_path):
    engine = GoalEngine(SimpleNamespace(), persistence_file=str(tmp_path / "goals.json"))
    engine._is_external_task_topic = lambda _topic: False
    engine._is_valid_goal_topic = lambda topic: topic == "grounded perception"

    assert engine.thought_proposal_rejection_reason("grounded perception") is None
    assert engine.thought_proposal_rejection_reason("notice pull toward") == "quality_unavailable"
    assert engine.thought_proposal_rejection_reason("module") == "lexical_noise"


def test_enhanced_cycle_competes_only_admissible_goal_proposals():
    class _Workspace:
        seen_thoughts = None

        def compete(self, **kwargs):
            self.seen_thoughts = kwargs["thoughts"]
            return {"winner": {"name": "existing thought", "type": "thought", "score": 0.5}}

    class _GoalEngine:
        def thought_proposal_rejection_reason(self, topic):
            return "low_quality_topic" if topic == "notice pull toward" else None

    phase1 = Phase1Orchestrator.__new__(Phase1Orchestrator)
    workspace = _Workspace()
    phase1._global_workspace = None
    phase1.components = {"workspace": workspace}
    phase1.goal_engine = _GoalEngine()
    phase1.cycle_count = 4
    phase1.gather_perception = lambda _input: {}
    phase1.get_decision_pressure = lambda: {"total": 0.2}
    phase1.evaluate_thoughts_and_create_goals = lambda: [
        {"concept": "notice_pull_toward", "origin_thought": "noise"},
        {"concept": "grounded_perception", "origin_thought": "useful"},
    ]
    phase1._load_goals = lambda: []
    phase1._load_recent_thoughts = lambda: []
    phase1._load_tensions = lambda: {}
    phase1._plan_for_winner = lambda *_args: []
    phase1._recommend_from_winner = lambda *_args: "continue"

    result = phase1.enhanced_cycle()

    proposal_topics = [item["topic"] for item in workspace.seen_thoughts]
    assert proposal_topics == ["grounded perception"]
    assert result["rejected_goal_suggestions"][0]["reason"] == "low_quality_topic"


def test_enhanced_cycle_can_skip_unconsumed_advisory_plan():
    class _Workspace:
        def compete(self, **_kwargs):
            return {"winner": {"name": "focused thought", "type": "thought", "score": 0.7}}

    phase1 = Phase1Orchestrator.__new__(Phase1Orchestrator)
    phase1._global_workspace = None
    phase1.components = {"workspace": _Workspace()}
    phase1.cycle_count = 0
    phase1.gather_perception = lambda _input: {}
    phase1.get_decision_pressure = lambda: {"total": 0.2}
    phase1._load_goals = lambda: []
    phase1._load_recent_thoughts = lambda: []
    phase1._load_tensions = lambda: {}
    phase1._plan_for_winner = lambda *_args: (_ for _ in ()).throw(
        AssertionError("internal-loop mode must not build an unconsumed plan")
    )
    phase1._recommend_from_winner = lambda *_args: (_ for _ in ()).throw(
        AssertionError("internal-loop mode must not build an unconsumed recommendation")
    )

    result = phase1.enhanced_cycle(include_advisory_plan=False)

    assert result["winner"]["name"] == "focused thought"
    assert result["plan"] == []
    assert result["recommendation"] is None


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
    enhanced_cycle_calls = [
        node for node in ast.walk(slow_cycle)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "enhanced_cycle"
    ]

    assert evaluator_calls == [], "Phase1 owns proposal evaluation; no second independent loop may consume thoughts"
    assert len(executor_calls) == 1, "the executor must receive arbitration authority explicitly"
    assert len(enhanced_cycle_calls) == 1
    assert any(
        keyword.arg == "include_advisory_plan"
        and isinstance(keyword.value, ast.Constant)
        and keyword.value.value is False
        for keyword in enhanced_cycle_calls[0].keywords
    ), "the internal loop must not generate the advisory plan it never consumes"


def test_rejected_proposal_stays_in_cycle_evidence_but_not_consumer_focus():
    candidate = {
        "type": "thought",
        "name": "notice pull toward",
        "topic": "notice pull toward",
        "score": 0.63,
        "source_data": {"_goal_proposal": {"concept": "notice pull toward"}},
    }

    published = InternalThoughtLoop._workspace_focus_for_consumers(candidate, admitted=False)

    assert candidate["name"] == "notice pull toward"  # retain raw cycle evidence
    assert published == {
        "type": "rejected_proposal",
        "proposal_admission": "rejected",
        "name": "",
        "topic": "",
        "score": 0.0,
    }
    assert CognitivePreProcessor._workspace_winner_block(
        SimpleNamespace(_v32_workspace_winner=published)
    ) == ""
    assert InternalThoughtLoop._workspace_focus_for_consumers(candidate, admitted=True) is candidate


def test_explicit_empty_workspace_decision_replaces_stale_focus_and_is_not_promptable():
    organism = SimpleNamespace(
        _v32_workspace_winner={
            "type": "goal", "name": "old objective", "topic": "old objective", "score": 0.91,
        },
    )
    evidence = []
    loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
    loop._slow_cycle_count = 12
    loop._record_cycle_stage = lambda stage, status, **kwargs: (
        evidence.append((stage, status, kwargs)) or "evidence-ref"
    )

    loop._publish_empty_workspace_focus(
        organism, reason="no_candidate", status="no_winner",
    )

    assert organism._v32_workspace_winner["type"] == "no_winner"
    assert organism._v32_workspace_winner["name"] == ""
    assert organism._v32_workspace_winner_cycle == 12
    assert organism._v32_workspace_winner_evidence_ref == "evidence-ref"
    assert organism._v32_workspace_winner_evidence_cycle == 12
    assert CognitivePreProcessor._workspace_winner_block(organism) == ""
    assert evidence[0][0:2] == ("winner_published_to_workspace_state", "no_winner")


def test_phase1_error_publishes_fresh_empty_focus_to_block_old_goal_fallback():
    organism = SimpleNamespace(_v32_workspace_winner={
        "type": "goal", "id": "old-goal", "name": "old objective", "score": 0.9,
    })
    loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
    loop._slow_cycle_count = 13
    loop._record_cycle_stage = lambda *_args, **_kwargs: "failure-clear-ref"

    loop._publish_empty_workspace_focus(
        organism, reason="phase1_failed", status="cleared_after_error",
    )

    assert organism._v32_workspace_winner["type"] == "no_winner"
    assert organism._v32_workspace_winner_cycle == 13

    class _GoalEngine:
        def get_active_goals(self, min_activation):
            return [SimpleNamespace(id="old-goal", topic="stale objective")]

    executor = GoalActionExecutor.__new__(GoalActionExecutor)
    executor._get_goal_engine = lambda: _GoalEngine()
    executor._select_eligible_goal = lambda _active: (_ for _ in ()).throw(
        AssertionError("a cleared focus must not fall back to an older goal")
    )
    result = executor.run_tick(
        selection_is_authoritative=True,
        cycle_id=organism._v32_workspace_winner_cycle,
    )

    assert result is None


def test_failed_workspace_cycle_publishes_an_explicit_empty_focus():
    empty_focus = InternalThoughtLoop._empty_workspace_focus("phase1_failed")

    assert empty_focus == {
        "type": "no_winner",
        "proposal_admission": "phase1_failed",
        "name": "",
        "topic": "",
        "score": 0.0,
    }
