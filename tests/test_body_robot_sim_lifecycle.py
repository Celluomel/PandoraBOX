import json
import unittest
import urllib.request


class BodyRobotSimulatorLifecycleTests(unittest.TestCase):
    def test_body_can_start_and_stop_embedded_fnk0031_simulator(self):
        from body_runtime_host.runtime import BodyHost

        host = BodyHost()
        started = host.start_robot_sim({"port": 0})
        try:
            self.assertTrue(started["running"])
            request = urllib.request.Request(started["url"] + "/capabilities")
            with urllib.request.urlopen(request, timeout=5) as response:
                capabilities = json.loads(response.read().decode())
            self.assertEqual(capabilities["platform"], "fnk0031_simulator")
            self.assertEqual(capabilities["servo_count"], 18)
        finally:
            stopped = host.stop_robot_sim()
        self.assertTrue(stopped["stopped"])
        self.assertFalse(host.robot_sim_status()["running"])


if __name__ == "__main__":
    unittest.main()
