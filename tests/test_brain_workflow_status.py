import ast
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core.state import AppState
from core.internal_loop import InternalThoughtLoop
from cognition.persona_bridge import PersonaBridge


class _Task:
    def __init__(self, done=False):
        self._done = done

    def done(self):
        return self._done


class _CallbackTask:
    def __init__(self):
        self.callback = None

    def add_done_callback(self, callback):
        self.callback = callback


class BrainWorkflowStatusTests(unittest.TestCase):
    def _state(self):
        state = AppState.__new__(AppState)
        loop = SimpleNamespace(
            _thread=threading.current_thread(),
            _running=True,
            _slow_cycle_count=12,
            _last_fast_cycle_at=100.0,
            _fast_cycle_error_count=1,
            _last_slow_cycle_at=90.0,
            _slow_cycle_error_count=2,
            _last_slow_cycle_error_type="ValueError",
            _tte=object(),
            _cde=None,
            _dts=object(),
            _phase1=object(),
            _phase2=None,
            _long_horizon_planner=None,
        )
        organism = SimpleNamespace(
            _loop=loop,
            workspace=object(),
            energy=object(),
            attention=object(),
            curiosity=object(),
            goal_ecology=object(),
            arbitration=object(),
            meta_cognition=object(),
            semantic_memory=None,
        )
        persona = SimpleNamespace(
            _organism=organism,
            _chat_stage="idle",
            is_ready=True,
            get_last_turn_trace=lambda: {"status": "completed"},
            get_goal_means_status=lambda: {},
        )
        state.ready = True
        state.initializing = False
        state.llm = object()
        state.persona = persona
        state.memory = object()
        state.vision = None
        state._vision_attached_to_cognition = False
        state.orchestrator = SimpleNamespace(
            _running=True,
            _task=_Task(done=False),
            _cycle_count=31,
            _last_activity="user_message",
            _last_cycle_at=110.0,
            _cycle_error_count=3,
            _last_cycle_error_type="RuntimeError",
        )
        return state

    def test_status_distinguishes_initialized_modules_from_loop_execution_health(self):
        status = self._state().brain_workflow_status()["components"]

        organism = status["cognitive_organism"]
        self.assertTrue(organism["initialized_modules"]["energy"])
        self.assertFalse(organism["initialized_modules"]["semantic_memory"])

        loop = status["internal_thought_loop"]
        self.assertTrue(loop["thread_alive"])
        self.assertEqual(loop["slow_cycles"], 12)
        self.assertEqual(loop["slow_cycle_errors"], 2)
        self.assertEqual(loop["last_slow_cycle_error_type"], "ValueError")
        self.assertTrue(loop["initialized_modules"]["tte"])
        self.assertFalse(loop["initialized_modules"]["cde"])
        self.assertFalse(loop["initialized_modules"]["long_horizon_planner"])

    def test_status_does_not_call_orchestrator_running_without_live_task(self):
        state = self._state()
        state.orchestrator._task = _Task(done=True)
        status = state.brain_workflow_status()["components"]["autonomous_orchestrator"]

        self.assertFalse(status["running"])
        self.assertTrue(status["requested_running"])
        self.assertFalse(status["task_alive"])
        self.assertEqual(status["cycles"], 31)
        self.assertEqual(status["cycle_errors"], 3)
        self.assertEqual(status["last_cycle_error_type"], "RuntimeError")

    def test_status_requires_both_requested_state_and_live_task(self):
        state = self._state()
        state.orchestrator._running = False
        status = state.brain_workflow_status()["components"]["autonomous_orchestrator"]

        self.assertFalse(status["running"])
        self.assertFalse(status["requested_running"])
        self.assertTrue(status["task_alive"])

    def test_internal_loop_records_slow_cycle_success_and_exception(self):
        loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
        loop._lock = threading.Lock()
        loop._last_slow_cycle_at = 0.0
        loop._slow_cycle_error_count = 0
        loop._last_slow_cycle_error_type = ""
        loop._slow_cycle_impl = Mock(side_effect=ValueError("cycle failed"))

        with self.assertRaises(ValueError):
            loop._slow_cycle()
        self.assertEqual(loop._slow_cycle_error_count, 1)
        self.assertEqual(loop._last_slow_cycle_error_type, "ValueError")
        self.assertEqual(loop._last_slow_cycle_at, 0.0)

        loop._slow_cycle_impl = Mock(return_value=None)
        loop._slow_cycle()
        self.assertGreater(loop._last_slow_cycle_at, 0.0)
        self.assertEqual(loop._slow_cycle_error_count, 1)

    def test_accepted_human_turn_is_queued_but_blank_input_is_not(self):
        state = AppState.__new__(AppState)
        state.orchestrator = SimpleNamespace(notify_user_message=Mock())

        self.assertFalse(state.notify_user_turn("   ", "fred"))
        state.orchestrator.notify_user_message.assert_not_called()

        self.assertTrue(state.notify_user_turn("  hello Brain  ", "fred"))
        state.orchestrator.notify_user_message.assert_called_once_with("hello Brain", "fred")

    def test_all_human_chat_entrypoints_feed_the_orchestrator(self):
        root = Path(__file__).resolve().parents[1]
        required = {
            "pages/main_page.py": "handle_send",
            "core/interface_api.py": "chat",
            "brain.py": "chat",
        }
        for relative_path, function_name in required.items():
            with self.subTest(path=relative_path):
                module = ast.parse((root / relative_path).read_text(encoding="utf-8"))
                functions = [
                    node for node in ast.walk(module)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == function_name
                ]
                self.assertTrue(functions, f"{relative_path} is missing {function_name}()")
                self.assertTrue(
                    any(
                        isinstance(call, ast.Call)
                        and isinstance(call.func, ast.Attribute)
                        and call.func.attr == "notify_user_turn"
                        for function in functions
                        for call in ast.walk(function)
                    ),
                    f"{relative_path}:{function_name} does not feed the cognitive orchestrator",
                )
                self.assertTrue(
                    any(
                        isinstance(call, ast.Call)
                        and isinstance(call.func, ast.Attribute)
                        and call.func.attr == "schedule_deferred_cognitive_stages"
                        for function in functions
                        for call in ast.walk(function)
                    ),
                    f"{relative_path}:{function_name} skips deferred post-turn cognition",
                )

    def test_deferred_post_turn_stages_are_scheduled_and_share_the_completed_turn(self):
        persona = SimpleNamespace(
            get_last_turn_trace=Mock(return_value={
                "turn_id": "turn-123", "cognitive_scope_id": "scope-123",
            }),
            record_deferred_turn_stage=Mock(),
            run_deferred_analysis=Mock(return_value="completed"),
            run_deferred_goal_means_analysis=Mock(return_value={"status": "not_applicable"}),
        )
        state = AppState.__new__(AppState)
        state.persona = persona
        state._deferred_cognitive_tasks = set()
        task = _CallbackTask()
        captured = {}

        def fake_to_thread(callback):
            captured["callback"] = callback
            return object()

        with patch("core.state.asyncio.to_thread", new=Mock(side_effect=fake_to_thread)):
            with patch("core.state.asyncio.create_task", new=Mock(return_value=task)) as create_task:
                scheduled = state.schedule_deferred_cognitive_stages(
                    "practical user request", "completed answer", "fred", 7,
                )

        self.assertTrue(scheduled)
        create_task.assert_called_once()
        self.assertIn(task, state._deferred_cognitive_tasks)
        self.assertTrue(callable(task.callback))
        captured["callback"]()
        persona.run_deferred_analysis.assert_called_once_with(
            "practical user request", "completed answer", "fred", 7,
        )
        persona.run_deferred_goal_means_analysis.assert_called_once_with(
            "practical user request", "fred", "fred", "scope-123",
        )
        persona.record_deferred_turn_stage.assert_any_call(
            "turn-123", "continuity_analysis_post_response", "scheduled", "",
        )
        persona.record_deferred_turn_stage.assert_any_call(
            "turn-123", "continuity_analysis_post_response", "completed", "",
        )
        persona.record_deferred_turn_stage.assert_any_call(
            "turn-123", "goal_means_post_response", "not_applicable", "",
        )

    def test_deferred_continuity_error_type_is_recorded_without_message(self):
        persona = SimpleNamespace(
            get_last_turn_trace=Mock(return_value={"turn_id": "turn-safe"}),
            record_deferred_turn_stage=Mock(),
            run_deferred_analysis=Mock(return_value={
                "status": "failed", "error_type": "ProviderTimeout",
            }),
        )
        state = AppState.__new__(AppState)
        state.persona = persona
        state._deferred_cognitive_tasks = set()
        task = _CallbackTask()
        captured = {}

        def fake_to_thread(callback):
            captured["callback"] = callback
            return object()

        with patch("core.state.asyncio.to_thread", new=Mock(side_effect=fake_to_thread)):
            with patch("core.state.asyncio.create_task", new=Mock(return_value=task)):
                self.assertTrue(state.schedule_deferred_cognitive_stages(
                    "question", "answer", "fred", 1,
                ))

        captured["callback"]()
        persona.record_deferred_turn_stage.assert_any_call(
            "turn-safe", "continuity_analysis_post_response", "failed", "",
            error_type="ProviderTimeout",
        )

    def test_deferred_stage_updates_its_original_turn_after_a_new_turn_starts(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._turn_sequence = 0
        bridge._last_turn_trace = {}
        bridge._turn_trace_history = []
        bridge._turn_stage_health = {}

        original_turn_id = bridge._start_turn_trace("fred")
        bridge._record_turn_context_source(
            "body_runtime", "injected", observation_count=3, fresh_count=2,
            stale_count=1, oldest_age_seconds=16.25,
            turn_id=original_turn_id,
            raw_observation={"secret": "must not be retained"},
        )
        bridge._record_turn_stage(
            "provider", "failed", "provider exception echoed confidential prompt text",
        )
        bridge._finish_turn_trace("completed")
        current_turn_id = bridge._start_turn_trace("fred")

        bridge.record_deferred_turn_stage(
            original_turn_id, "continuity_analysis_post_response", "completed",
        )
        trace = bridge.get_last_turn_trace()

        self.assertEqual(trace["turn_id"], current_turn_id)
        prior = next(item for item in trace["recent_turns"] if item["turn_id"] == original_turn_id)
        self.assertEqual(
            prior["stages"]["continuity_analysis_post_response"]["status"], "completed",
        )
        self.assertNotIn("detail", prior["stages"]["continuity_analysis_post_response"])
        self.assertEqual(prior["context_sources"]["body_runtime"]["observation_count"], 3)
        self.assertNotIn("raw_observation", prior["context_sources"]["body_runtime"])
        self.assertNotIn("detail", prior["stages"]["provider"])

    def test_context_source_is_attributed_to_its_turn_when_turns_overlap(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._turn_sequence = 0
        bridge._last_turn_trace = {}
        bridge._turn_trace_history = []
        bridge._turn_stage_health = {}

        first_turn_id = bridge._start_turn_trace("fred")
        second_turn_id = bridge._start_turn_trace("fred")
        bridge._record_turn_context_source(
            "memory", "injected", turn_id=first_turn_id, record_count=2,
        )
        bridge._record_turn_context_source(
            "brain_pc_camera", "fresh", turn_id=second_turn_id, active=True,
        )
        bridge._finish_turn_trace("completed", first_turn_id)

        trace = bridge.get_last_turn_trace()
        prior = next(
            item for item in trace["recent_turns"]
            if item["turn_id"] == first_turn_id
        )
        self.assertEqual(trace["turn_id"], second_turn_id)
        self.assertEqual(prior["context_sources"]["memory"]["record_count"], 2)
        self.assertNotIn("brain_pc_camera", prior["context_sources"])
        self.assertEqual(prior["status"], "completed")
        self.assertEqual(trace["status"], "running")
        self.assertTrue(trace["context_sources"]["brain_pc_camera"]["active"])


if __name__ == "__main__":
    unittest.main()
