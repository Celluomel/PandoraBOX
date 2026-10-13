import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

from body_runtime_host.sensor_bridge_rpc import call_sensor_rpc


class ConcurrentBridge:
    def __init__(self):
        self.active = 0
        self.max_active = 0
        self.guard = threading.Lock()

    def call(self, method, timeout):
        with self.guard:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        time.sleep(0.01)
        with self.guard:
            self.active -= 1
        return method


class SensorBridgeRpcTests(unittest.TestCase):
    def test_imu_and_tof_calls_share_one_serialized_rpc_channel(self):
        bridge = ConcurrentBridge()
        methods = ["body_imu_read", "body_tof_read"] * 5

        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(lambda method: call_sensor_rpc(bridge, method, timeout=0.5), methods))

        self.assertEqual(results, methods)
        self.assertEqual(bridge.max_active, 1)


if __name__ == "__main__":
    unittest.main()
