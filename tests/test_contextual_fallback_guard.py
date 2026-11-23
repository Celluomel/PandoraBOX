"""The contextless legacy fallback must not answer live-context questions."""

import ast
from pathlib import Path

from cognition.conversation_context import recent_dialogue_anchor
from cognition.persona_bridge import PersonaBridge

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


def test_conversation_context_helper_is_imported_and_callable():
    history = [
        {"role": "user", "content": "We are comparing organic and synthetic states."},
        {"role": "assistant", "content": "The latter are computational variables."},
    ]
    excerpt, message_count = recent_dialogue_anchor(history, "And the first case?")
    assert message_count == 2
    assert "organic and synthetic states" in excerpt
    assert "computational variables" in excerpt


def test_local_camera_fallback_guard_resolves_at_runtime():
    assert PersonaBridge._may_route_to_local_camera("Can you see me through the camera?")
    assert not PersonaBridge._may_route_to_local_camera("How are you doing today?")


def test_history_source_and_continuity_are_linked_into_final_prompt():
    tree = ast.parse((ROOT / "cognition" / "persona_bridge.py").read_text(encoding="utf-8"))
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_record_turn_stage"
    ]
    history_source = next(
        node for node in calls
        if node.args and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "conversation_history"
    )
    continuity = next(
        node for node in calls
        if node.args and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "conversation_continuity_context"
    )
    final_prompt = next(
        node for node in calls
        if node.args and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "prompt_assembly"
    )
    continuity_consumes = next(
        kw.value for kw in continuity.keywords if kw.arg == "consumes"
    )
    prompt_consumes = next(
        kw.value for kw in final_prompt.keywords if kw.arg == "consumes"
    )
    assert "conversation_history" in ast.unparse(continuity_consumes)
    assert "conversation_continuity_context" in ast.unparse(prompt_consumes)
    assert history_source.lineno < continuity.lineno < final_prompt.lineno
