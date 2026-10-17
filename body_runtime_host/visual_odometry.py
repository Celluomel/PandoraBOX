"""Experimental camera odometry using synchronized MiDaS depth and YOLO tracks.

This estimates relative motion only. It is not a navigation-grade pose source
until camera intrinsics, depth scale, drift, and hardware runs are validated.
"""
from __future__ import annotations

import base64
import math
import threading
import time
from typing import Any


class VisualOdometry:
    def __init__(self, *, horizontal_fov_deg: float = 65.0, max_features: int = 700):
        self.horizontal_fov_deg = float(horizontal_fov_deg)
        self.max_features = max(100, int(max_features))
        self._lock = threading.RLock()
        self._previous: dict[str, Any] | None = None
        self._position = [0.0, 0.0, 0.0]
        self._yaw = 0.0
        self._last: dict[str, Any] = {"state": "waiting", "available": False,
                                      "source": "camera_midas_rgbd", "simulated": False}

    @staticmethod
    def _decode_image(encoded: str):
        import cv2
        import numpy as np

        raw = base64.b64decode(encoded, validate=True)
        image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ValueError("could not decode synchronized camera/depth image")
        if image.ndim == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if image.dtype != np.uint8:
            maximum = float(np.iinfo(image.dtype).max)
            image = np.clip(image.astype(np.float32) * (255.0 / maximum), 0, 255).astype(np.uint8)
        return image

    @staticmethod
    def _wrap_angle(value: float) -> float:
        return (value + math.pi) % (2.0 * math.pi) - math.pi

    @staticmethod
    def _imu_at(samples: list[dict] | None, timestamp: float) -> dict | None:
        valid = [item for item in (samples or []) if isinstance(item, dict)
                 and item.get("attitude_valid") and item.get("yaw_relative_deg") is not None]
        if not valid:
            return None
        nearest = min(valid, key=lambda item: abs(float(item.get("timestamp") or 0.0) - timestamp))
        if abs(float(nearest.get("timestamp") or 0.0) - timestamp) > 0.15:
            return None
        return nearest

    def status(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._last)

    def reset(self) -> None:
        with self._lock:
            self._previous = None
            self._position = [0.0, 0.0, 0.0]
            self._yaw = 0.0
            self._last = {"state": "waiting", "available": False,
                          "source": "camera_midas_rgbd", "simulated": False}

    def update(self, frame: dict, depth: dict, calibration: dict,
               detections: list[dict] | None = None,
               imu_history: list[dict] | None = None) -> dict[str, Any]:
        """Consume one synchronized RGB/depth pair and estimate camera motion."""
        frame_id = str(frame.get("frame_id") or "")
        with self._lock:
            if frame_id and self._previous and frame_id == self._previous["frame_id"]:
                return dict(self._last)
        current: dict[str, Any] | None = None
        try:
            captured_at = float(frame["captured_at"])
            depth_at = float(depth["captured_at"])
            if not calibration.get("available"):
                raise ValueError("radar-anchored MiDaS metric calibration is unavailable")
            inverse_scale = float(calibration["inverse_scale_per_relative_unit"])
            inverse_offset = float(calibration["inverse_offset_per_m"])
            rmse = float(calibration.get("rmse_m", 0.0))
            if not frame_id or not math.isfinite(captured_at) or not math.isfinite(depth_at):
                raise ValueError("camera/depth timestamps are unavailable")
            if abs(captured_at - depth_at) > 0.35:
                raise ValueError("MiDaS depth is not synchronized to the camera frame")
            if not 1e-6 <= abs(inverse_scale) <= 1e3 or not -1e3 <= inverse_offset <= 1e3:
                raise ValueError("radar-anchored MiDaS metric calibration is unavailable")
            depth_encoded = depth.get("depth_raw_png_base64") or depth.get("depth_gray_jpeg_base64")
            if not frame.get("image_base64") or not depth_encoded:
                raise ValueError("camera image or MiDaS depth image is unavailable")

            import cv2
            import numpy as np

            gray = self._decode_image(frame["image_base64"])
            depth_gray = self._decode_image(depth_encoded)
            if depth_gray.shape != gray.shape:
                depth_gray = cv2.resize(depth_gray, (gray.shape[1], gray.shape[0]), interpolation=cv2.INTER_LINEAR)
            height, width = gray.shape
            focal = width / (2.0 * math.tan(math.radians(self.horizontal_fov_deg) / 2.0))
            camera = np.array([[focal, 0.0, width / 2.0],
                               [0.0, focal, height / 2.0],
                               [0.0, 0.0, 1.0]], dtype=np.float64)
            mask = np.full((height, width), 255, dtype=np.uint8)
            for detection in detections or []:
                box = detection.get("bbox")
                if not isinstance(box, (list, tuple)) or len(box) < 4:
                    continue
                x1, y1, x2, y2 = (float(v) for v in box[:4])
                # YOLOX boxes are normalized in the sensor perception contract.
                if max(abs(x1), abs(y1), abs(x2), abs(y2)) <= 1.5:
                    x1, x2, y1, y2 = x1 * width, x2 * width, y1 * height, y2 * height
                cv2.rectangle(mask, (max(0, int(x1)), max(0, int(y1))),
                              (min(width - 1, int(x2)), min(height - 1, int(y2))), 0, -1)

            points = cv2.goodFeaturesToTrack(gray, maxCorners=self.max_features, qualityLevel=0.01,
                                             minDistance=8, mask=mask, blockSize=7)
            current = {"frame_id": frame_id, "captured_at": captured_at, "gray": gray,
                       "depth": depth_gray, "points": points, "camera": camera,
                       "imu_attitude": self._imu_at(imu_history, captured_at)}
            with self._lock:
                if self._previous is None:
                    self._previous = current
                    self._last = {"state": "initializing", "available": False,
                                  "source": "camera_midas_rgbd", "frame_id": frame_id,
                                  "captured_at": captured_at, "simulated": False,
                                  "position_m": list(self._position), "yaw_rad": self._yaw,
                                  "reason": "waiting for the next synchronized camera/depth frame"}
                    return dict(self._last)
                previous = self._previous
                if points is None or previous["points"] is None or len(previous["points"]) < 12:
                    raise ValueError("too few static visual features for odometry")

                tracked, status, _ = cv2.calcOpticalFlowPyrLK(
                    previous["gray"], gray, previous["points"], None,
                    winSize=(21, 21), maxLevel=3,
                    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
                )
                good = status.reshape(-1).astype(bool)
                old_pixels = previous["points"].reshape(-1, 2)[good]
                new_pixels = tracked.reshape(-1, 2)[good]
                if len(old_pixels) < 12:
                    raise ValueError("too few tracked static features")

                old_depth = previous["depth"]
                px = np.clip(np.rint(old_pixels[:, 0]).astype(int), 0, width - 1)
                py = np.clip(np.rint(old_pixels[:, 1]).astype(int), 0, height - 1)
                raw_min = float(depth.get("depth_raw_min", 0.0) or 0.0)
                raw_max = float(depth.get("depth_raw_max", 0.0) or 0.0)
                if depth.get("depth_raw_png_base64") and raw_max > raw_min:
                    relative = raw_min + old_depth[py, px].astype(np.float64) / 255.0 * (raw_max - raw_min)
                else:
                    relative = old_depth[py, px].astype(np.float64) / 255.0
                inverse_range = inverse_scale * relative + inverse_offset
                z = np.divide(1.0, inverse_range, out=np.full_like(inverse_range, np.nan), where=inverse_range > 1e-6)
                valid = np.isfinite(z) & (z >= 0.25) & (z <= 10.0)
                old_pixels, new_pixels, z = old_pixels[valid], new_pixels[valid], z[valid]
                if len(z) < 12:
                    raise ValueError("too few tracked features have calibrated MiDaS depth")
                fx, fy = camera[0, 0], camera[1, 1]
                cx, cy = camera[0, 2], camera[1, 2]
                object_points = np.column_stack(((old_pixels[:, 0] - cx) * z / fx,
                                                 (old_pixels[:, 1] - cy) * z / fy, z)).astype(np.float32)
                ok, rotation, translation, inliers = cv2.solvePnPRansac(
                    object_points, new_pixels.astype(np.float32), camera, None,
                    iterationsCount=100, reprojectionError=3.0, confidence=0.995,
                    flags=cv2.SOLVEPNP_EPNP,
                )
                inlier_count = len(inliers) if inliers is not None else 0
                if not ok or inlier_count < 10:
                    raise ValueError("RGB-D motion fit has too few consistent inliers")
                rotation_matrix, _ = cv2.Rodrigues(rotation)
                camera_delta = -rotation_matrix.T @ translation.reshape(3)
                dt = captured_at - previous["captured_at"]
                if not 0.03 <= dt <= 2.0:
                    self._previous = current
                    self._last = {"state": "reacquiring", "available": False,
                                  "source": "camera_midas_rgbd", "frame_id": frame_id,
                                  "captured_at": captured_at, "simulated": False,
                                  "position_m": list(self._position), "yaw_rad": self._yaw,
                                  "reason": "waiting for consecutive synchronized frames within 2 seconds"}
                    return dict(self._last)
                travel = float(np.linalg.norm(camera_delta))
                if not math.isfinite(travel) or travel > 1.0:
                    raise ValueError("estimated frame-to-frame motion is implausible")
                # Camera coordinates (right, down, forward) -> body/map (forward, left, up).
                local_forward = float(camera_delta[2])
                local_left = -float(camera_delta[0])
                visual_yaw_delta = math.atan2(float(rotation_matrix[0, 2]), float(rotation_matrix[2, 2]))
                previous_imu = previous.get("imu_attitude")
                current_imu = current.get("imu_attitude")
                imu_yaw_delta = None
                if previous_imu and current_imu:
                    imu_yaw_delta = self._wrap_angle(math.radians(
                        float(current_imu["yaw_relative_deg"]) - float(previous_imu["yaw_relative_deg"])))
                yaw_delta = (self._wrap_angle(0.7 * imu_yaw_delta + 0.3 * visual_yaw_delta)
                             if imu_yaw_delta is not None else visual_yaw_delta)
                self._position[0] += local_forward * math.cos(self._yaw) - local_left * math.sin(self._yaw)
                self._position[1] += local_forward * math.sin(self._yaw) + local_left * math.cos(self._yaw)
                self._yaw = self._wrap_angle(self._yaw + yaw_delta)
                inlier_ratio = inlier_count / max(1, len(object_points))
                self._previous = current
                self._last = {
                    "state": "tracking", "available": True, "source": "camera_midas_rgbd",
                    "frame_id": frame_id, "captured_at": captured_at, "simulated": False,
                    "coordinate_frame": "visual_odom", "position_m": [round(v, 4) for v in self._position],
                    "yaw_rad": round(self._yaw, 5), "delta_m": [round(float(v), 4) for v in camera_delta],
                    "delta_yaw_rad": round(yaw_delta, 5), "speed_mps": round(travel / dt, 4),
                    "visual_yaw_delta_rad": round(visual_yaw_delta, 5),
                    "imu_yaw_delta_rad": round(imu_yaw_delta, 5) if imu_yaw_delta is not None else None,
                    "yaw_fusion": "imu_visual_70_30" if imu_yaw_delta is not None else "visual_only",
                    "imu_attitude_valid": current_imu is not None,
                    "inliers": inlier_count, "features": len(object_points),
                    "confidence": round(min(1.0, inlier_ratio * min(1.0, inlier_count / 40.0)), 3),
                    "depth_calibration_rmse_m": rmse,
                    "quality": "experimental; drift and camera intrinsics not yet validated",
                }
                return dict(self._last)
        except Exception as exc:
            with self._lock:
                if current is not None:
                    self._previous = current
                self._last = {"state": "degraded", "available": False,
                              "source": "camera_midas_rgbd", "frame_id": frame_id or None,
                              "simulated": False, "position_m": list(self._position),
                              "yaw_rad": self._yaw, "reason": str(exc)[:240]}
                return dict(self._last)
