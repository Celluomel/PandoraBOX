"""Abstract reasoning should preserve its result while avoiding serial LLM passes."""

import json

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


def test_invalid_single_call_output_uses_existing_heuristic_fallback_path():
    llm = _LLM("not json")
    engine = AbstractReasoningEngine(_Organism(), llm)

    result = engine._llm_reason("user-1", "A sufficiently abstract question?", 0.8)

    assert len(llm.calls) == 1
    assert result is None


def test_short_social_question_does_not_start_an_abstract_reasoning_call():
    llm = _LLM("{}")
    engine = AbstractReasoningEngine(_Organism(), llm)

    result = engine.reason("user-1", "How are you doing?")

    assert result is None
    assert llm.calls == []
