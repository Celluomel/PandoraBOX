import threading
import unittest
from unittest.mock import Mock


class FastRoundManagerTest(unittest.TestCase):
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
