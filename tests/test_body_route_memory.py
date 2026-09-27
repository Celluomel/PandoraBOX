import tempfile
import unittest
from pathlib import Path

from body_runtime_host.worldmodel.route_memory import RouteMemory


class RouteMemoryTests(unittest.TestCase):
    def test_records_waypoints_flags_and_reloads(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "route_memory.json"
            memory = RouteMemory(path)
            objects = [{"id": "chair", "label": "chair", "kind": "chair", "position": [8.0, 3.0, 0.0]}]

            memory.record({"position": [1.0, 1.0, 0.0], "orientation": 0.0}, objects, frame_id="frame-1")
            memory.record({"position": [1.1, 1.1, 0.0], "orientation": 0.0}, objects, frame_id="ignored")
            memory.record({"position": [2.0, 1.0, 0.0], "orientation": 0.0}, objects, frame_id="frame-2")

            summary = memory.snapshot()
            self.assertEqual(summary["routes"], 1)
            self.assertEqual(summary["waypoints"], 2)
            self.assertAlmostEqual(summary["distance"], 1.0, places=3)
            self.assertEqual(summary["flags"][0]["id"], "chair")

            route = memory.route_to("chair")
            self.assertTrue(route["available"])
            self.assertEqual(route["mode"], "replayable_metric_route")
            self.assertEqual(len(route["waypoints"]), 2)

            back = memory.route_to_start()
            self.assertTrue(back["available"])
            self.assertEqual(back["mode"], "return_to_start")
            self.assertEqual(back["waypoints"][0]["position"], [2.0, 1.0, 0.0])

            reloaded = RouteMemory(path)
            self.assertEqual(reloaded.snapshot()["waypoints"], 2)
            self.assertTrue(reloaded.route_to("chair")["available"])

    def test_reset_closes_route_before_new_route(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = RouteMemory(Path(directory) / "route_memory.json")
            memory.record({"position": [0.0, 0.0, 0.0], "orientation": 0.0}, [])
            memory.close_current()
            memory.record({"position": [4.0, 0.0, 0.0], "orientation": 0.0}, [])
            snapshot = memory.snapshot()
            self.assertEqual(snapshot["routes"], 2)
            self.assertFalse(snapshot["current"]["closed"])

    def test_spatial_fix_metadata_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = RouteMemory(Path(directory) / "route_memory.json")
            body = {
                "position": [1.0, 2.0, 0.0],
                "orientation": 0.5,
                "coordinate_frame": "world",
                "position_source": "gnss",
                "position_accuracy_m": 1.7,
                "geo": {"latitude": 48.8566, "longitude": 2.3522},
            }
            objects = [{
                "id": "chair", "label": "chair", "kind": "chair", "position": [4.0, 2.0, 0.0],
                "coordinate_frame": "world", "position_source": "vision_gnss_fusion",
                "position_accuracy_m": 2.1, "geo": {"latitude": 48.8567, "longitude": 2.3523},
            }]
            memory.record(body, objects, frame_id="gnss-frame")
            snapshot = memory.snapshot()
            self.assertEqual(snapshot["coordinate_frame"], "world")
            self.assertEqual(snapshot["position_source"], "gnss")
            self.assertEqual(snapshot["origin"]["geo"]["latitude"], 48.8566)
            flag = snapshot["flags"][0]
            self.assertEqual(flag["position_source"], "vision_gnss_fusion")
            self.assertEqual(flag["geo"]["longitude"], 2.3523)


if __name__ == "__main__":
    unittest.main()
