"""Small, dependency-light decoders for Body-owned UART sensors.

These functions deliberately decode bytes only. Serial-port ownership, device
discovery and polling are handled by the runtime adapters, not by parsers.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import time
from typing import Any


LD2450_HEADER = b"\xaa\xff\x03\x00"
LD2450_TAIL = b"\x55\xcc"
LD2450_FRAME_SIZE = 30


@dataclass
class GnssFix:
    timestamp: float
    latitude_deg: float
    longitude_deg: float
    altitude_m: float | None
    fix_quality: int
    satellites: int | None = None
    hdop: float | None = None
    speed_mps: float | None = None
    course_deg: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _ld2450_signed_magnitude(raw: int) -> int:
    magnitude = raw & 0x7FFF
    return magnitude if raw & 0x8000 else -magnitude


def parse_ld2450_frame(frame: bytes, *, timestamp: float | None = None) -> dict[str, Any]:
    """Decode one 30-byte LD2450 report into metric radar coordinates.

    LD2450 reports X lateral and Y forward in millimetres, and target velocity
    in centimetres/second. A zeroed target slot is an unused slot.
    """
    if len(frame) != LD2450_FRAME_SIZE or not frame.startswith(LD2450_HEADER) or not frame.endswith(LD2450_TAIL):
        raise ValueError("invalid LD2450 frame boundary or length")
    targets = []
    for index in range(3):
        offset = 4 + index * 8
        x_raw = int.from_bytes(frame[offset:offset + 2], "little")
        y_raw = int.from_bytes(frame[offset + 2:offset + 4], "little")
        speed_raw = int.from_bytes(frame[offset + 4:offset + 6], "little")
        gate_mm = int.from_bytes(frame[offset + 6:offset + 8], "little")
        if x_raw == y_raw == speed_raw == gate_mm == 0:
            continue
        targets.append({
            "target_id": f"ld2450-{index + 1}",
            "position_m": [
                _ld2450_signed_magnitude(x_raw) / 1000.0,
                _ld2450_signed_magnitude(y_raw) / 1000.0,
                0.0,
            ],
            "velocity_mps": [_ld2450_signed_magnitude(speed_raw) / 100.0, 0.0, 0.0],
            "distance_gate_m": gate_mm / 1000.0,
            "confidence": 1.0,
            "classification": "moving_target",
        })
    return {
        "timestamp": float(timestamp if timestamp is not None else time.time()),
        "frame": "radar",
        "source": "hlk_ld2450",
        "quality": 1.0,
        "targets": targets,
    }


def extract_ld2450_frames(buffer: bytearray) -> list[bytes]:
    """Extract complete reports in-place, retaining a partial trailing frame."""
    frames = []
    while True:
        start = buffer.find(LD2450_HEADER)
        if start < 0:
            keep = min(len(buffer), len(LD2450_HEADER) - 1)
            if keep:
                del buffer[:-keep]
            else:
                buffer.clear()
            return frames
        if start:
            del buffer[:start]
        if len(buffer) < LD2450_FRAME_SIZE:
            return frames
        if buffer[LD2450_FRAME_SIZE - 2:LD2450_FRAME_SIZE] != LD2450_TAIL:
            del buffer[0]
            continue
        frames.append(bytes(buffer[:LD2450_FRAME_SIZE]))
        del buffer[:LD2450_FRAME_SIZE]


def _nmea_coordinate(value: str, hemisphere: str) -> float | None:
    if not value or hemisphere not in {"N", "S", "E", "W"}:
        return None
    degrees_digits = 2 if hemisphere in {"N", "S"} else 3
    try:
        degrees = int(value[:degrees_digits])
        minutes = float(value[degrees_digits:])
    except (ValueError, TypeError):
        return None
    coordinate = degrees + minutes / 60.0
    return -coordinate if hemisphere in {"S", "W"} else coordinate


def parse_nmea_sentence(sentence: str, *, timestamp: float | None = None) -> GnssFix | None:
    """Parse checksum-verified GGA or RMC sentences into a GNSS fix."""
    line = str(sentence or "").strip()
    if not line.startswith("$") or "*" not in line:
        return None
    body, checksum_text = line[1:].rsplit("*", 1)
    checksum = 0
    for char in body:
        checksum ^= ord(char)
    try:
        if checksum != int(checksum_text[:2], 16):
            return None
    except ValueError:
        return None
    fields = body.split(",")
    sentence_type = fields[0][-3:]
    now = float(timestamp if timestamp is not None else time.time())
    if sentence_type == "GGA" and len(fields) >= 10:
        try:
            quality = int(fields[6] or 0)
            if quality <= 0:
                return None
            lat = _nmea_coordinate(fields[2], fields[3])
            lon = _nmea_coordinate(fields[4], fields[5])
            if lat is None or lon is None:
                return None
            return GnssFix(now, lat, lon, float(fields[9]) if fields[9] else None,
                           quality, int(fields[7]) if fields[7] else None,
                           float(fields[8]) if fields[8] else None)
        except (ValueError, IndexError):
            return None
    if sentence_type == "RMC" and len(fields) >= 9:
        try:
            if fields[2] != "A":
                return None
            lat = _nmea_coordinate(fields[3], fields[4])
            lon = _nmea_coordinate(fields[5], fields[6])
            if lat is None or lon is None:
                return None
            speed = float(fields[7]) * 0.514444 if fields[7] else None
            course = float(fields[8]) if fields[8] else None
            return GnssFix(now, lat, lon, None, 1, speed_mps=speed, course_deg=course)
        except (ValueError, IndexError):
            return None
    return None
