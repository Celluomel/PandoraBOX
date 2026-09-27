import unittest

from body_runtime_host.fnk0031_protocol import PROTOCOL_VERSION, normalize_command, normalize_sensors


class FNK0031ProtocolTests(unittest.TestCase):
    def test_normalizes_sensor_pose_and_imu(self):
        result = normalize_sensors({"x": 1, "y": 2, "yaw": 0.5, "imu_data": {"pitch": 0.1}})
        self.assertEqual(result["protocol_version"], PROTOCOL_VERSION)
        self.assertEqual(result["position"], [1.0, 2.0, 0.0])
        self.assertEqual(result["orientation"], 0.5)
        self.assertEqual(result["imu"]["pitch"], 0.1)

    def test_rejects_malformed_sensor_payload(self):
        with self.assertRaises(ValueError):
            normalize_sensors({"position": [1]})

    def test_normalizes_command(self):
        result = normalize_command({"type": "FORWARD"})
        self.assertEqual(result["protocol_version"], PROTOCOL_VERSION)
        self.assertEqual(result["type"], "forward")
        self.assertEqual(result["params"], {})


if __name__ == "__main__":
    unittest.main()
