from __future__ import annotations

import importlib
import threading
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cognition.persona_bridge import PersonaBridge


class _Selection:
    dominant = SimpleNamespace(id="thread-17")

    @staticmethod
    def to_prompt_block() -> str:
        return "[DOMINANT THOUGHT] continue the causal audit"


def _bridge(selection: _Selection, *, selected_at: float | None = None) -> PersonaBridge:
    organism = SimpleNamespace(
        _dominant_thought=selection,
        _dominant_thought_cycle=42,
        _dominant_thought_updated_at=time.time() if selected_at is None else selected_at,
        self_model=SimpleNamespace(prompt_fragment=Mock(return_value="")),
        attractors=SimpleNamespace(prompt_fragment=Mock(return_value="")),
    )
    bridge = PersonaBridge.__new__(PersonaBridge)
    bridge._organism = organism
    bridge._turn_trace_lock = threading.Lock()
    bridge._last_turn_trace = {"turn_id": "turn-1", "stages": {}}
    bridge._turn_trace_history = []
    return bridge


def _empty_cognitive_state():
    return SimpleNamespace(acc=None, empathy_engine=None, sce=None, are=None)


def test_primary_human_prompt_injects_fresh_dts_selection_with_provenance():
    bridge = _bridge(_Selection())
    core_state = importlib.import_module("core.state")

    with patch.object(core_state, "state", _empty_cognitive_state()):
        prompt = bridge._append_cognitive_prompt_context(
            "base", user_id="fred", audit_turn_id="turn-1",
        )

    assert "[DOMINANT THOUGHT] continue the causal audit" in prompt
    stage = bridge._last_turn_trace["stages"]["dominant_thought_context"]
    assert stage["status"] == "injected"
    evidence = bridge._last_turn_trace["context_sources"]["dominant_thought"]
    assert evidence["status"] == "injected"
    assert evidence["source_cycle"] == 42
    assert evidence["thread_id"] == "thread-17"
    assert stage["output_fingerprint"]


def test_stale_dts_selection_is_not_injected():
    bridge = _bridge(_Selection(), selected_at=time.time() - 1000)
    core_state = importlib.import_module("core.state")

    with patch.object(core_state, "state", _empty_cognitive_state()):
        prompt = bridge._append_cognitive_prompt_context(
            "base", user_id="fred", audit_turn_id="turn-1",
        )

    assert "[DOMINANT THOUGHT]" not in prompt
    stage = bridge._last_turn_trace["stages"]["dominant_thought_context"]
    assert stage["status"] == "skipped_stale"
    evidence = bridge._last_turn_trace["context_sources"]["dominant_thought"]
    assert evidence["status"] == "stale"
    assert evidence["source_cycle"] == 42


def test_peer_prompt_does_not_receive_global_dts_selection():
    bridge = _bridge(_Selection())
    core_state = importlib.import_module("core.state")

    with patch.object(core_state, "state", _empty_cognitive_state()):
        prompt = bridge._append_cognitive_prompt_context(
            "base", user_id="peer:flux", peer_name="FLUX", audit_turn_id="turn-1",
        )

    assert "[DOMINANT THOUGHT]" not in prompt
    stage = bridge._last_turn_trace["stages"]["dominant_thought_context"]
    assert stage["status"] == "skipped_by_scope"
