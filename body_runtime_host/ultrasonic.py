"""Three HC-SR04 ranges acquired by the VENTUNO STM32 sensor bridge."""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

from .sensor_bridge_rpc import call_sensor_rpc


class VentunoBridgeUltrasonicSource:
    name = "hc_sr04_ventuno_bridge"
    method = "body_ultrasonic_read"
    stale_after_s = 0.6

    def __init__(self, bridge_factory=None):
        self._bridge_factory = bridge_factory
        self._bridge = None
        self.last_error = ""
        self.last_sample: Optional[Dict[str, Any]] = None
        self.last_ok: Optional[float] = None

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
            payload = call_sensor_rpc(self._client(), self.method, timeout=0.5)
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            if isinstance(payload, str):
                payload = json.loads(payload)
            if not isinstance(payload, dict) or not isinstance(payload.get("sensors"), list):
                raise ValueError("Ventuno Bridge returned an invalid HC-SR04 payload")

            now = time.time()
            device_now_ms = int(payload.get("timestamp_ms", 0) or 0) & 0xFFFFFFFF
            sensors = []
            for item in payload["sensors"]:
                if not isinstance(item, dict):
                    continue
                distance = item.get("distance_mm")
                distance = int(distance) if distance is not None else None
                age_ms = (device_now_ms - (int(item.get("timestamp_ms", 0) or 0) & 0xFFFFFFFF)) & 0xFFFFFFFF
                available = bool(item.get("available")) and distance is not None \
                    and 20 <= distance <= 4000 and age_ms <= self.stale_after_s * 1000
                sensors.append({
                    "id": str(item.get("id") or "unknown"),
                    "trigger_pin": str(item.get("trigger_pin") or ""),
                    "echo_pin": str(item.get("echo_pin") or ""),
                    "available": available,
                    "distance_mm": distance if available else None,
                    "distance_m": distance / 1000.0 if available else None,
                    "age_ms": age_ms if item.get("timestamp_ms") else None,
                    "sequence": int(item.get("sequence", 0) or 0),
                    "error": "" if available else str(item.get("error") or "stale_or_no_echo"),
                })
            expected = {"front_left", "front_right", "rear"}
            if {sensor["id"] for sensor in sensors} != expected:
                raise ValueError("Ventuno Bridge HC-SR04 payload must contain all three named channels")

            sample = {
                "timestamp": now,
                "source": self.name,
                "sensor": str(payload.get("sensor") or "hc_sr04_array"),
                "transport": "stm32_gpio_router_rpc",
                "sequence": int(payload.get("sequence", 0) or 0),
                "firmware_setup_stage": int(payload.get("setup_stage", 0) or 0),
                "firmware_loop_sequence": int(payload.get("loop_sequence", 0) or 0),
                "available": any(sensor["available"] for sensor in sensors),
                "simulated": False,
                "units": "m",
                "sensors": sensors,
            }
            self.last_sample = sample
            self.last_ok = now
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
            "bridge_available": os.path.exists("/run/arduino-router.sock") or self._bridge is not None,
            "available": bool(self.last_sample and age is not None and age <= 1.5
                               and self.last_sample.get("available")),
            "last_ok_age_s": round(age, 2) if age is not None else None,
            "last_error": self.last_error,
            "sample": self.last_sample,
        }


class UltrasonicAugmentedSource:
    """Add physical HC-SR04 channels without replacing existing observations."""

    def __init__(self, source, ultrasonic: VentunoBridgeUltrasonicSource):
        self.source = source
        self.ultrasonic = ultrasonic
        self.name = getattr(source, "name", "body")
        self.simulated = bool(getattr(source, "simulated", False))

    def __getattr__(self, name):
        return getattr(self.source, name)

    def observe(self):
        observation = self.source.observe()
        try:
            observation.modalities["ultrasonic"] = self.ultrasonic.read()
        except Exception as exc:
            observation.modalities["ultrasonic"] = {
                "timestamp": time.time(), "sensor": "hc_sr04_array",
                "available": False, "simulated": False, "error": str(exc)[:240],
            }
        return observation

    def status(self):
        base = self.source.status() if callable(getattr(self.source, "status", None)) else {}
        return {**(base if isinstance(base, dict) else {}),
                "ultrasonic": self.ultrasonic.status()}
