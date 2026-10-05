"""USB serial transport for the FNK0031's stock FNHR protocol."""
from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from typing import Any


LOG = logging.getLogger("lumina.body.fnk0031_usb")
_SERIAL_LOCK = threading.RLock()
_SERIAL_CONNECTIONS: dict[tuple[str, Any], Any] = {}

FRAME_START = 0x80
FRAME_END = 0x81
ORDER_ECHO_REQUEST = 0
ORDER_ECHO_RESPONSE = 1
ORDER_VOLTAGE_REQUEST = 10
ORDER_VOLTAGE_RESPONSE = 11
ORDER_STARTED = 21
ORDER_DONE = 23
SERIAL_STARTUP_SETTLE_SECONDS = 3.0

# Native Freenove commands. The FNHR firmware, not this host adapter, executes
# each gait and continues polling the RF24 remote and ESP8266 between actions.
MOTION_ORDERS = {
    "forward": 80,
    "backward": 82,
    "left": 84,
    "right": 86,
    "turn_left": 88,
    "turn_right": 90,
    "active_mode": 92,
    "sleep_mode": 94,  # Not an emergency-stop circuit.
    "switch_mode": 96,
}
ACTION_ALIASES = {
    "crawl_forward": "forward",
    "crawl_backward": "backward",
    "crawl_left": "left",
    "crawl_right": "right",
    "stop": "sleep_mode",
    "change_height": "change_body_height",
    "leg_move": "leg_move_to_relatively",
}
PARAMETERIZED_ORDERS = {
    "crawl": (110, ("x", "y", "angle")),
    "change_body_height": (112, ("height",)),
    "move_body": (114, ("x", "y", "z")),
    "rotate_body": (116, ("x", "y", "z")),
    "twist_body": (118, ("x_move", "y_move", "z_move", "x_rotate", "y_rotate", "z_rotate")),
}
UNSUPPORTED_ACTIONS = {"set_action_speed", "set_action_group"}


def available_serial_ports() -> list[dict[str, str]]:
    try:
        from serial.tools import list_ports
    except ImportError:
        return []
    return [
        {
            "device": str(port.device),
            "description": str(port.description or "Serial device"),
            "hwid": str(port.hwid or ""),
            "vid": f"{port.vid:04x}" if port.vid is not None else "",
            "pid": f"{port.pid:04x}" if port.pid is not None else "",
            "serial_number": str(port.serial_number or ""),
            "manufacturer": str(port.manufacturer or ""),
            "product": str(port.product or ""),
            "interface": str(port.interface or ""),
        }
        for port in list_ports.comports()
    ]


class FNK0031USBSource:
    """Speak the framed binary protocol used by stock Freenove FNHR firmware."""

    name = "fnk0031_usb"

    def __init__(self, port: str, timeout: float = 5.0, actuation_enabled: bool = False,
                 serial_factory=None):
        self.port = str(port or "").strip()
        self.timeout = max(0.2, float(timeout or 5.0))
        self.motion_timeout = max(30.0, self.timeout)
        self.actuation_enabled = bool(actuation_enabled)
        self._serial_factory = serial_factory
        self.last_error = ""
        self.last_ok: float | None = None
        self.supply_voltage: float | None = None

    @contextmanager
    def _open(self):
        factory = self._serial_factory
        if factory is None:
            try:
                import serial
            except ImportError as exc:
                raise RuntimeError("pyserial is missing; install body_requirements.txt") from exc
            factory = serial.Serial
        key = (self.port, factory if self._serial_factory is not None else 0)
        with _SERIAL_LOCK:
            connection = _SERIAL_CONNECTIONS.get(key)
            if connection is None or getattr(connection, "is_open", True) is False:
                if self._serial_factory is None:
                    connection = factory(None, 115200, timeout=0.1, write_timeout=self.timeout)
                    connection.port = self.port
                    connection.dtr = False
                    connection.open()
                    LOG.info(
                        "FNK0031 USB port %s opened; waiting %.1fs for controller startup",
                        self.port,
                        SERIAL_STARTUP_SETTLE_SECONDS,
                    )
                    time.sleep(SERIAL_STARTUP_SETTLE_SECONDS)
                else:
                    connection = factory(self.port, 115200, timeout=0.1, write_timeout=self.timeout)
                _SERIAL_CONNECTIONS[key] = connection
            try:
                yield connection
            except Exception:
                close = getattr(connection, "close", None)
                if callable(close):
                    close()
                _SERIAL_CONNECTIONS.pop(key, None)
                raise

    @staticmethod
    def _frame(order: int, payload: bytes = b"") -> bytes:
        if not 0 <= order < 0x80 or any(value >= 0x80 for value in payload):
            raise ValueError("FNHR order and payload bytes must be in range 0..127")
        return bytes((FRAME_START, order)) + payload + bytes((FRAME_END,))

    @staticmethod
    def _encode_coordinate(value: Any, name: str) -> int:
        if isinstance(value, bool):
            raise ValueError(f"FNHR parameter '{name}' must be numeric")
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"FNHR parameter '{name}' must be numeric") from exc
        if not (-64.0 <= numeric <= 63.0):
            raise ValueError(f"FNHR parameter '{name}' must be between -64 and 63")
        return int(round(numeric)) + 64

    @classmethod
    def _action_frame(cls, action_type: str, params: dict[str, Any]) -> tuple[bytes, bool]:
        """Return (native FNHR frame, whether FNHR sends orderStart first)."""
        action_type = ACTION_ALIASES.get(action_type, action_type)
        if action_type in MOTION_ORDERS:
            return cls._frame(MOTION_ORDERS[action_type]), True
        if action_type in PARAMETERIZED_ORDERS:
            order, names = PARAMETERIZED_ORDERS[action_type]
            payload = bytes(cls._encode_coordinate(params.get(name), name) for name in names)
            return cls._frame(order, payload), True
        if action_type == "leg_move_to_relatively":
            try:
                raw_leg = float(params.get("leg"))
            except (TypeError, ValueError) as exc:
                raise ValueError("FNHR parameter 'leg' must be an integer from 1 to 6") from exc
            if not raw_leg.is_integer():
                raise ValueError("FNHR parameter 'leg' must be an integer from 1 to 6")
            leg = int(raw_leg)
            if leg < 1 or leg > 6:
                raise ValueError("FNHR parameter 'leg' must be an integer from 1 to 6")
            payload = bytes((leg, *(
                cls._encode_coordinate(params.get(axis), axis) for axis in ("x", "y", "z")
            )))
            return cls._frame(30, payload), False
        if action_type in UNSUPPORTED_ACTIONS:
            raise NotImplementedError(
                f"'{action_type}' is not exposed by the stock FNHR serial protocol"
            )
        raise KeyError(action_type)

    @staticmethod
    def _read_frame(connection, deadline: float) -> bytes:
        frame = bytearray()
        in_frame = False
        while time.monotonic() < deadline:
            raw = connection.read(1)
            if not raw:
                continue
            value = raw[0]
            if not in_frame:
                if value == FRAME_START:
                    frame = bytearray((value,))
                    in_frame = True
                continue
            frame.append(value)
            if value == FRAME_END:
                return bytes(frame)
            if len(frame) > 32:
                frame.clear()
                in_frame = False
        raise TimeoutError("timed out waiting for a framed FNHR response")

    def _request(self, connection, order: int, expected_order: int,
                 payload: bytes = b"", timeout: float | None = None) -> bytes:
        if hasattr(connection, "reset_input_buffer"):
            connection.reset_input_buffer()
        connection.write(self._frame(order, payload))
        connection.flush()
        response = self._read_frame(connection, time.monotonic() + (timeout or self.timeout))
        if len(response) < 3 or response[1] != expected_order:
            raise RuntimeError(
                f"unexpected FNHR response {response.hex(' ')}; expected order {expected_order}"
            )
        return response

    def ping(self) -> bool:
        if not self.port:
            self.last_error = "USB serial port is not configured"
            return False
        try:
            with self._open() as connection:
                self._request(connection, ORDER_ECHO_REQUEST, ORDER_ECHO_RESPONSE)
            self.last_error = ""
            self.last_ok = time.time()
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def read_supply_voltage(self) -> float | None:
        if not self.port:
            self.last_error = "USB serial port is not configured"
            return None
        try:
            with self._open() as connection:
                response = self._request(connection, ORDER_VOLTAGE_REQUEST, ORDER_VOLTAGE_RESPONSE)
            if len(response) != 5:
                raise RuntimeError(f"invalid FNHR voltage response length: {len(response)}")
            self.supply_voltage = (response[2] * 128 + response[3]) / 100.0
            self.last_error = ""
            self.last_ok = time.time()
            return self.supply_voltage
        except Exception as exc:
            self.last_error = str(exc)
            return None

    def observe(self):
        from .worldmodel.types import Observation

        connected = self.ping()
        voltage = self.read_supply_voltage() if connected else None
        text = (
            "FNK0031 connected over USB using the stock FNHR framed protocol. "
            "RF remote and ESP8266 control remain owned by the FNHR firmware; "
            "pose and odometry are unavailable."
            if connected else f"FNK0031 FNHR USB unavailable: {self.last_error}"
        )
        value = {
            "protocol": "fnhr_framed_serial",
            "pose_available": False,
            "supply_voltage_v": voltage,
        }
        return Observation(
            subject="fnk0031",
            value=value,
            source=self.name,
            kind="hardware_status",
            confidence=1.0 if connected else 0.0,
            timestamp=time.time(),
            text=text,
            scene=[],
        )

    def body_state(self):
        from .worldmodel.types import BodyState

        return BodyState(
            posture={"pose_available": False},
            capabilities={"reach": 0.0, "speed": 0.0, "strength": 0.0, "gripper": 0.0, "legs": 6},
            position_source="unavailable",
        )

    def execute(self, action):
        from .worldmodel.types import Outcome

        return self.observe(), Outcome(kind="neutral", description="physical actuation requires an approved Body command")

    def execute_authorized(self, action):
        from .worldmodel.types import Outcome

        action_type = str(action.type).strip().lower()
        if action_type == "wait":
            return self.observe(), Outcome(kind="neutral", description="wait is a no-op; no FNHR command sent")
        if not self.actuation_enabled:
            return self.observe(), Outcome(kind="neutral", description="physical actuation disabled in Body configuration")
        try:
            packet, blocking = self._action_frame(action_type, dict(action.params or {}))
        except NotImplementedError as exc:
            return self.observe(), Outcome(
                kind="failure", reward=-0.1,
                description=str(exc),
            )
        except (KeyError, ValueError) as exc:
            return self.observe(), Outcome(kind="failure", reward=-0.1, description=str(exc))
        try:
            with self._open() as connection:
                if hasattr(connection, "reset_input_buffer"):
                    connection.reset_input_buffer()
                connection.write(packet)
                connection.flush()
                deadline = time.monotonic() + self.motion_timeout
                first = self._read_frame(connection, deadline)
                if blocking and (len(first) < 3 or first[1] != ORDER_STARTED):
                    raise RuntimeError(f"FNHR did not acknowledge action start: {first.hex(' ')}")
                done = self._read_frame(connection, deadline) if blocking else first
                if len(done) < 3 or done[1] != ORDER_DONE:
                    raise RuntimeError(f"FNHR did not confirm action completion: {done.hex(' ')}")
            self.last_ok = time.time()
            self.last_error = ""
            outcome = Outcome(
                kind="success", reward=0.0,
                description=(
                    f"FNHR action '{action_type}' completed; physical displacement is unverified "
                    "because the stock firmware provides no odometry."
                ),
            )
            return self.observe(), outcome
        except Exception as exc:
            self.last_error = str(exc)
            LOG.error("FNK0031 FNHR USB action %s failed on %s: %s", action_type, self.port, exc)
            return self.observe(), Outcome(kind="failure", reward=-0.1, description=f"USB command failed: {exc}")

    def status(self) -> dict[str, Any]:
        connected = self.ping()
        return {
            "source": self.name,
            "transport": "USB serial / stock FNHR framed protocol",
            "protocol": "fnhr_framed_serial",
            "port": self.port,
            "baudrate": 115200,
            "connected": connected,
            "actuation_enabled": self.actuation_enabled,
            "pose_available": False,
            "supply_voltage_v": self.read_supply_voltage() if connected else None,
            "battery_v": self.supply_voltage,
            "last_ok": self.last_ok,
            "last_error": self.last_error,
            "supported_actions": [
                *MOTION_ORDERS, *ACTION_ALIASES, *PARAMETERIZED_ORDERS,
                "leg_move_to_relatively", "wait",
            ],
            "unsupported_actions": sorted(UNSUPPORTED_ACTIONS),
            "remote_preserved": True,
        }
