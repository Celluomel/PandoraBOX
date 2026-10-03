import sys
import unittest
from unittest.mock import patch

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class BodyRuntimeStatusPublicationTest(unittest.TestCase):
    def test_status_is_published_to_observation_store_and_bridge_buffer(self):
        from body_runtime_host.runtime import BodyHost

        host = BodyHost()
        host.config = {
            "BODY_CAMERA_STARTUP_ENABLED": True,
            "BODY_PLUGIN_ROBOT_ENABLED": False,
            "BODY_WORLDMODEL_ENABLED": True,
        }
        with patch.object(host, "camera_settings", return_value={
            "capture": {"status": "capturing", "available": True, "observed_fps": 12.5,
                        "width": 640, "height": 480, "frame_age_s": 0.04, "last_error": ""}
        }):
            host.publish_runtime_status()

        entry = host.latest["body.runtime.status"]
        self.assertEqual(entry["source"], "body_runtime")
        self.assertEqual(entry["kind"], "runtime_status")
        self.assertTrue(entry["value"]["camera"]["available"])
        self.assertFalse(entry["value"]["robot"]["enabled"])
        self.assertEqual(entry["value"]["world_model"]["enabled"], True)
        self.assertEqual(host._bridge_latest["body.runtime.status"]["observation"]["subject"], "body.runtime")


if __name__ == "__main__":
    unittest.main()
