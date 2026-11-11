"""Ensure the classic chat UI treats auxiliary stream events as metadata."""

import ast
from pathlib import Path


def test_main_chat_skips_non_meta_event_dicts_before_appending_answer_text():
    source_path = Path(__file__).parents[1] / "pages" / "main_page.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    stream_loops = [
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
    answer_loops = [
        node for node in stream_loops
        if any(
            isinstance(child, ast.AugAssign)
            and isinstance(child.target, ast.Name)
            and child.target.id == "accumulated_text"
            for child in ast.walk(node)
        )
    ]
    assert len(answer_loops) == 1
    loop = answer_loops[0]

    dict_guards = [
        node for node in loop.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Call)
        and isinstance(node.test.func, ast.Name)
        and node.test.func.id == "isinstance"
        and len(node.test.args) == 2
        and isinstance(node.test.args[0], ast.Name)
        and node.test.args[0].id == "chunk"
        and isinstance(node.test.args[1], ast.Name)
        and node.test.args[1].id == "dict"
    ]
    assert len(dict_guards) == 1
    guard = dict_guards[0]
    assert any(isinstance(child, ast.Continue) for child in ast.walk(guard))

    text_append = next(
        node for node in loop.body
        if isinstance(node, ast.AugAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "accumulated_text"
    )
    assert loop.body.index(guard) < loop.body.index(text_append)
