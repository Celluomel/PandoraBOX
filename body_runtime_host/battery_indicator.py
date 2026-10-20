"""Send the estimated charge to the VENTUNO Q's RGB LED and LED matrix."""
from __future__ import annotations

import time
from typing import Any, Callable

from .sensor_bridge_rpc import call_sensor_rpc


def estimated_level_percent(consumed_wh: float, capacity_wh: float,
                            usable_fraction: float) -> int:
    usable_wh = max(1.0, float(capacity_wh)) * max(0.5, min(1.0, float(usable_fraction)))
    remaining = max(0.0, usable_wh - max(0.0, float(consumed_wh)))
    return max(0, min(100, int(round(remaining / usable_wh * 100.0))))


class VentunoBatteryIndicator:
    """Update the user RGB LED and MCU matrix without touching system LEDs."""

    method = "body_battery_indicator_set"
    rgb_led_paths = {
        "red": "/sys/class/leds/pca963x:red/brightness",
        "green": "/sys/class/leds/pca963x:green/brightness",
        "blue": "/sys/class/leds/pca963x:blue/brightness",
    }

    def __init__(self, bridge_factory: Callable[[], Any] | None = None,
                 clock: Callable[[], float] = time.monotonic,
                 led_writer: Callable[[str, int], None] | None = None):
        self._bridge_factory = bridge_factory
        self._clock = clock
        self._bridge = None
        self._last_sent: int | None = None
        self._retry_after = 0.0
        self._last_color: str | None = None
        self._rgb_retry_after = 0.0
        self._led_writer = led_writer or self._write_led

    @classmethod
    def _write_led(cls, color: str, brightness: int) -> None:
        with open(cls.rgb_led_paths[color], "w", encoding="ascii") as led:
            led.write(f"{brightness}\n")

    def _set_rgb(self, level: int | None, now: float) -> None:
        color = "unknown" if level is None else (
            "red" if level <= 20 else "amber" if level <= 50 else "green")
        if color == self._last_color or now < self._rgb_retry_after:
            return
        values = {
            "unknown": (0, 0, 0),
            "red": (255, 0, 0),
            "amber": (255, 120, 0),
            "green": (0, 255, 0),
        }[color]
        try:
            for name, value in zip(("red", "green", "blue"), values):
                self._led_writer(name, value)
            self._last_color = color
            self._rgb_retry_after = 0.0
        except OSError:
            self._rgb_retry_after = now + 10.0

    def update(self, level_percent: int | None) -> bool:
        value = -1 if level_percent is None else max(0, min(100, int(level_percent)))
        now = self._clock()
        self._set_rgb(None if value < 0 else value, now)
        if value == self._last_sent or now < self._retry_after:
            return False
        try:
            if self._bridge is None:
                factory = self._bridge_factory
                if factory is None:
                    from arduino.router_bridge import Bridge
                    factory = Bridge
                self._bridge = factory()
                if not self._bridge.connect(timeout=1.0):
                    raise ConnectionError("Arduino Router Bridge is not available locally")
            call_sensor_rpc(self._bridge, self.method, timeout=0.5, args=(value,))
            self._last_sent = value
            self._retry_after = 0.0
            return True
        except Exception:
            self._bridge = None
            self._retry_after = now + 5.0
            return False
