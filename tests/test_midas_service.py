import unittest
import importlib.util

from body_runtime_host.midas_service import MiDaSDepthService


class MiDaSDepthServiceTests(unittest.TestCase):
    def test_service_is_opt_in_and_reports_relative_depth(self):
        values = {"BODY_MIDAS_ENABLED": False, "BODY_MIDAS_INTERVAL_S": 1.0}
        service = MiDaSDepthService(lambda key, default: values.get(key, default), lambda: {})

        service.start()

        self.assertEqual(service.status()["state"], "disabled")
        self.assertEqual(service.settings()["depth_type"], "relative")
        self.assertEqual(service.settings()["model"], "MiDaS-V2-Small-HTP")
        self.assertEqual(service.settings()["runtime"], "htp_auto")

    def test_inference_interval_is_bounded(self):
        values = {"BODY_MIDAS_ENABLED": False, "BODY_MIDAS_INTERVAL_S": 0.1}
        service = MiDaSDepthService(lambda key, default: values.get(key, default), lambda: {})

        self.assertEqual(service.settings()["interval_s"], 0.15)

    def test_runtime_prefers_htp_and_allows_safe_cpu_fallback(self):
        values = {"BODY_MIDAS_ENABLED": False, "BODY_MIDAS_RUNTIME": "htp_auto"}
        service = MiDaSDepthService(lambda key, default: values.get(key, default), lambda: {})
        self.assertEqual(service.settings()["runtime"], "htp_auto")

    def test_analyzed_frame_returns_exact_camera_input_for_depth_frame(self):
        service = MiDaSDepthService(lambda key, default: default, lambda: {})
        service._analyzed_frame = {
            "frame_id": "camera-7", "captured_at": 7.0, "image_base64": "jpeg",
        }
        self.assertEqual(service.analyzed_frame("camera-7")["captured_at"], 7.0)
        self.assertIsNone(service.analyzed_frame("camera-8"))

    def test_invalid_runtime_setting_falls_back_to_htp_auto(self):
        values = {"BODY_MIDAS_ENABLED": False, "BODY_MIDAS_RUNTIME": "cuda"}
        service = MiDaSDepthService(lambda key, default: values.get(key, default), lambda: {})
        self.assertEqual(service.settings()["runtime"], "htp_auto")

    @unittest.skipUnless(importlib.util.find_spec("cv2"), "OpenCV is not installed in the local test runtime")
    def test_qnn_preprocess_preserves_aspect_and_restores_depth_to_camera_size(self):
        import numpy as np
        from body_runtime_host.midas_worker import _prepare_input, _restore_depth

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        tensor, scale, padding = _prepare_input(frame, (1, 256, 256, 3))
        self.assertEqual(tensor.shape, (1, 256, 256, 3))
        self.assertAlmostEqual(scale, 0.4)
        self.assertEqual(padding, (0, 32))
        restored = _restore_depth(np.ones((1, 256, 256, 1), dtype=np.float32), (640, 480), scale, padding)
        self.assertEqual(restored.shape, (480, 640))

    def test_inference_cadence_waits_only_for_remaining_interval(self):
        started = 10.0
        self.assertAlmostEqual(MiDaSDepthService._remaining_cadence_wait(0.5, started, 10.2), 0.3)
        self.assertEqual(MiDaSDepthService._remaining_cadence_wait(0.5, started, 10.6), 0.0)


if __name__ == "__main__":
    unittest.main()
