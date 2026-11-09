import ast
import importlib.util
from pathlib import Path
import sys
import threading
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
package = ModuleType("cognition")
package.__path__ = [str(ROOT / "cognition")]
sys.modules["cognition"] = package

from cognition.peer_conversation import PeerConversationStore, PeerTurnUnavailable
from cognition.lumina_network import ChildLumina, LuminaNetwork


class _Persona:
    def __init__(self, response="reply"):
        self.response = response
        self.calls = []

    async def get_response_stream(self, text, **kwargs):
        self.calls.append((text, kwargs))
        yield self.response
        yield {"__meta__": True, "raw": self.response}

    def get_last_turn_trace(self):
        options = self.calls[-1][1]
        return {
            "turn_id": "fake-peer-turn",
            "scope": "peer",
            "peer_name": options.get("peer_name"),
            "cognitive_scope_id": options.get("cognitive_scope_id"),
            "status": "completed",
            "stages": {
                "readiness": {"status": "passed", "at": 1.0, "detail": "private"},
            },
            "context_sources": {"peer_history": {"status": "injected", "secret": "private"}},
        }


class _ImmediateLock:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False


def _run(coro):
    try:
        coro.send(None)
    except StopIteration as result:
        return result.value
    raise AssertionError("peer generation unexpectedly awaited external I/O")


class _FakeRouter:
    def __init__(self):
        self.routes = []

    def _register(self, path, methods):
        def decorate(endpoint):
            self.routes.append(SimpleNamespace(path=path, methods=set(methods), endpoint=endpoint))
            return endpoint
        return decorate

    def post(self, path):
        return self._register(path, {"POST"})

    def get(self, path):
        return self._register(path, {"GET"})


class _FakeFastAPI(SimpleNamespace):
    def __init__(self):
        super().__init__(routes=[])

    def include_router(self, router):
        self.routes.extend(router.routes)


def _load_peer_api():
    """Load the route module without requiring FastAPI in the test venv."""
    fastapi = ModuleType("fastapi")
    fastapi.APIRouter = _FakeRouter
    class _HTTPException(Exception):
        def __init__(self, status_code=500, detail=""):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    fastapi.HTTPException = _HTTPException
    fastapi.Request = object
    spec = importlib.util.spec_from_file_location(
        "lumina_peer_api_under_test", ROOT / "core" / "lumina_peer_api.py",
    )
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"fastapi": fastapi}):
        spec.loader.exec_module(module)
    return module


class PeerConversationStoreTests(unittest.TestCase):
    def test_brain_receiver_route_uses_scoped_store_without_shared_memory_writes(self):
        route_file = ROOT / "core" / "lumina_peer_api.py"
        source = route_file.read_text(encoding="utf-8")
        tree = ast.parse(source)
        route = next(
            node for node in tree.body
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "lumina_network_chat"
        )
        route_source = ast.get_source_segment(source, route)

        self.assertIn("peer_conversation_store.generate_reply", route_source)
        self.assertNotIn("state.memory.add_memory", route_source)
        self.assertNotIn("state.llm.history.append", route_source)

    def test_full_and_headless_apps_mount_the_same_peer_routes(self):
        for relative_path, app_name in (("app.py", "_nicegui_app"), ("brain.py", "api")):
            source = (ROOT / relative_path).read_text(encoding="utf-8")
            tree = ast.parse(source)
            mounted = any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "mount_lumina_peer_routes"
                and node.args
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == app_name
                for node in ast.walk(tree)
            )
            self.assertTrue(mounted, f"{relative_path} must mount the shared peer API")

        peer_api = (ROOT / "core" / "lumina_peer_api.py").read_text(encoding="utf-8")
        for route in (
            "/lumina-network/chat",
            "/lumina-network/receive",
            "/lumina-network/children",
            "/lumina-network/epistemic",
        ):
            self.assertIn(route, peer_api)

        module = _load_peer_api()
        mounted_app = _FakeFastAPI()
        module.mount_lumina_peer_routes(mounted_app)
        paths = {route.path for route in mounted_app.routes}
        self.assertTrue({
            "/lumina-network/chat",
            "/lumina-network/receive",
            "/lumina-network/children",
            "/lumina-network/epistemic",
        }.issubset(paths))

    def test_peer_api_requires_shared_key_for_remote_request(self):
        module = _load_peer_api()
        managers_package = ModuleType("managers")
        managers_package.__path__ = [str(ROOT / "managers")]
        settings_module = ModuleType("managers.settings_manager")
        settings_module.config = SimpleNamespace(LUMINA_NETWORK_API_KEY="")

        class _Request:
            def __init__(self, host, headers=None):
                self.client = SimpleNamespace(host=host)
                self.headers = headers or {}

        with patch.dict(sys.modules, {
            "managers": managers_package,
            "managers.settings_manager": settings_module,
        }):
            module._authorize_peer_request(_Request("127.0.0.1"))
            with self.assertRaises(module.HTTPException) as missing:
                module._authorize_peer_request(_Request("192.168.0.49"))
            self.assertEqual(missing.exception.status_code, 503)

            settings_module.config.LUMINA_NETWORK_API_KEY = "shared-peer-secret"
            with self.assertRaises(module.HTTPException) as invalid:
                module._authorize_peer_request(_Request("192.168.0.49"), {"api_key": "wrong"})
            self.assertEqual(invalid.exception.status_code, 401)
            module._authorize_peer_request(
                _Request("192.168.0.49"), {"api_key": "shared-peer-secret"},
            )

    def test_shared_chat_endpoint_executes_peer_scoped_persona_turn(self):
        peer_store = PeerConversationStore()
        peer_store._conversation_lock = lambda _key: _ImmediateLock()
        persona = _Persona("grounded FLUX reply")
        runtime_state = SimpleNamespace(ready=True, persona=persona, lumina_network=None)

        core_package = ModuleType("core")
        core_package.__path__ = [str(ROOT / "core")]
        core_state = ModuleType("core.state")
        core_state.state = runtime_state
        cognition_package = ModuleType("cognition")
        cognition_package.__path__ = [str(ROOT / "cognition")]
        peer_store_module = ModuleType("cognition.peer_conversation")
        peer_store_module.PeerTurnUnavailable = PeerTurnUnavailable
        peer_store_module.peer_conversation_store = peer_store
        managers_package = ModuleType("managers")
        managers_package.__path__ = [str(ROOT / "managers")]
        settings_module = ModuleType("managers.settings_manager")
        settings_module.config = SimpleNamespace(
            PERSONA_NAME="Flux", LUMINA_NETWORK_API_KEY="",
            LUMINA_NETWORK_ROLE="child", LUMINA_MASTER_ID="master",
        )

        module = _load_peer_api()
        endpoint = next(
            route.endpoint for route in module.router.routes
            if route.path == "/lumina-network/chat" and "POST" in route.methods
        )

        class _Request:
            client = SimpleNamespace(host="127.0.0.1")

            async def json(self):
                return {
                    "text": "FLUX, analyze the measured state",
                    "sender_id": "master",
                    "sender_name": "Lumina",
                    "conversation_id": "turn-4",
                }

        with patch.dict(sys.modules, {
            "core": core_package,
            "core.state": core_state,
            "cognition": cognition_package,
            "cognition.peer_conversation": peer_store_module,
            "managers": managers_package,
            "managers.settings_manager": settings_module,
        }):
            response = _run(endpoint(_Request()))

        self.assertEqual(response, {
            "response": "grounded FLUX reply",
            "sender_id": "flux",
            "sender_name": "Flux",
            "conversation_id": "turn-4",
            "cognitive_trace": {
                "turn_id": "fake-peer-turn",
                "scope": "peer",
                "peer_name": "Lumina",
                "cognitive_scope_id": "peer:master:turn-4",
                "status": "completed",
                "stages": {"readiness": {"status": "passed", "at": 1.0}},
                "context_sources": {"peer_history": {"status": "injected"}},
            },
        })
        self.assertEqual(persona.calls[0][1]["cognitive_scope_id"], "peer:master:turn-4")
        self.assertFalse(persona.calls[0][1]["record_history"])
        self.assertFalse(persona.calls[0][1]["allow_body_actions"])
        self.assertEqual(peer_store.history("master", "turn-4"), [
            {"role": "user", "content": "FLUX, analyze the measured state"},
            {"role": "assistant", "content": "grounded FLUX reply"},
        ])

    def test_peer_routes_enforce_configured_master_child_direction(self):
        module = _load_peer_api()
        chat_endpoint = next(
            route.endpoint for route in module.router.routes
            if route.path == "/lumina-network/chat" and "POST" in route.methods
        )
        receive_endpoint = next(
            route.endpoint for route in module.router.routes
            if route.path == "/lumina-network/receive" and "POST" in route.methods
        )
        epistemic_endpoint = next(
            route.endpoint for route in module.router.routes
            if route.path == "/lumina-network/epistemic" and "POST" in route.methods
        )
        core_package = ModuleType("core")
        core_package.__path__ = [str(ROOT / "core")]
        core_state = ModuleType("core.state")
        core_state.state = SimpleNamespace(ready=False, persona=None, lumina_network=None)
        managers_package = ModuleType("managers")
        managers_package.__path__ = [str(ROOT / "managers")]
        settings_module = ModuleType("managers.settings_manager")
        settings_module.config = SimpleNamespace(
            LUMINA_NETWORK_API_KEY="", LUMINA_NETWORK_ROLE="master",
            LUMINA_MASTER_ID="master", LUMINA_ALLOW_CHILD_INITIATED_MESSAGES=False,
        )

        class Request:
            client = SimpleNamespace(host="127.0.0.1")

            def __init__(self, payload):
                self.payload = payload

            async def json(self):
                return self.payload

        with patch.dict(sys.modules, {
            "core": core_package,
            "core.state": core_state,
            "managers": managers_package,
            "managers.settings_manager": settings_module,
        }):
            with self.assertRaises(module.HTTPException) as master_chat:
                _run(chat_endpoint(Request({"text": "unexpected inbound"})))
            self.assertEqual(master_chat.exception.status_code, 403)
            with self.assertRaises(module.HTTPException) as master_epistemic:
                _run(epistemic_endpoint(Request({"sender_id": "master"})))
            self.assertEqual(master_epistemic.exception.status_code, 403)

            settings_module.config.LUMINA_NETWORK_ROLE = "child"
            with self.assertRaises(module.HTTPException) as child_push:
                _run(receive_endpoint(Request({"sender_id": "flux", "text": "unsolicited"})))
            self.assertEqual(child_push.exception.status_code, 403)

            # Even in child mode, only the configured master may initiate turns.
            with self.assertRaises(module.HTTPException) as wrong_master:
                _run(chat_endpoint(Request({
                    "text": "unexpected peer", "sender_id": "other-brain",
                })))
            self.assertEqual(wrong_master.exception.status_code, 403)

            with self.assertRaises(module.HTTPException) as wrong_epistemic_sender:
                _run(epistemic_endpoint(Request({"sender_id": "other-brain"})))
            self.assertEqual(wrong_epistemic_sender.exception.status_code, 403)
            self.assertFalse(_run(epistemic_endpoint(Request({"sender_id": "master"})))['incorporated'])

    def test_end_to_end_peer_exchange_transports_scoped_reply_and_trace(self):
        child_store = PeerConversationStore()
        child_store._conversation_lock = lambda _key: _ImmediateLock()
        child_persona = _Persona("FLUX cognitive reply")
        master_persona = SimpleNamespace(_organism=None, _system=None, ai_system=None)
        runtime_state = SimpleNamespace(
            ready=True, persona=master_persona, lumina_network=None,
            memory=SimpleNamespace(add_memory=Mock()),
        )

        core_package = ModuleType("core")
        core_package.__path__ = [str(ROOT / "core")]
        core_state = ModuleType("core.state")
        core_state.state = runtime_state
        cognition_package = ModuleType("cognition")
        cognition_package.__path__ = [str(ROOT / "cognition")]
        store_module = ModuleType("cognition.peer_conversation")
        store_module.PeerTurnUnavailable = PeerTurnUnavailable
        store_module.peer_conversation_store = child_store
        managers_package = ModuleType("managers")
        managers_package.__path__ = [str(ROOT / "managers")]
        settings_module = ModuleType("managers.settings_manager")
        settings_module.config = SimpleNamespace(
            PERSONA_NAME="Flux", LUMINA_NETWORK_API_KEY="",
            LUMINA_NETWORK_ROLE="child", LUMINA_MASTER_ID="master",
        )
        peer_api = _load_peer_api()
        chat_endpoint = next(
            route.endpoint for route in peer_api.router.routes
            if route.path == "/lumina-network/chat" and "POST" in route.methods
        )

        class Request:
            def __init__(self, payload):
                self.payload = payload
                self.client = SimpleNamespace(host="127.0.0.1")

            async def json(self):
                return self.payload

        class HttpResponse:
            status = 200

            def __init__(self, payload):
                self.payload = payload

            async def json(self):
                return self.payload

        sent_payloads = []

        class PeerRequest:
            def __init__(self, payload):
                self.payload = payload
                sent_payloads.append(dict(payload))

            async def __aenter__(self):
                prior = runtime_state.persona
                runtime_state.persona = child_persona
                try:
                    self.response = await chat_endpoint(Request(self.payload))
                finally:
                    runtime_state.persona = prior
                return HttpResponse(self.response)

            async def __aexit__(self, *_args):
                return False

        class Session:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            def post(self, _url, *, json, **_kwargs):
                return PeerRequest(json)

        network = LuminaNetwork.__new__(LuminaNetwork)
        network._lock = threading.RLock()
        network._active_conversations = {}
        network._active_dialogues = {}
        network._dialogue_injections = {}
        network._peer_turn_locks = {}
        network._peer_turn_locks_guard = threading.RLock()
        network._children = {"flux": ChildLumina("flux", "FLUX", "http://flux.local")}
        network._persona = None
        network._llm = SimpleNamespace(history=[{"role": "user", "content": "human-only"}])
        network._history = {}
        network._aiohttp = SimpleNamespace(
            ClientSession=Session, ClientTimeout=lambda **_kwargs: None,
        )
        network._bubble_fn = None
        network._master_url = ""
        network._master_name = "Lumina"
        network._conversation_lock = lambda *_args: _ImmediateLock()

        with patch.dict(sys.modules, {
            "core": core_package,
            "core.state": core_state,
            "cognition": cognition_package,
            "cognition.peer_conversation": store_module,
            "managers": managers_package,
            "managers.settings_manager": settings_module,
        }):
            response = _run(network.send_to_child(
                "flux", "Evaluate this hypothesis", show_in_ui=False,
            ))

        conversation_id = network._active_conversations["flux"]
        self.assertEqual(response, "FLUX cognitive reply")
        self.assertEqual(child_store.history("master", conversation_id), [
            {"role": "user", "content": "Evaluate this hypothesis"},
            {"role": "assistant", "content": "FLUX cognitive reply"},
        ])
        self.assertEqual(
            child_persona.calls[0][1]["cognitive_scope_id"],
            f"peer:master:{conversation_id}",
        )
        self.assertFalse(child_persona.calls[0][1]["record_history"])
        self.assertFalse(child_persona.calls[0][1]["allow_body_actions"])
        self.assertEqual(network._children["flux"].last_cognitive_trace["scope"], "peer")
        self.assertEqual(network._children["flux"].last_cognitive_trace["status"], "completed")
        self.assertEqual([item.text for item in network.get_history(conversation_id, "flux")], [
            "Evaluate this hypothesis", "FLUX cognitive reply",
        ])
        self.assertEqual(network._llm.history, [{"role": "user", "content": "human-only"}])
        runtime_state.memory.add_memory.assert_not_called()
        self.assertNotIn("master_callback_url", sent_payloads[0])

    def test_generation_uses_peer_scope_and_keeps_pair_history_separate(self):
        store = PeerConversationStore()
        store._conversation_lock = lambda _key: _ImmediateLock()
        persona = _Persona()

        answer = _run(store.generate_reply(
            persona,
            sender_id="master",
            sender_name="Lumina",
            conversation_id="pair-1",
            text="First message",
        ))

        self.assertEqual(answer, "reply")
        _, options = persona.calls[0]
        self.assertEqual(options["user_id"], "lumina_peer_master")
        self.assertEqual(options["peer_name"], "Lumina")
        self.assertFalse(options["allow_body_actions"])
        self.assertFalse(options["record_history"])
        self.assertEqual(options["conversation_history"], [])
        self.assertEqual(options["cognitive_scope_id"], "peer:master:pair-1")
        self.assertEqual(store.history("master", "pair-1"), [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "reply"},
        ])

        _run(store.generate_reply(
            persona,
            sender_id="master",
            sender_name="Lumina",
            conversation_id="pair-1",
            text="Follow-up",
        ))
        self.assertEqual(persona.calls[1][1]["conversation_history"], [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "reply"},
        ])
        self.assertEqual(persona.calls[1][1]["cognitive_scope_id"], "peer:master:pair-1")
        self.assertEqual(store.history("another-peer", "pair-1"), [])
        self.assertEqual(store.history("master", "other-conversation"), [])

    def test_optional_cognitive_trace_is_scope_checked_and_redacted(self):
        store = PeerConversationStore()
        store._conversation_lock = lambda _key: _ImmediateLock()
        persona = _Persona("auditable reply")

        result = _run(store.generate_reply(
            persona, sender_id="flux", sender_name="FLUX", conversation_id="c-9",
            text="Show your cognitive stages", include_trace=True,
        ))

        self.assertEqual(result["response"], "auditable reply")
        self.assertEqual(result["cognitive_trace"]["cognitive_scope_id"], "peer:flux:c-9")
        self.assertNotIn("detail", result["cognitive_trace"]["stages"]["readiness"])
        self.assertNotIn("secret", result["cognitive_trace"]["context_sources"]["peer_history"])

    def test_optional_cognitive_trace_is_omitted_on_scope_mismatch(self):
        class _WrongScope(_Persona):
            def get_last_turn_trace(self):
                return {"cognitive_scope_id": "human:fred", "stages": {}}

        store = PeerConversationStore()
        store._conversation_lock = lambda _key: _ImmediateLock()
        result = _run(store.generate_reply(
            _WrongScope(), sender_id="flux", sender_name="FLUX", conversation_id="c-10",
            text="Stay in peer scope", include_trace=True,
        ))
        self.assertIsNone(result["cognitive_trace"])

    def test_failed_or_empty_peer_generation_does_not_commit_transcript(self):
        class _FailingPersona:
            async def get_response_stream(self, *_args, **_kwargs):
                yield {"__meta__": True, "error": "provider unavailable"}

        store = PeerConversationStore()
        store._conversation_lock = lambda _key: _ImmediateLock()
        with self.assertRaises(PeerTurnUnavailable):
            _run(store.generate_reply(
                _FailingPersona(), sender_id="master", sender_name="Lumina",
                conversation_id="pair-2", text="Do not lose this request",
            ))
        self.assertEqual(store.history("master", "pair-2"), [])

        class _EmptyPersona:
            async def get_response_stream(self, *_args, **_kwargs):
                yield {"__meta__": True, "raw": ""}

        with self.assertRaises(PeerTurnUnavailable):
            _run(store.generate_reply(
                _EmptyPersona(), sender_id="master", sender_name="Lumina",
                conversation_id="pair-3", text="Empty response",
            ))
        self.assertEqual(store.history("master", "pair-3"), [])

    def test_transcript_store_bounds_history_and_conversation_count(self):
        store = PeerConversationStore(max_messages=2, max_conversations=1)
        store.record_exchange("master", "old", "old request", "old reply")
        store.record_exchange("master", "new", "new request", "new reply")
        store.record_exchange("master", "new", "next request", "next reply")

        self.assertEqual(store.history("master", "old"), [])
        self.assertEqual(store.history("master", "new"), [
            {"role": "user", "content": "next request"},
            {"role": "assistant", "content": "next reply"},
        ])


if __name__ == "__main__":
    unittest.main()
