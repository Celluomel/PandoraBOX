import unittest
import importlib.util
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "core" / "body_bridge_config.py"
_SPEC = importlib.util.spec_from_file_location("body_bridge_config_test_target", _CONFIG_PATH)
_CONFIG = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CONFIG)
validate_bind = _CONFIG.validate_bind


class BodyBridgeListenerTests(unittest.TestCase):
    def test_listener_exposes_only_the_authenticated_websocket_route(self):
        if importlib.util.find_spec("fastapi") is None:
            self.skipTest("FastAPI is not installed in the Body-only test environment")
        from fastapi.routing import APIWebSocketRoute
        from core.body_bridge_listener import app

        routes = [route for route in app.routes if isinstance(route, APIWebSocketRoute)]
        self.assertEqual([route.path for route in routes], ["/api/interface/body/bridge"])
        self.assertFalse(any(getattr(route, "methods", None) for route in app.routes))

    def test_defaults_to_loopback_and_separate_port(self):
        self.assertEqual(validate_bind("127.0.0.1", 8786, "127.0.0.1", 8765), ("127.0.0.1", 8786))

    def test_empty_body_token_falls_back_to_brain_shared_token(self):
        if importlib.util.find_spec("fastapi") is None:
            self.skipTest("FastAPI is not installed in the Body-only test environment")
        from types import SimpleNamespace
        from core.body_bridge import _expected_bridge_token

        body = SimpleNamespace(config_value=lambda key, fallback=None: "")
        config = SimpleNamespace(BODY_BRIDGE_TOKEN="shared-secret")
        self.assertEqual(_expected_bridge_token(body, config), "shared-secret")

    def test_rejects_public_hosts_bad_ports_and_api_port_collision(self):
        for args in (
            ("8.8.8.8", 8786, "127.0.0.1", 8765),
            ("127.0.0.1", 80, "127.0.0.1", 8765),
            ("127.0.0.1", 8765, "0.0.0.0", 8765),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                validate_bind(*args)


if __name__ == "__main__":
    unittest.main()
