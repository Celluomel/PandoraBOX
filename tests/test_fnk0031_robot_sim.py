import json
import unittest
import urllib.request
from pathlib import Path


def request(base, method="GET", path="/", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode())


class FNK0031RobotSimTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from body_runtime_host.robot_sim import RobotSimServer
        cls.server = RobotSimServer(port=0)
        cls.server.start()
        cls.base = f"http://127.0.0.1:{cls.server.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_fnk0031_capabilities_and_sensor_contract(self):
        capabilities = request(self.base, path="/capabilities")
        sensors = request(self.base, path="/sensors")
        self.assertEqual(capabilities["platform"], "fnk0031_simulator")
        self.assertEqual(capabilities["servo_count"], 18)
        self.assertEqual(sensors["protocol_version"], "fnk0031.body.v1")
        self.assertEqual(sensors["capabilities"]["leg_count"], 6)
        self.assertEqual(len(sensors["actuators"]["targets"]), 18)

    def test_commands_change_pose_and_actuator_telemetry(self):
        before = request(self.base, path="/sensors")
        result = request(self.base, "POST", "/command", {"type": "forward", "params": {}})
        after = request(self.base, path="/sensors")
        self.assertEqual(result["protocol_version"], "fnk0031.body.v1")
        self.assertNotEqual(before["position"][:2], after["position"][:2])
        self.assertEqual(after["actuators"]["gait"], "forward")
        self.assertTrue(any(abs(value) > 0 for value in after["actuators"]["targets"]))
        stopped = request(self.base, "POST", "/stop", {"reason": "test"})
        self.assertTrue(stopped["stopped"])
        self.assertEqual(request(self.base, path="/sensors")["actuators"]["gait"], "idle")


if __name__ == "__main__":
    unittest.main()
