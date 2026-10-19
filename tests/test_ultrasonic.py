import json
import unittest

from body_runtime_host.ultrasonic import VentunoBridgeUltrasonicSource


class FakeBridge:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def connect(self, timeout):
        return True

    def call(self, method, timeout):
        self.calls.append(method)
        return json.dumps(self.payload)


def payload(channels):
    return {
        "available": any(channel["available"] for channel in channels),
        "sensor": "hc_sr04_array",
        "timestamp_ms": 1000,
        "sequence": 9,
        "sensors": channels,
    }


def channel(sensor_id, trigger, echo, distance, available=True, error=""):
    return {
        "id": sensor_id, "trigger_pin": trigger, "echo_pin": echo,
        "available": available, "distance_mm": distance,
        "timestamp_ms": 950 if available else 0,
        "sequence": 3 if available else 0, "error": error,
    }


class UltrasonicTests(unittest.TestCase):
    def test_reads_all_three_named_ranges_and_pin_assignments(self):
        bridge = FakeBridge(payload([
            channel("front_left", "D2", "D3", 480),
            channel("front_right", "D4", "D5", 920),
            channel("rear", "D6", "D9", 1350),
        ]))
        source = VentunoBridgeUltrasonicSource(bridge_factory=lambda: bridge)

        sample = source.read()

        self.assertTrue(sample["available"])
        self.assertEqual(bridge.calls, ["body_ultrasonic_read"])
        self.assertEqual([item["echo_pin"] for item in sample["sensors"]], ["D3", "D5", "D9"])
        self.assertEqual([item["distance_mm"] for item in sample["sensors"]], [480, 920, 1350])
        self.assertEqual([item["distance_m"] for item in sample["sensors"]], [0.48, 0.92, 1.35])
        cached = source.read()
        self.assertEqual(bridge.calls, ["body_ultrasonic_read"])
        self.assertEqual(cached["sensors"][0]["distance_mm"], 480)

    def test_concurrent_hud_reads_share_recent_rpc_sample_without_mutating_cache(self):
        bridge = FakeBridge(payload([
            channel("front_left", "D2", "D3", 480),
            channel("front_right", "D4", "D5", 920),
            channel("rear", "D6", "D9", 1350),
        ]))
        source = VentunoBridgeUltrasonicSource(bridge_factory=lambda: bridge)

        first = source.read()
        first["sensors"][0]["age_ms"] = 599
        cached = source.read()

        self.assertEqual(bridge.calls, ["body_ultrasonic_read"])
        self.assertTrue(cached["sensors"][0]["available"])
        self.assertGreaterEqual(cached["sensors"][0]["age_ms"], 50)

    def test_exposes_firmware_startup_and_loop_diagnostics(self):
        raw = payload([
            channel("front_left", "D2", "D3", None, False, "no_echo"),
            channel("front_right", "D4", "D5", None, False, "no_echo"),
            channel("rear", "D6", "D9", None, False, "no_echo"),
        ])
        raw.update({"setup_stage": 60, "loop_sequence": 1234})
        sample = VentunoBridgeUltrasonicSource(
            bridge_factory=lambda: FakeBridge(raw)
        ).read()

        self.assertEqual(sample["firmware_setup_stage"], 60)
        self.assertEqual(sample["firmware_loop_sequence"], 1234)

    def test_no_echo_remains_unavailable_without_fabricating_zero(self):
        bridge = FakeBridge(payload([
            channel("front_left", "D2", "D3", None, False, "no_echo"),
            channel("front_right", "D4", "D5", None, False, "no_echo"),
            channel("rear", "D6", "D9", None, False, "echo_timeout"),
        ]))
        sample = VentunoBridgeUltrasonicSource(bridge_factory=lambda: bridge).read()

        self.assertFalse(sample["available"])
        self.assertTrue(all(item["distance_m"] is None for item in sample["sensors"]))
        self.assertEqual([item["error"] for item in sample["sensors"]],
                         ["no_echo", "no_echo", "echo_timeout"])

    def test_firmware_and_live_status_keep_the_existing_bridge_methods(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        sketch = (root / "firmware/ventuno_sensor_bridge/ventuno_sensor_bridge.ino").read_text(encoding="utf-8")
        runtime = (root / "body_runtime_host/runtime.py").read_text(encoding="utf-8")
        ui = (root / "body_runtime_host/world_map_3d.js").read_text(encoding="utf-8")

        self.assertIn('Bridge.provide_safe("body_ultrasonic_read"', sketch)
        self.assertIn("{D2, D4, D6}", sketch)
        self.assertIn("{D3, D5, D9}", sketch)
        self.assertIn("ULTRASONIC_TRIGGER_INTERVAL_US = 100000", sketch)
        self.assertIn("updateUltrasonic();", sketch)
        self.assertIn("firmwareLoopSequence", sketch)
        self.assertIn("BODY_ULTRASONIC_CHANNEL_MASK", sketch)
        self.assertNotIn("pulseIn(", sketch)
        for existing_rpc in ("body_imu_read", "body_tof_read", "body_ld2450_read", "body_gps_read"):
            self.assertIn(existing_rpc, sketch)
        self.assertIn('path == "/plugins/ultrasonic/status"', runtime)
        self.assertIn("/plugins/ultrasonic/status", ui)
        self.assertIn("world-map-ultrasonic-rear", ui)


if __name__ == "__main__":
    unittest.main()
