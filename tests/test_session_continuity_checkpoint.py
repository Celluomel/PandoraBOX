import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from managers.llm_manager import LLMManager
from managers.session_manager import SessionManager, archived_context_for_explicit_recall
from core.state import _create_llm_with_restored_session


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

    def test_application_llm_startup_restores_persisted_dialogue(self):
        with tempfile.TemporaryDirectory() as folder:
            raw_path = Path(folder) / "session.json"
            summary_path = Path(folder) / "summary.json"
            with patch("managers.session_manager.SESSION_PATH", str(raw_path)), patch(
                "managers.session_manager.SUMMARY_PATH", str(summary_path)
            ):
                previous_session = SessionManager()
                previous_session.on_exchange_complete([
                    {"role": "user", "content": "we are discussing synthetic emotions"},
                    {"role": "assistant", "content": "They are computational state variables."},
                ])

                restarted_session = SessionManager()
                restarted_llm = SimpleNamespace(history=[], generate_bare=lambda *_a, **_k: "")
                with patch("core.state.create_llm_manager", return_value=restarted_llm), patch(
                    "core.state.get_session_manager", return_value=restarted_session
                ):
                    llm, receipt = _create_llm_with_restored_session()

        self.assertIs(llm, restarted_llm)
        self.assertTrue(receipt["restored"])
        self.assertEqual(llm.history[-2:], [
            {"role": "user", "content": "we are discussing synthetic emotions"},
            {"role": "assistant", "content": "They are computational state variables."},
        ])
        self.assertIs(restarted_session._llm_fn, llm.generate_bare)

    def test_session_restore_failure_does_not_block_llm_startup(self):
        llm = SimpleNamespace(history=[], generate_bare=lambda *_a, **_k: "")
        session = Mock()
        session.load_on_boot.side_effect = OSError("session unavailable")
        with patch("core.state.create_llm_manager", return_value=llm), patch(
            "core.state.get_session_manager", return_value=session
        ):
            started_llm, receipt = _create_llm_with_restored_session()

        self.assertIs(started_llm, llm)
        self.assertFalse(receipt["restored"])
        self.assertEqual(started_llm.history, [])

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

    def test_compression_rewrites_prior_summary_instead_of_appending_it(self):
        with tempfile.TemporaryDirectory() as folder:
            raw_path = Path(folder) / "session.json"
            summary_path = Path(folder) / "summary.json"
            captured = {}

            def summarize(prompt, _system):
                captured["prompt"] = prompt
                return "[CONTEXT FROM EARLIER IN THIS CONVERSATION]\nUpdated bounded summary."

            with patch("managers.session_manager.SESSION_PATH", str(raw_path)), patch(
                "managers.session_manager.SUMMARY_PATH", str(summary_path)
            ):
                session = SessionManager(llm_fn=summarize)
                session._summary = "Previous active objective. " + ("historical detail " * 900)
                history = [
                    {"role": "user", "content": f"new archived user turn {i}"}
                    for i in range(10)
                ]
                session._save_raw(history)

                self.assertTrue(session._compress_unlocked())
                saved = json.loads(summary_path.read_text(encoding="utf-8"))["text"]

        self.assertIn("Previously compressed conversation context", captured["prompt"])
        self.assertIn("new archived user turn 0", captured["prompt"])
        self.assertEqual(saved, "[CONTEXT FROM EARLIER IN THIS CONVERSATION]\nUpdated bounded summary.")
        self.assertNotIn("[ADDITIONAL CONTEXT]", saved)

    def test_compression_preserves_provenance_labelled_exact_source_excerpt(self):
        with tempfile.TemporaryDirectory() as folder:
            raw_path = Path(folder) / "session.json"
            summary_path = Path(folder) / "summary.json"

            def summarize(_prompt, _system):
                return "[CONTEXT FROM EARLIER IN THIS CONVERSATION]\nRecent task state only."

            with patch("managers.session_manager.SESSION_PATH", str(raw_path)), patch(
                "managers.session_manager.SUMMARY_PATH", str(summary_path)
            ):
                session = SessionManager(llm_fn=summarize)
                source = (
                    'Retrieved user-authored source (verbatim): '
                    '"For this audit, remember the exact marker: cobalt fern 8421."'
                )
                session._summary = "Prior archive.\n" + source
                history = [
                    {"role": "user", "content": f"new archived user turn {i}"}
                    for i in range(10)
                ]
                session._save_raw(history)

                self.assertTrue(session._compress_unlocked())
                saved = json.loads(summary_path.read_text(encoding="utf-8"))["text"]

        self.assertIn("Recent task state only.", saved)
        self.assertIn("Retrieved user-authored source (verbatim):", saved)
        self.assertIn("cobalt fern 8421", saved)

    def test_legacy_oversized_summary_is_bounded_but_not_injected_into_history(self):
        with tempfile.TemporaryDirectory() as folder:
            raw_path = Path(folder) / "session.json"
            summary_path = Path(folder) / "summary.json"
            raw_path.write_text(json.dumps({"history": []}), encoding="utf-8")
            summary_path.write_text(json.dumps({
                "text": "ACTIVE OBJECTIVE " + ("middle " * 3000) + " LATEST STATE",
                "saved_at": "test",
            }), encoding="utf-8")

            with patch("managers.session_manager.SESSION_PATH", str(raw_path)), patch(
                "managers.session_manager.SUMMARY_PATH", str(summary_path)
            ):
                session = SessionManager()
                llm = SimpleNamespace(history=[])
                receipt = session.load_on_boot(llm)

        self.assertTrue(receipt["restored"])
        self.assertEqual(llm.history, [])
        self.assertLessEqual(len(llm.archived_conversation_context), 10_000)
        self.assertIn("ACTIVE OBJECTIVE", llm.archived_conversation_context)
        self.assertIn("LATEST STATE", llm.archived_conversation_context)
        self.assertIn("Middle of older session summary omitted", llm.archived_conversation_context)

    def test_archived_claim_is_separate_from_current_checking_turn(self):
        with tempfile.TemporaryDirectory() as folder:
            raw_path = Path(folder) / "session.json"
            summary_path = Path(folder) / "summary.json"
            raw_path.write_text(json.dumps({"history": [
                {"role": "user", "content": "checking"},
            ]}), encoding="utf-8")
            summary_path.write_text(json.dumps({
                "text": (
                    "Assistant replied/claimed: The user confirmed the next step. "
                    "The marker is LUMINA-MEMORY-8B2R."
                ),
                "saved_at": "test",
            }), encoding="utf-8")

            with patch("managers.session_manager.SESSION_PATH", str(raw_path)), patch(
                "managers.session_manager.SUMMARY_PATH", str(summary_path)
            ):
                session = SessionManager()
                llm = SimpleNamespace(history=[])
                session.load_on_boot(llm)

        self.assertEqual(llm.history, [{"role": "user", "content": "checking"}])
        self.assertIn("The user confirmed the next step", llm.archived_conversation_context)
        self.assertEqual(archived_context_for_explicit_recall(llm, False), "")
        self.assertIn(
            "LUMINA-MEMORY-8B2R",
            archived_context_for_explicit_recall(llm, True),
        )

    def test_explicit_recall_archive_requires_recall_intent(self):
        llm = SimpleNamespace(
            archived_conversation_context="Historical marker: LUMINA-MEMORY-8B2R",
        )
        self.assertEqual(archived_context_for_explicit_recall(llm, False), "")
        self.assertEqual(
            archived_context_for_explicit_recall(llm, True),
            llm.archived_conversation_context,
        )

    def test_fallback_summary_stays_bounded_across_compressions(self):
        session = SessionManager.__new__(SessionManager)
        session._llm_fn = None
        previous = "Older objective. " + ("old context " * 1500)

        summary = session._run_compression(
            "USER: New request.\n\nASSISTANT: New answer.",
            previous_summary=previous,
        )

        self.assertLessEqual(len(summary), 10_000)
        self.assertIn("New request.", summary)
        self.assertIn("New answer.", summary)

    def test_restored_summary_is_not_duplicated_in_raw_session_history(self):
        with tempfile.TemporaryDirectory() as folder:
            raw_path = Path(folder) / "session.json"
            summary_path = Path(folder) / "summary.json"
            synthetic = {
                "role": "assistant",
                "content": "[MEMORY FROM PREVIOUS SESSION]\nOld compressed context",
            }
            raw_path.write_text(json.dumps({"history": [
                synthetic,
                {"role": "user", "content": "recent question"},
                {"role": "assistant", "content": "recent answer"},
            ]}), encoding="utf-8")
            summary_path.write_text(json.dumps({
                "text": "[CONTEXT FROM EARLIER IN THIS CONVERSATION]\nCanonical summary",
                "saved_at": "test",
            }), encoding="utf-8")

            with patch("managers.session_manager.SESSION_PATH", str(raw_path)), patch(
                "managers.session_manager.SUMMARY_PATH", str(summary_path)
            ):
                session = SessionManager()
                llm = SimpleNamespace(history=[])
                session.load_on_boot(llm)
                session.on_exchange_complete(llm.history)
                persisted = json.loads(raw_path.read_text(encoding="utf-8"))["history"]

        self.assertEqual(persisted, [
            {"role": "user", "content": "recent question"},
            {"role": "assistant", "content": "recent answer"},
        ])
        self.assertFalse(any(
            str(item.get("content", "")).startswith((
                "[MEMORY FROM PREVIOUS SESSION",
                "[ARCHIVED CONVERSATION CONTEXT",
            ))
            for item in persisted
        ))

    def test_llm_reload_restores_summary_and_raw_turns_once(self):
        with tempfile.TemporaryDirectory() as folder:
            raw_path = Path(folder) / "session.json"
            summary_path = Path(folder) / "summary.json"
            raw_path.write_text(json.dumps({"history": [
                {"role": "user", "content": "recent question"},
                {"role": "assistant", "content": "recent answer"},
            ]}), encoding="utf-8")
            summary_path.write_text(json.dumps({
                "text": "[CONTEXT FROM EARLIER IN THIS CONVERSATION]\nCanonical summary",
                "saved_at": "test",
            }), encoding="utf-8")

            with patch("managers.session_manager.SESSION_PATH", str(raw_path)), patch(
                "managers.session_manager.SUMMARY_PATH", str(summary_path)
            ):
                session = SessionManager()
                session.load_on_boot(SimpleNamespace(history=[]))
                reloaded = SimpleNamespace(history=[])
                count = session.restore_after_reload(reloaded)

        self.assertEqual(count, 2)
        self.assertEqual(reloaded.archived_conversation_context, "[CONTEXT FROM EARLIER IN THIS CONVERSATION]\nCanonical summary")
        self.assertEqual(reloaded.history, [
            {"role": "user", "content": "recent question"},
            {"role": "assistant", "content": "recent answer"},
        ])

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
