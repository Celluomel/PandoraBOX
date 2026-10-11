"""Physical IMU readings from the VENTUNO Q's on-board STM32 Bridge."""
from __future__ import annotations

import json
import math
import time
from typing import Any, Callable, Dict, Optional


class VentunoBridgeImuSource:
    name = "modulino_movement_ventuno_bridge"

    def __init__(self, bridge_factory=None, method: str = "body_imu_read"):
        self._bridge_factory = bridge_factory
        self._bridge = None
        self.method = str(method or "body_imu_read")
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
                raise ValueError("Ventuno Bridge returned an invalid IMU payload")
            if not payload.get("available"):
                raise TimeoutError(str(payload.get("error") or "Modulino Movement has no fresh sample"))
            acceleration = payload.get("acceleration_g")
            angular_velocity = payload.get("angular_velocity_dps")
            if not (isinstance(acceleration, list) and len(acceleration) == 3
                    and isinstance(angular_velocity, list) and len(angular_velocity) == 3):
                raise ValueError("IMU payload is missing three-axis acceleration or angular velocity")
            ax, ay, az = (float(v) for v in acceleration)
            gx, gy, gz = (float(v) for v in angular_velocity)
            acceleration_norm = math.sqrt(ax * ax + ay * ay + az * az)
            # Gravity gives a useful static tilt estimate, but is not a valid
            # attitude reference while the robot is accelerating strongly.
            gravity_valid = 0.75 <= acceleration_norm <= 1.25
            roll = math.degrees(math.atan2(ay, az)) if gravity_valid else None
            pitch = math.degrees(math.atan2(-ax, math.hypot(ay, az))) if gravity_valid else None
            sample = {
                "timestamp": time.time(),
                "source": self.name,
                "device": "Arduino Modulino Movement / LSM6DSOX",
                "frame": str(payload.get("frame") or "imu_sensor"),
                "sequence": int(payload.get("sequence", 0) or 0),
                "acceleration_g": [ax, ay, az],
                "angular_velocity_dps": [gx, gy, gz],
                "roll_deg": roll,
                "pitch_deg": pitch,
                "attitude_valid": gravity_valid,
                "attitude_source": "accelerometer_gravity" if gravity_valid else "invalid_during_linear_acceleration",
                "yaw_rate_dps": gz,
                "units": {"acceleration": "g", "angular_velocity": "deg/s"},
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
        return {
            "source": self.name,
            "transport": "local_arduino_router_rpc",
            "method": self.method,
            "last_ok_age_s": round(time.time() - self.last_ok, 2) if self.last_ok else None,
            "last_error": self.last_error,
            "available": self.last_sample is not None and not self.last_error,
            "sample": self.last_sample,
        }


class ImuAugmentedSource:
    """Attach measured IMU samples to observations without replacing the robot source."""

    def __init__(self, source, imu: VentunoBridgeImuSource):
        self.source = source
        self.imu = imu
        self.name = getattr(source, "name", "body")
        self.simulated = bool(getattr(source, "simulated", False))

    def __getattr__(self, name):
        return getattr(self.source, name)

    def observe(self):
        observation = self.source.observe()
        try:
            observation.modalities["imu"] = self.imu.read()
        except Exception as exc:
            observation.modalities["imu"] = {
                "timestamp": time.time(), "source": self.imu.name,
                "device": "Arduino Modulino Movement / LSM6DSOX",
                "available": False, "simulated": False, "error": str(exc)[:240],
            }
        return observation

    def status(self):
        base = self.source.status() if callable(getattr(self.source, "status", None)) else {}
        return {**(base if isinstance(base, dict) else {}), "imu": self.imu.status()}
