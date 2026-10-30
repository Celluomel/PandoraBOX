import sys
import unittest
from unittest.mock import patch

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class BodyRuntimeStatusPublicationTest(unittest.TestCase):
    def test_status_is_published_to_observation_store_and_bridge_buffer(self):
        from body_runtime_host.runtime import BodyHost

        host = BodyHost()
        host.config = {
            "BODY_CAMERA_STARTUP_ENABLED": True,
            "BODY_PLUGIN_ROBOT_ENABLED": False,
            "BODY_WORLDMODEL_ENABLED": True,
        }
        with patch.object(host, "camera_settings", return_value={
            "capture": {"status": "capturing", "available": True, "observed_fps": 12.5,
                        "width": 640, "height": 480, "frame_age_s": 0.04, "last_error": ""}
        }), patch.object(host, "power_mode_status", return_value={
            "mode": "DEV",
            "board_input_w": 12.0,
            "battery_estimate": {
                "level_percent_est": 10.2,
                "remaining_wh_est": 8.562,
                "source": "continuous INA232 input-rail integration; estimate only",
            },
        }):
            host.publish_runtime_status()

        entry = host.latest["body.runtime.status"]
        self.assertEqual(entry["source"], "body_runtime")
        self.assertEqual(entry["kind"], "runtime_status")
        self.assertTrue(entry["value"]["camera"]["available"])
        self.assertFalse(entry["value"]["robot"]["enabled"])
        self.assertEqual(entry["value"]["world_model"]["enabled"], True)
        self.assertEqual(entry["value"]["power"]["battery_estimate"]["level_percent_est"], 10.2)
        self.assertEqual(host._bridge_latest["body.runtime.status"]["observation"]["subject"], "body.runtime")

    def test_worldmodel_bridge_separates_live_sensors_from_simulated_scene(self):
        from types import SimpleNamespace
        from body_runtime_host.runtime import BodyHost

        host = BodyHost()
        host._worldmodel = SimpleNamespace(status_summary=lambda: {"perception": {
            "available": True,
            "timestamp": 100.0,
            "source": "sim_robot",
            "ground_truth_available": True,
            "body": {"position": [99, 99, 0], "orientation": 1.2, "capabilities": {"fake": True}},
            "objects": [{"label": "simulated table"}],
            "modalities": {
                "ultrasonic": {"timestamp": 99.9, "source": "hc_sr04_ventuno_bridge", "available": True,
                               "simulated": False, "sensors": [{"id": "front_left", "available": True, "distance_m": 0.7}]},
                "camera": {"simulated": True, "available": True},
                "lidar": {"available": True, "source": "ros2_simulation", "provenance": {"simulated": True}},
            },
            "affordances": {"which2act": ["fake"]},
            "sensor_projections": {"quality": {"fake": True}},
            "perception_frame": {"fake": True},
            "scene_interpreter": {"objects": ["fake"]},
            "text": "fake room",
        }})

        host.publish_worldmodel_perception()

        sensor = host.latest["body.sensor.ultrasonic"]
        self.assertEqual(sensor["value"]["sensors"][0]["distance_m"], 0.7)
        self.assertFalse(sensor["provenance"]["simulated"])
        scene = host.latest["world_model.body_state"]["value"]
        self.assertTrue(scene["simulated_only"])
        self.assertEqual(scene["objects"], [])
        self.assertIsNone(scene["position"])
        self.assertEqual(scene["modalities"].keys(), {"ultrasonic"})

    def test_live_sensor_adapters_publish_separate_timestamped_observations(self):
        from unittest.mock import patch
        from body_runtime_host.runtime import BodyHost

        host = BodyHost()
        host.config = {
            "BODY_PLUGIN_MMWAVE_RADAR_ENABLED": True,
            "BODY_PLUGIN_GPS_ENABLED": True,
            "BODY_PLUGIN_IMU_ENABLED": True,
            "BODY_PLUGIN_TOF_ENABLED": True,
            "BODY_PLUGIN_ULTRASONIC_ENABLED": True,
        }
        stamp = __import__("time").time()
        sample = {"available": True, "timestamp": stamp, "simulated": False}
        statuses = {
            "mmwave_radar_status": {"available": True, "sample": {**sample, "source": "ld2450", "targets": []}},
            "gps_status": {"available": True, "sample": {**sample, "source": "gps", "fix": False}},
            "imu_status": {"available": True, "sample": {**sample, "source": "imu", "attitude_valid": False}},
            "tof_status": {"available": True, "sample": {**sample, "source": "tof", "distance_m": 0.4}},
            "ultrasonic_status": {"available": True, "sample": {**sample, "source": "hc_sr04", "sensors": []}},
        }
        with patch.object(host, "mmwave_radar_status", return_value=statuses["mmwave_radar_status"]), \
             patch.object(host, "gps_status", return_value=statuses["gps_status"]), \
             patch.object(host, "imu_status", return_value=statuses["imu_status"]), \
             patch.object(host, "tof_status", return_value=statuses["tof_status"]), \
             patch.object(host, "ultrasonic_status", return_value=statuses["ultrasonic_status"]):
            host.publish_live_sensor_observations()

        for name in ("mmwave_radar", "gps", "imu", "tof", "ultrasonic"):
            entry = host.latest[f"body.sensor.{name}"]
            self.assertEqual(entry["subject"], f"sensor.{name}")
            self.assertFalse(entry["provenance"]["simulated"])
            self.assertEqual(entry["observed_at"], stamp)


if __name__ == "__main__":
    unittest.main()
