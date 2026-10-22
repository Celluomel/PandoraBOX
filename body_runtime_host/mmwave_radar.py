"""Vendor-neutral mmWave radar contract for the Body.

The Body consumes metric detections, not a proprietary product API.  A radar
adapter may be backed by a TI module, a VENTUNO gateway, a serial bridge, or a
simulator as long as it returns :class:`MmWaveFrame`.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
import struct
import threading
import time
import urllib.request
from typing import Any, Callable, Dict, Iterable, List, Optional

from .sensor_bridge_rpc import call_sensor_rpc


@dataclass
class MmWaveTarget:
    """One tracked radar target in the configured metric frame."""

    target_id: str
    position_m: List[float]
    velocity_mps: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    radial_speed_mps: Optional[float] = None
    rcs_db: Optional[float] = None
    confidence: float = 1.0
    classification: str = "unknown"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MmWaveFrame:
    """Normalized frame exchanged between radar adapters and the Body."""

    timestamp: float
    frame: str = "body"
    targets: List[MmWaveTarget] = field(default_factory=list)
    quality: float = 1.0
    source: str = "mmwave_radar"
    sequence: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["targets"] = [target.as_dict() for target in self.targets]
        return result


class MmWaveRadarSource:
    """Small adapter protocol implemented by every radar backend."""

    name = "mmwave_radar"

    def read(self) -> MmWaveFrame:  # pragma: no cover - interface contract
        raise NotImplementedError

    def status(self) -> Dict[str, Any]:
        return {"source": self.name, "available": True}


def frame_from_payload(payload: Dict[str, Any], source: str = "mmwave_radar") -> MmWaveFrame:
    """Normalize common gateway payload variants into the stable contract."""
    raw_targets = payload.get("targets") or payload.get("tracks") or payload.get("detections") or []
    targets: List[MmWaveTarget] = []
    for index, raw in enumerate(raw_targets):
        if not isinstance(raw, dict):
            continue
        position = raw.get("position_m") or raw.get("position") or [raw.get("x", 0), raw.get("y", 0), raw.get("z", 0)]
        velocity = raw.get("velocity_mps") or raw.get("velocity") or [raw.get("vx", 0), raw.get("vy", 0), raw.get("vz", 0)]
        try:
            position = [float(position[i]) for i in range(3)]
            velocity = [float(velocity[i]) for i in range(3)]
        except (IndexError, TypeError, ValueError):
            continue
        targets.append(MmWaveTarget(
            target_id=str(raw.get("target_id") or raw.get("id") or f"target-{index}"),
            position_m=position,
            velocity_mps=velocity,
            radial_speed_mps=(float(raw["radial_speed_mps"]) if raw.get("radial_speed_mps") is not None else None),
            rcs_db=(float(raw["rcs_db"]) if raw.get("rcs_db") is not None else None),
            confidence=max(0.0, min(1.0, float(raw.get("confidence", 1.0) or 0.0))),
            classification=str(raw.get("classification") or raw.get("class") or "unknown"),
        ))
    return MmWaveFrame(
        timestamp=float(payload.get("timestamp") or time.time()),
        frame=str(payload.get("frame") or payload.get("coordinate_frame") or "body"),
        targets=targets,
        quality=max(0.0, min(1.0, float(payload.get("quality", 1.0) or 0.0))),
        source=source,
        sequence=(int(payload["sequence"]) if payload.get("sequence") is not None else None),
        metadata=dict(payload.get("metadata") or {}),
    )


class HttpMmWaveRadarSource(MmWaveRadarSource):
    """Generic JSON gateway adapter; no Aqara assumptions are made."""

    def __init__(self, url: str, token: str = "", timeout: float = 3.0):
        self.url = str(url or "").rstrip("/")
        self.token = str(token or "")
        self.timeout = float(timeout or 3.0)
        self.last_error = ""
        self.last_ok: Optional[float] = None
        self.last_frame: Optional[MmWaveFrame] = None

    def read(self) -> MmWaveFrame:
        request = urllib.request.Request(f"{self.url}/radar", headers={"Accept": "application/json"})
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("mmWave gateway returned a non-object payload")
            self.last_frame = frame_from_payload(payload, source=self.name)
            self.last_ok = time.time()
            self.last_error = ""
            return self.last_frame
        except Exception as exc:
            self.last_error = str(exc)
            raise

    def status(self) -> Dict[str, Any]:
        return {
            "source": self.name,
            "url": self.url,
            "last_ok_age_s": round(time.time() - self.last_ok, 1) if self.last_ok else None,
            "last_error": self.last_error,
            "targets": len(self.last_frame.targets) if self.last_frame else 0,
        }


def parse_ld2450_frame(frame_data: bytes, timestamp: Optional[float] = None,
                       sequence: Optional[int] = None) -> MmWaveFrame:
    """Decode one 30-byte HLK-LD2450 reporting frame into metric targets."""
    if len(frame_data) != 30 or frame_data[:4] != b"\xaa\xff\x03\x00" or frame_data[-2:] != b"\x55\xcc":
        raise ValueError("invalid LD2450 reporting frame")

    targets: List[MmWaveTarget] = []
    for slot in range(3):
        offset = 4 + slot * 8
        raw_x, raw_y, raw_speed, distance_gate_mm = struct.unpack_from("<HHHH", frame_data, offset)
        if not (raw_x or raw_y or raw_speed or distance_gate_mm):
            continue

        def signed_magnitude(value: int, scale: float) -> float:
            magnitude = value & 0x7fff
            return (magnitude if value & 0x8000 else -magnitude) / scale

        x_m = signed_magnitude(raw_x, 1000.0)
        y_m = signed_magnitude(raw_y, 1000.0)
        speed_mps = signed_magnitude(raw_speed, 100.0)
        targets.append(MmWaveTarget(
            target_id=f"ld2450-{slot + 1}",
            position_m=[x_m, y_m, 0.0],
            radial_speed_mps=speed_mps,
            confidence=1.0,
            classification="moving_target" if abs(speed_mps) >= 0.05 else "target",
        ))

    return MmWaveFrame(
        timestamp=float(timestamp or time.time()),
        frame="body",
        targets=targets,
        source="hlk_ld2450",
        sequence=sequence,
        metadata={"protocol": "ld2450_uart_v1", "distance_gate_mm": [
            struct.unpack_from("<H", frame_data, 10 + slot * 8)[0] for slot in range(3)
        ]},
    )


class LD2450SerialSource(MmWaveRadarSource):
    """Persistent UART reader for the HLK-LD2450 target-reporting protocol."""

    name = "hlk_ld2450"

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 256000,
                 timeout: float = 0.35, serial_factory=None):
        self.port = str(port or "/dev/ttyUSB0")
        self.baudrate = int(baudrate or 256000)
        self.timeout = max(0.05, float(timeout or 0.35))
        self._serial_factory = serial_factory
        self._serial = None
        self._buffer = bytearray()
        self._sequence = 0
        self.last_error = ""
        self.last_ok: Optional[float] = None
        self.last_frame: Optional[MmWaveFrame] = None

    def _open(self):
        if self._serial is None:
            factory = self._serial_factory
            if factory is None:
                import serial
                factory = serial.Serial
            self._serial = factory(self.port, self.baudrate, timeout=0.05)
        return self._serial

    def read(self) -> MmWaveFrame:
        deadline = time.monotonic() + self.timeout
        try:
            port = self._open()
            while time.monotonic() < deadline:
                chunk = port.read(max(1, min(int(getattr(port, "in_waiting", 0) or 1), 256)))
                if chunk:
                    self._buffer.extend(chunk)
                while True:
                    start = self._buffer.find(b"\xaa\xff\x03\x00")
                    if start < 0:
                        if len(self._buffer) > 3:
                            del self._buffer[:-3]
                        break
                    if start:
                        del self._buffer[:start]
                    if len(self._buffer) < 30:
                        break
                    candidate = bytes(self._buffer[:30])
                    if candidate[-2:] != b"\x55\xcc":
                        del self._buffer[0]
                        continue
                    del self._buffer[:30]
                    self._sequence += 1
                    self.last_frame = parse_ld2450_frame(candidate, sequence=self._sequence)
                    self.last_ok = time.time()
                    self.last_error = ""
                    return self.last_frame
            raise TimeoutError("no complete LD2450 frame received before timeout")
        except Exception as exc:
            self.last_error = str(exc)
            raise

    def close(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    def status(self) -> Dict[str, Any]:
        return {
            "source": self.name,
            "port": self.port,
            "baudrate": self.baudrate,
            "last_ok_age_s": round(time.time() - self.last_ok, 1) if self.last_ok else None,
            "last_error": self.last_error,
            "targets": len(self.last_frame.targets) if self.last_frame else 0,
        }


class VentunoBridgeMmWaveSource(MmWaveRadarSource):
    """Read the latest LD2450 frame from the Ventuno STM32 over local RPC."""

    name = "hlk_ld2450_ventuno_bridge"

    def __init__(self, bridge_factory=None, method: str = "body_ld2450_read"):
        self._bridge_factory = bridge_factory
        self._bridge = None
        self.method = str(method or "body_ld2450_read")
        self.last_error = ""
        self.last_ok: Optional[float] = None
        self.last_frame: Optional[MmWaveFrame] = None
        self._read_lock = threading.Lock()

    def _client(self):
        if self._bridge is None:
            factory = self._bridge_factory
            if factory is None:
                from arduino.router_bridge import Bridge
                factory = Bridge
            self._bridge = factory()
            if not self._bridge.connect(timeout=1.0):
                raise ConnectionError("Arduino Router Bridge is not available locally")
        return self._bridge

    def read(self) -> MmWaveFrame:
        with self._read_lock:
            return self._read_locked()

    def _read_locked(self) -> MmWaveFrame:
        try:
            bridge = self._client()
            request_started = time.time()
            payload = call_sensor_rpc(bridge, self.method, timeout=0.5)
            request_finished = time.time()
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            if isinstance(payload, str):
                payload = json.loads(payload)
            if not isinstance(payload, dict):
                raise ValueError("Ventuno Bridge returned an invalid LD2450 payload")
            if not payload.get("available", True):
                raise TimeoutError(str(payload.get("error") or "No LD2450 frame received yet"))
            self.last_frame = frame_from_payload(payload, source=self.name)
            try:
                sensor_timestamp = float(payload.get("timestamp"))
            except (TypeError, ValueError):
                sensor_timestamp = 0.0
            if not math.isfinite(sensor_timestamp) or sensor_timestamp <= 0:
                round_trip = max(0.0, request_finished - request_started)
                self.last_frame.timestamp = (request_started + request_finished) / 2.0
                self.last_frame.metadata.update({
                    "timestamp_source": "bridge_rpc_midpoint",
                    "rpc_round_trip_s": round(round_trip, 4),
                })
            self.last_ok = time.time()
            self.last_error = ""
            return self.last_frame
        except Exception as exc:
            self.last_error = str(exc)
            self._bridge = None
            raise

    def status(self) -> Dict[str, Any]:
        age = time.time() - self.last_ok if self.last_ok else None
        return {
            "source": self.name,
            "transport": "local_arduino_router_rpc",
            "method": self.method,
            "available": bool(self.last_frame and not self.last_error and age is not None and age <= 1.0),
            "last_ok_age_s": round(age, 1) if age is not None else None,
            "last_error": self.last_error,
            "targets": len(self.last_frame.targets) if self.last_frame else 0,
            "sequence": self.last_frame.sequence if self.last_frame else None,
        }


class MmWaveAugmentedSource:
    """Add an independent radar feed to a primary Body source."""

    def __init__(self, source, radar: MmWaveRadarSource):
        self.source = source
        self.radar = radar
        self.name = getattr(source, "name", "body")
        self.simulated = bool(getattr(source, "simulated", False))

    def __getattr__(self, name):
        return getattr(self.source, name)

    def observe(self):
        observation = self.source.observe()
        try:
            observation.modalities["mmwave_radar"] = {
                **self.radar.read().as_dict(), "simulated": False,
            }
        except Exception as exc:
            observation.modalities["mmwave_radar"] = {
                "timestamp": time.time(), "frame": "body", "targets": [],
                "source": getattr(self.radar, "name", "mmwave_radar"),
                "available": False, "error": str(exc),
            }
        return observation

    def status(self):
        base = self.source.status() if callable(getattr(self.source, "status", None)) else {}
        return {**(base if isinstance(base, dict) else {}), "mmwave_radar": self.radar.status()}


class SimulatedMmWaveRadarSource(MmWaveRadarSource):
    """Radar adapter for tests and the simulated Body scene."""

    def __init__(self, scene_provider: Callable[[], Iterable[Any]], body_provider: Callable[[], Any]):
        self.scene_provider = scene_provider
        self.body_provider = body_provider
        self.sequence = 0

    def read(self) -> MmWaveFrame:
        body = self.body_provider()
        targets: List[MmWaveTarget] = []
        bx, by = float(body.position[0]), float(body.position[1])
        for item in self.scene_provider():
            position = list(getattr(item, "position", [0, 0, 0]))
            vx = float(getattr(item, "props", {}).get("velocity_x", 0.0) or 0.0)
            vy = float(getattr(item, "props", {}).get("velocity_y", 0.0) or 0.0)
            distance = ((float(position[0]) - bx) ** 2 + (float(position[1]) - by) ** 2) ** 0.5
            confidence = max(0.35, min(0.99, 1.0 - distance / 30.0))
            targets.append(MmWaveTarget(
                target_id=str(getattr(item, "id", f"target-{len(targets)}")),
                position_m=[float(position[0]), float(position[1]), float(position[2] if len(position) > 2 else 0.0)],
                velocity_mps=[vx, vy, 0.0],
                confidence=confidence,
                classification=str(getattr(item, "kind", "unknown")),
            ))
        self.sequence += 1
        return MmWaveFrame(time.time(), frame="local_map", targets=targets, quality=0.9, source=self.name, sequence=self.sequence)
