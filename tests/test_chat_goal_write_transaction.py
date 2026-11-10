import json
from types import SimpleNamespace

from cognition.goal_engine import GoalEngine
from cognition.goal_completion import goal_completion_eligible, record_goal_completion
from cognition.long_horizon_planner import LongHorizonPlanner
from cognition.persona_bridge import PersonaBridge


def test_explicit_goal_request_is_parsed_as_a_write_request():
    prompt = (
        "For this audit, create and persist one development goal: improve the ability "
        "to distinguish directly observed facts from inferences in future answers. "
        "Give it a measurable success criterion and report whether it was actually saved."
    )

    assert PersonaBridge._is_explicit_goal_persistence_request(prompt)
    topic, criteria = PersonaBridge._parse_explicit_goal_request(prompt)
    assert topic == (
        "improve the ability to distinguish directly observed facts from inferences in future answers"
    )
    assert "five consecutive relevant answers" in criteria


def test_goal_engine_persists_and_links_explicit_goal_to_turn(tmp_path):
    engine = GoalEngine(ai_system=None, persistence_file=str(tmp_path / "goals.json"))
    engine._is_valid_goal_topic = lambda _topic: True

    result = engine.create_user_requested_goal(
        "improve the ability to distinguish observed facts from inferences",
        "Five consecutive reviewed answers have zero fact/inference category errors.",
        "turn-test-42",
    )

    assert result["created"] is True
    assert result["verified"] is True
    assert result["source_turn_id"] == "turn-test-42"
    stored = json.loads((tmp_path / "goals.json").read_text(encoding="utf-8"))
    row = stored["goals"][result["id"]]
    assert row["source_turn_id"] == "turn-test-42"
    assert row["success_criteria"].startswith("Five consecutive")


def test_goal_engine_does_not_report_success_when_persistence_fails(tmp_path):
    engine = GoalEngine(ai_system=None, persistence_file=str(tmp_path / "goals.json"))
    engine._is_valid_goal_topic = lambda _topic: True
    engine._save_goals = lambda: False

    result = engine.create_user_requested_goal(
        "improve grounded uncertainty reporting",
        "Five reviewed answers have no unsupported claims.",
        "turn-test-43",
    )

    assert result["created"] is False
    assert result["verified"] is False
    assert engine._goals == {}


def test_goal_persistence_status_links_id_to_previous_turn(tmp_path):
    engine = GoalEngine(ai_system=None, persistence_file=str(tmp_path / "goals.json"))
    engine._is_valid_goal_topic = lambda _topic: True
    result = engine.create_user_requested_goal(
        "improve grounded uncertainty reporting",
        "Five reviewed answers have no unsupported claims.",
        "turn-prior-9",
    )
    assert result["verified"] is True

    bridge = PersonaBridge.__new__(PersonaBridge)
    bridge._system = SimpleNamespace(goal_engine=engine)
    bridge._turn_trace_history = [{"turn_id": "turn-prior-9"}]
    report = bridge._goal_persistence_status(f"What is the exact ID {result['id']} of the saved goal?")

    assert report["status"] == "found_and_causally_linked"
    assert result["id"] in report["response"]


def test_goal_write_detector_does_not_capture_analysis_questions():
    assert not PersonaBridge._is_explicit_goal_persistence_request(
        "Could we discuss how the GoalEngine decides which goals to persist?"
    )
    assert PersonaBridge._is_explicit_goal_persistence_request(
        "Créer un objectif : améliorer la séparation des faits et des inférences."
    )


def test_explicit_goal_handler_executes_transaction_and_returns_verified_receipt(tmp_path):
    engine = GoalEngine(ai_system=None, persistence_file=str(tmp_path / "goals.json"))
    engine._is_valid_goal_topic = lambda _topic: True
    bridge = PersonaBridge.__new__(PersonaBridge)
    bridge._system = SimpleNamespace(goal_engine=engine)
    bridge._last_turn_trace = {"turn_id": "turn-explicit-goal-1"}

    prompt = (
        "For this audit, create and persist one development goal: improve the ability "
        "to distinguish directly observed facts from inferences in future answers. "
        "Give it a measurable success criterion and report whether it was actually saved."
    )

    result = bridge._explicit_goal_write_gate(prompt)
    assert result["status"] == "persisted_verified"
    assert result["goal_write"]["verified"] is True
    assert result["goal_write"]["source_turn_id"] == "turn-explicit-goal-1"
    stored = json.loads((tmp_path / "goals.json").read_text(encoding="utf-8"))
    assert result["goal_write"]["id"] in stored["goals"]


def test_goal_success_criterion_flows_into_downstream_plan(tmp_path):
    criteria = "Five consecutive reviewed answers have zero fact/inference category errors."
    engine = GoalEngine(ai_system=None, persistence_file=str(tmp_path / "goals.json"))
    engine._is_valid_goal_topic = lambda _topic: True
    written = engine.create_user_requested_goal(
        "improve grounded fact and inference separation",
        criteria,
        "turn-plan-flow-1",
    )
    assert written["verified"] is True

    planner = LongHorizonPlanner(
        organism=SimpleNamespace(ai_system=SimpleNamespace(goal_engine=engine)),
        ai_system=engine,
        path=str(tmp_path / "plans.json"),
    )
    planner._get_reasoner = lambda: None
    goal = engine.get_goal_by_id(written["id"])
    plan = planner.ensure_goal_plan(goal)

    assert plan is not None
    assert plan.source == "goal"
    assert plan.source_id == written["id"]
    assert plan.success_criteria == criteria
    assert planner.factual_self_report_snapshot()["dominant_plan"][
        "success_criteria_status"
    ] == "unverified"
    assert engine.record_success_criteria_verification(
        written["id"], criteria, "reviewed test evidence", "audit_test"
    ) is True
    assert planner.factual_self_report_snapshot()["dominant_plan"][
        "success_criteria_status"
    ] == "verified"


def test_successful_action_cannot_complete_user_goal_without_criterion_evidence(tmp_path):
    engine = GoalEngine(ai_system=None, persistence_file=str(tmp_path / "goals.json"))
    engine._is_valid_goal_topic = lambda _topic: True
    written = engine.create_user_requested_goal(
        "improve sensor interpretation",
        "Five reviewed sensor summaries match source readings.",
        "turn-criteria-gate-1",
    )
    goal = engine.get_goal_by_id(written["id"])
    engine.mark_action(goal.id, "web_search")

    eligible, reason = goal_completion_eligible(goal)
    assert eligible is False
    assert "criterion has not been verified" in reason
    assert engine.complete_goal(goal.id) is False
    assert record_goal_completion(goal, goal_engine=engine) is False
    assert engine.get_goal_by_id(goal.id).status == "active"

    # The exact criterion, evidence, and verifier are persisted as one record.
    criteria = goal.success_criteria
    assert engine.record_success_criteria_verification(
        goal.id,
        criteria,
        "Five reviewed summaries were checked against timestamped sensor records.",
        "audit_review",
    ) is True
    assert engine.record_success_criteria_verification(
        goal.id,
        "a different criterion",
        "evidence",
        "audit_review",
    ) is False
    assert goal_completion_eligible(goal)[0] is True
    assert engine.complete_goal(goal.id) is True
    assert engine.get_goal_by_id(goal.id).status == "completed"
