import unittest
import json
import tempfile
from pathlib import Path

from body_runtime_host.nav2_simulation import Nav2Simulation


class Nav2SimulationTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
