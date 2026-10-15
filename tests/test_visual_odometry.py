import unittest

from body_runtime_host.visual_odometry import VisualOdometry


class VisualOdometryTests(unittest.TestCase):
    def test_rejects_depth_that_is_not_time_aligned(self):
        odometry = VisualOdometry()
        result = odometry.update(
            {"frame_id": "camera-1", "captured_at": 10.0, "image_base64": "unused"},
            {"captured_at": 9.0, "depth_gray_jpeg_base64": "unused"},
            {"available": True, "scale_m_per_relative_unit": 0.5, "offset_m": 0.0},
        )
        self.assertFalse(result["available"])
        self.assertEqual(result["state"], "degraded")
        self.assertIn("not synchronized", result["reason"])

    def test_requires_persistent_radar_anchored_depth_calibration(self):
        odometry = VisualOdometry()
        result = odometry.update(
            {"frame_id": "camera-1", "captured_at": 10.0, "image_base64": "unused"},
            {"captured_at": 10.0, "depth_gray_jpeg_base64": "unused"},
            {"available": False},
        )
        self.assertFalse(result["available"])
        self.assertIn("calibration is unavailable", result["reason"])

    def test_repeated_frame_does_not_advance_or_recompute_pose(self):
        odometry = VisualOdometry()
        odometry._previous = {"frame_id": "camera-1"}
        odometry._last = {"state": "tracking", "available": True, "position_m": [0.2, 0.1, 0.0]}
        result = odometry.update(
            {"frame_id": "camera-1"}, {}, {},
        )
        self.assertEqual(result, odometry._last)
        self.assertEqual(result["position_m"], [0.2, 0.1, 0.0])


if __name__ == "__main__":
    unittest.main()
