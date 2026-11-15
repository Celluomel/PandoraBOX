from __future__ import annotations

import importlib
import threading
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cognition.persona_bridge import PersonaBridge


def test_peer_prompt_receives_only_peer_keyed_abstract_reasoning():
    acc = Mock()
    acc.get_prompt_fragment.return_value = "human-private-context"
    empathy = Mock()
    empathy.get_prompt_fragment.return_value = "human-affect-context"
    sce = Mock()
    sce.get_strategic_context_fragment.return_value = "shared-strategic-posture"
    are = Mock()
    are.get_reasoning_fragment.return_value = "peer-scoped-abstract-reasoning"
    core_state = importlib.import_module("core.state")
    fake_state = SimpleNamespace(acc=acc, empathy_engine=empathy, sce=sce, are=are)

    bridge = PersonaBridge.__new__(PersonaBridge)
    bridge._organism = SimpleNamespace(
        self_model=SimpleNamespace(prompt_fragment=Mock(return_value="self-model")),
        attractors=SimpleNamespace(prompt_fragment=Mock(return_value="stable-traits")),
    )
    bridge._turn_trace_lock = threading.Lock()
    bridge._last_turn_trace = {"stages": {}}

    with patch.object(core_state, "state", fake_state):
        prompt = bridge._append_cognitive_prompt_context(
            "base", user_id="peer:flux", peer_name="FLUX",
        )

    assert "peer-scoped-abstract-reasoning" in prompt
    assert "shared-strategic-posture" in prompt
    assert "human-private-context" not in prompt
    assert "human-affect-context" not in prompt
    are.get_reasoning_fragment.assert_called_once_with("peer:flux")
    acc.get_prompt_fragment.assert_not_called()
    empathy.get_prompt_fragment.assert_not_called()
    assert bridge._last_turn_trace["stages"]["abstract_reasoning_context"]["status"] == "injected"
    assert bridge._last_turn_trace["stages"]["active_context_prompt"]["status"] == "skipped_by_scope"
    assert bridge._last_turn_trace["stages"]["empathy_context"]["status"] == "skipped_by_scope"
