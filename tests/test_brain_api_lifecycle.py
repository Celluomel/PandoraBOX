import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class BrainApiLifecycleTests(unittest.TestCase):
    def test_full_app_starts_and_stops_brain_api_separately(self):
        tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
        startup = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "_on_startup"
        )
        shutdown = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "_on_shutdown"
        )
        start_line = next(
            node.lineno for node in ast.walk(startup)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "start_brain_api_server"
        )
        initialize_line = next(
            node.lineno for node in ast.walk(startup)
            if isinstance(node, ast.Await)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "initialize"
        )
        self.assertLess(start_line, initialize_line)
        self.assertTrue(any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "stop_brain_api_server"
            for node in ast.walk(shutdown)
        ))

    def test_headless_launcher_uses_same_server_lifecycle(self):
        source = (ROOT / "brain.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = {
            node.func.id for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertIn("start_brain_api_server", calls)
        self.assertIn("stop_brain_api_server", calls)
        self.assertIn("parse_args([])", source)

    def test_shared_brain_api_contains_health_chat_and_flux_peer_routes(self):
        # Avoid importing brain.py here: it initializes the full cognitive
        # runtime as an import side effect. Verify both launchers mount the
        # same route module; route-level behavior is covered separately.
        for filename in ("brain.py", "app.py"):
            tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
            imports_shared_routes = any(
                isinstance(node, ast.ImportFrom)
                and node.module == "core.lumina_peer_api"
                and any(alias.name == "mount_lumina_peer_routes" for alias in node.names)
                for node in ast.walk(tree)
            )
            mounts_shared_routes = any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "mount_lumina_peer_routes"
                for node in ast.walk(tree)
            )
            self.assertTrue(imports_shared_routes, filename)
            self.assertTrue(mounts_shared_routes, filename)

    def test_listener_uses_configured_loopback_host_and_api_port(self):
        if importlib.util.find_spec("uvicorn") is None:
            self.skipTest("Uvicorn is not installed in this test environment")
        from core.brain_api_server import start_brain_api_server, stop_brain_api_server

        api = object()
        settings = SimpleNamespace(BRAIN_API_HOST="127.0.0.1", BRAIN_API_PORT=8765)
        class _ImmediateThread:
            def __init__(self, target, **_kwargs):
                self.target = target

            def start(self):
                self.target()

            def is_alive(self):
                return False

            def join(self, timeout=None):
                return None

        with patch("core.brain_api_server.uvicorn.Config") as config_cls, \
                patch("core.brain_api_server.uvicorn.Server") as server_cls, \
                patch("core.brain_api_server.asyncio.run") as asyncio_run, \
                patch("core.brain_api_server.threading.Thread", _ImmediateThread):
            server = server_cls.return_value
            server.started = True
            server.serve = lambda: None
            listener = start_brain_api_server(settings, api)
            asyncio_run.assert_called_once()
            config_cls.assert_called_once_with(
                app=api, host="127.0.0.1", port=8765,
                log_level="warning", access_log=False,
            )
            self.assertEqual((listener.host, listener.port), ("127.0.0.1", 8765))
            stop_brain_api_server(listener)
            self.assertTrue(server.should_exit)


if __name__ == "__main__":
    unittest.main()
