import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from body_runtime_host.local_camera import LocalCameraCapture
from body_runtime_host.worldmodel.sources import SimRobotSource


class LocalCameraTests(unittest.TestCase):
    def test_capture_is_stopped_by_default(self):
        capture = LocalCameraCapture()
        self.assertEqual(capture.status()["status"], "stopped")
        self.assertEqual(capture.latest(), {})

    def test_sim_source_prefers_external_camera_frame(self):
        frame = {
            "image_base64": "aGVsbG8=",
            "mime_type": "image/jpeg",
            "width": 640,
            "height": 480,
            "captured_at": 123.0,
            "source": "pc_camera",
        }
        source = SimRobotSource(camera_provider=lambda: dict(frame))
        observation = source.observe()
        self.assertEqual(observation.modalities["camera"]["source"], "pc_camera")
        self.assertEqual(observation.modalities["camera"]["image_base64"], "aGVsbG8=")

    def test_opencv_is_optional(self):
        capture = LocalCameraCapture()
        with patch.dict("sys.modules", {"cv2": None}):
            self.assertFalse(capture._opencv_available())

    def test_live_capture_toggle_does_not_change_startup_preference(self):
        import body_runtime_host.runtime as brt
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(brt, "CONFIG_PATH", Path(tmp) / "config.json"), patch.object(brt, "_load_dotenv"):
                host = brt.BodyHost()
                with patch.object(host, "_configure_local_camera", return_value={"status": "starting"}) as configure:
                    started = host.set_camera_capture(True)
                    configure.assert_called_once_with(start=True)
                    self.assertTrue(started["ok"])
                    self.assertFalse(host.camera_settings()["startup_enabled"])
                with patch.object(host, "_configure_local_camera", return_value={"status": "stopped"}) as configure:
                    stopped = host.set_camera_capture(False)
                    configure.assert_called_once_with(start=False)
                    self.assertTrue(stopped["ok"])
                    self.assertFalse(host.camera_settings()["startup_enabled"])

    def test_saving_settings_does_not_restart_stopped_camera_when_startup_enabled(self):
        import json
        import body_runtime_host.runtime as brt
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            with patch.object(brt, "CONFIG_PATH", config_path), patch.object(brt, "_load_dotenv"):
                host = brt.BodyHost()
                with patch.object(host, "_configure_local_camera", return_value={"status": "stopped"}) as configure:
                    result = host.update_camera_settings({"startup_enabled": True})
                configure.assert_called_once_with(start=False)
                self.assertTrue(result["startup_enabled"])
                self.assertTrue(json.loads(config_path.read_text(encoding="utf-8"))["BODY_CAMERA_STARTUP_ENABLED"])


if __name__ == "__main__":
    unittest.main()
