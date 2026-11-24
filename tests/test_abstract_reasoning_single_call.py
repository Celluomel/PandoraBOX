"""Abstract reasoning should preserve its result while avoiding serial LLM passes."""

import json
import time
from unittest.mock import patch

from cognition.abstract_reasoning_engine import AbstractReasoningEngine


class _Memory:
    def get_context(self, _text, top_k=3):
        assert top_k == 3
        return "Memory says the concept was discussed as a system property."


class _WorldModel:
    def prompt_fragment(self):
        return "No independently verified causal relation is recorded."


class _Organism:
    world_model = _WorldModel()


class _LLM:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate_bare(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        return self.response

    def generate_bare_result(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        return {
            "text": self.response,
            "status": "ok",
            "completion_verified": True,
            "provider_call_count": 1,
        }


def test_abstract_reasoning_gets_all_three_outputs_from_one_llm_call():
    response = {
        "core_concept": "identity continuity",
        "components": ["memory", "belief revision"],
        "best_analogy_domain": "language",
        "structural_mapping": "Stable grammar supports changing sentences.",
        "confidence": 0.72,
        "derived_insight": "Continuity can depend on preserved relations, not fixed values.",
        "open_question": "Which relations should remain invariant?",
        "causal_antecedent": "",
        "causal_consequent": "",
        "prompt_note": "Distinguish continuity from unchanged state.",
    }
    llm = _LLM(json.dumps(response))
    engine = AbstractReasoningEngine(_Organism(), llm, _Memory())

    result = engine._llm_reason("user-1", "How can identity persist through change?", 0.8)

    assert len(llm.calls) == 1
    prompt, kwargs = llm.calls[0]
    assert "Semantic memory context" in prompt
    assert "World model context" in prompt
    assert "Candidate analogy domains" in prompt
    assert kwargs["max_tokens"] == 420
    assert result is not None
    assert result.method == "llm"
    assert result.core_concept == "identity continuity"
    assert result.components == ["memory", "belief revision"]
    assert result.analogy_confidence == 0.72
    assert result.derived_insight.startswith("Continuity can depend")
    assert result.causal_pair == ("", "")


def test_abstract_reasoning_clamps_bad_confidence_and_bounds_fields():
    response = {
        "core_concept": "x" * 200,
        "components": ["a" * 200, "ok", None, 4, "fifth"],
        "confidence": 4,
    }
    llm = _LLM(json.dumps(response))
    engine = AbstractReasoningEngine(_Organism(), llm)

    result = engine._llm_reason("user-1", "A sufficiently abstract question?", 0.8)

    assert result is not None
    assert len(result.core_concept) == 120
    assert result.components == ["a" * 120, "ok", "4"]
    assert result.analogy_confidence == 1.0


def test_invalid_single_call_output_is_not_replaced_by_keyword_heuristic():
    llm = _LLM("not json")
    engine = AbstractReasoningEngine(_Organism(), llm)

    with patch("core.llm_scheduler.llm_scheduler.is_busy", return_value=False), \
         patch.object(engine, "_score_abstractness", return_value=0.8):
        result = engine.reason("user-1", "A sufficiently abstract question?")

    assert len(llm.calls) == 1
    assert result is not None
    assert result.method == "failed"
    assert result.reason_code == "JSONDecodeError"
    assert result.llm_call_count == 1
    with patch.object(engine, "_score_abstractness", return_value=0.8):
        retry = engine.reason("user-1", "A sufficiently abstract question?")
    assert retry is not None and retry.method == "deferred"
    assert retry.reason_code == "per_user_cooldown"
    assert len(llm.calls) == 1


def test_failed_reanalysis_cannot_relabel_previous_same_text_as_current():
    from cognition.abstract_reasoning_engine import ARE_COOLDOWN_S, ReasoningResult

    llm = _LLM("not json")
    engine = AbstractReasoningEngine(_Organism(), llm)
    previous = ReasoningResult(
        user_id="user-1", method="llm", core_concept="old result",
        prompt_fragment="old result from an earlier turn",
    )
    engine._cache["user-1"] = previous
    engine._last_input["user-1"] = "a sufficiently abstract question?"
    engine._last_run["user-1"] = time.time() - ARE_COOLDOWN_S - 1

    with patch("core.llm_scheduler.llm_scheduler.is_busy", return_value=False), \
         patch.object(engine, "_score_abstractness", return_value=0.8):
        failed = engine.reason("user-1", "A sufficiently abstract question?")

    assert failed is not None and failed.method == "failed"
    assert engine._cache.get("user-1") is None
    assert engine._continuity_cache.get("user-1") is previous

    with patch.object(engine, "_score_abstractness", return_value=0.8):
        retry = engine.reason("user-1", "A sufficiently abstract question?")

    assert retry is not None and retry.method == "deferred"
    assert retry.reason_code == "per_user_cooldown"
    assert engine._cache.get("user-1") is None
    assert len(llm.calls) == 1


def test_busy_provider_defers_without_inventing_analogy_or_side_effects():
    engine = AbstractReasoningEngine(_Organism(), _LLM("{}"))
    previous = engine._deferred_result("user-1", 0.8, "prior")
    previous.method = "llm"
    previous.prompt_fragment = "verified prior analysis"
    previous.timestamp = time.time()
    engine._cache["user-1"] = previous

    with patch("core.llm_scheduler.llm_scheduler.is_busy", return_value=True), \
         patch.object(engine, "_apply_side_effects") as apply_effects:
        result = engine.reason("user-1", "How does identity remain stable while beliefs change?")

    assert result is not None
    assert result.method == "deferred"
    assert result.reason_code == "llm_scheduler_busy"
    assert result.prompt_fragment == ""
    assert result.llm_call_count == 0
    apply_effects.assert_not_called()
    fragment = engine.get_reasoning_fragment("user-1")
    assert "verified prior analysis" in fragment
    assert "chess" not in fragment


def test_cooldown_defers_new_topic_instead_of_using_default_analogy():
    llm = _LLM("{}")
    engine = AbstractReasoningEngine(_Organism(), llm)
    engine._last_run["user-1"] = time.time()
    engine._last_input["user-1"] = "a different earlier abstract question"

    with patch.object(engine, "_score_abstractness", return_value=0.8), \
         patch.object(engine, "_apply_side_effects") as apply_effects:
        result = engine.reason("user-1", "A new conceptual question about identity")

    assert result is not None and result.method == "deferred"
    assert result.reason_code == "per_user_cooldown"
    assert result.prompt_fragment == ""
    assert llm.calls == []
    apply_effects.assert_not_called()


def test_short_social_question_does_not_start_an_abstract_reasoning_call():
    llm = _LLM("{}")
    engine = AbstractReasoningEngine(_Organism(), llm)

    result = engine.reason("user-1", "How are you doing?")

    assert result is None
    assert llm.calls == []


def test_llm_manager_deferred_status_reaches_are_without_a_provider_call():
    from managers.llm_manager import LLMManager

    class _Provider:
        model = "test-model"

        def generate_background_result(self, *_args, **_kwargs):
            raise AssertionError("provider must not run while chat is active")

    llm = LLMManager(_Provider())
    llm._chat_active.set()
    engine = AbstractReasoningEngine(_Organism(), llm)

    with patch("core.llm_scheduler.llm_scheduler.is_busy", return_value=False), \
         patch.object(engine, "_score_abstractness", return_value=0.8):
        result = engine.reason("user-1", "A conceptual question deserving analysis")

    assert result is not None
    assert result.method == "deferred"
    assert result.reason_code == "interactive turn active"
    assert result.llm_call_count == 0


def test_are_explicit_foreground_call_runs_once_during_reserved_chat_turn():
    from managers.llm_manager import LLMManager, current_llm_call_role

    response = {
        "core_concept": "identity continuity",
        "components": ["memory", "belief revision"],
        "best_analogy_domain": "language",
        "structural_mapping": "Stable grammar supports changing sentences.",
        "confidence": 0.72,
        "derived_insight": "Continuity can depend on preserved relations.",
        "open_question": "Which relations should remain invariant?",
        "causal_antecedent": "",
        "causal_consequent": "",
        "prompt_note": "Keep the claim provisional.",
    }

    class _Provider:
        model = "test-model"

        def __init__(self):
            self.calls = 0
            self.roles = []

        def generate_background_result(self, *_args, **_kwargs):
            self.calls += 1
            self.roles.append(current_llm_call_role.get())
            return {
                "text": json.dumps(response), "status": "ok",
                "completion_verified": True,
            }

    provider = _Provider()
    llm = LLMManager(provider)
    llm._chat_active.set()
    engine = AbstractReasoningEngine(_Organism(), llm)

    with patch("core.llm_scheduler.llm_scheduler.is_busy", return_value=True), \
         patch.object(engine, "_score_abstractness", return_value=0.8):
        result = engine.reason(
            "user-1", "How can identity persist through change?",
            allow_interactive_turn=True,
        )

    assert result is not None and result.method == "llm"
    assert result.llm_call_count == 1
    assert result.core_concept == "identity continuity"
    assert provider.calls == 1
    assert provider.roles == ["foreground_auxiliary"]


def test_are_does_not_promote_unverified_provider_fallback_into_cognitive_state():
    from managers.llm_manager import LLMManager

    response = {
        "core_concept": "identity continuity",
        "components": ["memory", "belief revision"],
        "best_analogy_domain": "language",
        "structural_mapping": "Stable grammar supports changing sentences.",
        "confidence": 0.72,
        "derived_insight": "Continuity can depend on preserved relations.",
        "open_question": "Which relations should remain invariant?",
        "causal_antecedent": "",
        "causal_consequent": "",
        "prompt_note": "Keep the claim provisional.",
    }

    class _Provider:
        model = "test-model"

        def generate_background_result(self, *_args, **_kwargs):
            raise RuntimeError("native path unavailable")

        def _generate_messages(self, *_args, **_kwargs):
            return json.dumps(response)

    class _Curiosity:
        def __init__(self):
            self.questions = []

        def plant_question(self, question, priority):
            self.questions.append((question, priority))

    organism = _Organism()
    organism.curiosity_engine = _Curiosity()
    engine = AbstractReasoningEngine(organism, LLMManager(_Provider()))

    with patch("core.llm_scheduler.llm_scheduler.is_busy", return_value=False), \
         patch.object(engine, "_score_abstractness", return_value=0.8):
        result = engine.reason("user-1", "How can identity persist through change?")

    assert result is not None and result.method == "unverified"
    assert result.llm_call_count == 2
    assert result.reason_code == "provider_completion_unverified"
    assert result.completion_verified is False
    assert result.prompt_fragment == ""
    assert organism.curiosity_engine.questions == []
    assert engine._cache == {}


def test_are_rejects_stream_recovery_marked_incomplete_even_when_status_is_ok():
    response = {
        "core_concept": "identity continuity",
        "structural_mapping": "Stable grammar supports changing sentences.",
        "confidence": 0.72,
    }

    class _LLM:
        def generate_bare_result(self, *_args, **_kwargs):
            return {
                "text": json.dumps(response),
                "status": "ok",
                "completion_verified": False,
                "reason": "stream_fallback",
                "provider_call_count": 2,
            }

    engine = AbstractReasoningEngine(_Organism(), _LLM())
    with patch("core.llm_scheduler.llm_scheduler.is_busy", return_value=False), \
         patch.object(engine, "_score_abstractness", return_value=0.8), \
         patch.object(engine, "_apply_side_effects") as apply_effects:
        result = engine.reason("user-1", "How can identity persist through change?")

    assert result is not None and result.method == "unverified"
    assert result.reason_code == "provider_completion_unverified"
    assert result.llm_call_count == 2
    assert result.prompt_fragment == ""
    assert engine.get_reasoning_fragment("user-1") == ""
    apply_effects.assert_not_called()
