import json
import unittest
from unittest.mock import patch

from body_runtime_host.tof import TofAugmentedSource, VentunoBridgeTofSource


class FakeBridge:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def connect(self, timeout):
        return True

    def call(self, method, timeout):
        self.calls.append(method)
        return json.dumps(self.payload)


class FakeObservation:
    def __init__(self):
        self.modalities = {"camera": {"available": True}}


class FakeBody:
    name = "fake_body"
    simulated = False

    def observe(self):
        return FakeObservation()

    def status(self):
        return {"source": self.name}


class TofTests(unittest.TestCase):
    def test_bridge_payload_is_normalized_as_forward_metric_range(self):
        bridge = FakeBridge({
            "available": True, "distance_mm": 843, "sequence": 12,
            "sensor": "cqrobot_vl53l1x", "frame": "body_front",
        })
        source = VentunoBridgeTofSource(bridge_factory=lambda: bridge)

        sample = source.read()

        self.assertEqual(sample["distance_mm"], 843)
        self.assertAlmostEqual(sample["distance_m"], 0.843)
        self.assertEqual(sample["direction"], "front")
        self.assertFalse(sample["simulated"])
        self.assertEqual(bridge.calls, ["body_tof_read"])

    def test_missing_or_invalid_range_never_becomes_a_fake_sample(self):
        for payload in (
            {"available": False, "error": "sensor_not_detected"},
            {"available": True, "distance_mm": 0},
            {"available": True, "distance_mm": 4201},
        ):
            source = VentunoBridgeTofSource(bridge_factory=lambda p=payload: FakeBridge(p))
            with self.assertRaises((TimeoutError, ValueError)):
                source.read()
            self.assertFalse(source.status()["available"])

    def test_body_observation_gets_tof_without_losing_other_sensors(self):
        bridge = FakeBridge({"available": True, "distance_mm": 1250})
        tof = VentunoBridgeTofSource(bridge_factory=lambda: bridge)
        observation = TofAugmentedSource(FakeBody(), tof).observe()

        self.assertEqual(observation.modalities["tof"]["distance_m"], 1.25)
        self.assertIn("camera", observation.modalities)

    def test_firmware_and_both_huds_include_the_range_path(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        sketch = (root / "firmware/ventuno_sensor_bridge/ventuno_sensor_bridge.ino").read_text(encoding="utf-8")
        preview = (root / "body_runtime_host/quest_hud_preview.html").read_text(encoding="utf-8")
        preview_js = (root / "body_runtime_host/quest_hud_preview.js").read_text(encoding="utf-8")
        vr_js = (root / "body_runtime_host/quest_vr_dashboard.js").read_text(encoding="utf-8")

        self.assertIn("Modulino.begin(Wire1)", sketch)
        self.assertIn('Bridge.provide_safe("body_tof_read"', sketch)
        self.assertIn("tof.begin(0x29, &Wire1)", sketch)
        self.assertIn('id="tof-value"', preview)
        self.assertIn("drawTofRangeBar", preview_js)
        self.assertIn("drawTofRangeBar(ctx", vr_js)


if __name__ == "__main__":
    unittest.main()
