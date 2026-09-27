"""Body-owned sensor projections for visual and volumetric perception.

The simulator remains the source of truth, but the cognitive boundary should
look like sensors: a 2-D camera projection and a sparse 3-D range return. The
same payload can later be produced by a camera/LiDAR plugin or sent to a
vision-language model without changing the planner contract.
"""
from __future__ import annotations

import math
import re
import time
from typing import Any, Dict, Iterable, List


def _item_dict(item: Any) -> Dict[str, Any]:
    if hasattr(item, "as_dict"):
        return item.as_dict()
    return dict(item)


def _stable_phase(identifier: str) -> float:
    return (sum((index + 1) * ord(char) for index, char in enumerate(identifier)) % 360) * math.pi / 180.0


def _native_points(modalities: Dict[str, Any]) -> List[Dict[str, Any]]:
    lidar = modalities.get("lidar") or modalities.get("point_cloud") or {}
    if isinstance(lidar, list):
        return [item for item in lidar if isinstance(item, dict)]
    if isinstance(lidar, dict):
        points = lidar.get("points") or lidar.get("returns") or []
        return [item for item in points if isinstance(item, dict)]
    return []


def _lidar_source(modalities: Dict[str, Any]) -> str:
    lidar = modalities.get("lidar") or modalities.get("point_cloud") or {}
    return str(lidar.get("source") or "native_lidar") if isinstance(lidar, dict) else "native_lidar"


def _native_camera_objects(modalities: Dict[str, Any]) -> List[Dict[str, Any]]:
    camera = modalities.get("camera") or modalities.get("vision") or {}
    if isinstance(camera, dict):
        objects = camera.get("objects") or camera.get("detections") or []
    elif isinstance(camera, list):
        objects = camera
    else:
        objects = []
    return [item for item in objects if isinstance(item, dict)]


def _camera_available(modalities: Dict[str, Any]) -> bool:
    camera = modalities.get("camera") or modalities.get("vision") or {}
    return bool(_native_camera_objects(modalities) or (isinstance(camera, dict) and (camera.get("image_base64") or camera.get("image_url"))))


def canonical_category(value: Any) -> str:
    """Return a stable category for cross-sensor association.

    Sensor producers use different identifiers (for example ``mug`` and
    ``cup``). This is semantic normalization only; it never supplies a
    position or overrides measured geometry.
    """
    text = re.sub(r"[_-]+", " ", str(value or "").strip().lower())
    text = " ".join(text.split())
    if not text:
        return "object"
    aliases = {
        "mug": "cup",
        "tumbler": "cup",
        "column": "obstacle",
        "pillar": "obstacle",
        "post": "obstacle",
        "moving object": "mobile_obstacle",
        "moving obstacle": "mobile_obstacle",
        "mobile object": "mobile_obstacle",
        "mobile obstacle": "mobile_obstacle",
        "seat": "chair",
        "desk": "table",
        "work surface": "table",
    }
    return aliases.get(text, text)


def _relative_geometry(point: Dict[str, Any], *, body_x: float, body_y: float,
                       body_yaw: float, frame: str) -> tuple[float, float]:
    """Return range/bearing for a LiDAR point in the Body frame."""
    try:
        x, y = float(point.get("x", 0.0)), float(point.get("y", 0.0))
    except (TypeError, ValueError):
        return 0.0, 0.0
    if str(frame).lower() in {"body", "sensor", "robot", "body_sensor"}:
        dx, dy = x, y
    else:
        dx, dy = x - body_x, y - body_y
    distance = math.hypot(dx, dy)
    bearing = math.atan2(dy, dx)
    if str(frame).lower() not in {"body", "sensor", "robot", "body_sensor"}:
        bearing -= body_yaw
        bearing = math.atan2(math.sin(bearing), math.cos(bearing))
    return distance, bearing


def fuse_sensor_modalities(camera_objects: List[Dict[str, Any]],
                           lidar_points: List[Dict[str, Any]], *,
                           body_x: float, body_y: float, body_yaw: float,
                           lidar_frame: str) -> Dict[str, Any]:
    """Associate visual detections with LiDAR returns.

    Identity is a useful prior when a sensor provides it, but an association
    still requires geometric agreement. For unlabeled returns, nearest range
    and bearing are used. The result is evidence for the Body LLM; the LiDAR
    coordinates remain authoritative.
    """
    prepared = []
    for index, point in enumerate(lidar_points):
        distance, bearing = _relative_geometry(
            point, body_x=body_x, body_y=body_y, body_yaw=body_yaw, frame=lidar_frame,
        )
        prepared.append({
            "index": index,
            "distance": distance,
            "bearing": bearing,
            "category": canonical_category(point.get("object_id") or point.get("label")),
        })

    used_indices: set[int] = set()
    associations = []
    unmatched_vision = []
    for vision in camera_objects:
        category = canonical_category(vision.get("label") or vision.get("kind") or vision.get("id"))
        try:
            visual_range = float(vision.get("range"))
            visual_bearing = float(vision.get("bearing_rad"))
        except (TypeError, ValueError):
            unmatched_vision.append(str(vision.get("id") or vision.get("label") or "object"))
            continue
        candidates = []
        for item in prepared:
            range_error = abs(item["distance"] - visual_range)
            bearing_error = abs(math.atan2(
                math.sin(item["bearing"] - visual_bearing),
                math.cos(item["bearing"] - visual_bearing),
            ))
            category_match = item["category"] == category and category != "object"
            geometric_match = (
                range_error <= max(1.25, visual_range * 0.35)
                and bearing_error <= 0.45
            )
            if category_match or geometric_match:
                score = (2.0 if category_match else 0.0) - range_error - bearing_error
                candidates.append((score, item, range_error, bearing_error, category_match))
        if not candidates:
            unmatched_vision.append(str(vision.get("id") or vision.get("label") or "object"))
            continue
        candidates.sort(key=lambda value: value[0], reverse=True)
        best_score, best, range_error, bearing_error, category_match = candidates[0]
        indices = [item["index"] for _, item, _, _, _ in candidates if item["category"] == category]
        if not indices:
            indices = [best["index"]]
        used_indices.update(indices)
        confidence = max(0.0, min(1.0, (0.75 if category_match else 0.45)
                                   + math.exp(-range_error / 1.5) * 0.2
                                   + math.exp(-bearing_error / 0.5) * 0.1))
        associations.append({
            "vision_id": str(vision.get("id") or vision.get("label") or "object"),
            "vision_label": str(vision.get("label") or vision.get("kind") or "object"),
            "category": category,
            "lidar_point_indices": indices,
            "range_m": round(best["distance"], 3),
            "bearing_rad": round(best["bearing"], 4),
            "range_error_m": round(range_error, 3),
            "bearing_error_rad": round(bearing_error, 4),
            "confidence": round(confidence, 3),
            "geometry_source": "lidar",
        })

    unmatched_lidar = [item["index"] for item in prepared if item["index"] not in used_indices]
    return {
        "associations": associations,
        "matched": len(associations),
        "unmatched_vision": unmatched_vision,
        "unmatched_lidar_point_indices": unmatched_lidar,
        "lidar_returns": len(prepared),
        "method": "category_prior_plus_range_bearing",
        "geometry_authoritative": "lidar",
    }


def sensor_projections(body: Any, objects: Iterable[Any], *, width: float = 12.0,
                       height: float = 12.0, modalities: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Build the unified 2-D/3-D perception boundary.

    Native plugin measurements are preferred. Object-derived projections stay
    available for simulation and are explicitly marked as derived.
    """
    modalities = dict(modalities or {})
    bx, by = float(body.position[0]), float(body.position[1])
    yaw = float(body.orientation)
    camera_objects: List[Dict[str, Any]] = []
    lidar_points: List[Dict[str, Any]] = []

    native_camera = _native_camera_objects(modalities)
    native_lidar = _native_points(modalities)
    for raw in (native_camera or objects):
        item = _item_dict(raw)
        position = item.get("position") or [item.get("x", 0.0), item.get("y", 0.0), item.get("z", 0.0)]
        ox, oy = float(position[0]), float(position[1])
        dx, dy = ox - bx, oy - by
        distance = math.hypot(dx, dy)
        bearing = math.atan2(dy, dx) - yaw
        bearing = math.atan2(math.sin(bearing), math.cos(bearing))
        kind = str(item.get("kind") or "object")
        size = max(0.25, float(item.get("size") or 0.5))
        confidence = max(0.25, min(0.99, 1.0 - distance / max(width, height * 1.25)))
        camera_objects.append({
            "id": str(item.get("id") or "object"),
            "label": str(item.get("label") or kind),
            "kind": kind,
            "range": round(distance, 3),
            "bearing_rad": round(bearing, 4),
            "screen_x": round(0.5 + bearing / math.pi, 4),
            "screen_y": round(0.58 - min(0.38, distance / max(width, height) * 0.08), 4),
            "apparent_size": round(min(0.42, size / max(distance, 1.0)), 4),
            "confidence": round(confidence, 3),
        })

        # A sparse ring plus a top return gives the UI a volumetric signal
        # while keeping the payload small enough for frequent polling.
        radius = max(0.12, size * 0.45)
        phase = _stable_phase(str(item.get("id") or kind))
        for sample in range(8):
            angle = phase + sample * math.pi / 4.0
            lidar_points.append({
                "x": round(ox + math.cos(angle) * radius, 3),
                "y": round(oy + math.sin(angle) * radius, 3),
                "z": round(0.22 + (sample % 3) * 0.28 + min(0.5, size * 0.2), 3),
                "intensity": round(confidence, 3),
                "object_id": str(item.get("id") or "object"),
            })

    if native_lidar:
        lidar_points = []
        for point in native_lidar:
            try:
                lidar_points.append({
                    "x": round(float(point.get("x", 0.0)), 3),
                    "y": round(float(point.get("y", 0.0)), 3),
                    "z": round(float(point.get("z", 0.0)), 3),
                    "intensity": round(float(point.get("intensity", point.get("confidence", 1.0))), 3),
                    "object_id": str(point.get("object_id") or point.get("id") or "return"),
                })
            except (TypeError, ValueError):
                continue
    camera_native = _camera_available(modalities)
    lidar_source = _lidar_source(modalities)
    lidar_native = bool(native_lidar) and lidar_source not in {"virtual_lidar", "derived_scene"}
    camera_objects.sort(key=lambda item: item["range"])
    timestamp = float(getattr(body, "timestamp", 0.0) or time.time())
    frame_id = str(modalities.get("frame_id") or modalities.get("frame") or f"body-{int(timestamp * 1000)}")
    lidar_quality = "native" if lidar_native else "virtual" if lidar_source == "virtual_lidar" else "derived"
    lidar_meta = modalities.get("lidar") or {}
    lidar_frame = str(lidar_meta.get("frame") or "body_world") if isinstance(lidar_meta, dict) else "body_world"
    fusion = fuse_sensor_modalities(
        camera_objects, lidar_points,
        body_x=bx, body_y=by, body_yaw=yaw, lidar_frame=lidar_frame,
    )
    vertical_layers = (
        int(lidar_meta.get("vertical_layers"))
        if isinstance(lidar_meta, dict) and lidar_meta.get("vertical_layers") is not None
        else len({round(float(point.get("z", 0.0)), 3) for point in lidar_points})
    )
    return {
        "frame": {
            "timestamp": round(timestamp, 3),
            "frame_id": frame_id,
            "width": float(width),
            "height": float(height),
            "body": [round(bx, 3), round(by, 3), 0.0],
            "yaw_rad": round(yaw, 4),
        },
        "vision_projection": {
            "projection": "egocentric_2d",
            "objects": camera_objects,
            "source": "native_camera" if camera_native else "derived_scene",
            "native": camera_native,
            "llm_ready": True,
            "guidance": "Use object identity, range, bearing and confidence; do not infer unseen geometry.",
        },
        "lidar": {
            "projection": "sparse_3d_points",
            "frame": str((modalities.get("lidar") or {}).get("frame") or "body_world")
            if isinstance(modalities.get("lidar") or {}, dict) else "body_world",
            "points": lidar_points,
            "source": lidar_source if native_lidar else "derived_scene",
            "native": lidar_native,
            "returns": len(lidar_points),
            "vertical_layers": max(1, vertical_layers),
            "llm_ready": True,
        },
        "fusion": fusion,
        "quality": {
            "camera": "native" if camera_native else "derived",
            "lidar": lidar_quality,
            "authoritative_geometry": "world_model",
        },
    }


def build_body_perception_frame(
    body: Any,
    observation: Any,
    *,
    projections: Dict[str, Any] | None = None,
    motion: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build the synchronized ``body_perception_frame.v2`` contract.

    Sensor payloads stay attached to one timestamp and one metric frame. The
    VLM may interpret the camera image, but associations and geometry remain
    explicit evidence owned by the Body.
    """
    modalities = dict(getattr(observation, "modalities", {}) or {})
    projections = projections or sensor_projections(
        body, getattr(observation, "scene", []) or [], modalities=modalities,
    )
    camera = dict(modalities.get("camera") or {})
    lidar = dict(modalities.get("lidar") or {})
    observation_timestamp = float(
        getattr(observation, "timestamp", getattr(body, "timestamp", time.time()))
    )
    body_timestamp = float(getattr(body, "timestamp", observation_timestamp) or observation_timestamp)
    camera_timestamp = camera.get("timestamp", observation_timestamp)
    lidar_timestamp = lidar.get("timestamp", observation_timestamp)
    try:
        camera_timestamp = float(camera_timestamp)
    except (TypeError, ValueError):
        camera_timestamp = observation_timestamp
    try:
        lidar_timestamp = float(lidar_timestamp)
    except (TypeError, ValueError):
        lidar_timestamp = observation_timestamp
    timestamps = [observation_timestamp, body_timestamp, camera_timestamp, lidar_timestamp]
    sync_error = max(timestamps) - min(timestamps)
    motion = dict(motion or {})
    quality = dict(projections.get("quality") or {})
    fusion = dict(projections.get("fusion") or {})
    associations = list(fusion.get("associations") or [])
    association_confidence = [float(item.get("confidence", 0.0) or 0.0) for item in associations]
    image = camera.get("image_base64") or camera.get("image_url")
    lidar_points = list((projections.get("lidar") or {}).get("points") or [])
    camera_confidence = float(camera.get("confidence", 1.0 if image else 0.0) or 0.0)
    lidar_confidence = float(lidar.get("confidence", 1.0 if lidar_points else 0.0) or 0.0)
    return {
        "contract": "body_perception_frame.v2",
        "frame_id": str(
            modalities.get("frame_id")
            or (projections.get("frame") or {}).get("frame_id")
            or f"body-{int(observation_timestamp * 1000)}"
        ),
        "timestamp": observation_timestamp,
        "synchronization": {
            "policy": "single_observation_timestamp",
            "observation_timestamp": observation_timestamp,
            "body_timestamp": body_timestamp,
            "camera_timestamp": camera_timestamp,
            "lidar_timestamp": lidar_timestamp,
            "max_skew_s": round(sync_error, 6),
            "synchronized": sync_error <= 0.1,
        },
        "camera": {
            "image_base64": camera.get("image_base64"),
            "image_url": camera.get("image_url"),
            "mime_type": camera.get("mime_type", "image/jpeg"),
            "profile": camera.get("camera_profile") or (camera.get("calibration") or {}).get("profile"),
            "calibration": dict(camera.get("calibration") or {}),
            "projection": projections.get("vision_projection") or {},
            "quality": {
                "source": quality.get("camera", "unknown"),
                "confidence": round(max(0.0, min(1.0, camera_confidence)), 3),
                "image_present": bool(image),
            },
        },
        "lidar": {
            "points": lidar_points,
            "frame": (projections.get("lidar") or {}).get("frame") or lidar.get("frame", "body_world"),
            "calibration": dict(lidar.get("calibration") or {}),
            "projection": projections.get("lidar") or {},
            "quality": {
                "source": quality.get("lidar", "unknown"),
                "confidence": round(max(0.0, min(1.0, lidar_confidence)), 3),
                "returns": len(lidar_points),
            },
        },
        "body": {
            "pose": {
                "position_m": list(getattr(body, "position", [0.0, 0.0, 0.0]))[:3],
                "yaw_rad": float(getattr(body, "orientation", 0.0)),
                "coordinate_frame": str(getattr(body, "coordinate_frame", "local_map")),
                "position_source": str(getattr(body, "position_source", "unknown")),
                "accuracy_m": getattr(body, "position_accuracy_m", None),
            },
            "velocity": {
                "linear_mps": list(motion.get("linear_velocity_mps") or motion.get("velocity_mps") or [motion.get("speed", 0.0), 0.0, 0.0])[:3],
                "speed_mps": float(motion.get("speed", 0.0) or 0.0),
                "angular_speed_rad_s": float(motion.get("angular_speed", 0.0) or 0.0),
                "relative_speed_mps": float(motion.get("relative_speed", 0.0) or 0.0),
                "closing_speed_mps": float(motion.get("closing_speed", 0.0) or 0.0),
            },
        },
        "metric_frame": {
            "length_unit": "m",
            "display_unit": "cm",
            "coordinate_frame": str(getattr(body, "coordinate_frame", "local_map")),
            "meters_per_grid_unit": 1.0,
        },
        "associations": {
            "method": fusion.get("method", "unavailable"),
            "geometry_authoritative": fusion.get("geometry_authoritative", "lidar"),
            "items": associations,
            "matched": int(fusion.get("matched", 0) or 0),
            "unmatched_vision": list(fusion.get("unmatched_vision") or []),
            "unmatched_lidar_point_indices": list(fusion.get("unmatched_lidar_point_indices") or []),
            "average_confidence": round(sum(association_confidence) / len(association_confidence), 3) if association_confidence else 0.0,
        },
        "uncertainty": {
            "camera": round(1.0 - max(0.0, min(1.0, camera_confidence)), 3),
            "lidar": round(1.0 - max(0.0, min(1.0, lidar_confidence)), 3),
            "association": round(1.0 - (sum(association_confidence) / len(association_confidence)), 3) if association_confidence else 1.0,
            "synchronization": round(min(1.0, sync_error / 0.1), 3),
        },
        "quality": {
            "camera": quality.get("camera", "unknown"),
            "lidar": quality.get("lidar", "unknown"),
            "authoritative_geometry": quality.get("authoritative_geometry", "lidar"),
            "synchronized": sync_error <= 0.1,
        },
    }
