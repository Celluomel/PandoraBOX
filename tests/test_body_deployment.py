import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from body_runtime_host.deployment import build_bundle
from body_runtime_host.ventuno_gateway import VentunoGateway


class BodyDeploymentTests(unittest.TestCase):
    def test_bundle_contains_sanitized_config_and_excludes_virtual_env(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "body_runtime_host").mkdir()
            (root / "body_runtime_host" / "runtime.py").write_text("# body", encoding="utf-8")
            (root / "body_runtime_host" / "quest_vr.html").write_text("<script src='/quest-vr.js'></script>", encoding="utf-8")
            (root / "body_runtime_host" / "quest-vr.bundle.js").write_text("// bundled renderer", encoding="utf-8")
            (root / ".venv" / "Scripts").mkdir(parents=True)
            (root / ".venv" / "Scripts" / "python.exe").write_bytes(b"secret env")
            config = {"BODY_PORT": 8766, "FNK0031_TOKEN": "do-not-copy", "NORMAL": "ok"}
            (root / "data" / "body").mkdir(parents=True)
            (root / "data" / "body" / "config.json").write_text(json.dumps(config), encoding="utf-8")
            bundle, manifest = build_bundle(root)
            with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
                names = archive.namelist()
                copied = json.loads(archive.read("data/body/config.json"))
            self.assertIn("body_runtime_host/runtime.py", names)
            self.assertIn("body_runtime_host/quest_vr.html", names)
            self.assertIn("body_runtime_host/quest-vr.bundle.js", names)
            self.assertNotIn(".venv/Scripts/python.exe", names)
            self.assertNotIn("FNK0031_TOKEN", copied)
            self.assertEqual(copied["NORMAL"], "ok")
            self.assertFalse(manifest["secrets_included"])

    def test_gateway_stages_only_when_enabled_and_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            output = io.BytesIO()
            with zipfile.ZipFile(output, "w") as archive:
                archive.writestr("BODY_BUNDLE_MANIFEST.json", json.dumps({"contract": "pandorabox.body_bundle.v1"}))
                archive.writestr("data/body/config.json", "{}")
            gateway = VentunoGateway("http://fnk0031.local", deploy_enabled=True, deploy_dir=directory)
            result = gateway.stage_bundle(output.getvalue())
            self.assertTrue(result["staged"])
            self.assertTrue(result["stage_id"].startswith("bundle-"))
            self.assertTrue((Path(result["path"]) / "data/body/config.json").exists())
            activated = gateway.activate_bundle(result["stage_id"])
            self.assertTrue(activated["activated"])
            self.assertEqual(gateway.deployment_status()["active_stage"], result["stage_id"])
            with self.assertRaises(PermissionError):
                VentunoGateway("http://fnk0031.local").stage_bundle(output.getvalue())
            unsafe = io.BytesIO()
            with zipfile.ZipFile(unsafe, "w") as archive:
                archive.writestr("BODY_BUNDLE_MANIFEST.json", json.dumps({"contract": "pandorabox.body_bundle.v1"}))
                archive.writestr("../escape.txt", "no")
            with self.assertRaises(ValueError):
                gateway.stage_bundle(unsafe.getvalue())


if __name__ == "__main__":
    unittest.main()
