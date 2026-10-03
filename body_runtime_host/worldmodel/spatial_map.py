"""Evidence-preserving sparse metric map built from perception frames.

This module stores observed range endpoints only. It deliberately does not
infer free space or make the map a navigation authority; unobserved voxels stay
unknown until a sensor model with validated ray evidence is added.
"""
from __future__ import annotations

import json
import logging
import math
import os
import tempfile
import threading
import time
from collections import deque
from itertools import islice
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

logger = logging.getLogger(__name__)


class MetricVoxelMap:
    """Accumulate LiDAR endpoint evidence in a sparse, map-frame voxel grid."""

    def __init__(self, *, resolution_m: float = 0.1, max_voxels: int = 100_000,
                 path: str | Path | None = None, persist_every_frames: int = 25,
                 persist_interval_s: float = 10.0) -> None:
        if not math.isfinite(resolution_m) or resolution_m <= 0:
            raise ValueError("resolution_m must be a positive finite number")
        if max_voxels < 1:
            raise ValueError("max_voxels must be positive")
        if persist_every_frames < 1 or not math.isfinite(persist_interval_s) or persist_interval_s <= 0:
            raise ValueError("persistence cadence must be positive")
        self.resolution_m = float(resolution_m)
        self.max_voxels = int(max_voxels)
        self.persist_every_frames = int(persist_every_frames)
        self.persist_interval_s = float(persist_interval_s)
        self.path = Path(path) if path is not None else None
        self._lock = threading.RLock()
        self._voxels: Dict[Tuple[int, int, int], Dict[str, Any]] = {}
        self._frames = 0
        self._rejected_frames = 0
        self._sources: set[str] = set()
        self._recent_frame_ids: deque[str] = deque(maxlen=4096)
        self._recent_frame_id_set: set[str] = set()
        self._dirty_frames = 0
        self._last_saved_at = 0.0
        self._next_retry_at = 0.0
        if self.path and self.path.exists():
            self._load()

    def integrate(self, frame: Dict[str, Any], *, allow_non_native: bool = False) -> Dict[str, Any]:
        """Integrate a synchronized perception frame or return a rejection reason.

        Supported LiDAR frames are map/world coordinates or sensor coordinates
        with an explicit ``sensor_to_body`` calibration. Synthetic/derived data
        is rejected by default and can only be admitted explicitly for tests.
        """
        reason = self._validate(frame, allow_non_native=allow_non_native)
        if reason:
            with self._lock:
                self._rejected_frames += 1
            return {"accepted": False, "reason": reason, "integrated_returns": 0}

        lidar = frame["lidar"]
        pose = frame["body"]["pose"]
        position = pose["position_m"]
        yaw = float(pose["yaw_rad"])
        source = str(lidar.get("source") or lidar.get("quality", {}).get("source") or "unknown")
        timestamp = float(frame["timestamp"])
        frame_id = str(frame["frame_id"])
        points = lidar.get("points") or []
        accepted = 0

        with self._lock:
            if frame_id in self._recent_frame_id_set:
                self._rejected_frames += 1
                return {"accepted": False, "reason": "duplicate_frame_id", "integrated_returns": 0}
            if len(self._recent_frame_ids) == self._recent_frame_ids.maxlen:
                self._recent_frame_id_set.discard(self._recent_frame_ids[0])
            self._recent_frame_ids.append(frame_id)
            self._recent_frame_id_set.add(frame_id)
            for point in points:
                try:
                    if not isinstance(point, dict):
                        continue
                    xyz = self._to_map(point, lidar, position, yaw)
                    confidence = float(point.get("intensity", point.get("confidence", 1.0)))
                    if not all(math.isfinite(value) for value in (*xyz, confidence)):
                        continue
                    key = tuple(math.floor(value / self.resolution_m) for value in xyz)
                except (KeyError, IndexError, TypeError, ValueError, OverflowError):
                    continue
                voxel = self._voxels.get(key)
                if voxel is None:
                    if len(self._voxels) >= self.max_voxels:
                        continue
                    voxel = {
                        "hits": 0,
                        "confidence_sum": 0.0,
                        "first_seen": timestamp,
                        "last_seen": timestamp,
                        "sources": set(),
                        "frame_ids": set(),
                    }
                    self._voxels[key] = voxel
                voxel["hits"] += 1
                voxel["confidence_sum"] += max(0.0, min(1.0, confidence))
                voxel["last_seen"] = max(voxel["last_seen"], timestamp)
                voxel["sources"].add(source)
                if len(voxel["frame_ids"]) < 8:
                    voxel["frame_ids"].add(frame_id)
                accepted += 1
            self._frames += 1
            self._sources.add(source)
            if self.path:
                self._dirty_frames += 1
            should_persist = bool(self.path) and (
                self._frames == 1
                or self._dirty_frames >= self.persist_every_frames
                or time.monotonic() - self._last_saved_at >= self.persist_interval_s
            ) and time.monotonic() >= self._next_retry_at
            if should_persist:
                self._persist_locked()

        return {
            "accepted": True,
            "integrated_returns": accepted,
            "skipped_returns": len(points) - accepted,
            "voxel_count": len(self._voxels),
            "source": source,
            "persistence_pending": self._dirty_frames > 0,
            "safety_authoritative": False,
        }

    def snapshot(self, *, limit: int | None = 5_000) -> Dict[str, Any]:
        with self._lock:
            voxel_count = len(self._voxels)
            if limit is not None:
                limit = max(0, min(100_000, int(limit)))
                selected_voxels = islice(self._voxels.items(), limit)
            else:
                selected_voxels = self._voxels.items()
            voxels = []
            for (ix, iy, iz), item in selected_voxels:
                voxels.append({
                    "index": [ix, iy, iz],
                    "center_m": [
                        round((ix + 0.5) * self.resolution_m, 4),
                        round((iy + 0.5) * self.resolution_m, 4),
                        round((iz + 0.5) * self.resolution_m, 4),
                    ],
                    "state": "observed_return",
                    "hits": item["hits"],
                    "confidence": round(item["confidence_sum"] / item["hits"], 4),
                    "first_seen": item["first_seen"],
                    "last_seen": item["last_seen"],
                    "sources": sorted(item["sources"]),
                    "frame_ids": sorted(item["frame_ids"]),
                })
            return {
                "contract": "body_metric_voxel_map.v1",
                "coordinate_frame": "map",
                "length_unit": "m",
                "resolution_m": self.resolution_m,
                "frames_integrated": self._frames,
                "frames_rejected": self._rejected_frames,
                "voxel_count": voxel_count,
                "returned_voxel_count": len(voxels),
                "truncated": len(voxels) < voxel_count,
                "sources": sorted(self._sources),
                "recent_frame_ids": list(self._recent_frame_ids),
                "unknown_space_is_implicit": True,
                "free_space_observed": False,
                "safety_authoritative": False,
                "voxels": voxels,
            }

    def clear(self) -> None:
        with self._lock:
            self._voxels.clear()
            self._frames = 0
            self._rejected_frames = 0
            self._sources.clear()
            self._recent_frame_ids.clear()
            self._recent_frame_id_set.clear()
            self._dirty_frames = 1 if self.path else 0
            self._next_retry_at = 0.0
            if self.path:
                self._persist_locked()

    def flush(self) -> bool:
        """Persist pending frames at orderly shutdown without per-frame writes."""
        with self._lock:
            if self.path and self._dirty_frames:
                return self._persist_locked()
            return True

    def _persist_locked(self) -> bool:
        try:
            self._save()
        except (OSError, TypeError, ValueError) as exc:
            self._next_retry_at = time.monotonic() + 30.0
            logger.warning("[body-map] persistence failed; retaining in-memory map and retrying later: %s", exc)
            return False
        self._dirty_frames = 0
        self._last_saved_at = time.monotonic()
        self._next_retry_at = 0.0
        return True

    def _validate(self, frame: Dict[str, Any], *, allow_non_native: bool) -> str:
        if not isinstance(frame, dict) or frame.get("contract") != "body_perception_frame.v2":
            return "unsupported_frame_contract"
        synchronization = frame.get("synchronization")
        if not isinstance(synchronization, dict) or not synchronization.get("synchronized"):
            return "frame_not_synchronized"
        try:
            if not str(frame.get("frame_id") or "").strip():
                return "missing_frame_id"
            timestamp = float(frame["timestamp"])
            body = frame["body"]
            if not isinstance(body, dict):
                return "invalid_metric_pose_or_timestamp"
            pose = body["pose"]
            if not isinstance(pose, dict):
                return "invalid_metric_pose_or_timestamp"
            if str(pose.get("coordinate_frame") or "").lower() not in {"map", "world", "local_map"}:
                return "unsupported_pose_coordinate_frame"
            position = pose["position_m"]
            values = [timestamp, *(float(value) for value in position[:3]), float(pose["yaw_rad"])]
            if len(position) < 3 or not all(math.isfinite(value) for value in values):
                return "invalid_metric_pose_or_timestamp"
        except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError):
            return "invalid_metric_pose_or_timestamp"
        lidar = frame.get("lidar") or {}
        if not isinstance(lidar, dict):
            return "invalid_lidar_payload"
        projection = lidar.get("projection")
        projection = projection if isinstance(projection, dict) else {}
        is_native = lidar.get("native") is True or projection.get("native") is True
        if not is_native and not allow_non_native:
            return "non_native_lidar_requires_explicit_opt_in"
        if not isinstance(lidar.get("points"), list):
            return "missing_lidar_points"
        frame_name = str(lidar.get("frame") or "").lower()
        if frame_name in {"body", "sensor", "robot", "body_sensor"}:
            calibration = lidar.get("calibration") or {}
            if not isinstance(calibration, dict) or not isinstance(calibration.get("sensor_to_body"), dict):
                return "missing_sensor_to_body_calibration"
        elif frame_name not in {"map", "world", "local_map", "body_world"}:
            return "unsupported_lidar_coordinate_frame"
        return ""

    @staticmethod
    def _to_map(point: Dict[str, Any], lidar: Dict[str, Any],
                position: Iterable[float], body_yaw: float) -> Tuple[float, float, float]:
        px, py, pz = (float(point.get(axis, 0.0)) for axis in ("x", "y", "z"))
        frame = str(lidar.get("frame") or "").lower()
        if frame in {"map", "world", "local_map", "body_world"}:
            return px, py, pz
        extrinsic = lidar["calibration"]["sensor_to_body"]
        translation = extrinsic.get("translation_m", [0.0, 0.0, 0.0])
        if len(translation) < 3:
            raise ValueError("sensor translation must have three coordinates")
        sensor_yaw = float(extrinsic.get("yaw_rad", 0.0))
        sx = px * math.cos(sensor_yaw) - py * math.sin(sensor_yaw) + float(translation[0])
        sy = px * math.sin(sensor_yaw) + py * math.cos(sensor_yaw) + float(translation[1])
        sz = pz + float(translation[2])
        bx, by, bz = (float(value) for value in list(position)[:3])
        return (
            bx + sx * math.cos(body_yaw) - sy * math.sin(body_yaw),
            by + sx * math.sin(body_yaw) + sy * math.cos(body_yaw),
            bz + sz,
        )

    def _load(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return
            if payload.get("contract") != "body_metric_voxel_map.v1":
                return
            self._frames = int(payload.get("frames_integrated", 0))
            self._rejected_frames = int(payload.get("frames_rejected", 0))
            self._sources = set(payload.get("sources") or [])
            raw_frame_ids = payload.get("recent_frame_ids")
            if not isinstance(raw_frame_ids, list):
                raw_frame_ids = []
            self._recent_frame_ids = deque(
                [str(value)[:160] for value in raw_frame_ids[-4096:] if value is not None],
                maxlen=4096,
            )
            self._recent_frame_id_set = set(self._recent_frame_ids)
            for item in payload.get("voxels", []):
                if len(self._voxels) >= self.max_voxels:
                    break
                index = tuple(int(value) for value in item["index"])
                if len(index) != 3 or int(item["hits"]) < 1:
                    continue
                self._voxels[index] = {
                    "hits": int(item["hits"]),
                    "confidence_sum": float(item["confidence"]) * int(item["hits"]),
                    "first_seen": float(item["first_seen"]),
                    "last_seen": float(item["last_seen"]),
                    "sources": set(item.get("sources") or []),
                    "frame_ids": set(item.get("frame_ids") or []),
                }
            self._last_saved_at = time.monotonic()
        except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
            self._voxels.clear()
            self._frames = 0
            self._rejected_frames = 0
            self._sources.clear()
            self._recent_frame_ids.clear()
            self._recent_frame_id_set.clear()
            self._dirty_frames = 0

    def _save(self) -> None:
        assert self.path is not None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.snapshot(limit=None)
        fd, temp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, separators=(",", ":"), ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
