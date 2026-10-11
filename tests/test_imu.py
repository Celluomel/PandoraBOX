import json
import math
import unittest

from body_runtime_host.imu import ImuAugmentedSource, VentunoBridgeImuSource


class FakeObservation:
    def __init__(self):
        self.modalities = {}


class FakeBridge:
    def __init__(self, payload):
        self.payload = payload
        self.connected = False
        self.calls = []

    def connect(self, timeout):
        self.connected = True
        return True

    def call(self, method, timeout):
        self.calls.append((method, timeout))
        return json.dumps(self.payload)


class FakeBodySource:
    name = "fake_body"
    simulated = False

    def observe(self):
        return FakeObservation()

    def status(self):
        return {"source": self.name}


class ModulinoImuTests(unittest.TestCase):
    def test_bridge_sample_derives_gravity_attitude_and_preserves_angular_rates(self):
        bridge = FakeBridge({
            "available": True,
            "sequence": 7,
            "acceleration_g": [0, math.sqrt(0.5), math.sqrt(0.5)],
            "angular_velocity_dps": [1.25, -2.5, 3.75],
        })
        source = VentunoBridgeImuSource(bridge_factory=lambda: bridge)

        sample = source.read()

        self.assertAlmostEqual(sample["roll_deg"], 45.0)
        self.assertAlmostEqual(sample["pitch_deg"], 0.0)
        self.assertTrue(sample["attitude_valid"])
        self.assertEqual(sample["yaw_rate_dps"], 3.75)
        self.assertFalse(sample["simulated"])
        self.assertEqual(bridge.calls[0][0], "body_imu_read")

    def test_acceleration_invalidates_gravity_attitude_during_linear_acceleration(self):
        bridge = FakeBridge({
            "available": True,
            "acceleration_g": [0, 0, 2],
            "angular_velocity_dps": [0, 0, 0],
        })

        sample = VentunoBridgeImuSource(bridge_factory=lambda: bridge).read()

        self.assertFalse(sample["attitude_valid"])
        self.assertIsNone(sample["roll_deg"])
        self.assertIsNone(sample["pitch_deg"])

    def test_augmented_body_observation_exposes_real_imu_modality(self):
        bridge = FakeBridge({
            "available": True,
            "acceleration_g": [0, 0, 1],
            "angular_velocity_dps": [0, 0, -4],
        })
        imu = VentunoBridgeImuSource(bridge_factory=lambda: bridge)
        observation = ImuAugmentedSource(FakeBodySource(), imu).observe()

        self.assertEqual(observation.modalities["imu"]["source"], imu.name)
        self.assertEqual(observation.modalities["imu"]["yaw_rate_dps"], -4.0)
        self.assertFalse(observation.modalities["imu"]["simulated"])

    def test_unavailable_device_is_reported_without_fabricating_a_sample(self):
        bridge = FakeBridge({"available": False, "error": "modulino_movement_not_detected"})
        source = VentunoBridgeImuSource(bridge_factory=lambda: bridge)

        with self.assertRaises(TimeoutError):
            source.read()

        self.assertFalse(source.status()["available"])
        self.assertIn("not_detected", source.status()["last_error"])


if __name__ == "__main__":
    unittest.main()
