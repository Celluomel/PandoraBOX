"""Persistent affine calibration from MiDaS-relative values to radar metres."""
from __future__ import annotations

import json
import math
import statistics
import time
from pathlib import Path
from typing import Any


def fit_metric_depth(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Fit a robust affine mapping after rejecting poorly aligned samples."""
    valid = []
    for sample in samples if isinstance(samples, list) else []:
        if not isinstance(sample, dict):
            continue
        try:
            relative = float(sample["relative_depth"])
            distance = float(sample["distance_m"])
            bearing_error = abs(float(sample.get("bearing_error_deg", 0.0)))
            frame_delta = abs(float(sample.get("frame_delta_s", 0.0)))
        except (KeyError, TypeError, ValueError):
            continue
        if (math.isfinite(relative) and math.isfinite(distance) and math.isfinite(bearing_error)
                and math.isfinite(frame_delta) and frame_delta <= 0.75
                and 1.1 <= relative <= 6.9 and 0.25 <= distance <= 10.0
                and bearing_error <= 15.0):
            valid.append((relative, distance))

    if len(valid) < 8:
        raise ValueError(f"Need at least 8 synchronized radar/YOLOX samples; got {len(valid)}")
    distances = [item[1] for item in valid]
    if max(distances) - min(distances) < 0.8:
        raise ValueError("Move the detected person at least 0.8 m closer/farther during calibration")
    if len({round(distance / 0.25) for distance in distances}) < 3:
        raise ValueError("Need samples from at least three distinct radar distance bands")

    def regress(items: list[tuple[float, float]]) -> tuple[float, float]:
        mean_x = sum(item[0] for item in items) / len(items)
        mean_y = sum(item[1] for item in items) / len(items)
        variance = sum((item[0] - mean_x) ** 2 for item in items)
        if variance < 1e-6:
            raise ValueError("MiDaS values did not vary enough; change target distance")
        slope = sum((x - mean_x) * (y - mean_y) for x, y in items) / variance
        return slope, mean_y - slope * mean_x

    slope, offset = regress(valid)
    residuals = [distance - (slope * relative + offset) for relative, distance in valid]
    median_residual = statistics.median(residuals)
    mad = statistics.median(abs(value - median_residual) for value in residuals)
    cutoff = max(0.35, 3.0 * mad)
    inliers = [item for item, residual in zip(valid, residuals) if abs(residual - median_residual) <= cutoff]
    if len(inliers) < 8:
        raise ValueError(f"Only {len(inliers)} well-matched samples remain after outlier rejection")

    slope, offset = regress(inliers)
    if not 0.05 <= slope <= 5.0 or not -10.0 <= offset <= 10.0:
        raise ValueError("The fitted depth scale is implausible; check camera/radar alignment and matches")
    rmse = math.sqrt(sum((distance - (slope * relative + offset)) ** 2
                         for relative, distance in inliers) / len(inliers))
    if rmse > 1.0:
        raise ValueError(f"Radar/YOLOX matches are too inconsistent (fit error {rmse:.2f} m; maximum 1.00 m)")
    return {
        "schema": "midas_metric_calibration.v1",
        "available": True,
        "scale_m_per_relative_unit": round(slope, 8),
        "offset_m": round(offset, 8),
        "sample_count": len(inliers),
        "rejected_sample_count": len(valid) - len(inliers),
        "rmse_m": round(rmse, 4),
        "calibrated_range_m": [round(min(item[1] for item in inliers), 2),
                                round(max(item[1] for item in inliers), 2)],
        "calibrated_relative_range": [round(min(item[0] for item in inliers), 4),
                                      round(max(item[0] for item in inliers), 4)],
        "radar_source": "hlk_ld2450",
        "calibrated_at": time.time(),
    }


class MiDaSMetricCalibrationStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def status(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if (data.get("schema") == "midas_metric_calibration.v1"
                    and math.isfinite(float(data["scale_m_per_relative_unit"]))
                    and math.isfinite(float(data["offset_m"]))):
                return {**data, "available": True}
        except (OSError, ValueError, TypeError, KeyError):
            pass
        return {"schema": "midas_metric_calibration.v1", "available": False}

    def calibrate(self, payload: dict[str, Any]) -> dict[str, Any]:
        calibration = fit_metric_depth(payload.get("samples") if isinstance(payload, dict) else [])
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        temporary.write_text(json.dumps(calibration, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)
        return calibration
