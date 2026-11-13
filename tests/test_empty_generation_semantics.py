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
