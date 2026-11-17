import importlib.util
from pathlib import Path
import sys

from core.turn_execution_context import current_turn_id, normalize_turn_id


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "runtime_python_execution_audit_under_test",
    ROOT / "scripts" / "audit_runtime_python_execution.py",
)
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


def test_active_turn_id_reads_only_safe_contextvar_identity():
    token = current_turn_id.set("lumina-turn-123")
    try:
        assert audit._active_turn_id() == "lumina-turn-123"
    finally:
        current_turn_id.reset(token)


def test_turn_id_normalization_rejects_free_text_and_oversized_values():
    assert normalize_turn_id("caller-turn_7:slot.2") == "caller-turn_7:slot.2"
    assert normalize_turn_id("turn id with spaces") == ""
    assert normalize_turn_id("x" * 121) == ""


def test_per_turn_file_counts_and_module_imports_are_distinguished():
    audit.turn_file_calls.clear()
    audit.turn_module_calls.clear()
    audit._record_call("cognition/sample.py", False, "turn-a")
    audit._record_call("cognition/sample.py", True, "turn-a")

    assert audit.turn_file_calls["turn-a"]["cognition/sample.py"] == 2
    assert audit.turn_module_calls["turn-a"]["cognition/sample.py"] == 1


def test_turn_history_is_bounded():
    old_max = audit.MAX_AUDIT_TURNS
    audit.MAX_AUDIT_TURNS = 2
    audit.turn_file_calls.clear()
    audit.turn_module_calls.clear()
    try:
        for turn_id in ("turn-a", "turn-b", "turn-c"):
            audit._record_call("cognition/sample.py", False, turn_id)
        assert list(audit.turn_file_calls) == ["turn-b", "turn-c"]
        assert list(audit.turn_module_calls) == ["turn-b", "turn-c"]
    finally:
        audit.MAX_AUDIT_TURNS = old_max
        audit.turn_file_calls.clear()
        audit.turn_module_calls.clear()
