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
            "Bonjour", "Choose direct or deep", model="microsoft/Phi-4-mini-reasoning"
        )

        self.assertIn('"route":"direct"', result)
        manager.provider.generate.assert_called_once()
        self.assertEqual(
            manager.provider.generate.call_args.kwargs["model"],
            "microsoft/Phi-4-mini-reasoning",
        )

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


if __name__ == "__main__":
    unittest.main()
