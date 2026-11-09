import asyncio
import importlib.util
import json
from pathlib import Path
import threading
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "lumina_network_routing_under_test", ROOT / "cognition" / "lumina_network.py",
)
lumina_network_module = importlib.util.module_from_spec(SPEC)
import sys
sys.modules[SPEC.name] = lumina_network_module
SPEC.loader.exec_module(lumina_network_module)

ChildLumina = lumina_network_module.ChildLumina
LuminaNetwork = lumina_network_module.LuminaNetwork
sanitize_trace = lumina_network_module._sanitize_cognitive_trace


class LuminaNetworkConversationRoutingTests(unittest.TestCase):
    def _network(self):
        network = LuminaNetwork.__new__(LuminaNetwork)
        network._lock = threading.RLock()
        network._active_conversations = {}
        network._active_dialogues = {}
        network._dialogue_injections = {}
        network._peer_turn_locks = {}
        network._peer_turn_locks_guard = threading.RLock()
        network._children = {
            "flux": ChildLumina("flux", "FLUX", "http://flux.local"),
            "other": ChildLumina("other", "Other", "http://other.local"),
        }
        return network

    def test_manual_asks_reuse_one_scoped_transcript_per_child(self):
        network = self._network()
        observed = []

        class ImmediateLock:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

        async def capture(child_id, text, *, conversation_id, show_in_ui):
            observed.append((child_id, text, conversation_id))
            return "reply"

        network._send_to_child_locked = capture
        network._conversation_lock = lambda *_args: ImmediateLock()

        async def send_turns():
            await network.send_to_child("flux", "first question")
            await network.send_to_child("flux", "follow-up")
            await network.send_to_child("other", "separate peer")

        coroutine = send_turns()
        try:
            coroutine.send(None)
        except StopIteration:
            pass
        else:
            self.fail("fake transport unexpectedly awaited external I/O")

        self.assertEqual(observed[0][2], observed[1][2])
        self.assertNotEqual(observed[0][2], observed[2][2])
        self.assertEqual(network._active_conversations["flux"], observed[0][2])

    def test_new_dialogue_or_explicit_id_updates_peer_default(self):
        network = self._network()
        previous = network._conversation_for_peer("flux")
        dialogue = network._conversation_for_peer("flux", new=True)
        self.assertNotEqual(previous, dialogue)
        self.assertEqual(network._conversation_for_peer("flux"), dialogue)
        self.assertEqual(network._conversation_for_peer("flux", "provided-id"), "provided-id")

    def test_ambiguous_injection_is_rejected_and_named_peer_isolated(self):
        network = self._network()
        network._active_dialogues = {
            "flux": "flux-conversation",
            "other": "other-conversation",
        }

        self.assertFalse(network.inject_user_message("do not misroute this"))
        self.assertEqual(network._dialogue_injections, {})
        self.assertTrue(network.inject_user_message("continue with Flux", child_id="flux"))
        self.assertEqual(
            list(network._dialogue_injections[("flux", "flux-conversation")]),
            ["continue with Flux"],
        )
        self.assertNotIn(("other", "other-conversation"), network._dialogue_injections)

    def test_injection_targets_the_sole_active_dialogue(self):
        network = self._network()
        network._active_dialogues = {"flux": "flux-conversation"}
        self.assertTrue(network.inject_user_message("clarify the last point"))
        self.assertEqual(
            list(network._dialogue_injections[("flux", "flux-conversation")]),
            ["clarify the last point"],
        )

    def test_config_loader_ignores_commented_examples_and_missing_urls(self):
        network = self._network()
        network._children = {}

        network.load_from_config([
            {
                "_comment": "Remove this example entry and fill in real child details",
                "id": "child", "name": "Flux", "url": "http://192.168.0.28:8765",
            },
            {"id": "not-ready", "name": "Not ready", "url": "  "},
            {"id": "real-flux", "name": "Flux", "url": "http://192.168.0.49:8765/"},
        ])

        self.assertEqual(list(network._children), ["real-flux"])
        self.assertEqual(network._children["real-flux"].url, "http://192.168.0.49:8765")

    def test_current_primary_config_registers_the_local_flux_brain(self):
        config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
        network = self._network()
        network._children = {}

        network.load_from_config(config["LUMINA_CHILDREN"])

        self.assertEqual(list(network._children), ["child"])
        self.assertEqual(network._children["child"].name, "Flux")
        self.assertEqual(network._children["child"].url, "http://192.168.0.28:8765")
        self.assertEqual(config["LUMINA_MASTER_NAME"], "Lumina")

    def test_remote_cognitive_trace_is_bounded_and_requires_peer_scope(self):
        sanitized = sanitize_trace({
            "turn_id": "remote-turn",
            "scope": "peer",
            "peer_name": "FLUX",
            "cognitive_scope_id": "peer:master:c-1",
            "status": "completed",
            "stages": {"readiness": {"status": "passed", "detail": "prompt leak"}},
            "context_sources": {"history": {"status": "injected", "payload": "private"}},
            "raw_prompt": "must not be forwarded",
        })
        self.assertEqual(sanitized["cognitive_scope_id"], "peer:master:c-1")
        self.assertNotIn("detail", sanitized["stages"]["readiness"])
        self.assertNotIn("payload", sanitized["context_sources"]["history"])
        self.assertNotIn("raw_prompt", sanitized)
        self.assertIsNone(sanitize_trace({
            "scope": "human", "cognitive_scope_id": "fred", "stages": {},
        }))

    def test_child_response_trace_is_retained_in_peer_status(self):
        network = self._network()

        class AsyncContext:
            def __init__(self, value):
                self.value = value

            async def __aenter__(self):
                return self.value

            async def __aexit__(self, *_args):
                return False

        class Response:
            status = 200

            async def json(self):
                return {
                    "response": "FLUX reply", "sender_name": "FLUX",
                    "cognitive_trace": {
                        "scope": "peer", "cognitive_scope_id": "peer:master:c-1",
                        "status": "completed", "stages": {"readiness": {"status": "passed"}},
                    },
                }

        class Session:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            def post(self, *_args, **_kwargs):
                return AsyncContext(Response())

        network._aiohttp = SimpleNamespace(
            ClientSession=Session, ClientTimeout=lambda **_kwargs: None,
        )
        network._persona = None
        network._llm = None
        network._history = {}
        network._bubble_fn = None
        network._master_url = ""
        network._master_name = "Lumina"
        class ImmediateLock:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

        network._conversation_lock = lambda *_args: ImmediateLock()
        core_package = ModuleType("core")
        core_package.__path__ = []
        core_state = ModuleType("core.state")
        relational = Mock()
        organism = SimpleNamespace(ai_system=None, _loop=SimpleNamespace())
        core_state.state = SimpleNamespace(persona=SimpleNamespace(
            _organism=organism, _system=None,
            ai_system=SimpleNamespace(relational_memory=relational),
        ))

        async def exchange():
            return await network.send_to_child("flux", "question", show_in_ui=False)

        with patch.dict(sys.modules, {"core": core_package, "core.state": core_state}):
            coroutine = exchange()
            try:
                coroutine.send(None)
            except StopIteration as result:
                response = result.value
            else:
                self.fail("fake transport unexpectedly awaited external I/O")

        self.assertEqual(response, "FLUX reply")
        child = next(item for item in network.list_children() if item["id"] == "flux")
        trace = child["last_cognitive_trace"]
        self.assertEqual(trace["cognitive_scope_id"], "peer:master:c-1")
        self.assertEqual(trace["stages"]["readiness"]["status"], "passed")
        relational.record_exchange.assert_called_once()
        self.assertEqual(relational.record_exchange.call_args.kwargs["valence"], "Neutral")


if __name__ == "__main__":
    unittest.main()
