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
    def test_ventuno_firmware_uses_qwiic_and_keeps_ld2450_rpc(self):
        from pathlib import Path

        sketch = (Path(__file__).resolve().parents[1] / "firmware" / "ventuno_sensor_bridge"
                  / "ventuno_sensor_bridge.ino").read_text(encoding="utf-8")

        self.assertIn("Modulino.begin(Wire1)", sketch)
        self.assertIn('Bridge.provide_safe("body_imu_read"', sketch)
        self.assertIn('Bridge.provide("body_ld2450_read"', sketch)
        self.assertIn("bytes_received", sketch)
        self.assertIn("header_complete", sketch)
        self.assertIn("last_bytes_hex", sketch)
        self.assertIn("#define BODY_ENABLE_TOF 0", sketch)
        self.assertIn("#define BODY_ENABLE_IMU 1", sketch)
        setup = sketch.split("void setup()", 1)[1].split("void loop()", 1)[0]
        self.assertLess(setup.index("Bridge.begin()"), setup.index("Modulino.begin(Wire1)"))
        reader = sketch.split("String readMovementSample()", 1)[1].split("String readTofSample()", 1)[0]
        loop = sketch.split("void loop()", 1)[1]
        self.assertNotIn("movement.update()", reader)
        self.assertIn("movement.update()", loop)
        self.assertIn("latestImuSampleValid", reader)

    def test_standalone_imu_firmware_uses_qwiic_without_app_lab_runtime(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parents[1]
        sketch = (repo / "firmware" / "ventuno_modulino_imu_bridge"
                  / "ventuno_modulino_imu_bridge.ino").read_text(encoding="utf-8")
        deploy = (repo / "scripts" / "deploy_ventuno_modulino_imu.sh")
        deploy_text = deploy.read_text(encoding="utf-8")

        self.assertIn("Modulino.begin(Wire1)", sketch)
        self.assertIn('Bridge.provide_safe("body_imu_read"', sketch)
        self.assertIn("arduino-cli compile", deploy_text)
        self.assertIn("arduino-cli upload", deploy_text)
        self.assertNotIn("arduino-app-cli", deploy_text)

    def test_bridge_preserves_firmware_fused_attitude_and_gyro_rates(self):
        bridge = FakeBridge({
            "available": True,
            "sequence": 7,
            "timestamp_ms": 1120,
            "acceleration_g": [0, math.sqrt(0.5), math.sqrt(0.5)],
            "angular_velocity_dps": [1.25, -2.5, 3.75],
            "roll_deg": 44.5,
            "pitch_deg": -1.2,
            "yaw_relative_deg": 12.0,
            "attitude_valid": True,
            "gravity_reference_valid": False,
            "gyro_bias_ready": True,
            "calibration_stable": False,
            "motion_state": "turning",
        })
        source = VentunoBridgeImuSource(bridge_factory=lambda: bridge)

        sample = source.read()

        self.assertAlmostEqual(sample["roll_deg"], 44.5)
        self.assertAlmostEqual(sample["pitch_deg"], -1.2)
        self.assertAlmostEqual(sample["yaw_relative_deg"], 12.0)
        self.assertTrue(sample["attitude_valid"])
        self.assertFalse(sample["calibration_stable"])
        self.assertEqual(sample["motion_state"], "turning")
        self.assertEqual(sample["yaw_rate_dps"], 3.75)
        self.assertFalse(sample["simulated"])
        self.assertEqual(bridge.calls[0][0], "body_imu_read")

    def test_missing_firmware_fusion_is_not_misreported_as_valid_attitude(self):
        bridge = FakeBridge({
            "available": True,
            "sequence": 1,
            "acceleration_g": [0, 0, 1],
            "angular_velocity_dps": [0, 0, 1],
        })

        sample = VentunoBridgeImuSource(bridge_factory=lambda: bridge).read()

        self.assertFalse(sample["attitude_valid"])
        self.assertIsNone(sample["roll_deg"])
        self.assertEqual(sample["attitude_source"], "fused_attitude_unavailable")

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

    def test_firmware_updates_fused_attitude_at_sensor_rate_and_gates_calibration(self):
        from pathlib import Path

        sketch = (Path(__file__).resolve().parents[1] / "firmware" / "ventuno_sensor_bridge"
                  / "ventuno_sensor_bridge.ino").read_text(encoding="utf-8")
        self.assertIn("updateImuAttitude(latestAccelX, latestAccelY, latestAccelZ", sketch)
        self.assertIn("gyroBiasReady", sketch)
        self.assertIn("calibrationStable", sketch)
        self.assertIn("expf(-dt / 1.5f)", sketch)
        self.assertIn("yaw_relative_deg", sketch)

    def test_attitude_at_interpolates_only_near_capture_timestamp(self):
        source = VentunoBridgeImuSource(bridge_factory=lambda: None)
        source._history.extend([
            {"timestamp": 1.0, "roll_deg": 10.0, "pitch_deg": 0.0, "yaw_relative_deg": 179.0,
             "attitude_valid": True},
            {"timestamp": 1.1, "roll_deg": 20.0, "pitch_deg": 4.0, "yaw_relative_deg": -179.0,
             "attitude_valid": True},
        ])

        result = source.attitude_at(1.05)

        self.assertAlmostEqual(result["roll_deg"], 15.0)
        self.assertAlmostEqual(result["pitch_deg"], 2.0)
        self.assertIsNone(source.attitude_at(2.0))

    def test_unavailable_device_is_reported_without_fabricating_a_sample(self):
        bridge = FakeBridge({"available": False, "error": "modulino_movement_not_detected"})
        source = VentunoBridgeImuSource(bridge_factory=lambda: bridge)

        with self.assertRaises(TimeoutError):
            source.read()

        self.assertFalse(source.status()["available"])
        self.assertIn("not_detected", source.status()["last_error"])


if __name__ == "__main__":
    unittest.main()
