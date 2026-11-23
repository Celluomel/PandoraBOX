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

    result = engine._llm_reason("user-1", "A sufficiently abstract question?", 0.8)

    assert len(llm.calls) == 1
    assert result is None


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
