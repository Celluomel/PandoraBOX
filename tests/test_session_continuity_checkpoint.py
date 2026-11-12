import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from managers.llm_manager import LLMManager
from managers.session_manager import SessionManager


class _Provider:
    model = "test-model"

    def generate_with_history_stream(self, prompt, history, system_prompt=None, **kwargs):
        yield "completed answer"

    def generate_with_history(self, prompt, history, system_prompt=None, **kwargs):
        return "completed answer"


class SessionContinuityCheckpointTests(unittest.TestCase):
    def _manager(self, session):
        manager = LLMManager.__new__(LLMManager)
        manager.provider = _Provider()
        manager.text_model = "test-model"
        manager.history = []
        manager._session = session
        manager._provider_lock = threading.Lock()
        manager._chat_active = threading.Event()
        manager._trim_history = lambda: None
        return manager

    def test_streamed_exchange_is_checkpointed_after_assistant_reply(self):
        session = Mock()
        manager = self._manager(session)

        self.assertEqual(
            list(manager.generate_stream("resume the task")),
            ["completed answer"],
        )

        session.on_exchange_complete.assert_called_once()
        saved_history = session.on_exchange_complete.call_args.args[0]
        self.assertEqual(saved_history[-2:], [
            {"role": "user", "content": "resume the task"},
            {"role": "assistant", "content": "completed answer"},
        ])

    def test_stream_persists_canonical_user_turn_when_generation_prompt_is_enriched(self):
        session = Mock()
        manager = self._manager(session)
        model_prompt = (
            "What is the latest audit result?\n\n"
            "Silently follow the private factual self-report contract."
        )

        self.assertEqual(
            list(manager.generate_stream(
                model_prompt,
                history_user_input="What is the latest audit result?",
            )),
            ["completed answer"],
        )

        saved_history = session.on_exchange_complete.call_args.args[0]
        self.assertEqual(saved_history[-2:], [
            {"role": "user", "content": "What is the latest audit result?"},
            {"role": "assistant", "content": "completed answer"},
        ])
        self.assertNotIn("private factual", saved_history[-2]["content"])

    def test_nonstream_exchange_is_checkpointed_after_assistant_reply(self):
        session = Mock()
        manager = self._manager(session)

        self.assertEqual(manager.generate("resume the task"), "completed answer")

        session.on_exchange_complete.assert_called_once()
        self.assertEqual(
            session.on_exchange_complete.call_args.args[0][-1]["content"],
            "completed answer",
        )

    def test_session_checkpoint_is_written_before_return(self):
        with tempfile.TemporaryDirectory() as folder:
            raw_path = Path(folder) / "session.json"
            summary_path = Path(folder) / "summary.json"
            with patch("managers.session_manager.SESSION_PATH", str(raw_path)), patch(
                "managers.session_manager.SUMMARY_PATH", str(summary_path)
            ):
                session = SessionManager()
                history = [
                    {"role": "user", "content": "continue audit"},
                    {"role": "assistant", "content": "verified result"},
                ]
                session.on_exchange_complete(history)
                persisted = json.loads(raw_path.read_text(encoding="utf-8"))

        self.assertEqual(persisted["history"], history)

    def test_completed_exchange_restores_after_new_session_manager_boot(self):
        with tempfile.TemporaryDirectory() as folder:
            raw_path = Path(folder) / "session.json"
            summary_path = Path(folder) / "summary.json"
            with patch("managers.session_manager.SESSION_PATH", str(raw_path)), patch(
                "managers.session_manager.SUMMARY_PATH", str(summary_path)
            ):
                original_session = SessionManager()
                manager = self._manager(original_session)
                list(manager.generate_stream("resume the audit"))

                restarted_session = SessionManager()
                restarted_manager = SimpleNamespace(history=[])
                boot = restarted_session.load_on_boot(restarted_manager)

        self.assertTrue(boot["restored"])
        self.assertEqual(restarted_manager.history[-2:], [
            {"role": "user", "content": "resume the audit"},
            {"role": "assistant", "content": "completed answer"},
        ])

    def test_fallback_compression_keeps_both_sides_as_unverified_history(self):
        session = SessionManager.__new__(SessionManager)
        session._llm_fn = None

        summary = session._run_compression(
            "USER: Continue the cognitive audit.\n\n"
            "ASSISTANT: The verified result is 3/4 checks passed.\n\n"
            "USER: Which checks remain?"
        )

        self.assertIn("User asked/stated: Continue the cognitive audit.", summary)
        self.assertIn("Assistant replied/claimed: The verified result is 3/4 checks passed.", summary)
        self.assertIn("not independently verified", summary)
        self.assertIn("User asked/stated: Which checks remain?", summary)

    def test_checkpoint_is_not_blocked_by_slow_compression(self):
        with tempfile.TemporaryDirectory() as folder:
            raw_path = Path(folder) / "session.json"
            summary_path = Path(folder) / "summary.json"
            entered_compressor = threading.Event()
            release_compressor = threading.Event()

            def slow_compressor(prompt, system):
                entered_compressor.set()
                release_compressor.wait(timeout=3)
                return "[CONTEXT FROM EARLIER IN THIS CONVERSATION]\ncompressed history"

            with patch("managers.session_manager.SESSION_PATH", str(raw_path)), patch(
                "managers.session_manager.SUMMARY_PATH", str(summary_path)
            ):
                session = SessionManager(llm_fn=slow_compressor)
                history = [
                    {"role": "user", "content": f"question {i}"}
                    for i in range(16)
                ]
                session.on_exchange_complete(history)

                compressor = threading.Thread(target=session._compress, args=(history,))
                compressor.start()
                self.assertTrue(entered_compressor.wait(timeout=1))

                newer_history = history + [
                    {"role": "assistant", "content": "new answer"}
                ]
                checkpoint = threading.Thread(
                    target=session.on_exchange_complete, args=(newer_history,)
                )
                checkpoint.start()
                checkpoint.join(timeout=0.5)
                self.assertFalse(checkpoint.is_alive(), "checkpoint waited on compression inference")

                persisted = json.loads(raw_path.read_text(encoding="utf-8"))
                self.assertEqual(persisted["history"], newer_history)

                release_compressor.set()
                compressor.join(timeout=2)
                self.assertFalse(compressor.is_alive())

                # Compression may legitimately compact the newer checkpoint,
                # but it must retain the latest exchange in its raw tail.
                persisted = json.loads(raw_path.read_text(encoding="utf-8"))
                self.assertEqual(
                    persisted["history"][-1],
                    {"role": "assistant", "content": "new answer"},
                )


if __name__ == "__main__":
    unittest.main()
