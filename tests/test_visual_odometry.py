import unittest
from types import SimpleNamespace
from unittest.mock import patch

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

    def test_degraded_motion_fit_rebases_on_current_synchronized_frame(self):
        class FakePoints:
            def __len__(self):
                return 20

        class FakeImage:
            shape = (24, 32)

        points = FakePoints()
        cv2 = SimpleNamespace(
            goodFeaturesToTrack=lambda *args, **kwargs: points,
            calcOpticalFlowPyrLK=lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("synthetic LK failure")),
        )
        numpy = SimpleNamespace(array=lambda *args, **kwargs: [], full=lambda *args, **kwargs: [], float64=float, uint8=int)
        calibration = {"available": True, "scale_m_per_relative_unit": 0.5, "offset_m": 0.0}
        odometry = VisualOdometry()
        with patch.dict("sys.modules", {"cv2": cv2, "numpy": numpy}), \
                patch.object(odometry, "_decode_jpeg", return_value=FakeImage()):
            first = {"frame_id": "camera-1", "captured_at": 10.0, "image_base64": "image"}
            depth = {"captured_at": 10.0, "depth_gray_jpeg_base64": "depth"}
            initial = odometry.update(first, depth, calibration)
            self.assertEqual(initial["state"], "initializing", initial)
            second = {**first, "frame_id": "camera-2", "captured_at": 10.2}
            result = odometry.update(second, {**depth, "captured_at": 10.2}, calibration)

        self.assertEqual(result["state"], "degraded")
        self.assertEqual(odometry._previous["frame_id"], "camera-2")


if __name__ == "__main__":
    unittest.main()
