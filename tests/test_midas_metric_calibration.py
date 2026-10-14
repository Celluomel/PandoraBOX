import tempfile
import unittest
from pathlib import Path

from body_runtime_host.midas_metric_calibration import MiDaSMetricCalibrationStore, fit_metric_depth


class MiDaSMetricCalibrationTests(unittest.TestCase):
    @staticmethod
    def make_samples():
        return [
            {"relative_depth": relative, "distance_m": 0.72 * relative + 0.25 + offset,
             "bearing_error_deg": 4.0}
            for relative in (1.5, 2.5, 3.5, 4.5, 5.5)
            for offset in (-0.015, 0.015)
        ]

    def test_fits_metric_mapping_and_rejects_outlier(self):
        samples = self.make_samples()
        samples.append({"relative_depth": 3.0, "distance_m": 9.0, "bearing_error_deg": 1.0})
        result = fit_metric_depth(samples)
        self.assertAlmostEqual(result["scale_m_per_relative_unit"], 0.72, places=2)
        self.assertAlmostEqual(result["offset_m"], 0.25, places=2)
        self.assertEqual(result["sample_count"], 10)
        self.assertEqual(result["rejected_sample_count"], 1)
        self.assertLess(result["rmse_m"], 0.03)

    def test_accepts_five_synchronized_samples_with_range_coverage(self):
        samples = [
            {"relative_depth": relative, "distance_m": 0.72 * relative + 0.25,
             "bearing_error_deg": 4.0}
            for relative in (1.5, 2.5, 3.5, 4.5, 5.5)
        ]
        result = fit_metric_depth(samples)
        self.assertEqual(result["sample_count"], 5)
        self.assertAlmostEqual(result["scale_m_per_relative_unit"], 0.72, places=2)

    def test_rejects_fewer_than_five_synchronized_samples(self):
        samples = self.make_samples()[:4]
        with self.assertRaisesRegex(ValueError, "at least 5.*got 4"):
            fit_metric_depth(samples)

    def test_rejects_samples_without_range_variation(self):
        samples = [{"relative_depth": 2.0, "distance_m": 2.5} for _ in range(10)]
        with self.assertRaisesRegex(ValueError, "0.8 m"):
            fit_metric_depth(samples)

    def test_rejects_sensor_samples_that_are_not_time_aligned(self):
        samples = self.make_samples()
        for sample in samples:
            sample["radar_delta_s"] = 1.2

        with self.assertRaisesRegex(ValueError, "got 0"):
            fit_metric_depth(samples)

    def test_calibration_persists_and_loads_from_disk(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / "midas_metric_calibration.json"
            saved = MiDaSMetricCalibrationStore(path).calibrate({"samples": self.make_samples()})
            loaded = MiDaSMetricCalibrationStore(path).status()
        self.assertTrue(loaded["available"])
        self.assertEqual(loaded["sample_count"], saved["sample_count"])
        self.assertEqual(loaded["scale_m_per_relative_unit"], saved["scale_m_per_relative_unit"])


if __name__ == "__main__":
    unittest.main()
