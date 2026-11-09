import asyncio
import sys
import threading
import types
import unittest
import importlib
from unittest.mock import Mock, patch

from cognition.lumina_network import ChildLumina, LuminaNetwork, NetworkMessage
from managers.llm_manager import LLMManager


class _StreamingProvider:
    model = "test-model"

    def __init__(self):
        self.seen_history = None

    def generate_with_history_stream(self, prompt, history, system_prompt=None, **kwargs):
        self.seen_history = history
        yield "scoped answer"

    def generate_with_history(self, prompt, history, system_prompt=None, **kwargs):
        self.seen_history = history
        return "recovered answer"


class PeerHistoryIsolationTests(unittest.TestCase):
    def test_prompt_role_instruction_distinguishes_human_from_peer_ai(self):
        from cognition.persona_bridge import _interlocutor_role_instruction

        self.assertIn("human who sent this turn", _interlocutor_role_instruction())
        peer_instruction = _interlocutor_role_instruction("FLUX")
        self.assertIn("another AI system named FLUX", peer_instruction)
        self.assertIn("human operator is not the sender", peer_instruction)

    def _manager(self):
        provider = _StreamingProvider()
        manager = LLMManager.__new__(LLMManager)
        manager.provider = provider
        manager.text_model = "test-model"
        manager.history = [{"role": "user", "content": "human-only prior"}]
        manager._provider_lock = threading.Lock()
        manager._chat_active = threading.Event()
        manager._trim_history = lambda: None
        return manager, provider

    def test_scoped_stream_uses_peer_history_and_does_not_write_human_history(self):
        manager, provider = self._manager()
        original = list(manager.history)
        peer_history = [
            {"role": "assistant", "content": "previous Lumina turn"},
            {"role": "user", "content": "previous FLUX turn"},
        ]

        tokens = list(manager.generate_stream(
            "current peer input", history_override=peer_history, record_history=False,
        ))

        self.assertEqual(tokens, ["scoped answer"])
        self.assertEqual(provider.seen_history, peer_history)
        self.assertEqual(manager.history, original)

    def test_scoped_recovery_does_not_trim_or_rewrite_human_history(self):
        manager, provider = self._manager()
        original = list(manager.history)
        peer_history = [{"role": "user", "content": "prior peer context"}]

        answer = manager.recover_final_response(
            "current peer input", history_override=peer_history, record_history=False,
        )

        self.assertEqual(answer, "recovered answer")
        self.assertEqual(provider.seen_history, peer_history)
        self.assertEqual(manager.history, original)

    def test_peer_continuity_uses_scoped_transcript_not_human_chat(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        manager = types.SimpleNamespace(history=[
            {"role": "user", "content": "human secret topic"},
            {"role": "assistant", "content": "human-only answer"},
        ])
        bridge._llm_stream_fn = types.SimpleNamespace(__self__=manager)
        scoped = [
            {"role": "assistant", "content": "peer topic"},
            {"role": "user", "content": "peer answer"},
            {"role": "assistant", "content": "Lumina follow-up"},
        ]

        continuity = bridge._recent_dialogue_continuity("and then?", history_override=scoped)

        self.assertIn("peer topic", continuity)
        self.assertNotIn("human secret topic", continuity)

    def test_peer_post_turn_runs_cognitive_evaluation_without_human_memory_learning(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {"stages": {}}
        system = Mock()
        system._interaction_count = 7
        bridge._system = system
        organism = Mock()
        organism.goal_ecology.dominant_drive.return_value = types.SimpleNamespace(name="understand")
        organism.energy.level.return_value = 0.8
        organism.energy.temperature_hint.return_value = 0.4

        result = bridge._run_full_post_turn_lifecycle(
            "peer input", "lumina_child_flux", "peer reply", {}, {}, organism,
            human_interaction=False,
        )

        self.assertTrue(result)
        organism._post_interaction.assert_called_once()
        self.assertFalse(organism._post_interaction.call_args.kwargs["human_interaction"])
        system._post_response_processing.assert_not_called()
        system._queue_background_tasks.assert_not_called()
        self.assertEqual(system._interaction_count, 7)
        self.assertEqual(
            bridge._last_turn_trace["stages"]["peer_cognitive_evaluation"]["status"],
            "completed",
        )

    def test_post_turn_failure_is_not_reported_as_completed(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {"stages": {}}
        system = Mock()
        system._interaction_count = 3
        system._last_responses = []
        system._post_response_processing.side_effect = RuntimeError("memory store failed")
        bridge._system = system

        result = bridge._run_full_post_turn_lifecycle(
            "human input", "fred", "answer", {}, {}, organism=None,
        )

        self.assertFalse(result)
        self.assertEqual(
            bridge._last_turn_trace["stages"]["response_learning_and_memory"]["status"],
            "failed",
        )
        self.assertEqual(
            bridge._last_turn_trace["stages"]["cognitive_post_turn"]["status"],
            "failed",
        )
        system._queue_background_tasks.assert_not_called()

    def test_turn_trace_returns_detached_stage_snapshots(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {
            "turn_id": "test-turn",
            "stages": {"provider": {"status": "completed"}},
        }
        bridge._turn_stage_health = {}
        bridge._record_turn_stage("provider", "completed")
        bridge._record_turn_stage("provider", "failed", "provider timeout")

        snapshot = bridge.get_last_turn_trace()
        snapshot["stages"]["provider"]["status"] = "mutated"
        snapshot["stage_health"]["provider"]["status_counts"]["failed"] = 99

        self.assertEqual(bridge._last_turn_trace["stages"]["provider"]["status"], "failed")
        self.assertEqual(bridge._turn_stage_health["provider"]["status_counts"]["failed"], 1)
        self.assertEqual(bridge._turn_stage_health["provider"]["last_error"], "failed")

    def test_turn_trace_does_not_label_turn_complete_when_a_stage_failed(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {
            "stages": {"response_learning_and_memory": {"status": "failed"}},
        }

        bridge._finish_turn_trace("completed")

        self.assertEqual(
            bridge._last_turn_trace["status"], "completed_with_stage_failures",
        )
        self.assertEqual(
            bridge._last_turn_trace["pipeline_integrity"]["failed_stages"],
            ["response_learning_and_memory"],
        )
        self.assertEqual(
            bridge._last_turn_trace["pipeline_integrity"]["status"],
            "incomplete_evidence",
        )

    def test_late_deferred_failure_updates_finished_turn_integrity(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {"turn_id": "audit-turn", "stages": {}}
        bridge._turn_stage_health = {}
        bridge._finish_turn_trace("completed")

        bridge.record_deferred_turn_stage(
            "audit-turn", "continuity_analysis_post_response", "failed",
        )
        trace = bridge.get_last_turn_trace()

        self.assertEqual(trace["status"], "completed_with_stage_failures")
        self.assertEqual(
            trace["pipeline_integrity"]["status"], "incomplete_evidence",
        )
        self.assertEqual(
            trace["pipeline_integrity"]["failed_stages"],
            ["continuity_analysis_post_response"],
        )

    def test_pipeline_integrity_checks_core_stages_and_peer_scope(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {
            "scope": "peer",
            "stages": {
                "readiness": {"status": "passed"},
                "input_safety": {"status": "passed"},
                "prompt_assembly": {"status": "completed"},
                "primary_generation": {"status": "completed"},
                "output_safety": {"status": "passed"},
                "response_finalization": {"status": "completed"},
                "response": {"status": "completed"},
                "body_observation_context": {"status": "injected"},
                "memory_retrieval": {"status": "skipped_by_scope"},
                "optional": {"status": ["broken"]},
            },
        }

        bridge._finish_turn_trace("completed")
        integrity = bridge._last_turn_trace["pipeline_integrity"]

        self.assertEqual(integrity["status"], "incomplete_evidence")
        self.assertEqual(integrity["missing_core_stages"], [])
        self.assertEqual(integrity["malformed_stages"], ["optional"])
        self.assertEqual(integrity["peer_scope_violations"], ["body_observation_context"])

    def test_pipeline_integrity_accepts_complete_scoped_turn(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {
            "scope": "peer",
            "stages": {
                "readiness": {"status": "passed"},
                "input_safety": {"status": "passed"},
                "prompt_assembly": {"status": "completed"},
                "primary_generation": {"status": "completed"},
                "output_safety": {"status": "passed"},
                "response_finalization": {"status": "completed"},
                "response": {"status": "completed"},
                "body_observation_context": {"status": "skipped_by_scope"},
            },
        }

        bridge._finish_turn_trace("completed")

        self.assertEqual(
            bridge._last_turn_trace["pipeline_integrity"]["status"], "consistent",
        )

    def test_pipeline_integrity_flags_out_of_order_stages(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {
            "scope": "peer",
            "stages": {
                "readiness": {"status": "passed"},
                "input_safety": {"status": "passed"},
                "prompt_assembly": {"status": "completed", "at": 2.0},
                "primary_generation": {"status": "completed", "at": 1.0},
                "output_safety": {"status": "passed", "at": 3.0},
                "response_finalization": {"status": "completed", "at": 4.0},
                "response": {"status": "completed", "at": 5.0},
            },
        }

        bridge._finish_turn_trace("completed")
        integrity = bridge._last_turn_trace["pipeline_integrity"]

        self.assertEqual(integrity["status"], "incomplete_evidence")
        self.assertEqual(
            integrity["stage_order_violations"],
            ["primary_generation_before_prompt_assembly"],
        )

    def test_peer_turn_does_not_write_into_global_active_cognitive_context(self):
        from cognition.persona_bridge import PersonaBridge

        class _Loop:
            def __init__(self):
                self.calls = []

            def run_in_executor(self, executor, callback, *args):
                self.calls.append((executor, callback, args))
                return "scheduled"

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {"stages": {}}
        active_context = Mock()
        loop = _Loop()

        self.assertIsNone(bridge._schedule_active_context_update(
            loop, active_context, "FLUX private topic", "peer reply",
            "lumina_child_flux", "FLUX",
        ))
        active_context.update_from_turn.assert_not_called()
        self.assertEqual(loop.calls, [])
        self.assertEqual(
            bridge._last_turn_trace["stages"]["active_context_update"]["status"],
            "skipped_by_scope",
        )

        self.assertEqual(bridge._schedule_active_context_update(
            loop, active_context, "human topic", "human answer", "fred",
        ), "scheduled")
        self.assertEqual(loop.calls[0][2], ("human topic", "human answer", "fred"))

    def test_peer_prompt_excludes_brain_camera_and_body_live_evidence(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {"stages": {}}
        bridge._pending_vision_context = "private operator camera details"
        bridge._local_camera_prompt_context = Mock(
            return_value="private face recognition details",
        )
        body = Mock()
        body.context_for_brain.return_value = "private live body telemetry"
        bridge._organism = types.SimpleNamespace(_body_runtime=body)

        prompt, body_context, camera_context = bridge._append_live_evidence_context(
            "shared cognitive prompt", "FLUX",
        )

        self.assertEqual(prompt, "shared cognitive prompt")
        self.assertEqual(body_context, "")
        self.assertEqual(camera_context, "")
        bridge._local_camera_prompt_context.assert_not_called()
        body.context_for_brain.assert_not_called()
        self.assertIsNone(bridge._pending_vision_context)
        self.assertEqual(
            bridge._last_turn_trace["stages"]["brain_pc_camera_context"]["status"],
            "skipped_by_scope",
        )
        self.assertEqual(
            bridge._last_turn_trace["stages"]["body_observation_context"]["status"],
            "skipped_by_scope",
        )

    def test_peer_cognitive_prompt_keeps_shared_reasoning_but_excludes_human_context(self):
        from cognition.persona_bridge import PersonaBridge
        core_state = importlib.import_module("core.state")

        acc = Mock()
        acc.get_prompt_fragment.return_value = "human private topic and room scene"
        empathy = Mock()
        empathy.get_prompt_fragment.return_value = "human affect read"
        sce = Mock()
        sce.get_strategic_context_fragment.return_value = "shared strategic posture"
        are = Mock()
        are.get_reasoning_fragment.return_value = "peer-scoped abstract reasoning"
        fake_state = types.SimpleNamespace(acc=acc, empathy_engine=empathy, sce=sce, are=are)
        organism = types.SimpleNamespace(
            self_model=types.SimpleNamespace(prompt_fragment=Mock(return_value="self model")),
            attractors=types.SimpleNamespace(prompt_fragment=Mock(return_value="stable traits")),
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = organism
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {"stages": {}}

        with patch.object(core_state, "state", fake_state):
            prompt = bridge._append_cognitive_prompt_context(
                "base prompt", user_id="peer:flux", peer_name="FLUX",
            )

        self.assertIn("self model", prompt)
        self.assertIn("stable traits", prompt)
        self.assertIn("shared strategic posture", prompt)
        self.assertIn("peer-scoped abstract reasoning", prompt)
        self.assertNotIn("human private topic", prompt)
        self.assertNotIn("human affect read", prompt)
        acc.get_prompt_fragment.assert_not_called()
        empathy.get_prompt_fragment.assert_not_called()
        self.assertEqual(
            bridge._last_turn_trace["stages"]["active_context_prompt"]["status"],
            "skipped_by_scope",
        )
        self.assertEqual(
            bridge._last_turn_trace["stages"]["empathy_context"]["status"],
            "skipped_by_scope",
        )

    def test_human_cognitive_prompt_receives_acc_and_empathy_fragments(self):
        from cognition.persona_bridge import PersonaBridge
        core_state = importlib.import_module("core.state")

        acc = Mock()
        acc.get_prompt_fragment.return_value = "human active context"
        empathy = Mock()
        empathy.get_prompt_fragment.return_value = "human affect context"
        fake_state = types.SimpleNamespace(
            acc=acc, empathy_engine=empathy, sce=None, are=None,
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = None
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {"stages": {}}

        with patch.object(core_state, "state", fake_state):
            prompt = bridge._append_cognitive_prompt_context(
                "base prompt", user_id="fred",
            )

        self.assertIn("human active context", prompt)
        self.assertIn("human affect context", prompt)
        acc.get_prompt_fragment.assert_called_once_with()
        empathy.get_prompt_fragment.assert_called_once_with("fred")
        self.assertEqual(
            bridge._last_turn_trace["stages"]["active_context_prompt"]["status"],
            "injected",
        )
        self.assertEqual(
            bridge._last_turn_trace["stages"]["empathy_context"]["status"],
            "injected",
        )

    def test_human_prompt_receives_camera_and_body_evidence(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {"stages": {}}
        bridge._pending_vision_context = "current PC camera observation"
        bridge._local_camera_prompt_context = Mock(return_value="PC camera is live")
        body = Mock()
        body.context_for_brain.return_value = "Body sensor snapshot"
        bridge._organism = types.SimpleNamespace(_body_runtime=body)

        prompt, body_context, camera_context = bridge._append_live_evidence_context(
            "shared cognitive prompt",
        )

        self.assertIn("PC camera is live", prompt)
        self.assertIn("current PC camera observation", prompt)
        self.assertIn("Body sensor snapshot", prompt)
        self.assertEqual(body_context, "Body sensor snapshot")
        self.assertEqual(camera_context, "PC camera is live")
        bridge._local_camera_prompt_context.assert_called_once_with()
        body.context_for_brain.assert_called_once_with()
        self.assertIsNone(bridge._pending_vision_context)
        self.assertEqual(
            bridge._last_turn_trace["stages"]["brain_pc_camera_context"]["status"],
            "injected",
        )
        self.assertEqual(
            bridge._last_turn_trace["stages"]["body_observation_context"]["status"],
            "injected",
        )

    def test_real_persona_stream_wrapper_runs_peer_scope_and_records_policy_trace(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._response_turn_lock = None
        bridge._turn_trace_lock = threading.Lock()
        bridge._turn_sequence = 0
        bridge._last_turn_trace = {}
        bridge._ready = True
        bridge._system = object()
        bridge._pending_vision_context = None
        bridge._session_visuals = []
        bridge._MAX_SESSION_VISUALS = 8
        bridge._llm_stream_fn = object()
        captured = {}

        async def _fake_lifecycle(text, user_id, voice_mode=False, **kwargs):
            captured.update(text=text, user_id=user_id, voice_mode=voice_mode, **kwargs)
            yield "peer-scoped reply"
            yield {"__meta__": True, "raw": "peer-scoped reply"}

        bridge._stream_with_full_lifecycle = _fake_lifecycle

        async def _collect():
            bridge._response_turn_lock = asyncio.Lock()
            return [chunk async for chunk in bridge.get_response_stream(
                "message from FLUX",
                user_id="lumina_child_flux",
                vision_context="private Brain-PC frame description",
                record_history=False,
                conversation_history=[{"role": "assistant", "content": "prior pair turn"}],
                peer_name="FLUX",
                allow_body_actions=False,
            )]

        chunks = _run_immediate(_collect())

        self.assertEqual(chunks[0], "peer-scoped reply")
        self.assertEqual(captured["user_id"], "lumina_child_flux")
        self.assertFalse(captured["record_history"])
        self.assertEqual(captured["peer_name"], "FLUX")
        self.assertIsNone(bridge._pending_vision_context)
        self.assertEqual(bridge._session_visuals, [])
        self.assertEqual(bridge._last_turn_trace["scope"], "peer")
        self.assertEqual(bridge._last_turn_trace["status"], "completed")
        self.assertEqual(
            bridge._last_turn_trace["stages"]["body_action_gate"]["status"],
            "skipped_by_policy",
        )
        self.assertEqual(
            bridge._last_turn_trace["stages"]["brain_pc_vision_input"]["status"],
            "skipped_by_scope",
        )

    def test_deferred_goal_means_analysis_is_parsed_and_available_for_followup(self):
        from cognition.persona_bridge import PersonaBridge

        class _Manager:
            def generate_bare_result(self, prompt, **kwargs):
                self.prompt = prompt
                return {
                    "status": "ok",
                    "text": '''{
                      "primary_goal": "repair the bicycle",
                      "required_conditions": ["the bicycle must reach the workshop"],
                      "options": [{
                        "name": "walk there", "moves_patient_or_theme": false,
                        "agent_at_execution_location": true,
                        "patient_at_execution_location": false,
                        "required_resources_available": true,
                        "agent_capability_sufficient": true,
                        "feasible": false, "reason": "the bicycle stays home"
                      }],
                      "recommended_option": "ask for the missing option",
                      "decisive_reason": "the bicycle must arrive"
                    }''',
                }

        manager = _Manager()
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._external_llm_fn = types.SimpleNamespace(__self__=manager)
        bridge._reflection_lock = threading.Lock()
        bridge._goal_means_status = {}
        bridge._recent_goal_means = {}

        result = bridge.run_deferred_goal_means_analysis(
            "How should I repair my bicycle at the workshop?", "fred", "Fred",
            "peer:flux:conversation-a",
        )

        self.assertEqual(result["status"], "completed")
        self.assertIn('decision-maker is named "Fred"', manager.prompt)
        self.assertNotIn("fred", bridge._recent_goal_means)
        self.assertEqual(
            bridge._recent_goal_means["peer:flux:conversation-a"][0].primary_goal,
            "repair the bicycle",
        )
        self.assertEqual(
            bridge.get_goal_means_status("fred", "peer:flux:conversation-a")["status"],
            "completed",
        )
        self.assertEqual(bridge.get_goal_means_status("fred")["status"], "idle")


class _FakePersona:
    def __init__(self, response="Lumina peer response"):
        self.response = response
        self.calls = []

    async def get_response_stream(self, text, **kwargs):
        self.calls.append((text, kwargs))
        yield self.response
        yield {"__meta__": True, "raw": self.response}


def _run_immediate(coro):
    """Run fake-network coroutines on a real loop without external I/O."""
    return asyncio.run(coro)


def _state_module():
    module = types.ModuleType("core.state")
    module.state = types.SimpleNamespace(persona=None)
    return module


class LuminaNetworkFullTurnTests(unittest.TestCase):
    @patch.dict("sys.modules", {"core.state": _state_module()})
    def test_autonomous_peer_opening_excludes_unscoped_human_cognitive_state(self):
        persona = _FakePersona()
        state = sys.modules["core.state"].state
        state.persona = types.SimpleNamespace(
            _organism=types.SimpleNamespace(
                _read_emotion_state=lambda: "HUMAN_AFFECT_LEAK",
                _v32_workspace_winner="HUMAN_TOPIC_LEAK",
                _loop=types.SimpleNamespace(),
            ),
            ai_system=types.SimpleNamespace(relational_memory=None),
        )
        state.are = types.SimpleNamespace(_cache={
            "human": types.SimpleNamespace(open_question="HUMAN_ARE_LEAK"),
        })
        network = LuminaNetwork.__new__(LuminaNetwork)
        network._persona = persona
        network._master_name = "Lumina"

        answer = _run_immediate(network._generate_opening(
            "FLUX", "flux", seed_topic="shared robot cognition", conversation_id="pair-7",
        ))

        self.assertEqual(answer, "Lumina peer response")
        prompt, options = persona.calls[0]
        self.assertIn("shared robot cognition", prompt)
        self.assertIn("another AI system named FLUX", prompt)
        self.assertNotIn("HUMAN_AFFECT_LEAK", prompt)
        self.assertNotIn("HUMAN_TOPIC_LEAK", prompt)
        self.assertNotIn("HUMAN_ARE_LEAK", prompt)
        self.assertEqual(options["cognitive_scope_id"], "peer:flux:pair-7")

    @patch.dict("sys.modules", {"core.state": _state_module()})
    def test_outbound_peer_exchange_never_enters_shared_human_memory(self):
        class _AsyncContext:
            def __init__(self, value):
                self.value = value

            async def __aenter__(self):
                return self.value

            async def __aexit__(self, *_args):
                return False

        class _Response:
            status = 200

            async def json(self):
                return {"response": "FLUX reply", "sender_name": "FLUX"}

        class _Session:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            def post(self, *_args, **_kwargs):
                return _AsyncContext(_Response())

        state_module = sys.modules["core.state"]
        state_module.state.memory = Mock()
        pcm = Mock()
        pcm.classify.return_value = "philosophical"
        pcm.read_state.side_effect = [[0.1] * 5, [0.2] * 5]
        wsdm = Mock()
        wsdm.capture_context.side_effect = [[0.1] * 8, [0.2] * 8]
        relational = Mock()
        organism = types.SimpleNamespace(
            _loop=types.SimpleNamespace(
                _consequence_model=pcm,
                _world_self_dynamics=wsdm,
                _flux_mind_model=None,
            ),
            ai_system=None,
        )
        state_module.state.persona = types.SimpleNamespace(
            _organism=organism, _system=None,
            ai_system=types.SimpleNamespace(relational_memory=relational),
        )
        network = LuminaNetwork.__new__(LuminaNetwork)
        network._persona = None
        network._llm = Mock(history=[{"role": "user", "content": "human-only"}])
        original_human_history = list(network._llm.history)
        network._children = {
            "flux": ChildLumina("flux", "FLUX", "http://flux.local")
        }
        network._history = {}
        network._aiohttp = types.SimpleNamespace(
            ClientSession=_Session,
            ClientTimeout=lambda **_kwargs: None,
        )
        network._bubble_fn = None
        network._master_url = ""
        network._master_name = "Lumina"

        response = _run_immediate(network.send_to_child(
            "flux", "peer-only prompt", conversation_id="pair-1", show_in_ui=False,
        ))

        self.assertEqual(response, "FLUX reply")
        state_module.state.memory.add_memory.assert_not_called()
        self.assertEqual(network._llm.history, original_human_history)
        self.assertEqual([m.text for m in network.get_history("pair-1")], [
            "peer-only prompt", "FLUX reply",
        ])
        self.assertEqual(network._children["flux"].turn_count, 1)
        relational.record_exchange.assert_called_once()
        self.assertEqual(relational.record_exchange.call_args.kwargs["valence"], "Neutral")
        pcm.record_action.assert_not_called()
        pcm.record_outcome.assert_not_called()
        pcm.record_observed_transition.assert_called_once_with(
            "philosophical", [0.1] * 5, [0.2] * 5,
            interaction_n=0, outcome="neutral", resolve_calibration=False,
        )
        wsdm.record_context.assert_not_called()
        wsdm.record_outcome.assert_not_called()
        wsdm.record_observed_transition.assert_called_once_with(
            "philosophical", "lumina_child_flux", [0.1] * 8, [0.2] * 8,
            interaction_n=0, outcome="neutral", response_text="FLUX reply",
            user_input="peer-only prompt", resolve_calibration=False,
        )

    @patch.dict("sys.modules", {"core.state": _state_module()})
    def test_outbound_transport_error_is_not_saved_as_a_conversation_turn(self):
        class _AsyncContext:
            def __init__(self, value):
                self.value = value

            async def __aenter__(self):
                return self.value

            async def __aexit__(self, *_args):
                return False

        class _Response:
            status = 503

            async def text(self):
                return "service unavailable"

        class _Session:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            def post(self, *_args, **_kwargs):
                return _AsyncContext(_Response())

        network = LuminaNetwork.__new__(LuminaNetwork)
        network._persona = None
        network._children = {
            "flux": ChildLumina("flux", "FLUX", "http://flux.local")
        }
        network._history = {}
        network._aiohttp = types.SimpleNamespace(
            ClientSession=_Session,
            ClientTimeout=lambda **_kwargs: None,
        )
        network._bubble_fn = None
        network._master_url = ""
        network._master_name = "Lumina"

        response = _run_immediate(network.send_to_child(
            "flux", "prompt", conversation_id="failed-pair", show_in_ui=False,
        ))

        self.assertTrue(response.startswith("[Child error 503:"))
        self.assertEqual(network.get_history("failed-pair"), [])
        self.assertEqual(network._children["flux"].turn_count, 0)

    @patch.dict("sys.modules", {"core.state": _state_module()})
    def test_empty_http_200_is_not_committed_as_a_peer_exchange(self):
        class _Context:
            def __init__(self, value):
                self.value = value

            async def __aenter__(self):
                return self.value

            async def __aexit__(self, *_args):
                return False

        class _Response:
            status = 200

            async def json(self):
                return {"response": "   ", "sender_name": "Wrong name"}

        class _Session:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            def post(self, *_args, **_kwargs):
                return _Context(_Response())

        child = ChildLumina("flux", "FLUX", "http://flux.local")
        network = LuminaNetwork.__new__(LuminaNetwork)
        network._persona = None
        network._children = {"flux": child}
        network._history = {}
        network._aiohttp = types.SimpleNamespace(
            ClientSession=_Session,
            ClientTimeout=lambda **_kwargs: None,
        )
        network._bubble_fn = Mock()
        network._master_url = ""
        network._master_name = "Lumina"

        response = _run_immediate(network.send_to_child(
            "flux", "prompt", conversation_id="empty-pair", show_in_ui=True,
        ))

        self.assertTrue(response.startswith("[Child error 200:"))
        self.assertEqual(network.get_history("empty-pair"), [])
        self.assertEqual(child.name, "FLUX")
        self.assertEqual(child.turn_count, 0)
        self.assertEqual(network._bubble_fn.call_args_list, [
            unittest.mock.call("prompt", "master", "master", "Lumina"),
        ])

    @patch.dict("sys.modules", {"core.state": _state_module()})
    def test_master_reply_uses_persona_bridge_and_excludes_current_input_from_history(self):
        persona = _FakePersona()
        network = LuminaNetwork.__new__(LuminaNetwork)
        network._persona = persona
        network._llm = Mock()
        network._llm.generate_bare.side_effect = AssertionError("bare generation bypassed PersonaBridge")
        network._master_name = "Lumina"
        history = [
            NetworkMessage("opening", "master", "Lumina", "c1", direction="out"),
            NetworkMessage("earlier reply", "flux", "FLUX", "c1", direction="in"),
            NetworkMessage("follow-up", "master", "Lumina", "c1", direction="out"),
            NetworkMessage("current FLUX message", "flux", "FLUX", "c1", direction="in"),
        ]

        response = _run_immediate(network._master_generate(
            "topic", history, "FLUX", child_id="flux", conversation_id="c1",
        ))

        self.assertEqual(response, "Lumina peer response")
        text, options = persona.calls[0]
        self.assertIn("current FLUX message", text)
        self.assertEqual(options["conversation_history"], [
            {"role": "assistant", "content": "opening"},
            {"role": "user", "content": "earlier reply"},
            {"role": "assistant", "content": "follow-up"},
        ])
        self.assertFalse(options["allow_body_actions"])
        self.assertFalse(options["record_history"])
        self.assertEqual(options["peer_name"], "FLUX")
        self.assertEqual(options["cognitive_scope_id"], "peer:flux:c1")

    @patch.dict("sys.modules", {"core.state": _state_module()})
    def test_inbound_child_turn_uses_peer_scope_not_human_history(self):
        persona = _FakePersona("master answer")
        network = LuminaNetwork.__new__(LuminaNetwork)
        network._persona = persona
        network._history = {
            ("flux", "c2"): [NetworkMessage("earlier Lumina", "master", "Lumina", "c2", direction="out")]
        }
        network._bubble_fn = None
        network._master_name = "Lumina"

        response = _run_immediate(network.receive_from_child({
            "sender_id": "flux", "sender_name": "FLUX", "text": "new peer message",
            "conversation_id": "c2",
        }))

        self.assertEqual(response, "master answer")
        self.assertEqual(persona.calls[0][1]["cognitive_scope_id"], "peer:flux:c2")
        text, options = persona.calls[0]
        self.assertEqual(text, "new peer message")
        self.assertEqual(options["conversation_history"], [
            {"role": "assistant", "content": "earlier Lumina"}
        ])
        self.assertFalse(options["allow_body_actions"])
        self.assertFalse(options["record_history"])
        self.assertEqual(options["peer_name"], "FLUX")
        self.assertEqual(network.get_history("c2")[-2].text, "new peer message")
        self.assertEqual(network.get_history("c2")[-1].text, "master answer")

        _run_immediate(network.receive_from_child({
            "sender_id": "flux", "sender_name": "FLUX", "text": "peer follow-up",
            "conversation_id": "c2",
        }))
        _, followup_options = persona.calls[1]
        self.assertEqual(followup_options["conversation_history"], [
            {"role": "assistant", "content": "earlier Lumina"},
            {"role": "user", "content": "new peer message"},
            {"role": "assistant", "content": "master answer"},
        ])

        _run_immediate(network.receive_from_child({
            "sender_id": "flux", "sender_name": "FLUX", "text": "separate topic",
            "conversation_id": "c3",
        }))
        _, separate_options = persona.calls[2]
        self.assertEqual(separate_options["conversation_history"], [])

    @patch.dict("sys.modules", {"core.state": _state_module()})
    def test_concurrent_inbound_turns_same_pair_are_serialized(self):
        async def scenario():
            first_started = asyncio.Event()
            release_first = asyncio.Event()

            class _Persona:
                def __init__(self):
                    self.calls = []

                async def get_response_stream(self, text, **kwargs):
                    self.calls.append((text, kwargs["conversation_history"]))
                    if text == "first":
                        first_started.set()
                        await release_first.wait()
                    yield f"answer to {text}"

            persona = _Persona()
            network = LuminaNetwork.__new__(LuminaNetwork)
            network._persona = persona
            network._history = {}
            network._bubble_fn = None
            network._master_name = "Lumina"

            first = asyncio.create_task(network.receive_from_child({
                "sender_id": "flux", "sender_name": "FLUX", "text": "first",
                "conversation_id": "serial-pair",
            }))
            await first_started.wait()
            second = asyncio.create_task(network.receive_from_child({
                "sender_id": "flux", "sender_name": "FLUX", "text": "second",
                "conversation_id": "serial-pair",
            }))
            await asyncio.sleep(0)
            self.assertEqual(len(persona.calls), 1)
            release_first.set()
            self.assertEqual(await first, "answer to first")
            self.assertEqual(await second, "answer to second")
            self.assertEqual(persona.calls[1][1], [
                {"role": "user", "content": "first"},
                {"role": "assistant", "content": "answer to first"},
            ])

        asyncio.run(scenario())

    @patch.dict("sys.modules", {"core.state": _state_module()})
    def test_same_conversation_id_from_distinct_peers_stays_isolated(self):
        persona = _FakePersona("master answer")
        network = LuminaNetwork.__new__(LuminaNetwork)
        network._persona = persona
        network._history = {
            ("flux-a", "shared-id"): [
                NetworkMessage("private A context", "flux-a", "FLUX A", "shared-id", direction="in")
            ],
            ("flux-b", "shared-id"): [
                NetworkMessage("private B context", "flux-b", "FLUX B", "shared-id", direction="in")
            ],
        }
        network._bubble_fn = None
        network._master_name = "Lumina"

        _run_immediate(network.receive_from_child({
            "sender_id": "flux-a", "sender_name": "FLUX A", "text": "follow up A",
            "conversation_id": "shared-id",
        }))
        _run_immediate(network.receive_from_child({
            "sender_id": "flux-b", "sender_name": "FLUX B", "text": "follow up B",
            "conversation_id": "shared-id",
        }))

        self.assertEqual(persona.calls[0][1]["conversation_history"], [
            {"role": "user", "content": "private A context"},
        ])
        self.assertEqual(persona.calls[1][1]["conversation_history"], [
            {"role": "user", "content": "private B context"},
        ])
        self.assertEqual(network.get_history("shared-id", peer_id="flux-a")[-2].text, "follow up A")
        self.assertEqual(network.get_history("shared-id", peer_id="flux-b")[-2].text, "follow up B")
        self.assertEqual(network.get_history("shared-id"), [])

    @patch.dict("sys.modules", {"core.state": _state_module()})
    def test_scoped_generation_failure_is_not_saved_as_lumina_answer(self):
        class _FailingPersona:
            async def get_response_stream(self, *_args, **_kwargs):
                yield "Scoped peer generation failed."
                yield {
                    "__meta__": True,
                    "error": "scoped_peer_stream_failed",
                }

        network = LuminaNetwork.__new__(LuminaNetwork)
        network._persona = _FailingPersona()
        network._history = {}
        network._bubble_fn = None
        network._master_name = "Lumina"

        response = _run_immediate(network.receive_from_child({
            "sender_id": "flux", "sender_name": "FLUX", "text": "peer input",
            "conversation_id": "failure-case",
        }))

        self.assertEqual(response, "")
        self.assertEqual(
            [(message.direction, message.text) for message in network.get_history("failure-case")],
            [("in", "peer input")],
        )

    @patch.dict("sys.modules", {"core.state": _state_module()})
    def test_dialogue_summary_uses_scoped_persona_bridge(self):
        persona = _FakePersona("The dialogue explored cognition and left validation open.")
        network = LuminaNetwork.__new__(LuminaNetwork)
        network._persona = persona
        network._llm = Mock()
        network._llm.generate_bare.side_effect = AssertionError("summary bypassed PersonaBridge")
        network._master_name = "Lumina"
        network._bubble_fn = Mock()
        exchange = [
            NetworkMessage("What is cognition?", "master", "Lumina", "c1", direction="out"),
            NetworkMessage("It may involve several stages.", "flux", "FLUX", "c1", direction="in"),
        ]

        _run_immediate(network._deliver_summary(exchange, "FLUX", "flux"))

        text, options = persona.calls[0]
        self.assertIn("completed dialogue", text)
        self.assertFalse(options["allow_body_actions"])
        self.assertFalse(options["record_history"])
        self.assertEqual(options["peer_name"], "FLUX")
        self.assertTrue(network._bubble_fn.called)


if __name__ == "__main__":
    unittest.main()
