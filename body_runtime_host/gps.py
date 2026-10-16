"""GPS UART diagnostics and NMEA fix extraction from the VENTUNO bridge."""
from __future__ import annotations

import json
import time
from typing import Any

from .sensor_bridge_rpc import call_sensor_rpc


def _coordinate(raw: str, hemisphere: str) -> float:
    value = float(raw)
    degrees = int(value // 100)
    result = degrees + (value - degrees * 100) / 60.0
    if hemisphere in {"S", "W"}:
        result = -result
    if hemisphere not in {"N", "S", "E", "W"}:
        raise ValueError("invalid NMEA coordinate hemisphere")
    return result


class VentunoBridgeGpsSource:
    name = "ventuno_usart3_gps"
    method = "body_gps_read"

    def __init__(self, bridge_factory=None):
        self._bridge_factory = bridge_factory
        self._bridge = None
        self.last_error = ""
        self.last_sample: dict[str, Any] | None = None
        self.last_diagnostic: dict[str, Any] = {}
        self.last_ok: float | None = None

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

    def read(self) -> dict[str, Any]:
        try:
            payload = call_sensor_rpc(self._client(), self.method, timeout=0.5)
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            if isinstance(payload, str):
                payload = json.loads(payload)
            if not isinstance(payload, dict):
                raise ValueError("Ventuno Bridge returned an invalid GPS payload")
            self.last_diagnostic = payload
            if not payload.get("available"):
                reason = str(payload.get("error") or "GPS UART has no fresh NMEA sentence")
                raise TimeoutError(reason)

            sentence = str(payload.get("latest_gga") or "")
            fields = sentence.split(",")
            if not fields or not fields[0].endswith("GGA") or len(fields) < 10:
                raise TimeoutError("UART receives valid NMEA, but no GGA position sentence is available yet")
            quality = int(fields[6] or 0)
            sample = {
                "timestamp": time.time(),
                "source": self.name,
                "transport": str(payload.get("transport") or "Serial1_USART3_D0_D1"),
                "baudrate": int(payload.get("baudrate", 38400) or 38400),
                "connected": True,
                "fix": quality > 0,
                "fix_quality": quality,
                "satellites": int(fields[7] or 0),
                "hdop": float(fields[8]) if fields[8] else None,
                "latitude": _coordinate(fields[2], fields[3]) if fields[2] and fields[3] else None,
                "longitude": _coordinate(fields[4], fields[5]) if fields[4] and fields[5] else None,
                "altitude_m": float(fields[9]) if fields[9] else None,
                "sequence": int(payload.get("sequence", 0) or 0),
                "nmea_valid_sentences": int(payload.get("valid_sentences", 0) or 0),
                "nmea_checksum_errors": int(payload.get("checksum_errors", 0) or 0),
                "simulated": False,
            }
            self.last_sample = sample
            self.last_ok = sample["timestamp"]
            self.last_error = "" if sample["fix"] else "NMEA stream is valid but GPS has no position fix"
            return sample
        except Exception as exc:
            self.last_error = str(exc)[:240]
            raise

    def status(self) -> dict[str, Any]:
        age = time.time() - self.last_ok if self.last_ok else None
        return {
            "source": self.name,
            "transport": "Serial1 USART3 · D0/D1 via Ventuno STM32 Bridge",
            "method": self.method,
            "available": bool(self.last_sample and age is not None and age <= 3.0),
            "last_ok_age_s": round(age, 2) if age is not None else None,
            "last_error": self.last_error,
            "sample": self.last_sample,
            "diagnostic": self.last_diagnostic,
        }
