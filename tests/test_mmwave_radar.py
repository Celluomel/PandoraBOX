import unittest
import struct
import time


class MmWaveRadarTest(unittest.TestCase):
    def test_ld2450_frame_decodes_signed_metric_target(self):
        from body_runtime_host.mmwave_radar import parse_ld2450_frame

        frame = bytearray(b"\xaa\xff\x03\x00")
        frame.extend(struct.pack("<HHHH", 0x8019, 0x84b0, 0x801e, 360))
        frame.extend(bytes(16))
        frame.extend(b"\x55\xcc")
        decoded = parse_ld2450_frame(bytes(frame), timestamp=12.5, sequence=7)

        self.assertEqual(len(decoded.targets), 1)
        self.assertEqual(decoded.targets[0].position_m, [0.025, 1.2, 0.0])
        self.assertAlmostEqual(decoded.targets[0].radial_speed_mps, 0.3)
        self.assertEqual(decoded.targets[0].classification, "moving_target")
        self.assertEqual(decoded.sequence, 7)

    def test_ld2450_source_frames_sensor_timeouts_without_fabricating_targets(self):
        from body_runtime_host.mmwave_radar import LD2450SerialSource

        class Port:
            in_waiting = 0
            def read(self, count):
                return b""
            def close(self):
                pass

        source = LD2450SerialSource(
            timeout=0.05, serial_factory=lambda *args, **kwargs: Port()
        )
        with self.assertRaises(TimeoutError):
            source.read()
        self.assertIn("no complete LD2450 frame", source.status()["last_error"])

    def test_mmwave_adapter_augments_primary_observation(self):
        from types import SimpleNamespace
        from body_runtime_host.mmwave_radar import MmWaveAugmentedSource, MmWaveFrame

        class Primary:
            name = "robot"
            def observe(self):
                return SimpleNamespace(modalities={"camera": {"source": "body"}})
            def status(self):
                return {"source": self.name}

        class Radar:
            name = "test_radar"
            def read(self):
                return MmWaveFrame(timestamp=time.time()).as_dict()
            def status(self):
                return {"available": True}

        source = MmWaveAugmentedSource(Primary(), Radar())
        observation = source.observe()
        self.assertIn("camera", observation.modalities)
        self.assertEqual(observation.modalities["mmwave_radar"]["source"], "test_radar")
        self.assertTrue(source.status()["mmwave_radar"]["available"])

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
