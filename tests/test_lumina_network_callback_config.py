import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "lumina_network_config_under_test", ROOT / "core" / "lumina_network_config.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class LuminaNetworkCallbackConfigTests(unittest.TestCase):
    def test_default_remains_same_machine_loopback(self):
        self.assertEqual(MODULE.master_callback_base_url(SimpleNamespace(NICEGUI_PORT=8080)),
                         "http://127.0.0.1:8080")

    def test_explicit_reachable_address_is_used(self):
        settings = SimpleNamespace(LUMINA_MASTER_CALLBACK_URL="http://192.168.0.28:8080")
        self.assertEqual(MODULE.master_callback_base_url(settings), "http://192.168.0.28:8080")

    def test_wildcard_and_credential_urls_are_rejected(self):
        for url in ("http://0.0.0.0:8080", "http://user:pass@192.168.0.28:8080"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                MODULE.master_callback_base_url(SimpleNamespace(LUMINA_MASTER_CALLBACK_URL=url))

    def test_all_runtime_network_initializers_use_the_shared_url(self):
        for path in ("core/state.py", "pages/main_page.py", "core/interface_api.py"):
            source = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn("master_callback_base_url", source, path)

        settings = (ROOT / "managers/settings_manager.py").read_text(encoding="utf-8")
        api = (ROOT / "core/interface_api.py").read_text(encoding="utf-8")
        self.assertIn("LUMINA_MASTER_CALLBACK_URL: str", settings)
        self.assertIn("'LUMINA_MASTER_CALLBACK_URL'", api)


if __name__ == "__main__":
    unittest.main()
