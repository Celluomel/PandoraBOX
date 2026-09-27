import json
import tempfile
import unittest
from pathlib import Path


class FNK0031ModulesTest(unittest.TestCase):
    def test_simulator_modules_are_discovered_and_activation_persists(self):
        import body_runtime_host.runtime as brt
        from body_runtime_host.robot_sim import RobotSimServer

        with tempfile.TemporaryDirectory() as tmp:
            real_config_path = brt.CONFIG_PATH
            real_dotenv = brt._load_dotenv
            brt.CONFIG_PATH = Path(tmp) / "config.json"
            brt.CONFIG_PATH.write_text(json.dumps({
                "BODY_PLUGIN_ROBOT_ENABLED": True,
                "FNK0031_URL": "",
                "FNK0031_MODULES": {},
            }), encoding="utf-8")
            brt._load_dotenv = lambda: None
            server = RobotSimServer(port=0)
            server.start()
            host = brt.BodyHost()
            host.config["FNK0031_URL"] = f"http://127.0.0.1:{server.port}"
            try:
                payload = host.fnk0031_modules()
                by_id = {item["id"]: item for item in payload["modules"]}
                self.assertTrue(payload["connected"])
                self.assertTrue(by_id["imu"]["detected"])
                self.assertTrue(by_id["actuators"]["detected"])
                self.assertFalse(by_id["camera"]["detected"])

                live = host.fnk0031_module_status()
                live_by_id = {item["id"]: item for item in live["modules"]}
                self.assertEqual(live_by_id["imu"]["status"], "online")
                self.assertEqual(live_by_id["actuators"]["status"], "online")
                self.assertEqual(live_by_id["camera"]["status"], "not_detected")

                result = host.update_fnk0031_module({"id": "imu", "enabled": False})
                self.assertFalse({item["id"]: item for item in result["modules"]}["imu"]["enabled"])
                saved = json.loads(brt.CONFIG_PATH.read_text(encoding="utf-8"))
                self.assertFalse(saved["FNK0031_MODULES"]["imu"])
            finally:
                server.stop()
                brt.CONFIG_PATH = real_config_path
                brt._load_dotenv = real_dotenv


if __name__ == "__main__":
    unittest.main()
