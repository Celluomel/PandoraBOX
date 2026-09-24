import threading
import unittest
import importlib.util
from pathlib import Path
from unittest.mock import Mock

_reply_guard_spec = importlib.util.spec_from_file_location(
    "reply_guard_test", Path(__file__).resolve().parents[1] / "cognition" / "reply_guard.py"
)
_reply_guard = importlib.util.module_from_spec(_reply_guard_spec)
_reply_guard_spec.loader.exec_module(_reply_guard)
repeats_recent_assistant_reply = _reply_guard.repeats_recent_assistant_reply


class FastRoundManagerTest(unittest.TestCase):
    def test_repeated_long_assistant_answer_is_detected(self):
        answer = "I am ready to discuss any topic that interests you; tell me what you prefer. " * 2
        history = [{"role": "assistant", "content": answer}]
        self.assertTrue(repeats_recent_assistant_reply(answer, history))

    def test_short_or_new_answer_is_not_rejected(self):
        history = [{"role": "assistant", "content": "Good morning."}]
        self.assertFalse(repeats_recent_assistant_reply("Good morning.", history))
        self.assertFalse(repeats_recent_assistant_reply("A different answer with new detail.", history))

    def make_manager(self):
        from managers.llm_manager import LLMManager

        manager = object.__new__(LLMManager)
        manager._provider_lock = threading.Lock()
        manager.provider = Mock()
        manager.provider.generate.return_value = '{"route":"direct","answer":"Salut."}'
        manager.text_model = "primary-model"
        return manager

    def test_fast_round_uses_selected_model_without_history(self):
        manager = self.make_manager()

        result = manager.generate_fast_round(
            "Bonjour", "Choose direct or deep", model="microsoft/Phi-4-mini-reasoning",
            max_tokens=512,
        )

        self.assertIn('"route":"direct"', result)
        manager.provider.generate.assert_called_once()
        self.assertEqual(
            manager.provider.generate.call_args.kwargs["model"],
            "microsoft/Phi-4-mini-reasoning",
        )
        self.assertEqual(manager.provider.generate.call_args.kwargs["max_tokens"], 512)

    def test_fast_round_skips_when_provider_is_busy(self):
        manager = self.make_manager()
        manager._provider_lock.acquire()
        try:
            self.assertIsNone(manager.generate_fast_round(
                "Bonjour", "Choose direct or deep", model="microsoft/Phi-4-mini-reasoning"
            ))
        finally:
            manager._provider_lock.release()
        manager.provider.generate.assert_not_called()

    def test_fast_round_caps_token_and_elapsed_time_limits(self):
        manager = self.make_manager()

        manager.generate_fast_round(
            "Bonjour", "Choose direct or deep", model="microsoft/Phi-4-mini-reasoning",
            max_tokens=5000, timeout=90,
        )

        self.assertEqual(manager.provider.generate.call_args.kwargs["max_tokens"], 768)
        self.assertEqual(manager.provider.generate.call_args.kwargs["timeout"], 30.0)


if __name__ == "__main__":
    unittest.main()
