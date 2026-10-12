"""CQRobot VL53L1X range readings from the VENTUNO Q's local STM32 Bridge."""
from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional


class VentunoBridgeTofSource:
    name = "cqrobot_vl53l1x_ventuno_bridge"

    def __init__(self, bridge_factory=None, method: str = "body_tof_read"):
        self._bridge_factory = bridge_factory
        self._bridge = None
        self.method = str(method or "body_tof_read")
        self.last_error = ""
        self.last_ok: Optional[float] = None
        self.last_sample: Optional[Dict[str, Any]] = None

    def _client(self):
        if self._bridge is None:
            factory = self._bridge_factory
            if factory is None:
                from arduino.router_bridge import Bridge
                factory = Bridge
            self._bridge = factory()
            if not self._bridge.connect(timeout=1.0):
                self._bridge = None
                raise ConnectionError("Arduino Router Bridge is unavailable on this Body host")
        return self._bridge

    def read(self) -> Dict[str, Any]:
        try:
            payload = self._client().call(self.method, timeout=0.5)
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            if isinstance(payload, str):
                payload = json.loads(payload)
            if not isinstance(payload, dict):
                raise ValueError("Ventuno Bridge returned an invalid ToF payload")
            if not payload.get("available"):
                raise TimeoutError(str(payload.get("error") or "VL53L1X has no valid range"))
            distance_mm = int(payload.get("distance_mm", -1))
            if not 0 < distance_mm <= 4000:
                raise ValueError("VL53L1X range is outside the valid 1-4000 mm range")
            sample = {
                "timestamp": time.time(),
                "source": self.name,
                "sensor": str(payload.get("sensor") or "cqrobot_vl53l1x"),
                "frame": str(payload.get("frame") or "body_front"),
                "direction": str(payload.get("direction") or "front"),
                "sequence": int(payload.get("sequence", 0) or 0),
                "distance_mm": distance_mm,
                "distance_m": distance_mm / 1000.0,
                "min_range_m": 0.04,
                "max_range_m": 4.0,
                "units": "m",
                "available": True,
                "simulated": False,
            }
            self.last_sample = sample
            self.last_ok = sample["timestamp"]
            self.last_error = ""
            return sample
        except Exception as exc:
            self.last_error = str(exc)[:240]
            raise

    def status(self) -> Dict[str, Any]:
        age = time.time() - self.last_ok if self.last_ok else None
        return {
            "source": self.name,
            "transport": "local_arduino_router_rpc",
            "method": self.method,
            "available": bool(self.last_sample and not self.last_error and age is not None and age <= 1.5),
            "last_ok_age_s": round(age, 2) if age is not None else None,
            "last_error": self.last_error,
            "sample": self.last_sample,
        }


class TofAugmentedSource:
    """Add the forward single-beam range sensor without changing robot odometry."""

    def __init__(self, source, tof: VentunoBridgeTofSource):
        self.source = source
        self.tof = tof
        self.name = getattr(source, "name", "body")
        self.simulated = bool(getattr(source, "simulated", False))

    def __getattr__(self, name):
        return getattr(self.source, name)

    def observe(self):
        observation = self.source.observe()
        try:
            observation.modalities["tof"] = self.tof.read()
        except Exception as exc:
            observation.modalities["tof"] = {
                "timestamp": time.time(), "sensor": "cqrobot_vl53l1x",
                "frame": "body_front", "direction": "front",
                "available": False, "simulated": False, "error": str(exc)[:240],
            }
        return observation

    def status(self):
        base = self.source.status() if callable(getattr(self.source, "status", None)) else {}
        return {**(base if isinstance(base, dict) else {}), "tof": self.tof.status()}
