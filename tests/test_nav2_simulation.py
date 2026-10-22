import unittest
import json
import tempfile
from pathlib import Path

from body_runtime_host.nav2_simulation import Nav2Simulation


class Nav2SimulationTests(unittest.TestCase):
    def test_physical_nav2_preflight_never_confuses_simulation_with_robot_readiness(self):
        from body_runtime_host.ros2_bridge import Ros2ObservationBridge

        readiness = Ros2ObservationBridge._physical_nav2_preflight()
        self.assertFalse(readiness["ready"])
        self.assertTrue(readiness["simulation_only"])
        self.assertFalse(readiness["hardware_actuation_enabled"])
        self.assertTrue(any("odometry" in blocker.lower() for blocker in readiness["blockers"]))
        self.assertTrue(any("cmd_vel" in blocker for blocker in readiness["blockers"]))
        self.assertTrue(any("sampling cadence" in blocker for blocker in readiness["blockers"]))
        self.assertGreaterEqual(len(readiness["required_before_physical_test"]), 4)

    def test_physical_sensor_topic_contract_is_explicit(self):
        from body_runtime_host.ros2_bridge import BODY_SENSOR_PUBLISH_TOPICS

        self.assertEqual(BODY_SENSOR_PUBLISH_TOPICS["ultrasonic_front_left"], "/body/sensors/ultrasonic/front_left")
        self.assertEqual(BODY_SENSOR_PUBLISH_TOPICS["ultrasonic_front_right"], "/body/sensors/ultrasonic/front_right")
        self.assertEqual(BODY_SENSOR_PUBLISH_TOPICS["ultrasonic_rear"], "/body/sensors/ultrasonic/rear")
        self.assertEqual(BODY_SENSOR_PUBLISH_TOPICS["mmwave_targets"], "/body/sensors/mmwave/targets")

    def test_ros_typed_sensor_publisher_never_republishes_simulated_samples_as_hardware(self):
        from body_runtime_host.ros2_bridge import BODY_SENSOR_PUBLISH_TOPICS, Ros2ObservationBridge

        class Publisher:
            def __init__(self): self.messages = []
            def publish(self, message): self.messages.append(message)

        bridge = Ros2ObservationBridge(lambda _: None)
        bridge._node = object()
        bridge._body_sensor_publishers = {key: Publisher() for key in BODY_SENSOR_PUBLISH_TOPICS}
        result = bridge.publish_body_sensor_observation({"modalities": {
            "mmwave_radar": {"simulated": True, "targets": [{"position_m": [1, 2, 0]}]},
            "ultrasonic": {"simulated": True, "sensors": [{"id": "front_left", "available": True, "distance_m": 1.0}]},
        }})
        self.assertFalse(result)
        self.assertTrue(all(not publisher.messages for publisher in bridge._body_sensor_publishers.values()))

    def test_synthetic_world_has_free_start_and_goal_with_obstacles(self):
        self.assertFalse(Nav2Simulation._occupied(-5.0, 0.0))
        self.assertFalse(Nav2Simulation._occupied(5.0, 0.0))
        self.assertTrue(Nav2Simulation._occupied(2.5, 0.0))
        self.assertTrue(Nav2Simulation._occupied(2.5, 1.2))
        self.assertTrue(Nav2Simulation._occupied(20.0, 20.0))

    def test_synthetic_world_bounds_and_map_resolution_are_metric(self):
        self.assertEqual(Nav2Simulation.SIZE, 160)
        self.assertAlmostEqual(Nav2Simulation.SIZE * Nav2Simulation.RESOLUTION, 16.0)
        self.assertEqual(Nav2Simulation.ORIGIN, -8.0)

    def test_visualization_is_bounded_and_excludes_infinite_scan_ranges(self):
        import math

        simulation = object.__new__(Nav2Simulation)
        simulation.x, simulation.y, simulation.yaw = 1.5, -0.2, 0.3
        simulation._scan_angles = (-1.0, 0.0, 1.0)
        simulation._last_scan = (2.3456, math.inf, 0.8)
        simulation._last_scan_at = 123.0
        data = simulation.visualization()

        self.assertEqual(data["source"], "synthetic_nav2")
        self.assertTrue(data["simulation_only"])
        self.assertEqual(data["map"]["size_m"], 16.0)
        self.assertEqual(data["pose"]["x"], 1.5)
        self.assertEqual(data["scan"]["returns"], [[-1.0, 2.346], [1.0, 0.8]])
        json.dumps(data, allow_nan=False)

    def test_visualization_does_not_invent_a_real_ros_map(self):
        from body_runtime_host.ros2_bridge import Ros2ObservationBridge

        bridge = Ros2ObservationBridge(lambda _: None)
        data = bridge.visualization()
        self.assertFalse(data["available"])
        self.assertEqual(data["source"], "none")
        self.assertNotIn("map", data)

    def test_body_visualization_endpoint_contract_delegates_to_bridge(self):
        from types import SimpleNamespace
        from body_runtime_host.runtime import BodyHost

        host = object.__new__(BodyHost)
        host._ros2_bridge = None
        self.assertFalse(host.ros2_visualization()["available"])
        host._ros2_bridge = SimpleNamespace(visualization=lambda: {"available": True, "source": "synthetic_nav2"})
        self.assertEqual(host.ros2_visualization()["source"], "synthetic_nav2")

    def test_nav2_simulation_cannot_be_enabled_without_ros_bridge(self):
        import body_runtime_host.runtime as runtime

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            old_config, old_dotenv = runtime.CONFIG_PATH, runtime._load_dotenv
            runtime.CONFIG_PATH = Path(tmp) / "config.json"
            runtime.CONFIG_PATH.write_text(json.dumps({}), encoding="utf-8")
            runtime._load_dotenv = lambda: None
            try:
                host = runtime.BodyHost()
                with self.assertRaisesRegex(ValueError, "Enable the ROS 2 bridge"):
                    host.update_ros2_settings({"enabled": False, "nav2_simulation_enabled": True})
            finally:
                runtime.CONFIG_PATH, runtime._load_dotenv = old_config, old_dotenv

    def test_sensor_topic_configuration_persists_and_rejects_ambiguous_topics(self):
        import body_runtime_host.runtime as runtime

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            old_config, old_dotenv = runtime.CONFIG_PATH, runtime._load_dotenv
            runtime.CONFIG_PATH = Path(tmp) / "config.json"
            runtime.CONFIG_PATH.write_text(json.dumps({}), encoding="utf-8")
            runtime._load_dotenv = lambda: None
            try:
                host = runtime.BodyHost()
                topics = {"imu": "/robot/imu", "gps": "/robot/gps", "lidar": "/robot/scan",
                          "odometry": "/robot/odom", "range": ""}
                result = host.update_ros2_settings({"enabled": False, "sensor_topics": topics})
                self.assertTrue(result["persisted"])
                self.assertEqual(host.ros2_settings()["sensor_topics"], topics)
                with self.assertRaisesRegex(ValueError, "distinct topic"):
                    host.update_ros2_settings({"enabled": False, "sensor_topics": {
                        "imu": "/same", "gps": "/same",
                    }})
            finally:
                runtime.CONFIG_PATH, runtime._load_dotenv = old_config, old_dotenv

    def test_stop_destroys_actual_command_subscription_and_is_idempotent(self):
        from types import SimpleNamespace

        events = []
        timer = SimpleNamespace(cancel=lambda: events.append("timer-cancel"))
        node = SimpleNamespace(
            destroy_timer=lambda _value: events.append("timer-destroy"),
            destroy_subscription=lambda _value: events.append("subscription-destroy"),
            destroy_publisher=lambda _value: events.append("publisher-destroy"),
        )
        simulation = object.__new__(Nav2Simulation)
        simulation.node = node
        simulation._timer = timer
        simulation._cmd_sub = object()
        simulation._map_pub = object()
        simulation._odom_pub = object()
        simulation._scan_pub = object()
        simulation._stopped = False

        simulation.stop()
        simulation.stop()

        self.assertEqual(events.count("subscription-destroy"), 1)
        self.assertEqual(events.count("publisher-destroy"), 3)
        self.assertEqual(events.count("timer-destroy"), 1)

    def test_simulated_nav2_route_requires_all_simulation_gates_and_never_actuates(self):
        from types import SimpleNamespace
        import body_runtime_host.runtime as runtime

        class Bridge:
            def __init__(self):
                self.goal = None

            def status(self):
                return {
                    "available": True,
                    "nav2_simulation": {
                        "enabled": True,
                        "cmd_vel_hardware_isolated": True,
                        "pose": {"x": 4.92, "y": 0.08, "yaw": 0.0},
                    },
                }

            def navigate_to_pose(self, **kwargs):
                self.goal = kwargs
                return {"status": "succeeded", "action_status": 4}

        bridge = Bridge()
        host = object.__new__(runtime.BodyHost)
        host.value = lambda key, default=None: {
            "BODY_ROS2_ENABLED": True,
            "BODY_NAV2_SIMULATION_ENABLED": True,
        }.get(key, default)
        host._ros2_bridge = bridge
        host.nav2_stack_status = lambda: {"state": "running", "simulation_only": True}

        result = host.run_nav2_simulation_route()

        self.assertEqual(bridge.goal["frame_id"], "map")
        self.assertEqual(bridge.goal["x"], 5.0)
        self.assertTrue(result["simulation_only"])
        self.assertFalse(result["hardware_actuation"])
        self.assertLessEqual(result["position_error_m"], 0.35)

        bridge.status = lambda: {
            "available": True,
            "nav2_simulation": {
                "enabled": True,
                "cmd_vel_hardware_isolated": False,
                "pose": {"x": 5.0, "y": 0.0, "yaw": 0.0},
            },
        }
        bridge.goal = None
        with self.assertRaisesRegex(RuntimeError, "additional subscriber"):
            host.run_nav2_simulation_route()
        self.assertIsNone(bridge.goal)

        host.value = lambda key, default=None: False
        with self.assertRaisesRegex(RuntimeError, "Enable the ROS 2 bridge"):
            host.run_nav2_simulation_route()


if __name__ == "__main__":
    unittest.main()
