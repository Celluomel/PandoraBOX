import json
from types import SimpleNamespace

from cognition.goal_engine import GoalEngine
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
