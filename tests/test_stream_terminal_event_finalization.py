"""Terminal stream metadata must not precede turn cleanup/finalization."""

import ast
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_persona_finalizes_stream_trace_before_yielding_terminal_metadata():
    tree = ast.parse((ROOT / "cognition" / "persona_bridge.py").read_text(encoding="utf-8"))
    bridge = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge")
    method = next(
        node for node in bridge.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_get_response_stream_impl"
    )
    stream_loop = next(
        node for node in ast.walk(method)
        if isinstance(node, ast.AsyncFor)
        and any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "_stream_with_full_lifecycle"
            for call in ast.walk(node.iter)
        )
    )
    terminal_guard = next(
        node for node in stream_loop.body
        if isinstance(node, ast.If)
        and any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "get"
            and call.args
            and isinstance(call.args[0], ast.Constant)
            and call.args[0].value == "__meta__"
            for call in ast.walk(node.test)
        )
    )
    finish = next(
        node for node in ast.walk(terminal_guard)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_finish_turn_trace"
    )
    terminal_yield = next(
        node for node in ast.walk(stream_loop)
        if isinstance(node, ast.Yield)
        and isinstance(node.value, ast.Name)
        and node.value.id == "chunk"
    )
    assert finish.lineno < terminal_yield.lineno


def test_main_page_stream_consumers_drain_after_meta_instead_of_breaking():
    tree = ast.parse((ROOT / "pages" / "main_page.py").read_text(encoding="utf-8"))
    loops = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFor)
        and isinstance(node.target, ast.Name)
        and node.target.id == "chunk"
        and any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "get_response_stream"
            for call in ast.walk(node.iter)
        )
    ]
    assert len(loops) == 2
    for loop in loops:
        meta_branches = [
            node for node in ast.walk(loop)
            if isinstance(node, ast.If)
            and any(
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr == "get"
                and call.args
                and isinstance(call.args[0], ast.Constant)
                and call.args[0].value == "__meta__"
                for call in ast.walk(node.test)
            )
        ]
        assert meta_branches
        for branch in meta_branches:
            assert not any(isinstance(node, ast.Break) for node in ast.walk(branch))


def test_terminal_meta_is_yielded_after_turn_lock_is_released():
    tree = ast.parse((ROOT / "cognition" / "persona_bridge.py").read_text(encoding="utf-8"))
    bridge = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge")
    wrapper = next(
        node for node in bridge.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "get_response_stream"
    )
    lock_scope = next(
        node for node in wrapper.body
        if isinstance(node, ast.AsyncWith)
        and any("_response_turn_lock" in ast.unparse(item.context_expr) for item in node.items)
    )
    terminal_yield = next(
        node for node in ast.walk(wrapper)
        if isinstance(node, ast.Yield)
        and isinstance(node.value, ast.Name)
        and node.value.id == "_terminal_meta"
    )
    assert terminal_yield.lineno > lock_scope.end_lineno
    assert not any(
        isinstance(node, ast.Yield)
        and isinstance(node.value, ast.Name)
        and node.value.id == "_terminal_meta"
        for node in ast.walk(lock_scope)
    )
