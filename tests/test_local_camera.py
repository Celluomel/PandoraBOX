import unittest
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


if __name__ == "__main__":
    unittest.main()
