import json
import asyncio
import threading
import unittest

from cognition.persona_bridge import PersonaBridge
from cognition.self_description import affect_advisory_context
from core.turn_execution_context import current_turn_id


class _ReviewManager:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def generate_bare_result(self, *_args, **_kwargs):
        self.calls += 1
        return {"status": "ok", "text": json.dumps(self.payload)}


def _bridge_for_review(manager):
    bridge = PersonaBridge.__new__(PersonaBridge)
    bridge._external_llm_fn = manager.generate_bare_result
    bridge._turn_trace_lock = threading.RLock()
    bridge._last_turn_trace = {"turn_id": "turn-phase1", "stages": {}}
    bridge._turn_trace_history = []
    bridge._turn_stage_health = {}
    bridge._reflection_lock = threading.RLock()
    bridge._reflection_epochs = {"fred": 3}
    bridge._reflection_results = {}
    return bridge


class ConversationAuthorityPhase1Tests(unittest.TestCase):
    def test_next_turn_waits_for_prior_profile_learning_before_prompt_assembly(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._response_turn_lock = asyncio.Lock()
        bridge._pending_profile_learning = {}
        bridge._pending_memory_learning = {}
        bridge._last_turn_trace = {"turn_id": "turn-profile-2", "cognitive_scope_id": "fred"}
        bridge._turn_sequence = 0
        bridge._turn_trace_lock = threading.RLock()
        bridge._turn_trace_history = []
        bridge._turn_stage_health = {}
        profile_write_started = asyncio.Event()
        allow_profile_write = asyncio.Event()
        memory_write_started = asyncio.Event()
        allow_memory_write = asyncio.Event()
        implementation_started = asyncio.Event()
        observed_barriers = []

        async def exercise():
            loop = asyncio.get_running_loop()
            async def profile_write():
                profile_write_started.set()
                await allow_profile_write.wait()
                return {"status": "updated", "persisted": True}

            predecessor = loop.create_task(profile_write())
            bridge._pending_profile_learning["fred"] = {
                "future": predecessor,
                "turn_id": "turn-profile-1",
            }
            async def memory_write():
                memory_write_started.set()
                await allow_memory_write.wait()
                return {"status": "completed", "persisted": True}

            memory_predecessor = loop.create_task(memory_write())
            bridge._pending_memory_learning["fred"] = {
                "future": memory_predecessor,
                "turn_id": "turn-profile-1",
            }

            def fake_impl(*_args, **kwargs):
                async def stream():
                    bridge._start_turn_trace("fred", turn_id=kwargs["turn_id"])
                    bridge._record_turn_stage(
                        "turn_input", "received", output="next turn",
                        turn_id=kwargs["turn_id"],
                    )
                    barrier = kwargs["profile_learning_barrier"]
                    bridge._record_turn_stage(
                        "profile_learning_predecessor_barrier",
                        "completed" if barrier["status"] == "predecessor_completed" else "failed",
                        output={"type": "profile_learning_barrier_receipt", **barrier},
                        turn_id=kwargs["turn_id"],
                    )
                    memory_barrier = kwargs["memory_learning_barrier"]
                    bridge._record_turn_stage(
                        "memory_learning_predecessor_barrier",
                        "completed" if memory_barrier["status"] == "predecessor_completed" else "failed",
                        output={"type": "memory_learning_barrier_receipt", **memory_barrier},
                        turn_id=kwargs["turn_id"],
                    )
                    implementation_started.set()
                    observed_barriers.extend((barrier, memory_barrier))
                    yield {
                        "__meta__": True,
                        "raw": "ok",
                        "speech": "ok",
                        "emotion": "neutral",
                        "intensity": 0.1,
                    }
                return stream()

            bridge._get_response_stream_impl = fake_impl

            async def consume():
                return [chunk async for chunk in bridge.get_response_stream("next turn", "fred")]

            response_task = asyncio.create_task(consume())
            await profile_write_started.wait()
            await memory_write_started.wait()
            await asyncio.sleep(0)
            self.assertFalse(implementation_started.is_set())
            allow_profile_write.set()
            await asyncio.sleep(0)
            self.assertFalse(implementation_started.is_set())
            allow_memory_write.set()
            response_chunks = await response_task
            self.assertTrue(implementation_started.is_set())
            return response_chunks

        response_chunks = asyncio.run(exercise())
        self.assertEqual(observed_barriers, [{
            "status": "predecessor_completed",
            "learning_status": "updated",
            "persisted": True,
            "predecessor_turn_id": "turn-profile-1",
        }, {
            "status": "predecessor_completed",
            "learning_status": "completed",
            "persisted": True,
            "predecessor_turn_id": "turn-profile-1",
        }])
        current_turn_id = response_chunks[-1]["turn_id"]
        stage = bridge.get_turn_trace(current_turn_id)["stages"][
            "profile_learning_predecessor_barrier"
        ]
        self.assertEqual(stage["status"], "completed")
        self.assertEqual(stage["output_summary"]["predecessor_turn_id"], "turn-profile-1")
        self.assertNotIn("profile_text", stage["output_summary"])
        memory_stage = bridge.get_turn_trace(current_turn_id)["stages"][
            "memory_learning_predecessor_barrier"
        ]
        self.assertEqual(memory_stage["status"], "completed")
        self.assertEqual(memory_stage["output_summary"]["predecessor_turn_id"], "turn-profile-1")

    def test_chat_marker_covers_prompt_building_and_is_cleared_after_turn(self):
        class Provider:
            def __init__(self):
                self.model = "stub"
                self.calls = 0

            def generate_background_result(self, *_args, **_kwargs):
                self.calls += 1
                return {"text": "background result", "status": "ok"}

            def generate_with_history_stream(self, *_args, **_kwargs):
                yield "unused"

        from managers.llm_manager import LLMManager
        provider = Provider()
        manager = LLMManager(provider)
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._llm_stream_fn = manager.generate_stream
        bridge._response_turn_lock = asyncio.Lock()
        bridge._turn_sequence = 0
        bridge._last_turn_trace = {"turn_id": "", "cognitive_scope_id": "fred"}

        async def implementation(*_args, **_kwargs):
            assert manager._chat_active.is_set()
            deferred = manager.generate_bare_result("background thought")
            assert deferred["status"] == "deferred"
            assert provider.calls == 0
            yield "answer"
            yield {"__meta__": True, "status": "completed"}

        bridge._get_response_stream_impl = implementation

        async def exercise():
            chunks = [chunk async for chunk in bridge.get_response_stream("hello")]
            self.assertEqual(chunks, ["answer", {"__meta__": True, "status": "completed", "turn_id": "", "cognitive_scope_id": "fred"}])
            self.assertFalse(manager._chat_active.is_set())

        asyncio.run(exercise())

    def test_chat_marker_is_cleared_when_consumer_cancels_stream(self):
        class Provider:
            def __init__(self):
                self.model = "stub"

            def generate_with_history_stream(self, *_args, **_kwargs):
                yield "unused"

        from managers.llm_manager import LLMManager
        manager = LLMManager(Provider())
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._llm_stream_fn = manager.generate_stream
        bridge._response_turn_lock = asyncio.Lock()
        bridge._turn_sequence = 0
        bridge._last_turn_trace = {"turn_id": "", "cognitive_scope_id": "fred"}

        async def implementation(*_args, **_kwargs):
            assert manager._chat_active.is_set()
            yield "first token"
            await asyncio.sleep(60)

        bridge._get_response_stream_impl = implementation

        async def exercise():
            stream = bridge.get_response_stream("hello")
            self.assertEqual(await anext(stream), "first token")
            self.assertTrue(manager._chat_active.is_set())
            await stream.aclose()
            self.assertFalse(manager._chat_active.is_set())

        asyncio.run(exercise())

    def test_post_response_review_is_advisory_and_records_followup_without_replacing_answer(self):
        manager = _ReviewManager({
            "relevant": False,
            "claim_basis": "subjective_or_creative",
            "evidence_support": "insufficient_evidence",
            "contract_compliant": False,
            "material_issues": ["Answer may not address the request."],
            "repair": "A proposed repair is not delivered.",
        })
        bridge = _bridge_for_review(manager)
        original_answer = "Delivered answer remains the same."

        result = bridge.run_deferred_semantic_validation(
            "What is the audit status?", original_answer, "fred",
            turn_id="turn-phase1", reflection_epoch=3,
        )

        self.assertEqual(result, {"status": "completed"})
        self.assertEqual(manager.calls, 1)
        self.assertEqual(original_answer, "Delivered answer remains the same.")
        receipt = bridge._last_turn_trace["stages"]["semantic_answer_validation"]
        self.assertEqual(receipt["status"], "flagged_advisory")
        self.assertNotIn(original_answer, repr(receipt))
        self.assertIn("unverified advisory", bridge._reflection_results["fred"][1])

    def test_post_response_review_provider_call_is_correlated_to_originating_turn(self):
        observed = []

        class CorrelationManager:
            def generate_bare_result(self, *_args, **_kwargs):
                observed.append(current_turn_id.get())
                return {"status": "ok", "text": json.dumps({
                    "relevant": True,
                    "claim_basis": "subjective_or_creative",
                    "evidence_support": "insufficient_evidence",
                    "contract_compliant": True,
                    "material_issues": [],
                    "repair": "",
                })}

        bridge = _bridge_for_review(CorrelationManager())
        result = bridge.run_deferred_semantic_validation(
            "How is the audit?", "It is progressing.", "fred", turn_id="trace-42",
        )

        self.assertEqual(result, {"status": "completed"})
        self.assertEqual(observed, ["trace-42"])
        self.assertEqual(current_turn_id.get(), "")


    def test_post_response_collection_is_scheduled_without_waiting(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        recorded = []
        bridge._record_turn_stage = lambda *args, **kwargs: recorded.append((args, kwargs))
        finished = asyncio.Event()

        async def slow_effect():
            await asyncio.sleep(0.03)
            finished.set()

        async def exercise():
            task = bridge._schedule_post_response_collection(
                slow_effect(), "turn-phase1", ("response_learning_and_memory",)
            )
            self.assertFalse(finished.is_set())
            self.assertTrue(task in bridge._post_response_tasks)
            await task
            self.assertTrue(finished.is_set())
            await asyncio.sleep(0)
            self.assertFalse(bridge._post_response_tasks)

        asyncio.run(exercise())
        self.assertEqual(recorded[0][0][1], "scheduled_post_response")
        self.assertEqual(recorded[0][1]["turn_id"], "turn-phase1")

    def test_post_response_scheduler_preserves_completed_learning_receipts(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.RLock()
        bridge._turn_trace_history = []
        bridge._last_turn_trace = {
            "turn_id": "turn-memory-1",
            "stages": {"response_learning_and_memory": {"status": "completed"}},
            "context_sources": {},
            "stage_events": [],
        }
        bridge._post_response_tasks = set()

        async def exercise():
            task = bridge._schedule_post_response_collection(
                asyncio.sleep(0), "turn-memory-1", ("response_learning_and_memory",)
            )
            await task

        asyncio.run(exercise())
        self.assertEqual(
            bridge.get_turn_trace("turn-memory-1")["stages"][
                "response_learning_and_memory"
            ]["status"],
            "completed",
        )

    def test_depth_review_uses_the_stream_parameter_not_an_outer_local(self):
        import inspect
        source = inspect.getsource(PersonaBridge._stream_with_full_lifecycle)
        self.assertIn("displayed_cognitive_trace is not None", source)
        self.assertNotIn("_displayed_trace", source)

    def test_local_camera_wording_stays_on_the_main_conversation_path(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._pending_body_plans = {}
        bridge._is_developmental_autonomy_audit_request = lambda _text: False
        self.assertIsNone(bridge.handle_body_chat_turn(
            "Morning—glad to see the system awake.", "fred"
        ))

    def test_semantic_trace_distinguishes_single_pass_from_incomplete_review(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.RLock()
        bridge._turn_trace_history = []
        bridge._last_turn_trace = {
            "turn_id": "turn-phase1",
            "stages": {"semantic_answer_validation": {"status": "not_required_single_pass"}},
        }
        bridge._finish_turn_trace("completed", "turn-phase1")
        summary = bridge.get_last_turn_trace()["semantic_answer_validation"]
        self.assertEqual(summary["status"], "review_not_required_single_pass")
        self.assertEqual(summary["stage_status"], "not_required_single_pass")

    def test_audit_launcher_records_provider_calls_and_module_execution(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        launcher = (root / "start.bat").read_text(encoding="utf-8-sig")
        self.assertIn("scripts\\audit_llm_calls.py app.py", launcher)

    def test_affect_advisory_is_qualitative_and_does_not_expose_channel_values(self):
        context = affect_advisory_context("I feel strongly warm and curious")

        self.assertIn("software-state signal", context)
        self.assertIn("warm and curious", context)
        self.assertNotIn("0.91", context)
        self.assertNotIn("warmth=", context)
