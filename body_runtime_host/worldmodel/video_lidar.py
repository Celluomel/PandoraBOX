"""Video replay with a synchronized monocular LiDAR proxy.

The proxy is deliberately labelled as estimated data.  A video contains no
range measurement by itself, but it can exercise the same Body perception
contract before a physical LiDAR is connected: frame timing, camera
calibration, metric pose, 3-D point transport and downstream fusion.
"""
from __future__ import annotations

import base64
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List

from .perception import build_body_perception_frame, sensor_projections

COMMON_VIDEO_EXTENSIONS = {
    ".mp4", ".m4v", ".mov", ".mkv", ".avi", ".webm", ".wmv", ".flv",
    ".mpeg", ".mpg", ".m2ts", ".mts", ".ts", ".3gp", ".ogv", ".gif",
}


def _capture_dimensions(width: int | float, height: int | float) -> tuple[int, int]:
    """Normalize selectable replay dimensions while protecting VLM latency."""
    try:
        normalized_width = int(width)
        normalized_height = int(height)
    except (TypeError, ValueError) as exc:
        raise ValueError("capture width and height must be integers") from exc
    if normalized_width < 640 or normalized_height < 480:
        raise ValueError("capture size cannot be smaller than 640x480")
    if normalized_width > 3840 or normalized_height > 2160:
        raise ValueError("capture size cannot exceed 3840x2160")
    return normalized_width, normalized_height


def _ffmpeg_path() -> str:
    configured = str(os.environ.get("BODY_FFMPEG") or "").strip()
    bundled = ""
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        bundled = str(get_ffmpeg_exe() or "")
    except Exception:
        pass
    candidates = [configured, bundled, shutil.which("ffmpeg") or "", r"C:\Program Files\SteelSeries\GG\apps\moments\ffmpeg.exe"]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise RuntimeError("ffmpeg is required for video replay; set BODY_FFMPEG to ffmpeg.exe")


def _image_dimensions(payload: bytes) -> tuple[int, int]:
    if len(payload) >= 24 and payload[:8] == b"\x89PNG\r\n\x1a\n":
        return int.from_bytes(payload[16:20], "big"), int.from_bytes(payload[20:24], "big")
    # JPEG SOF markers carry the height and width. This parser avoids adding
    # Pillow just to validate replay metadata.
    if payload[:2] == b"\xff\xd8":
        offset = 2
        while offset + 9 < len(payload):
            if payload[offset] != 0xFF:
                offset += 1
                continue
            marker = payload[offset + 1]
            offset += 2
            if marker in {0xD8, 0xD9}:
                continue
            if offset + 2 > len(payload):
                break
            segment_length = int.from_bytes(payload[offset:offset + 2], "big")
            if marker in set(range(0xC0, 0xC4)) | set(range(0xC5, 0xC8)) | set(range(0xC9, 0xCC)) | set(range(0xCD, 0xD0)):
                if offset + 7 <= len(payload):
                    return int.from_bytes(payload[offset + 5:offset + 7], "big"), int.from_bytes(payload[offset + 3:offset + 5], "big")
                break
            offset += max(2, segment_length)
    raise ValueError("ffmpeg did not return a supported image")


def _png_dimensions(payload: bytes) -> tuple[int, int]:
    """Backward-compatible name used by older tests and integrations."""
    return _image_dimensions(payload)


def _extract_png_frames(path: Path, *, sample_fps: float, max_frames: int,
                        capture_width: int = 640, capture_height: int = 480) -> List[tuple[int, bytes]]:
    """Extract frames from any ffmpeg-readable container.

    The extension is only metadata. ffmpeg probes the file contents, so this
    also supports extensionless captures and future containers/codecs without
    a Python-side allow-list becoming a false rejection.
    """
    if not path.exists():
        raise FileNotFoundError(str(path))
    if not path.is_file():
        raise ValueError(f"video replay input is not a file: {path}")
    capture_width, capture_height = _capture_dimensions(capture_width, capture_height)
    with tempfile.TemporaryDirectory(prefix="body-video-replay-") as temp:
        pattern = str(Path(temp) / "frame-%06d.jpg")
        command = [
            _ffmpeg_path(), "-hide_banner", "-loglevel", "error", "-i", str(path),
            "-map", "0:v:0", "-an",
            "-vf", (
                f"fps={max(0.1, float(sample_fps))},"
                f"scale={capture_width}:{capture_height}:force_original_aspect_ratio=decrease,"
                f"pad={capture_width}:{capture_height}:(ow-iw)/2:(oh-ih)/2:color=black"
            ),
            "-frames:v", str(max_frames),
            "-vsync", "vfr", "-q:v", "4", pattern,
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=180)
        if completed.returncode:
            error = (completed.stderr or "ffmpeg failed").strip()[-1000:]
            if "decoder found for: hevc" in error.lower() or "hevc" in error.lower() and "decoder" in error.lower():
                raise RuntimeError(
                    "The supplied video is HEVC/H.265, but the configured ffmpeg has no HEVC decoder. "
                    "Install an ffmpeg build with HEVC support or convert the video to H.264, then retry. "
                    f"Original decoder error: {error}"
                )
            raise RuntimeError(error)
        frames: List[tuple[int, bytes]] = []
        for frame_path in sorted(Path(temp).glob("frame-*.jpg")):
            index = int(frame_path.stem.rsplit("-", 1)[-1]) - 1
            frames.append((max(0, index), frame_path.read_bytes()))
        if not frames:
            raise RuntimeError("video contained no decodable frames")
        return frames


def estimate_lidar_from_frame(
    image: bytes,
    *,
    width: int,
    height: int,
    horizontal_fov_deg: float = 100.0,
    camera_height_m: float = 0.24,
    vertical_fov_deg: float = 62.0,
    columns: int = 32,
    rows: int = 5,
) -> List[Dict[str, Any]]:
    """Create a deterministic, low-density range proxy from image geometry.

    It uses the image's pixel bytes only as a stable intensity signal and uses
    the calibrated floor projection for range. It is not depth perception and
    must never be reported as native LiDAR.
    """
    if not image or width <= 0 or height <= 0:
        return []
    # PNG decoding is intentionally avoided here. The byte sampling provides
    # deterministic return intensity while the calibrated projection supplies
    # the metric ray geometry.
    points: List[Dict[str, Any]] = []
    horizon = max(0.18, min(0.78, 0.52 - math.radians(-4.0) / math.radians(vertical_fov_deg)))
    fov = math.radians(max(20.0, min(170.0, horizontal_fov_deg)))
    for row in range(rows):
        normalized_y = horizon + (row + 1) / (rows + 1) * (1.0 - horizon) * 0.92
        elevation = (0.5 - normalized_y) * math.radians(vertical_fov_deg)
        ground_drop = max(0.035, -math.tan(elevation))
        range_m = min(18.0, max(0.35, camera_height_m / ground_drop))
        z = max(0.0, camera_height_m + math.tan(elevation) * range_m)
        for column in range(columns):
            normalized_x = (column + 0.5) / columns
            bearing = (normalized_x - 0.5) * fov
            x = range_m * math.cos(bearing)
            y = range_m * math.sin(bearing)
            sample_index = (int(normalized_y * height) * max(1, width) + int(normalized_x * width)) % len(image)
            intensity = round(0.25 + (image[sample_index] / 255.0) * 0.65, 3)
            points.append({
                "x": round(x, 3), "y": round(y, 3), "z": round(z, 3),
                "range": round(math.sqrt(x * x + y * y + z * z), 3),
                "bearing_rad": round(bearing, 5),
                "intensity": intensity,
                "object_id": "video_return",
                "source": "video_lidar_proxy",
            })
    return points


def _frame_packet(image: bytes, index: int, sample_fps: float, *, camera_height_m: float,
                  horizontal_fov_deg: float, vertical_fov_deg: float,
                  capture_width: int, capture_height: int) -> Dict[str, Any]:
    width, height = _image_dimensions(image)
    timestamp = float(index) / max(0.1, float(sample_fps))
    lidar_points = estimate_lidar_from_frame(
        image, width=width, height=height, camera_height_m=camera_height_m,
        horizontal_fov_deg=horizontal_fov_deg, vertical_fov_deg=vertical_fov_deg,
    )
    camera = {
        "image_base64": base64.b64encode(image).decode("ascii"),
        "mime_type": "image/jpeg", "timestamp": timestamp,
        "source": "video_replay", "camera_profile": "low_body_front",
        "calibration": {
            "profile": "video_replay_low_body_front", "height_m": camera_height_m,
            "image_width": width, "image_height": height,
            "horizontal_fov_deg": horizontal_fov_deg, "vertical_fov_deg": vertical_fov_deg,
            "elevation_deg": -4.0, "floor_biased_view": True,
        },
        "confidence": 0.7,
    }
    lidar = {
        "points": lidar_points, "timestamp": timestamp, "source": "video_lidar_proxy",
        "frame": "body_sensor", "confidence": 0.18,
        "calibration": {"method": "monocular_floor_projection", "estimated": True},
    }
    body = SimpleNamespace(
        position=[0.0, 0.0, 0.0], orientation=0.0,
        timestamp=timestamp, coordinate_frame="video_replay_local",
        position_source="video_replay_origin", position_accuracy_m=None,
    )
    observation = SimpleNamespace(timestamp=timestamp, scene=[], modalities={"camera": camera, "lidar": lidar})
    projections = sensor_projections(body, [], modalities=observation.modalities)
    frame = build_body_perception_frame(body, observation, projections=projections, motion={"speed": 0.0})
    frame["frame_id"] = f"video-replay-{index:06d}"
    frame["video"] = {"source": "video_replay", "frame_index": index, "sample_fps": sample_fps}
    return frame


def run_video_lidar_replay(
    video_path: str,
    *,
    sample_fps: float = 2.0,
    max_frames: int = 20,
    capture_width: int = 640,
    capture_height: int = 480,
    output_path: str | None = None,
    camera_height_m: float = 0.24,
    horizontal_fov_deg: float = 100.0,
    vertical_fov_deg: float = 62.0,
) -> Dict[str, Any]:
    """Build synchronized Body frames and optionally persist them as JSONL."""
    sample_fps = max(0.1, min(30.0, float(sample_fps)))
    max_frames = max(1, min(250, int(max_frames)))
    capture_width, capture_height = _capture_dimensions(capture_width, capture_height)
    extracted = _extract_png_frames(
        Path(video_path), sample_fps=sample_fps, max_frames=max_frames,
        capture_width=capture_width, capture_height=capture_height,
    )
    frames = [
        _frame_packet(image, index, sample_fps, camera_height_m=camera_height_m,
                      horizontal_fov_deg=horizontal_fov_deg, vertical_fov_deg=vertical_fov_deg,
                      capture_width=capture_width, capture_height=capture_height)
        for index, image in extracted
    ]
    if output_path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as handle:
            for frame in frames:
                handle.write(json.dumps(frame, ensure_ascii=False, separators=(",", ":")) + "\n")
    synchronized = sum(1 for frame in frames if frame["quality"].get("synchronized"))
    return {
        "status": "completed", "contract": "body_perception_frame.v2",
        "source": "video_replay", "video_path": str(video_path),
        "frames": len(frames), "sample_fps": sample_fps,
        "capture_size": {"width": capture_width, "height": capture_height, "minimum": "640x480"},
        "camera": {"source": "video_replay", "resolution": [len(frames) and _image_dimensions(extracted[0][1])[0], len(frames) and _image_dimensions(extracted[0][1])[1]]},
        "lidar": {"source": "video_lidar_proxy", "returns_per_frame": len(frames[0]["lidar"]["points"]) if frames else 0},
        "synchronized_frames": synchronized,
        "native_lidar": False,
        "warning": "LiDAR is estimated from monocular video; replace with a timestamp-matched native scan for physical validation.",
        "output_path": str(output_path) if output_path else None,
        "first_frame": frames[0] if frames else None,
        "last_frame": frames[-1] if frames else None,
    }
