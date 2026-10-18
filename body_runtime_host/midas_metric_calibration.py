"""Persistent inverse-depth calibration from MiDaS-relative values to radar metres."""
from __future__ import annotations

import json
import math
import statistics
import threading
import time
from pathlib import Path
from typing import Any

MIN_CALIBRATION_SAMPLES = 15
MIN_TRAINING_SAMPLES = 12
MAX_PAIR_DELTA_S = 0.25
MAX_RADAR_PAIR_DELTA_S = 0.75
MAX_BEARING_ERROR_DEG = 8.0


def fit_metric_depth(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Fit a robust affine mapping after rejecting poorly aligned samples."""
    valid = []
    for sample in samples if isinstance(samples, list) else []:
        if not isinstance(sample, dict):
            continue
        try:
            relative = float(sample["relative_depth"])
            distance = float(sample["forward_m"])
            bearing_error = abs(float(sample.get("bearing_error_deg", 0.0)))
            frame_delta = abs(float(sample.get("frame_delta_s", 0.0)))
            radar_delta = abs(float(sample.get("radar_delta_s", 0.0)))
            imu_delta = abs(float(sample.get("imu_delta_s", math.inf)))
        except (KeyError, TypeError, ValueError):
            continue
        frame_id_match = sample.get("frame_id_match") is True
        frame_aligned = math.isfinite(frame_delta) and (
            frame_delta <= MAX_PAIR_DELTA_S or frame_id_match
        )
        selected_target_confirmed = (sample.get("selected_target_confirmed") is True
                                     and bool(sample.get("selected_radar_target_id")))
        bearing_valid = selected_target_confirmed or bearing_error <= MAX_BEARING_ERROR_DEG
        if (math.isfinite(relative) and math.isfinite(distance) and math.isfinite(bearing_error)
                and frame_aligned
                and math.isfinite(radar_delta) and radar_delta <= MAX_RADAR_PAIR_DELTA_S
                and math.isfinite(imu_delta) and imu_delta <= MAX_PAIR_DELTA_S
                and sample.get("stationary") is True
                and 1.0 <= distance <= 5.0
                and bearing_valid):
            valid.append((relative, distance))

    if len(valid) < MIN_CALIBRATION_SAMPLES:
        raise ValueError(f"Need at least {MIN_CALIBRATION_SAMPLES} synchronized radar/YOLOX samples; got {len(valid)}")
    distances = [item[1] for item in valid]
    if min(distances) > 1.25 or max(distances) < 4.0:
        raise ValueError("Collect anchors spanning approximately 1–5 m; current samples do not cover that range")
    if len({int((distance - 1.0) / 0.8) for distance in distances}) < 4:
        raise ValueError("Need anchors spread across at least four distance bands between 1 and 5 m")

    def regress(items: list[tuple[float, float]]) -> tuple[float, float]:
        # MiDaS relative depth is disparity-like: inverse range is approximately
        # affine in the model output, while range itself is not.
        mean_x = sum(item[0] for item in items) / len(items)
        inverse_ranges = [1.0 / item[1] for item in items]
        mean_y = sum(inverse_ranges) / len(inverse_ranges)
        variance = sum((item[0] - mean_x) ** 2 for item in items)
        if variance < 1e-6:
            raise ValueError("MiDaS values did not vary enough; change target distance")
        slope = sum((item[0] - mean_x) * (inverse_range - mean_y)
                    for item, inverse_range in zip(items, inverse_ranges)) / variance
        return slope, mean_y - slope * mean_x

    def robust_fit(items: list[tuple[float, float]]) -> tuple[float, float, list[tuple[float, float]]]:
        inverse_samples = [(relative, 1.0 / distance) for relative, distance in items]
        pairwise_slopes = [
            (right[1] - left[1]) / (right[0] - left[0])
            for index, left in enumerate(inverse_samples)
            for right in inverse_samples[index + 1:]
            if abs(right[0] - left[0]) > 1e-6
        ]
        slope = statistics.median(pairwise_slopes)
        offset = statistics.median(value - slope * relative for relative, value in inverse_samples)
        residuals = [distance - 1 / (slope * relative + offset)
                     if slope * relative + offset > 0 else math.inf
                     for relative, distance in items]
        center = statistics.median(value for value in residuals if math.isfinite(value))
        mad = statistics.median(abs(value - center) for value in residuals if math.isfinite(value))
        cutoff = max(0.12, 2.5 * 1.4826 * mad)
        inliers = [item for item, residual in zip(items, residuals)
                   if math.isfinite(residual) and abs(residual - center) <= cutoff]
        if len(inliers) < MIN_TRAINING_SAMPLES:
            raise ValueError(f"Only {len(inliers)} consistent MiDaS/radar anchors remain; need {MIN_TRAINING_SAMPLES}")
        return (*regress(inliers), inliers)

    training = [item for index, item in enumerate(valid) if index % 5 != 0]
    held_out = [item for index, item in enumerate(valid) if index % 5 == 0]
    if len(training) < MIN_TRAINING_SAMPLES or len(held_out) < 3:
        raise ValueError("Need at least 15 anchors to reserve at least 3 independent validation samples")
    validation_slope, validation_offset, _ = robust_fit(training)
    held_out_errors = []
    for relative, distance in held_out:
        inverse_range = validation_slope * relative + validation_offset
        if inverse_range <= 0:
            raise ValueError("Validation fit predicts an invalid range; repeat calibration across 1–5 m")
        held_out_errors.append(distance - 1 / inverse_range)
    holdout_rmse = math.sqrt(sum(error ** 2 for error in held_out_errors) / len(held_out_errors))
    if holdout_rmse > 0.4:
        raise ValueError(f"Held-out radar range error is {holdout_rmse:.2f} m; maximum is 0.40 m")

    slope, offset, inliers = robust_fit(valid)
    denominators = [slope * relative + offset for relative, _ in inliers]
    if (not 1e-6 <= abs(slope) <= 1e3 or not -1e3 <= offset <= 1e3
            or min(denominators) <= 0):
        raise ValueError("The fitted depth scale is implausible; check camera/radar alignment and matches")
    rmse = math.sqrt(sum((distance - 1.0 / (slope * relative + offset)) ** 2
                         for relative, distance in inliers) / len(inliers))
    if rmse > 0.35:
        raise ValueError(f"Radar/YOLOX training fit error is {rmse:.2f} m; maximum is 0.35 m")
    return {
        "schema": "midas_metric_calibration.v4",
        "input": "midas_raw_depth",
        "distance_model": "inverse_affine",
        "available": True,
        "inverse_scale_per_relative_unit": round(slope, 10),
        "inverse_offset_per_m": round(offset, 10),
        "sample_count": len(inliers),
        "rejected_sample_count": len(valid) - len(inliers),
        "rmse_m": round(rmse, 4),
        "holdout_rmse_m": round(holdout_rmse, 4),
        "holdout_sample_count": len(held_out),
        "calibrated_range_m": [round(min(item[1] for item in inliers), 2),
                                round(max(item[1] for item in inliers), 2)],
        "calibrated_relative_range": [round(min(item[0] for item in inliers), 4),
                                      round(max(item[0] for item in inliers), 4)],
        "range_axis": "camera_forward_y",
        "window_seconds": 120,
        "camera_bearing_model": "approximate_70deg_hfov_no_measured_extrinsics",
        "radar_source": "hlk_ld2450",
        "calibrated_at": time.time(),
    }


class MiDaSMetricCalibrationStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._samples: list[dict[str, Any]] = []
        self._seen: set[str] = set()
        self._lock = threading.Lock()
        self._window_seconds = 120.0
        self._bad_residual_count = 0

    def status(self) -> dict[str, Any]:
        with self._lock:
            now = time.time()
            self._prune(now)
            try:
                return fit_metric_depth(self._samples)
            except ValueError as exc:
                return {"schema": "midas_metric_calibration.v4", "input": "midas_raw_depth",
                        "distance_model": "inverse_affine", "available": False,
                        "sample_count": len(self._samples), "window_seconds": self._window_seconds,
                        "reason": str(exc)}

    def _prune(self, now: float) -> None:
        self._samples = [item for item in self._samples
                         if now - float(item.get("_received_at", 0)) <= self._window_seconds]
        self._seen = {str(item.get("sample_id")) for item in self._samples}

    def calibrate(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = payload if isinstance(payload, dict) else {}
        with self._lock:
            now = time.time()
            self._prune(now)
            if body.get("reset") is True:
                self._samples.clear()
                self._seen.clear()
                self._bad_residual_count = 0
            sample = body.get("sample")
            accepted = False
            if isinstance(sample, dict):
                sample_id = str(sample.get("sample_id") or "")
                if sample_id and sample_id not in self._seen:
                    current = None
                    try:
                        current = fit_metric_depth(self._samples)
                    except ValueError:
                        pass
                    if current:
                        try:
                            relative = float(sample["relative_depth"])
                            forward = float(sample["forward_m"])
                            predicted_inverse = (current["inverse_scale_per_relative_unit"] * relative
                                                 + current["inverse_offset_per_m"])
                            error = abs(forward - 1 / predicted_inverse) if predicted_inverse > 0 else math.inf
                            self._bad_residual_count = self._bad_residual_count + 1 if error > 0.65 else 0
                        except (KeyError, TypeError, ValueError, ZeroDivisionError):
                            self._bad_residual_count = 0
                        if self._bad_residual_count >= 3:
                            self._samples.clear()
                            self._seen.clear()
                            self._bad_residual_count = 0
                    stored = dict(sample)
                    stored["_received_at"] = now
                    stored["sample_id"] = sample_id
                    self._samples.append(stored)
                    self._seen.add(sample_id)
                    accepted = True
                    self._prune(now)
            try:
                result = fit_metric_depth(self._samples)
            except ValueError as exc:
                result = {"schema": "midas_metric_calibration.v4", "input": "midas_raw_depth",
                          "distance_model": "inverse_affine", "available": False,
                          "sample_count": len(self._samples), "window_seconds": self._window_seconds,
                          "reason": str(exc)}
            return {**result, "accepted": accepted}
