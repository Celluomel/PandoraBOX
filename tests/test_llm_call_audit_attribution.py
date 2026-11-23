"""Provider audit events must separate chat calls from inherited background work."""

import importlib.util
import asyncio
from pathlib import Path
import sys

from core.turn_execution_context import current_turn_id
from managers.llm_manager import (
    LLMManager, current_llm_call_origin, current_llm_call_role,
)


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "llm_call_audit_under_test", ROOT / "scripts" / "audit_llm_calls.py",
)
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


class _Provider:
    model = "test-model"


def _event(role: str, origin: str = "", turn_id: str = "turn-7"):
    turn_token = current_turn_id.set(turn_id)
    role_token = current_llm_call_role.set(role)
    origin_token = current_llm_call_origin.set(origin)
    try:
        return audit._call_metadata(_Provider(), "generate_background_result", ("prompt",), {})
    finally:
        current_llm_call_origin.reset(origin_token)
        current_llm_call_role.reset(role_token)
        current_turn_id.reset(turn_token)


def test_inherited_turn_context_does_not_classify_background_inference_as_chat():
    event = _event("background", "cognition.simple_thought_evaluator._generate_hypothesis_result")

    assert event["execution"] == "background"
    assert event["turn_id"] is None
    assert event["turn_call_number"] is None
    assert event["causal_parent_turn_id"] == "turn-7"
    assert event["caller"] == "cognition.simple_thought_evaluator._generate_hypothesis_result"
    assert event["caller_file"] == "cognition/simple_thought_evaluator.py"


def test_explicit_foreground_role_keeps_turn_correlation():
    event = _event("foreground_primary", "cognition.persona_bridge._stream")

    assert event["execution"] == "foreground_primary"
    assert event["turn_id"] == "turn-7"
    assert event["causal_parent_turn_id"] is None
    assert event["caller"] == "cognition.persona_bridge._stream"


def test_manager_marks_bare_calls_background_even_with_inherited_turn_id():
    observed = []

    class Provider:
        model = "test-model"

        def generate_background_result(self, *_args, **_kwargs):
            observed.append((current_llm_call_role.get(), current_llm_call_origin.get()))
            return {"text": "thought", "status": "ok"}

    manager = LLMManager(Provider())
    turn_token = current_turn_id.set("turn-parent")
    try:
        result = manager.generate_bare_result("background thought")
    finally:
        current_turn_id.reset(turn_token)

    assert result["status"] == "ok"
    assert result["provider_call_count"] == 1
    assert observed == [("background", "test_llm_call_audit_attribution.test_manager_marks_bare_calls_background_even_with_inherited_turn_id")]
    assert current_llm_call_role.get() == ""
    assert current_llm_call_origin.get() == ""


def test_bare_result_counts_failed_native_attempt_and_fallback():
    class Provider:
        model = "test-model"

        def generate_background_result(self, *_args, **_kwargs):
            raise RuntimeError("native endpoint unavailable")

        def _generate_messages(self, *_args, **_kwargs):
            raise TimeoutError("fallback timed out")

    result = LLMManager(Provider()).generate_bare_result("background thought")

    assert result["status"] == "error"
    assert result["reason"] == "TimeoutError"
    assert result["provider_call_count"] == 2


def test_interactive_analysis_has_explicit_auxiliary_role_and_origin():
    observed = []

    class Provider:
        model = "test-model"

        def _generate_messages(self, *_args, **_kwargs):
            observed.append((current_llm_call_role.get(), current_llm_call_origin.get()))
            return "analysis"

    manager = LLMManager(Provider())
    result = manager.generate_interactive_analysis("inspect this")

    assert result == "analysis"
    assert observed == [("foreground_auxiliary", "test_llm_call_audit_attribution.test_interactive_analysis_has_explicit_auxiliary_role_and_origin")]
    assert current_llm_call_role.get() == ""
    assert current_llm_call_origin.get() == ""


def test_audit_executor_wrapper_preserves_turn_and_submission_provenance():
    loop_type = asyncio.BaseEventLoop
    original = loop_type.run_in_executor
    audit._install_executor_provenance()
    observed = []

    def provider_probe():
        observed.append((
            current_turn_id.get(),
            audit._executor_submission_origin.get(),
        ))

    async def run_probe():
        token = current_turn_id.set("turn-executor-parent")
        try:
            await asyncio.get_running_loop().run_in_executor(None, provider_probe)
        finally:
            current_turn_id.reset(token)

    try:
        asyncio.run(run_probe())
    finally:
        loop_type.run_in_executor = original

    assert observed == [(
        "turn-executor-parent",
        "test_llm_call_audit_attribution.run_probe",
    )]


def test_provider_event_uses_executor_submission_for_generic_worker_origin():
    token = audit._executor_submission_origin.set("cognition.persona_bridge._stream")
    try:
        event = _event(
            "background", "concurrent.futures.thread.run", "turn-dispatched",
        )
    finally:
        audit._executor_submission_origin.reset(token)

    assert event["caller"] == "cognition.persona_bridge._stream"
    assert event["caller_file"] == "cognition/persona_bridge.py"
    assert event["executor_submission_origin"] == "cognition.persona_bridge._stream"
    assert event["causal_parent_turn_id"] == "turn-dispatched"
