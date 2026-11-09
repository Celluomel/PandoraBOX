import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import managers.settings_manager as settings_manager
from managers.settings_manager import resolve_config_path


class ConfigProfileSelectionTests(unittest.TestCase):
    def test_default_profile_preserves_existing_behavior(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve_config_path(), Path("config.json"))

    def test_environment_selects_child_profile(self):
        with patch.dict(os.environ, {"LUMINA_CONFIG_PATH": "config_Flux.json"}):
            self.assertEqual(resolve_config_path(), Path("config_Flux.json"))

    def test_process_role_and_listener_can_be_overridden_without_editing_profile(self):
        env = {
            "LUMINA_NETWORK_ROLE": "child",
            "BRAIN_API_HOST": "127.0.0.1",
            "BRAIN_API_PORT": "8767",
        }
        with patch.dict(os.environ, env, clear=False), patch("builtins.print"):
            loaded, changed = settings_manager.apply_env_overrides(settings_manager.AppSettings())
        self.assertTrue(changed)
        self.assertEqual(loaded.LUMINA_NETWORK_ROLE, "child")
        self.assertEqual(loaded.BRAIN_API_HOST, "127.0.0.1")
        self.assertEqual(loaded.BRAIN_API_PORT, 8767)

    def test_explicit_path_is_expanded(self):
        self.assertEqual(resolve_config_path("~/lumina-child.json"), Path("~/lumina-child.json").expanduser())

    def test_load_resolves_shared_secret_when_old_profile_omits_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            profile = Path(temp_dir) / "child.json"
            profile.write_text(json.dumps({
                "PERSONA_NAME": "Flux", "LUMINA_NETWORK_ROLE": "child",
            }), encoding="utf-8")
            def resolve_secret(name, value=""):
                return "test-shared-key" if name == "LUMINA_NETWORK_API_KEY" else str(value or "")
            with patch.object(settings_manager, "CONFIG_FILE", profile), \
                    patch.object(settings_manager, "resolve", side_effect=resolve_secret):
                loaded = settings_manager.load_settings()
            self.assertEqual(loaded.PERSONA_NAME, "Flux")
            self.assertEqual(loaded.LUMINA_NETWORK_ROLE, "child")
            self.assertEqual(loaded.LUMINA_NETWORK_API_KEY, "test-shared-key")


if __name__ == "__main__":
    unittest.main()
