"""Physical IMU readings from the VENTUNO Q's on-board STM32 Bridge."""
from __future__ import annotations

import json
import math
import time
from collections import deque
import threading
from typing import Any, Callable, Dict, Optional

from .sensor_bridge_rpc import call_sensor_rpc


class VentunoBridgeImuSource:
    name = "modulino_movement_ventuno_bridge"

    def __init__(self, bridge_factory=None, method: str = "body_imu_read"):
        self._bridge_factory = bridge_factory
        self._bridge = None
        self.method = str(method or "body_imu_read")
        self.last_error = ""
        self.last_ok: Optional[float] = None
        self.last_sample: Optional[Dict[str, Any]] = None
        self._history = deque(maxlen=256)
        self._lock = threading.RLock()
        self._last_sequence: Optional[int] = None
        self._last_mcu_ms: Optional[int] = None
        self._unwrapped_mcu_ms = 0
        self._clock_offsets = deque(maxlen=64)

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
            received_at = time.time()
            raw_mcu_ms = payload.get("timestamp_ms")
            sequence = int(payload.get("sequence", 0) or 0)
            with self._lock:
                if raw_mcu_ms is not None:
                    raw_mcu_ms = int(raw_mcu_ms) & 0xFFFFFFFF
                    if self._last_mcu_ms is None:
                        self._unwrapped_mcu_ms = raw_mcu_ms
                    elif sequence != self._last_sequence:
                        delta_ms = (raw_mcu_ms - self._last_mcu_ms) & 0xFFFFFFFF
                        if delta_ms > 5000:
                            self._history.clear()
                            self._clock_offsets.clear()
                            self._unwrapped_mcu_ms = raw_mcu_ms
                        else:
                            self._unwrapped_mcu_ms += delta_ms
                    if sequence != self._last_sequence or not self._clock_offsets:
                        self._clock_offsets.append(received_at - self._unwrapped_mcu_ms / 1000.0)
                    self._last_mcu_ms = raw_mcu_ms
                    self._last_sequence = sequence
                    sample_at = min(self._clock_offsets) + self._unwrapped_mcu_ms / 1000.0
                else:
                    sample_at = received_at

            fused_attitude = all(
                key in payload and payload.get(key) is not None
                for key in ("roll_deg", "pitch_deg", "yaw_relative_deg")
            )
            attitude_valid = bool(payload.get("attitude_valid", False)) and fused_attitude
            sample = {
                "timestamp": sample_at,
                "received_at": received_at,
                "timestamp_uncertainty_s": round(max(0.0, received_at - sample_at), 4),
                "source": self.name,
                "device": "Arduino Modulino Movement / LSM6DSOX",
                "frame": str(payload.get("frame") or "imu_sensor"),
                "sequence": sequence,
                "acceleration_g": [ax, ay, az],
                "angular_velocity_dps": [gx, gy, gz],
                "roll_deg": float(payload["roll_deg"]) if fused_attitude else None,
                "pitch_deg": float(payload["pitch_deg"]) if fused_attitude else None,
                "yaw_relative_deg": float(payload["yaw_relative_deg"]) if fused_attitude else None,
                "attitude_valid": attitude_valid,
                "attitude_source": "gyro_accel_complementary" if attitude_valid else "fused_attitude_unavailable",
                "gravity_reference_valid": bool(payload.get("gravity_reference_valid", False)),
                "gyro_bias_ready": bool(payload.get("gyro_bias_ready", False)),
                "calibration_stable": bool(payload.get("calibration_stable", False)),
                "motion_state": str(payload.get("motion_state") or "unknown"),
                "acceleration_norm_g": payload.get("acceleration_norm_g"),
                "acceleration_jerk_gps": payload.get("acceleration_jerk_gps"),
                "yaw_rate_dps": float(payload.get("yaw_rate_dps", gz)),
                "units": {"acceleration": "g", "angular_velocity": "deg/s"},
                "simulated": False,
            }
            with self._lock:
                if not self._history or self._history[-1].get("sequence") != sequence:
                    self._history.append(sample)
                self.last_sample = sample
                self.last_ok = received_at
                self.last_error = ""
            return sample
        except Exception as exc:
            self.last_error = str(exc)[:240]
            raise

    def status(self) -> Dict[str, Any]:
        with self._lock:
            history = list(self._history)
            last_sample = dict(self.last_sample) if self.last_sample else None
            last_ok = self.last_ok
            last_error = self.last_error
        return {
            "source": self.name,
            "transport": "local_arduino_router_rpc",
            "method": self.method,
            "last_ok_age_s": round(time.time() - last_ok, 2) if last_ok else None,
            "last_error": last_error,
            "available": last_sample is not None and not last_error,
            "sample": last_sample,
            "history": history,
        }

    def attitude_at(self, timestamp: float, max_delta_s: float = 0.15) -> Optional[Dict[str, Any]]:
        """Return an interpolated fused attitude only when capture-time support is close."""
        target = float(timestamp)
        with self._lock:
            history = list(self._history)
        valid = [item for item in history if item.get("attitude_valid")
                 and math.isfinite(float(item.get("timestamp") or 0.0))]
        if not valid:
            return None
        before = max((item for item in valid if float(item["timestamp"]) <= target),
                     key=lambda item: float(item["timestamp"]), default=None)
        after = min((item for item in valid if float(item["timestamp"]) >= target),
                    key=lambda item: float(item["timestamp"]), default=None)
        if before and after:
            span = float(after["timestamp"]) - float(before["timestamp"])
            if span <= 0.25:
                fraction = 0.0 if span <= 1e-6 else (target - float(before["timestamp"])) / span
                result = {key: round(float(before[key]) + fraction * (float(after[key]) - float(before[key])), 4)
                          for key in ("roll_deg", "pitch_deg")}
                yaw_delta = (float(after["yaw_relative_deg"]) - float(before["yaw_relative_deg"]) + 540.0) % 360.0 - 180.0
                result["yaw_relative_deg"] = round(float(before["yaw_relative_deg"]) + fraction * yaw_delta, 4)
                result.update({"timestamp": target, "attitude_valid": True,
                               "source": self.name, "interpolated": True})
                return result
        nearest = min(valid, key=lambda item: abs(float(item["timestamp"]) - target))
        if abs(float(nearest["timestamp"]) - target) > max_delta_s:
            return None
        return {**nearest, "interpolated": False}


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
