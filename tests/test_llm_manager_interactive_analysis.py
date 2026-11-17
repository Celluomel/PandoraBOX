import threading
import unittest
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_semantic_spec = importlib.util.spec_from_file_location(
    "semantic_response_validation_under_test",
    ROOT / "cognition" / "semantic_response_validation.py",
)
_semantic_module = importlib.util.module_from_spec(_semantic_spec)
_semantic_spec.loader.exec_module(_semantic_module)
review_response = _semantic_module.review_response
from managers.llm_manager import LLMManager


class _EmptyNonStreamingProvider:
    model = "test-model"

    def _generate_messages(self, _messages, **_kwargs):
        return ""

    def _generate_messages_stream(self, _messages, **_kwargs):
        yield {"type": "reasoning", "text": "hidden reasoning"}
        yield {
            "type": "content",
            "text": (
                '{"relevant":true,"claim_basis":"factual",'
                '"evidence_support":"supported","contract_compliant":true,'
                '"material_issues":[],"repair":""}'
            ),
        }


class _LengthCappedStructuredProvider:
    model = "test-model"

    def __init__(self):
        self.output_limits = []

    def _generate_messages_stream(self, _messages, **kwargs):
        self.output_limits.append(kwargs["max_tokens"])
        if len(self.output_limits) == 1:
            yield {"type": "reasoning", "text": "bounded reasoning"}
            yield {"type": "finish", "reason": "length"}
            return
        yield {
            "type": "content",
            "text": (
                '{"relevant":true,"claim_basis":"factual",'
                '"evidence_support":"supported","contract_compliant":true,'
                '"material_issues":[],"repair":""}'
            ),
        }
        yield {"type": "finish", "reason": "stop"}


class InteractiveAnalysisTests(unittest.TestCase):
    def test_empty_nonstream_completion_uses_visible_stream_content_during_turn(self):
        manager = LLMManager.__new__(LLMManager)
        manager.provider = _EmptyNonStreamingProvider()
        manager.text_model = "test-model"
        manager._provider_lock = threading.Lock()
        manager._chat_active = threading.Event()
        manager._chat_active.set()

        result = review_response(
            manager.generate_interactive_analysis,
            request="How much is 2 + 2?",
            response="Four.",
            context="The arithmetic result is 4.",
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["claim_basis"], "factual")

    def test_length_capped_structured_review_retries_with_bounded_budget(self):
        provider = _LengthCappedStructuredProvider()
        manager = LLMManager.__new__(LLMManager)
        manager.provider = provider
        manager.text_model = "test-model"
        manager._provider_lock = threading.Lock()
        manager._chat_active = threading.Event()

        result = review_response(
            manager.generate_interactive_analysis,
            request="How much is 2 + 2?",
            response="Four.",
            context="The arithmetic result is 4.",
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(provider.output_limits, [768, 1536])


if __name__ == "__main__":
    unittest.main()
