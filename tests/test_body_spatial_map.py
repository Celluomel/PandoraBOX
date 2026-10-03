import tempfile
import unittest
from pathlib import Path

from body_runtime_host.worldmodel.spatial_map import MetricVoxelMap


def frame(*, source="native", lidar_frame="map", position=(0.0, 0.0, 0.0), yaw=0.0,
          points=None, calibration=None, synchronized=True, frame_id="fixture-1"):
    return {
        "contract": "body_perception_frame.v2",
        "frame_id": frame_id,
        "timestamp": 12.5,
        "synchronization": {"synchronized": synchronized},
        "body": {"pose": {
            "position_m": list(position), "yaw_rad": yaw,
            "coordinate_frame": "map", "position_source": "fixture",
        }},
        "lidar": {
            "frame": lidar_frame,
            "calibration": calibration or {},
            "native": source == "native",
            "quality": {"source": source},
            "points": points if points is not None else [{"x": 1.04, "y": 2.04, "z": 0.24, "intensity": 0.8}],
        },
    }


class MetricVoxelMapTests(unittest.TestCase):
    def test_accumulates_metric_returns_and_keeps_unknown_space_unknown(self):
        voxel_map = MetricVoxelMap(resolution_m=0.1)
        self.assertTrue(voxel_map.integrate(frame())["accepted"])
        self.assertTrue(voxel_map.integrate(frame(frame_id="fixture-2"))["accepted"])
        snapshot = voxel_map.snapshot()
        self.assertEqual(snapshot["contract"], "body_metric_voxel_map.v1")
        self.assertEqual(snapshot["voxel_count"], 1)
        self.assertEqual(snapshot["voxels"][0]["hits"], 2)
        self.assertEqual(snapshot["voxels"][0]["state"], "observed_return")
        self.assertTrue(snapshot["unknown_space_is_implicit"])
        self.assertFalse(snapshot["free_space_observed"])
        self.assertFalse(snapshot["safety_authoritative"])

    def test_rejects_simulated_source_by_default_and_allows_explicit_test_opt_in(self):
        voxel_map = MetricVoxelMap()
        result = voxel_map.integrate(frame(source="virtual"))
        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"], "non_native_lidar_requires_explicit_opt_in")
        self.assertTrue(voxel_map.integrate(frame(source="virtual"), allow_non_native=True)["accepted"])

    def test_rejects_unsynchronized_frames(self):
        result = MetricVoxelMap().integrate(frame(synchronized=False))
        self.assertEqual(result["reason"], "frame_not_synchronized")

    def test_duplicate_frame_is_not_counted_twice(self):
        voxel_map = MetricVoxelMap()
        self.assertTrue(voxel_map.integrate(frame())["accepted"])
        duplicate = voxel_map.integrate(frame())
        self.assertFalse(duplicate["accepted"])
        self.assertEqual(duplicate["reason"], "duplicate_frame_id")
        self.assertEqual(voxel_map.snapshot()["frames_integrated"], 1)

    def test_transforms_sensor_points_through_extrinsics_and_body_pose(self):
        voxel_map = MetricVoxelMap(resolution_m=0.01)
        sample = frame(
            lidar_frame="sensor", position=(2.0, 3.0, 0.0), yaw=1.5707963267948966,
            points=[{"x": 1.0, "y": 0.0, "z": 0.2}],
            calibration={"sensor_to_body": {"translation_m": [0.1, 0.0, 0.0], "yaw_rad": 0.0}},
        )
        self.assertTrue(voxel_map.integrate(sample)["accepted"])
        center = voxel_map.snapshot()["voxels"][0]["center_m"]
        self.assertAlmostEqual(center[0], 2.0, delta=0.02)
        self.assertAlmostEqual(center[1], 4.1, delta=0.02)
        self.assertAlmostEqual(center[2], 0.2, delta=0.02)

    def test_sensor_frame_without_calibration_is_rejected(self):
        result = MetricVoxelMap().integrate(frame(lidar_frame="sensor"))
        self.assertEqual(result["reason"], "missing_sensor_to_body_calibration")

    def test_sparse_map_round_trips_to_disk(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.json"
            MetricVoxelMap(path=path).integrate(frame())
            restored = MetricVoxelMap(path=path)
            self.assertEqual(restored.snapshot()["voxel_count"], 1)
            self.assertEqual(restored.snapshot()["frames_integrated"], 1)

    def test_world_model_does_not_promote_virtual_lidar_to_spatial_map(self):
        from body_runtime_host.worldmodel.core import EmbodiedWorldModel
        from body_runtime_host.worldmodel.sources import SimRobotSource

        with tempfile.TemporaryDirectory() as directory:
            world_model = EmbodiedWorldModel(
                data_dir=directory,
                config={"BODY_LLM_ENABLED": False},
                source=SimRobotSource(camera_interval=60.0),
            )
            world_model.step()
            snapshot = world_model.spatial_map.snapshot()
            self.assertEqual(snapshot["frames_integrated"], 0)
            self.assertEqual(snapshot["voxel_count"], 0)
            self.assertEqual(world_model._last_spatial_map_update["reason"], "no_native_lidar_frame")

    def test_world_model_integrates_explicit_native_frame(self):
        from body_runtime_host.worldmodel.core import EmbodiedWorldModel
        from body_runtime_host.worldmodel.sources import SimRobotSource

        class NativeFixtureSource(SimRobotSource):
            def observe(self):
                observation = super().observe()
                observation.modalities["lidar"] = {
                    "source": "test_fixture_range_sensor",
                    "native": True,
                    "frame": "body_world",
                    "timestamp": observation.timestamp,
                    "points": [{"x": 1.0, "y": 1.0, "z": 0.3, "intensity": 0.95}],
                }
                return observation

        with tempfile.TemporaryDirectory() as directory:
            world_model = EmbodiedWorldModel(
                data_dir=directory,
                config={"BODY_LLM_ENABLED": False},
                source=NativeFixtureSource(camera_interval=60.0),
            )
            world_model.step()
            snapshot = world_model.spatial_map.snapshot()
            self.assertEqual(snapshot["frames_integrated"], 1)
            self.assertEqual(snapshot["voxel_count"], 1)
            self.assertEqual(world_model._last_spatial_map_update["source"], "test_fixture_range_sensor")


if __name__ == "__main__":
    unittest.main()
