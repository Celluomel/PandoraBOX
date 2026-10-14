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


if __name__ == "__main__":
    unittest.main()
