"""Deterministic answer routes must pass the shared output policy."""

import ast
import threading
from pathlib import Path
from types import SimpleNamespace

from cognition.persona_bridge import PersonaBridge
from cognition.safety_constraints import ConstraintResult


def _bridge(safety):
    bridge = PersonaBridge.__new__(PersonaBridge)
    bridge._system = SimpleNamespace(_organism=SimpleNamespace(safety=safety))
    bridge._turn_trace_lock = threading.RLock()
    bridge._last_turn_trace = {"turn_id": "deterministic-output-test", "stages": {}}
    bridge._turn_trace_history = []
    bridge._turn_stage_health = {}
    return bridge


def test_deterministic_output_replaces_policy_block_and_records_dependency():
    safety = SimpleNamespace(check_output=lambda *_args: ConstraintResult(
        triggered=True, law="law1", forced_response="Withheld safely.",
        severity=10, pattern="matched", layer="output",
    ))
    bridge = _bridge(safety)
    bridge._record_turn_stage("body_action_resolution", "completed", output={"status": "refused"})

    response = bridge._check_deterministic_output(
        "unsafe-looking candidate", "test-user", "body_action_resolution",
    )

    assert response == "Withheld safely."
    stage = bridge._last_turn_trace["stages"]["output_safety"]
    assert stage["status"] == "replaced"
    assert stage["consumes"][0]["stage"] == "body_action_resolution"
    assert stage["consumes"][0]["fingerprint"]


def test_deterministic_output_evaluation_error_is_failed_and_withheld():
    safety = SimpleNamespace(check_output=lambda *_args: ConstraintResult(
        triggered=True, law="evaluation_error", forced_response="Withheld.",
        severity=10, pattern="evaluation_error:RuntimeError", layer="output",
        evaluation_error=True,
    ))
    bridge = _bridge(safety)
    bridge._record_turn_stage("goal_write_gate", "verified", output={"id": "g1"})

    response = bridge._check_deterministic_output(
        "candidate", "test-user", "goal_write_gate",
    )

    assert response == "Withheld."
    assert bridge._last_turn_trace["stages"]["output_safety"]["status"] == "failed"


def test_goal_and_body_routes_gate_output_before_recording_final_answer():
    source = Path(__file__).parents[1] / "cognition" / "persona_bridge.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    bridge_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge"
    )
    entrypoint = next(
        node for node in bridge_class.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "_get_response_stream_impl"
    )
    helper_calls = [
        node.lineno for node in ast.walk(entrypoint)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_check_deterministic_output"
    ]
    # Goal, Body, contextual fail-closed, and ordinary blocking fallback.
    assert len(helper_calls) == 4

    finish = next(
        node for node in bridge_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "_finish_turn_trace"
    )
    required_assignments = [
        node.value for node in ast.walk(finish)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "required_stages"
            for target in node.targets
        )
    ]
    routes = [ast.literal_eval(value) for value in required_assignments]
    deterministic_routes = [
        route for route in routes
        if any(item[0] == "deterministic_body_response" for item in route)
        or any(item[0] == "deterministic_goal_response" for item in route)
    ]
    assert len(deterministic_routes) == 2
    for route in deterministic_routes:
        stages = {item[0] for item in route}
        assert "input_safety" in stages
        assert "output_safety" in stages


def test_trace_requires_safety_evidence_for_blocking_fallback():
    bridge = _bridge(None)
    bridge._last_turn_trace["stages"].update({
        "readiness": {"status": "passed"},
        "input_safety": {"status": "passed"},
        "fallback_generation": {"status": "completed"},
        "output_safety": {"status": "passed"},
        "response_finalization": {"status": "completed"},
        "response": {"status": "completed"},
    })

    bridge._finish_turn_trace("completed")
    integrity = bridge._last_turn_trace["pipeline_integrity"]

    assert integrity["status"] == "consistent"
    assert integrity["execution_path"] == "blocking_fallback"
    assert integrity["missing_core_stages"] == []
