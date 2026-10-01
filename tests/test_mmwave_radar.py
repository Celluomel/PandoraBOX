import unittest


class MmWaveRadarTest(unittest.TestCase):
    def test_payload_is_normalized_to_metric_targets(self):
        from body_runtime_host.mmwave_radar import frame_from_payload

        frame = frame_from_payload({
            "timestamp": 12.5,
            "frame": "body",
            "sequence": 4,
            "quality": 0.8,
            "detections": [{"id": "person-1", "x": 1, "y": 2, "z": 0.5,
                            "vx": 0.2, "vy": -0.1, "confidence": 0.9,
                            "class": "person"}],
        }, source="ti_iwr6843")

        self.assertEqual(frame.source, "ti_iwr6843")
        self.assertEqual(frame.targets[0].position_m, [1.0, 2.0, 0.5])
        self.assertEqual(frame.targets[0].velocity_mps, [0.2, -0.1, 0.0])
        self.assertEqual(frame.targets[0].classification, "person")

    def test_simulated_radar_is_independent_of_aqara(self):
        from body_runtime_host.worldmodel.sim_world import SimulatedRoom
        from body_runtime_host.worldmodel.sources import SimRobotSource

        source = SimRobotSource(camera_interval=60.0, mmwave_enabled=True)
        observation = source.observe()
        radar = observation.modalities["mmwave_radar"]

        self.assertEqual(radar["source"], "mmwave_radar")
        self.assertEqual(radar["frame"], "local_map")
        self.assertEqual(len(radar["targets"]), len(observation.scene))
        self.assertNotIn("aqara", radar["source"].lower())

    def test_radar_can_be_disabled_without_removing_other_modalities(self):
        from body_runtime_host.worldmodel.sources import SimRobotSource

        observation = SimRobotSource(camera_interval=60.0, mmwave_enabled=False).observe()
        self.assertNotIn("mmwave_radar", observation.modalities)
        self.assertIn("lidar", observation.modalities)


if __name__ == "__main__":
    unittest.main()
