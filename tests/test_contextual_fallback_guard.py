"""The contextless legacy fallback must not answer live-context questions."""

import ast
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _persona_stream_method():
    tree = ast.parse((ROOT / "cognition" / "persona_bridge.py").read_text(encoding="utf-8"))
    bridge = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge")
    return next(
        node for node in bridge.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_get_response_stream_impl"
    )


def test_live_body_camera_and_trace_turns_are_gated_before_legacy_generation():
    method = _persona_stream_method()
    fallback_guard = next(
        node for node in method.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "_needs_live_context"
    )
    legacy_generation = next(
        node for node in ast.walk(method)
        if isinstance(node, ast.Attribute)
        and node.attr == "get_response"
    )
    assert fallback_guard.lineno < legacy_generation.lineno

    context_assignment = next(
        node for node in method.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "_needs_live_context"
            for target in node.targets
        )
    )
    guard_source = ast.unparse(context_assignment.value)
    # The UI supplies working-memory vision to ordinary turns too; it must not
    # disable the legacy fallback unless the user's intent needs that evidence.
    assert "vision_context" not in guard_source
    assert "_trace_query" in guard_source
    assert "_may_route_to_body" in guard_source
    assert "_may_route_to_local_camera" in guard_source


def test_contextless_fallback_records_failure_and_explicit_terminal_error():
    method = _persona_stream_method()
    fallback_guard = next(
        node for node in method.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "_needs_live_context"
    )
    branch_source = ast.unparse(fallback_guard)
    assert "fallback_generation" in branch_source and "blocked_context" in branch_source
    assert "_finish_turn_trace('failed', audit_turn_id)" in branch_source
    assert "contextual_fallback_blocked" in branch_source
    assert "response_finalization" in branch_source and "completed" in branch_source


def test_empty_blocking_fallback_is_failed_before_any_success_finalization():
    method = _persona_stream_method()
    empty_guard = next(
        node for node in method.body
        if isinstance(node, ast.If)
        and "not response.strip()" in ast.unparse(node.test)
    )
    guard_source = ast.unparse(empty_guard)
    assert "fallback_generation" in guard_source and "failed" in guard_source
    assert "EmptyFallbackResponse" in guard_source
    assert "empty_fallback_response" in guard_source
    assert "_finish_turn_trace('failed', audit_turn_id)" in guard_source
