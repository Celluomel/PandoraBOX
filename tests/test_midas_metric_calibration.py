import unittest
from pathlib import Path
from unittest.mock import patch

from body_runtime_host.midas_metric_calibration import MiDaSMetricCalibrationStore, fit_metric_depth


class MiDaSMetricCalibrationTests(unittest.TestCase):
    @staticmethod
    def make_samples():
        samples = []
        for distance in (1.1, 2.0, 3.0, 4.0, 4.8):
            relative = (1.0 / distance - 0.08) / 0.22
            for repeat in range(4):
                samples.append({
                    "sample_id": f"{distance}-{repeat}",
                    "relative_depth": relative + (repeat - 1.5) * 0.0003,
                    "forward_m": distance + (repeat - 1.5) * 0.005,
                    "bearing_error_deg": 2.0,
                    "frame_delta_s": 0.02,
                    "radar_delta_s": 0.03,
                    "imu_delta_s": 0.02,
                    "stationary": True,
                })
        return samples

    def test_inverse_depth_fit_validates_holdout_and_rejects_robust_outlier(self):
        samples = self.make_samples()
        outlier = dict(samples[7], sample_id="outlier", relative_depth=1.7, forward_m=1.3)
        samples.insert(1, outlier)
        result = fit_metric_depth(samples)

        self.assertTrue(result["available"])
        self.assertEqual(result["schema"], "midas_metric_calibration.v4")
        self.assertEqual(result["distance_model"], "inverse_affine")
        self.assertAlmostEqual(result["inverse_scale_per_relative_unit"], 0.22, places=2)
        self.assertAlmostEqual(result["inverse_offset_per_m"], 0.08, places=2)
        self.assertEqual(result["sample_count"], 20)
        self.assertEqual(result["rejected_sample_count"], 1)
        self.assertLess(result["holdout_rmse_m"], 0.05)
        self.assertEqual(result["range_axis"], "camera_forward_y")

    def test_requires_minimum_synchronized_stationary_samples(self):
        with self.assertRaisesRegex(ValueError, "at least 15"):
            fit_metric_depth(self.make_samples()[:14])

    def test_rejects_insufficient_distance_spread(self):
        samples = self.make_samples()
        for sample in samples:
            sample["forward_m"] = 2.5
        with self.assertRaisesRegex(ValueError, "spanning approximately 1–5 m"):
            fit_metric_depth(samples)

    def test_rejects_bad_time_bearing_or_imu_alignment(self):
        samples = self.make_samples()
        for sample in samples:
            sample["imu_delta_s"] = 0.2
        with self.assertRaisesRegex(ValueError, "got 0"):
            fit_metric_depth(samples)

    def test_exact_camera_frame_identity_allows_timestamp_bookkeeping_skew(self):
        samples = self.make_samples()
        for sample in samples:
            sample["frame_delta_s"] = 0.25
            sample["frame_id_match"] = True
        result = fit_metric_depth(samples)
        self.assertTrue(result["available"])

    def test_timestamp_only_camera_pairs_still_obey_100ms_limit(self):
        samples = self.make_samples()
        for sample in samples:
            sample["frame_delta_s"] = 0.101
        with self.assertRaisesRegex(ValueError, "got 0"):
            fit_metric_depth(samples)

    def test_rejects_nonstationary_anchors(self):
        samples = self.make_samples()
        for sample in samples:
            sample["stationary"] = False
        with self.assertRaisesRegex(ValueError, "got 0"):
            fit_metric_depth(samples)

    def test_rolling_store_accepts_samples_and_expires_them(self):
        store = MiDaSMetricCalibrationStore(Path("unused.json"))
        start = 1000.0
        with patch("body_runtime_host.midas_metric_calibration.time.time", return_value=start):
            results = [store.calibrate({"sample": sample}) for sample in self.make_samples()]
        self.assertTrue(results[-1]["available"])
        self.assertEqual(results[-1]["sample_count"], 20)
        with patch("body_runtime_host.midas_metric_calibration.time.time", return_value=start + 21):
            expired = store.status()
        self.assertFalse(expired["available"])
        self.assertEqual(expired["sample_count"], 0)

    def test_duplicate_sample_ids_do_not_count_twice_and_reset_clears_window(self):
        store = MiDaSMetricCalibrationStore(Path("unused.json"))
        samples = self.make_samples()
        with patch("body_runtime_host.midas_metric_calibration.time.time", return_value=1000.0):
            for sample in samples[:14]:
                store.calibrate({"sample": sample})
            duplicate = store.calibrate({"sample": samples[0]})
            cleared = store.calibrate({"reset": True})
        self.assertFalse(duplicate["accepted"])
        self.assertEqual(duplicate["sample_count"], 14)
        self.assertEqual(cleared["sample_count"], 0)


if __name__ == "__main__":
    unittest.main()
