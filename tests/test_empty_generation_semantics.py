"""Regression checks for turns where the provider yields no visible answer."""
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _method(path: Path, class_name: str, method_name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return next(
        node for node in cls.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == method_name
    )


def test_empty_generation_is_a_failed_turn_and_terminal_error():
    source = ROOT / "cognition" / "persona_bridge.py"
    stream = _method(source, "PersonaBridge", "_stream_with_full_lifecycle")
    calls = [
        node for node in ast.walk(stream)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_record_turn_stage"
    ]
    empty_fallback = next(
        call for call in calls
        if call.args and isinstance(call.args[0], ast.Constant)
        and call.args[0].value == "empty_generation_fallback"
    )
    assert any(
        isinstance(arg, ast.Constant) and arg.value == "failed"
        for arg in empty_fallback.args
    )
    assert any(
        isinstance(keyword.value, ast.Constant)
        and keyword.value.value == "EmptyProviderOutput"
        for keyword in empty_fallback.keywords
        if keyword.arg == "error_type"
    )
    assert any(
        isinstance(node, ast.Dict)
        and any(
            isinstance(key, ast.Constant) and key.value == "error"
            and isinstance(value, ast.Constant) and value.value == "provider_empty_output"
            for key, value in zip(node.keys, node.values)
        )
        for node in ast.walk(stream)
    )


def test_any_empty_visible_stream_reaches_the_single_recovery_attempt():
    source = ROOT / "cognition" / "persona_bridge.py"
    stream = _method(source, "PersonaBridge", "_stream_with_full_lifecycle")
    recovery_calls = [
        node for node in ast.walk(stream)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "callable"
    ]
    assert recovery_calls
    empty_recovery_conditions = [
        node for node in ast.walk(stream)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.UnaryOp)
        and isinstance(node.test.op, ast.Not)
        and isinstance(node.test.operand, ast.Call)
        and isinstance(node.test.operand.func, ast.Attribute)
        and node.test.operand.func.attr == "strip"
        and any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id == "callable"
            for child in ast.walk(node)
        )
    ]
    assert empty_recovery_conditions, (
        "Recovery must be eligible whenever visible output is empty, even when "
        "the provider reports a clean stop and emitted no reasoning channel."
    )


def test_response_outcome_learning_is_gated_on_real_generation():
    source = ROOT / "cognition" / "persona_bridge.py"
    stream = _method(source, "PersonaBridge", "_stream_with_full_lifecycle")
    guarded_stages = {
        "goal_means_post_response",
        "empathy_outcome",
        "abstract_reasoning_outcome",
        "cognitive_post_turn",
    }
    skipped = {
        node.value
        for node in ast.walk(stream)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value in guarded_stages
    }
    assert skipped == guarded_stages
    assert any(
        isinstance(node, ast.Constant)
        and node.value == "skipped_generation_failed"
        for node in ast.walk(stream)
    )
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_schedule_active_context_update"
        for node in ast.walk(stream)
    )


def test_terminal_error_marks_stream_lifecycle_failed():
    source = ROOT / "cognition" / "persona_bridge.py"
    stream_impl = _method(source, "PersonaBridge", "_get_response_stream_impl")
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_finish_turn_trace"
        and any(
            isinstance(arg, ast.Constant) and arg.value == "failed"
            for arg in node.args
        )
        for node in ast.walk(stream_impl)
    )
