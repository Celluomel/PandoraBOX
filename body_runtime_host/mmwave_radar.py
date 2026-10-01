"""Vendor-neutral mmWave radar contract for the Body.

The Body consumes metric detections, not a proprietary product API.  A radar
adapter may be backed by a TI module, a VENTUNO gateway, a serial bridge, or a
simulator as long as it returns :class:`MmWaveFrame`.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import time
import urllib.request
from typing import Any, Callable, Dict, Iterable, List, Optional


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
