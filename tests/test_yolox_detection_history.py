import unittest

from body_runtime_host.yolox_service import YoloXService


class YoloXDetectionHistoryTests(unittest.TestCase):
    def test_detection_results_are_addressable_by_camera_frame_id(self):
        service = YoloXService(lambda _key, default: default, lambda: {})
        service._detection_results["frame-1"] = {
            "state": "ready", "frame_id": "frame-1", "detections": [{"label": "person"}],
        }

        self.assertEqual(service.detection_result("frame-1")["detections"][0]["label"], "person")
        self.assertIsNone(service.detection_result("frame-2"))

    def test_nearest_detection_is_selected_by_capture_timestamp(self):
        service = YoloXService(lambda _key, default: default, lambda: {})
        service._detection_results.update({
            "older": {"state": "ready", "frame_id": "older", "captured_at": 10.0},
            "nearest": {"state": "ready", "frame_id": "nearest", "captured_at": 10.4},
            "newer": {"state": "ready", "frame_id": "newer", "captured_at": 11.0},
        })

        self.assertEqual(service.nearest_detection_result(10.45)["frame_id"], "nearest")
        self.assertIsNone(service.nearest_detection_result(12.0, max_delta_s=0.75))


if __name__ == "__main__":
    unittest.main()
