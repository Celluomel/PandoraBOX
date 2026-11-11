"""Guard the ordering of input policy and deterministic action routes."""

import ast
from pathlib import Path


def test_input_policy_precedes_goal_and_body_deterministic_routes():
    source = Path(__file__).parents[1] / "cognition" / "persona_bridge.py"
    module = ast.parse(source.read_text(encoding="utf-8"))
    bridge = next(
        node for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge"
    )
    entrypoint = next(
        node for node in bridge.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "_get_response_stream_impl"
    )

    def call_lines(method_name):
        return [
            node.lineno for node in ast.walk(entrypoint)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == method_name
        ]

    def call_line(method_name):
        matches = call_lines(method_name)
        assert len(matches) == 1
        return matches[0]

    safety_line = min(call_lines("check_input"))
    goal_write_line = call_line("_explicit_goal_write_gate")
    body_route_line = call_line("handle_body_chat_turn")
    blocked_response_lines = [
        node.lineno for node in ast.walk(entrypoint)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "_input_response"
        and any(isinstance(child, ast.Return) for child in ast.walk(node))
    ]

    assert safety_line < goal_write_line < body_route_line
    assert len(blocked_response_lines) == 1
    assert safety_line < blocked_response_lines[0] < goal_write_line
    assert "input_safety_checked" in ast.unparse(entrypoint)
