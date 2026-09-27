"""Dependency-free RGB camera for the simulated Body.

This is intentionally a sensor image, not a debug map: objects are projected
into the Body's forward camera frame, distant objects are drawn first, and the
image carries only pixels plus camera metadata. The world model still keeps
the exact scene separately for safety and evaluation.
"""
from __future__ import annotations

import base64
import math
import struct
import zlib
import time
from typing import Any, Dict, Iterable, List


def _png(width: int, height: int, pixels: bytearray) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    rows = b"".join(b"\x00" + bytes(pixels[y * width * 3:(y + 1) * width * 3]) for y in range(height))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b"")


def _png_gray(width: int, height: int, pixels: bytearray) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    rows = b"".join(b"\x00" + bytes(pixels[y * width:(y + 1) * width]) for y in range(height))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b"")


def _fill_rect(pixels: bytearray, width: int, height: int, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
    x0, x1 = max(0, min(x0, x1)), min(width - 1, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(height - 1, max(y0, y1))
    row = bytes(color) * (x1 - x0 + 1)
    for y in range(y0, y1 + 1):
        index = (y * width + x0) * 3
        pixels[index:index + len(row)] = row


def _fill_polygon(pixels: bytearray, width: int, height: int,
                  points: list[tuple[int, int]], color: tuple[int, int, int]) -> None:
    """Small scanline polygon fill used to keep the virtual camera dependency-free."""
    if len(points) < 3:
        return
    min_y = max(0, min(y for _, y in points))
    max_y = min(height - 1, max(y for _, y in points))
    for y in range(min_y, max_y + 1):
        intersections = []
        for index, (x0, y0) in enumerate(points):
            x1, y1 = points[(index + 1) % len(points)]
            if (y0 <= y < y1) or (y1 <= y < y0):
                intersections.append(int(x0 + (y - y0) * (x1 - x0) / (y1 - y0)))
        intersections.sort()
        for start in range(0, len(intersections) - 1, 2):
            _fill_rect(pixels, width, height, intersections[start], y,
                       intersections[start + 1], y, color)


def _fill_ellipse(pixels: bytearray, width: int, height: int,
                  cx: int, cy: int, rx: int, ry: int, color: tuple[int, int, int]) -> None:
    """Draw a filled ellipse for contact shadows and rounded object silhouettes."""
    if rx <= 0 or ry <= 0:
        return
    for y in range(max(0, cy - ry), min(height, cy + ry + 1)):
        normalized = (y - cy) / ry
        half_width = int(rx * math.sqrt(max(0.0, 1.0 - normalized * normalized)))
        _fill_rect(pixels, width, height, cx - half_width, y, cx + half_width, y, color)


def render_camera(body: Any, objects: Iterable[Any], *, width: int = 320, height: int = 240,
                  fov_deg: float = 100.0, frame_id: str = "",
                  profile: str = "low_body_front") -> Dict[str, Any]:
    """Return a JPEG-compatible API shape containing a dependency-free PNG."""
    started = time.perf_counter()
    pixels = bytearray([12, 21, 28] * (width * height))
    depth = bytearray([255] * (width * height))
    # Sky/ground bands and perspective grid make depth visible to a vision model.
    for y in range(height // 2, height):
        shade = int(27 + 20 * (y - height / 2) / (height / 2))
        _fill_rect(pixels, width, height, 0, y, width - 1, y, (18, shade, 26))
    _fill_rect(pixels, width, height, 0, height // 2, width - 1, height // 2 + 1, (62, 92, 78))
    profiles = {
        "low_body_front": {"horizon": 0.50, "ground": 0.82, "height_m": 0.18, "elevation_deg": -8.0},
        "level_body_front": {"horizon": 0.45, "ground": 0.79, "height_m": 0.35, "elevation_deg": -2.0},
        "high_body_front": {"horizon": 0.39, "ground": 0.75, "height_m": 0.65, "elevation_deg": 5.0},
    }
    view = profiles.get(str(profile), profiles["low_body_front"])
    horizon = int(height * float(view["horizon"]))
    for depth_level in range(1, 8):
        y = int(horizon + (height - horizon) * (depth_level / 8.0) ** 0.72)
        _fill_rect(pixels, width, height, 0, y, width - 1, y, (27 + depth_level * 2, 58 + depth_level * 2, 39 + depth_level))
    for column in range(-6, 7):
        bottom_x = int(width / 2 + column * width / 7)
        _fill_polygon(pixels, width, height,
                      [(width // 2, horizon), (width // 2 + column * 3, horizon),
                       (bottom_x, height), (bottom_x + 2, height)], (29, 61, 43))
    bx, by = float(body.position[0]), float(body.position[1])
    yaw = float(body.orientation)
    half_fov = math.radians(fov_deg) / 2.0
    visible: List[tuple[float, Dict[str, Any], float]] = []
    for raw in objects:
        item = raw.as_dict() if hasattr(raw, "as_dict") else dict(raw)
        position = item.get("position") or [0, 0, 0]
        dx, dy = float(position[0]) - bx, float(position[1]) - by
        distance = math.hypot(dx, dy)
        bearing = math.atan2(dy, dx) - yaw
        bearing = math.atan2(math.sin(bearing), math.cos(bearing))
        if distance < 0.15 or abs(bearing) > half_fov:
            continue
        visible.append((distance, item, bearing))
    for distance, item, bearing in sorted(visible, reverse=True, key=lambda value: value[0]):
        x = int(width / 2 + (bearing / half_fov) * width * 0.46)
        size = max(5, int(min(74, 110 * float(item.get("size") or 0.5) / max(distance, 0.8))))
        ground = int(height * float(view["ground"]) - min(72, distance * 4.0))
        top = ground - size
        kind = str(item.get("kind") or "object")
        colors = {
            "table": (196, 171, 96), "chair": (105, 157, 196),
            "obstacle": (155, 109, 153), "mobile_obstacle": (210, 112, 177),
            "target": (221, 143, 98),
        }
        color = colors.get(kind, (130, 174, 150))
        depth_value = max(18, min(240, int(255.0 * min(distance, 12.0) / 12.0)))
        for depth_y in range(max(0, top), min(height, ground + 1)):
            depth_start = max(0, x - size // 2)
            depth_end = min(width - 1, x + size // 2)
            for depth_x in range(depth_start, depth_end + 1):
                depth[depth_y * width + depth_x] = min(depth[depth_y * width + depth_x], depth_value)
        # Contact shadow anchors the object to the floor and gives depth order.
        _fill_ellipse(pixels, width, height, x, ground + 2, max(3, size), max(2, size // 4), (10, 28, 19))
        highlight = tuple(min(255, c + 35) for c in color)
        dark = tuple(max(0, c - 42) for c in color)
        if kind == "table":
            top_y = max(horizon + 4, top + size // 3)
            _fill_polygon(pixels, width, height,
                          [(x - size, top_y), (x + size, top_y - 2),
                           (x + size + 3, top_y + max(3, size // 5)),
                           (x - size + 3, top_y + max(3, size // 5))], highlight)
            _fill_rect(pixels, width, height, x - size + 3, top_y + size // 5,
                       x - size // 3, ground, dark)
            _fill_rect(pixels, width, height, x + size // 3, top_y + size // 5,
                       x + size - 3, ground, dark)
        elif kind == "chair":
            seat_y = top + size // 2
            _fill_rect(pixels, width, height, x - size // 2, seat_y, x + size // 2, seat_y + max(3, size // 5), color)
            _fill_rect(pixels, width, height, x - size // 2, top, x - size // 4, seat_y, highlight)
            _fill_rect(pixels, width, height, x + size // 4, seat_y, x + size // 2, ground, dark)
        elif kind == "target":
            _fill_rect(pixels, width, height, x - size // 2, top + size // 5, x + size // 2, ground, color)
            _fill_ellipse(pixels, width, height, x, top + size // 5, max(3, size // 2), max(2, size // 5), highlight)
            _fill_ellipse(pixels, width, height, x + size // 2, top + size // 2, max(2, size // 5), max(3, size // 3), color)
        else:
            _fill_rect(pixels, width, height, x - size // 2, top, x + size // 2, ground, color)
            _fill_rect(pixels, width, height, x - size // 2, top, x - size // 4, ground, highlight)
            _fill_rect(pixels, width, height, x + size // 4, top, x + size // 2, ground, dark)
        # A bright top edge gives every silhouette a stable visual cue.
        _fill_rect(pixels, width, height, x - size // 2, top, x + size // 2, top + max(2, size // 10), highlight)
    # Camera reticle / body lower edge, useful orientation cues but not labels.
    _fill_rect(pixels, width, height, width // 2 - 2, height - 30, width // 2 + 2, height - 26, (185, 239, 202))
    encoded = base64.b64encode(_png(width, height, pixels)).decode("ascii")
    depth_encoded = base64.b64encode(_png_gray(width, height, depth)).decode("ascii")
    return {
        "image_base64": encoded,
        "mime_type": "image/png",
        "depth_base64": depth_encoded,
        "depth_mime_type": "image/png",
        "width": width,
        "height": height,
        "fov_deg": fov_deg,
        "frame": "body_camera",
        "frame_id": frame_id,
        "source": "virtual_camera",
        "render_style": "perspective_scene_v2",
        "camera_profile": str(profile),
        "depth_cues": ["horizon", "floor_grid", "contact_shadows", "object_shading"],
        "calibration": {
            "projection": "pinhole_egocentric",
            "profile": str(profile),
            "fov_deg": fov_deg,
            "near_m": 0.15,
            "far_m": 12.0,
            "depth_encoding": "8bit_normalized_range",
            # The simulated camera is mounted low on the Body. These cues
            # tell a VLM why nearby legs/chassis dominate the foreground and
            # why apparent object size is not reliable geometry.
            "mount": "low_body_front",
            "height_m": float(view["height_m"]),
            "elevation_deg": float(view["elevation_deg"]),
            "floor_biased_view": True,
            "foreground_occluders": ["body_chassis", "legs"],
        },
        "render_ms": round((time.perf_counter() - started) * 1000.0, 3),
    }


def render_lidar(body: Any, objects: Iterable[Any], *, rays: int = 96,
                 max_range: float = 12.0, frame_id: str = "") -> Dict[str, Any]:
    """Produce a dense, deterministic body-frame LiDAR scan."""
    bx, by = float(body.position[0]), float(body.position[1])
    yaw = float(body.orientation)
    returns: List[Dict[str, Any]] = []
    candidates = []
    for raw in objects:
        item = raw.as_dict() if hasattr(raw, "as_dict") else dict(raw)
        pos = item.get("position") or [0.0, 0.0, 0.0]
        dx, dy = float(pos[0]) - bx, float(pos[1]) - by
        distance = math.hypot(dx, dy)
        if distance <= max_range:
            bearing = math.atan2(dy, dx) - yaw
            bearing = math.atan2(math.sin(bearing), math.cos(bearing))
            candidates.append((distance, bearing, item))
    vertical_layers = (0.12, 0.34, 0.56, 0.78, 1.0)
    emitted = set()

    def emit(distance: float, bearing: float, item: Dict[str, Any], *, sample: str) -> None:
        object_id = str(item.get("id") or "return")
        for layer, z in enumerate(vertical_layers):
            key = (object_id, round(bearing, 4), layer, sample)
            if key in emitted:
                continue
            emitted.add(key)
            returns.append({
                "x": round(math.cos(bearing) * distance, 3),
                "y": round(math.sin(bearing) * distance, 3),
                "z": z,
                "range": round(distance, 3),
                "intensity": 0.88 if layer in (1, 2, 3) else 0.62,
                "object_id": object_id,
                "sample": sample,
            })

    # Preserve the ray scan for free-space structure and add deterministic
    # object-surface samples so small or distant objects are not missed.
    for index in range(max(16, int(rays))):
        bearing = -math.pi + (2.0 * math.pi * index / max(16, int(rays)))
        hit = None
        for distance, object_bearing, item in sorted(candidates, key=lambda value: value[0]):
            radius = max(0.12, float(item.get("size") or 0.5) * 0.55)
            angular_radius = min(0.35, math.asin(min(0.99, radius / max(distance, radius))))
            if abs(math.atan2(math.sin(object_bearing - bearing), math.cos(object_bearing - bearing))) <= angular_radius:
                hit = (distance, item)
                break
        if hit is None:
            continue
        distance, item = hit
        emit(distance, bearing, item, sample="ray")

    for distance, object_bearing, item in candidates:
        radius = max(0.12, float(item.get("size") or 0.5) * 0.55)
        angular_radius = min(0.35, math.asin(min(0.99, radius / max(distance, radius))))
        for fraction in (-0.8, -0.4, 0.0, 0.4, 0.8):
            bearing = object_bearing + angular_radius * fraction
            surface_distance = max(0.05, distance - radius * math.cos(angular_radius * fraction))
            emit(surface_distance, bearing, item, sample="surface")
    return {
        "points": returns,
        "frame": "body",
        "frame_id": frame_id,
        "source": "virtual_lidar",
        "rays": int(rays),
        "max_range": float(max_range),
        "vertical_layers": len(vertical_layers),
    }
