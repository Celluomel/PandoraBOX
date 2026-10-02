"""USB serial adapter for the stock Freenove FNK0031 FNHR firmware."""
from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from typing import Any


LOG = logging.getLogger("lumina.body.fnk0031_usb")
_SERIAL_LOCK = threading.RLock()
_SERIAL_CONNECTIONS: dict[tuple[str, Any], Any] = {}

START = 128
END = 129
ORDER_START = 21
ORDER_DONE = 23

MOTION_ORDERS = {
    "forward": 80,
    "backward": 82,
    "turn_left": 88,
    "turn_right": 90,
}


def available_serial_ports() -> list[dict[str, str]]:
    try:
        from serial.tools import list_ports
    except ImportError:
        return []
    return [
        {"device": str(port.device), "description": str(port.description or "Serial device")}
        for port in list_ports.comports()
    ]


class FNK0031USBSource:
    """FNHR's framed 115200-baud serial protocol; no pose sensors assumed."""

    name = "fnk0031_usb"

    def __init__(self, port: str, timeout: float = 5.0, actuation_enabled: bool = False,
                 serial_factory=None):
        self.port = str(port or "").strip()
        self.timeout = max(0.2, float(timeout or 5.0))
        self.actuation_enabled = bool(actuation_enabled)
        self._serial_factory = serial_factory
        self.last_error = ""
        self.last_ok: float | None = None
        self.battery_v: float | None = None
        self._last_voltage_poll = 0.0

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
    def _frame(order: int, *args: int) -> bytes:
        values = (order, *args)
        if any(not 0 <= int(value) <= 127 for value in values):
            raise ValueError("FNHR command bytes must be in range 0..127")
        return bytes((START, *(int(value) for value in values), END))

    @staticmethod
    def _read_frame(connection, deadline: float) -> list[int]:
        frame: list[int] = []
        started = False
        while time.monotonic() < deadline:
            byte = connection.read(1)
            if not byte:
                continue
            value = byte[0]
            if value == START:
                frame = []
                started = True
            elif started and value == END:
                return frame
            elif started:
                frame.append(value)
        raise TimeoutError("timed out waiting for FNHR serial response")

    def _request(self, connection, order: int, *args: int) -> list[int]:
        if hasattr(connection, "reset_input_buffer"):
            connection.reset_input_buffer()
        connection.write(self._frame(order, *args))
        connection.flush()
        return self._read_frame(connection, time.monotonic() + self.timeout)

    def _send_order_and_wait(self, connection, order: int) -> None:
        connection.write(self._frame(order))
        connection.flush()
        deadline = time.monotonic() + self.timeout
        started = False
        while time.monotonic() < deadline:
            frame = self._read_frame(connection, deadline)
            if frame == [ORDER_START]:
                started = True
            elif frame == [ORDER_DONE]:
                return
            elif frame == [1]:
                continue
        raise TimeoutError("FNHR did not report orderDone" + (" after orderStart" if started else ""))

    def ping(self) -> bool:
        if not self.port:
            self.last_error = "USB serial port is not configured"
            return False
        try:
            with self._open() as connection:
                reply = self._request(connection, 0)
            if reply != [1]:
                raise RuntimeError(f"unexpected FNHR echo response: {reply}")
            self.last_error = ""
            self.last_ok = time.time()
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def observe(self) -> Observation:
        from .worldmodel.types import Observation

        voltage = self.battery_v
        now = time.time()
        if voltage is None or now - self._last_voltage_poll >= 1.0:
            self._last_voltage_poll = now
            try:
                with self._open() as connection:
                    reply = self._request(connection, 10)
                if len(reply) >= 3 and reply[0] == 11:
                    voltage = (reply[1] * 128 + reply[2]) / 100.0
                    self.battery_v = voltage
                    self.last_ok = now
                    self.last_error = ""
                else:
                    raise RuntimeError(f"unexpected FNHR voltage response: {reply}")
            except Exception as exc:
                self.last_error = str(exc)
                LOG.warning("FNK0031 USB sensor poll failed on %s: %s", self.port, exc)
        text = "FNK0031 connected over USB serial. Stock firmware reports supply voltage only; pose, heading and displacement are not measured."
        if voltage is not None:
            text += f" Supply voltage {voltage:.2f} V."
        return Observation(
            subject="fnk0031", value={"supply_voltage_v": voltage}, source=self.name,
            kind="hardware_status", confidence=1.0 if voltage is not None else 0.0,
            timestamp=time.time(), text=text, scene=[],
        )

    def body_state(self) -> BodyState:
        from .worldmodel.types import BodyState

        return BodyState(
            posture={"supply_voltage_v": self.battery_v, "pose_available": False},
            capabilities={"reach": 0.0, "speed": 0.0, "strength": 0.0, "gripper": 0.0, "legs": 6},
            position_source="unavailable",
        )

    def execute(self, action: Action) -> tuple[Observation, Outcome]:
        from .worldmodel.types import Outcome

        return self.observe(), Outcome(kind="neutral", description="physical actuation requires an approved Body command")

    def execute_authorized(self, action: Action) -> tuple[Observation, Outcome]:
        from .worldmodel.types import Outcome

        if not self.actuation_enabled:
            return self.observe(), Outcome(kind="neutral", description="physical actuation disabled in Body configuration")
        order = MOTION_ORDERS.get(str(action.type).lower())
        if action.type == "wait":
            return self.observe(), Outcome(kind="neutral", description="wait is a no-op; no firmware command sent")
        if action.type == "stop":
            order = 94  # FNHR SleepMode
        if order is None:
            return self.observe(), Outcome(
                kind="failure", reward=-0.1,
                description=f"FNK0031 USB firmware does not support Body action '{action.type}'",
            )
        try:
            with self._open() as connection:
                if order in MOTION_ORDERS.values():
                    self._send_order_and_wait(connection, 92)  # ActiveMode
                self._send_order_and_wait(connection, order)
                self.last_ok = time.time()
                self.last_error = ""
                outcome = Outcome(
                    kind="success", reward=0.0,
                    description="FNHR reports command complete; physical displacement is unverified (no odometry).",
                )
            return self.observe(), outcome
        except Exception as exc:
            self.last_error = str(exc)
            LOG.error("FNK0031 USB command %s failed on %s: %s", action.type, self.port, exc)
            return self.observe(), Outcome(kind="failure", reward=-0.1, description=f"USB command failed: {exc}")

    def status(self) -> dict[str, Any]:
        connected = self.ping()
        if connected:
            self.observe()
        return {
            "source": self.name,
            "transport": "USB serial / FNHR",
            "port": self.port,
            "baudrate": 115200,
            "connected": connected and not bool(self.last_error),
            "actuation_enabled": self.actuation_enabled,
            "battery_v": self.battery_v,
            "pose_available": False,
            "last_ok": self.last_ok,
            "last_error": self.last_error,
            "supported_actions": [*MOTION_ORDERS, "stop", "wait"],
        }
