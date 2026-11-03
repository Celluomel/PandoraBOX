import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from body_runtime_host.runtime import BodyHost


class BodyLiveRos2SensorFeedTests(unittest.TestCase):
    def test_power_aware_sensor_cadence(self):
        self.assertEqual(BodyHost.live_sensor_poll_interval("DEV"), 1.0)
        self.assertEqual(BodyHost.live_sensor_poll_interval("ATTENTIVE"), 2.0)
        self.assertEqual(BodyHost.live_sensor_poll_interval("IDLE"), 5.0)

    def test_typed_publish_uses_live_samples_without_world_model(self):
        host = object.__new__(BodyHost)
        host._power_mode = SimpleNamespace(status=lambda: {"mode": "DEV"})
        host._live_sensor_poll_monotonic = 0.0
        host._worldmodel = None
        host.latest = {}
        host._bridge_put = Mock()
        now = time.time()
        samples = {
            "mmwave_radar": {"timestamp": now, "available": True, "simulated": False,
                              "targets": [{"position_m": [1.0, 0.0, 0.0]}]},
            "gps": {"timestamp": now, "available": True, "simulated": False,
                    "fix": True, "latitude": 48.8, "longitude": 2.1},
            "imu": {"timestamp": now, "available": True, "simulated": False,
                    "attitude_valid": True},
            "tof": {"timestamp": now, "available": False, "simulated": False},
            "ultrasonic": {"timestamp": now, "available": True, "simulated": False,
                           "sensors": [{"id": "front_left", "available": True, "distance_m": 0.8}]},
        }
        host.value = lambda _key, default=None: True if default is False else default
        host.mmwave_radar_status = lambda: {"available": True, "sample": samples["mmwave_radar"]}
        host.gps_status = lambda: {"available": True, "sample": samples["gps"]}
        host.imu_status = lambda **_kwargs: {"available": True, "sample": samples["imu"]}
        host.tof_status = lambda: {"available": False, "sample": samples["tof"]}
        host.ultrasonic_status = lambda: {"available": True, "sample": samples["ultrasonic"]}
        publish = Mock(return_value=True)
        host._ros2_bridge = SimpleNamespace(publish_body_sensor_observation=publish)

        host.publish_live_sensor_observations()

        publish.assert_called_once()
        payload = publish.call_args.args[0]
        self.assertEqual(set(payload["modalities"]), set(samples))
        self.assertTrue(all(sample["simulated"] is False for sample in payload["modalities"].values()))
        self.assertEqual(host._bridge_put.call_count, len(samples))

    def test_running_world_model_remains_the_higher_rate_ros_source(self):
        host = object.__new__(BodyHost)
        host._power_mode = SimpleNamespace(status=lambda: {"mode": "DEV"})
        host._live_sensor_poll_monotonic = 0.0
        host._worldmodel = SimpleNamespace(status_summary=lambda: {"running": True})
        host.latest = {}
        host._bridge_put = Mock()
        host.value = lambda _key, default=None: True if default is False else default
        sample = {"timestamp": time.time(), "available": True, "simulated": False}
        host.mmwave_radar_status = lambda: {"available": True, "sample": sample}
        host.gps_status = lambda: {"available": True, "sample": sample}
        host.imu_status = lambda **_kwargs: {"available": True, "sample": sample}
        host.tof_status = lambda: {"available": True, "sample": sample}
        host.ultrasonic_status = lambda: {"available": True, "sample": sample}
        publish = Mock()
        host._ros2_bridge = SimpleNamespace(publish_body_sensor_observation=publish)

        host.publish_live_sensor_observations()

        publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
