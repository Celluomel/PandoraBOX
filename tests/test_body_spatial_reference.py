import unittest

from body_runtime_host.worldmodel.sources import RobotHttpSource
from body_runtime_host.worldmodel.spatial import LocalMapReference


class SpatialReferenceTests(unittest.TestCase):
    def test_projects_gnss_to_local_east_north(self):
        reference = LocalMapReference()
        self.assertEqual(reference.project({"latitude": 48.0, "longitude": 2.0}), [0.0, 0.0, 0.0])
        position = reference.project({"latitude": 48.00001, "longitude": 2.00001})
        self.assertAlmostEqual(position[0], 0.745, delta=0.02)
        self.assertAlmostEqual(position[1], 1.113, delta=0.02)

    def test_robot_source_accepts_gnss_only_payload(self):
        source = RobotHttpSource("http://robot")
        source._raw_sensors = lambda: {
            "timestamp": 1000.0,
            "gps": {"latitude": 48.0, "longitude": 2.0},
            "position_accuracy_m": 2.0,
            "orientation": 0.0,
            "objects": [{
                "id": "chair", "label": "chair", "kind": "chair",
                "gps": {"latitude": 48.00001, "longitude": 2.00001},
            }],
        }
        observation = source.observe()
        body = source.body_state()
        self.assertEqual(body.coordinate_frame, "local_map")
        self.assertEqual(body.position_source, "gnss_projected")
        self.assertEqual(body.position, [0.0, 0.0, 0.0])
        self.assertEqual(observation.scene[0].position_source, "gnss_projected")
        self.assertAlmostEqual(observation.scene[0].position[0], 0.745, delta=0.02)
        self.assertAlmostEqual(observation.scene[0].position[1], 1.113, delta=0.02)


if __name__ == "__main__":
    unittest.main()
