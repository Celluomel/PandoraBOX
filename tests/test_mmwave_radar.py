import unittest
import struct
import time


class MmWaveRadarTest(unittest.TestCase):
    def test_body_radar_status_reads_live_source_without_worldmodel_observation(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from body_runtime_host.runtime import BodyHost
        from body_runtime_host.mmwave_radar import MmWaveFrame, MmWaveTarget

        class Radar:
            def read(self):
                return MmWaveFrame(
                    timestamp=time.time(), sequence=12,
                    targets=[MmWaveTarget("1", [0.2, 1.4, 0.0])],
                )
            def status(self):
                return {"available": True, "sequence": 12}

        host = BodyHost.__new__(BodyHost)
        host.config = {
            "BODY_PLUGIN_MMWAVE_RADAR_ENABLED": True,
            "MMWAVE_RADAR_PROTOCOL": "ventuno_bridge_ld2450",
            "MMWAVE_RADAR_BAUDRATE": 256000,
        }
        host._worldmodel = SimpleNamespace(source=SimpleNamespace(radar=Radar()))
        with patch.object(host, "serial_device_inventory", return_value={"devices": []}):
            result = host.mmwave_radar_status()

        self.assertTrue(result["available"])
        self.assertEqual(result["sample"]["sequence"], 12)
        self.assertEqual(result["sample"]["targets"][0]["position_m"], [0.2, 1.4, 0.0])

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

    def test_ventuno_bridge_source_reads_latest_local_rpc_frame(self):
        from body_runtime_host.mmwave_radar import VentunoBridgeMmWaveSource

        class Bridge:
            def __init__(self):
                self.connected = False
            def connect(self, timeout):
                self.connected = True
                return True
            def call(self, method, timeout):
                self.asserted = (method, timeout)
                return '{"available":true,"frame":"body","sequence":9,"targets":[{"id":1,"x":0.4,"y":1.2,"z":0,"vx":0,"vy":0,"vz":0,"radial_speed_mps":0.2}]}'

        bridge = Bridge()
        source = VentunoBridgeMmWaveSource(bridge_factory=lambda: bridge)
        frame = source.read()

        self.assertEqual(bridge.asserted, ("body_ld2450_read", 0.5))
        self.assertEqual(frame.sequence, 9)
        self.assertEqual(frame.source, "hlk_ld2450_ventuno_bridge")
        self.assertEqual(frame.targets[0].position_m, [0.4, 1.2, 0.0])
        self.assertEqual(source.status()["transport"], "local_arduino_router_rpc")
        self.assertTrue(source.status()["available"])
        self.assertEqual(source.status()["sequence"], 9)

    def test_ventuno_bridge_source_invalidates_status_and_reconnects_after_rpc_error(self):
        from body_runtime_host.mmwave_radar import VentunoBridgeMmWaveSource

        class Bridge:
            def __init__(self, fails=False):
                self.fails = fails
            def connect(self, timeout):
                return True
            def call(self, method, timeout):
                if self.fails:
                    raise ConnectionError("router socket reset")
                return '{"available":true,"sequence":10,"targets":[]}'

        clients = [Bridge(fails=True), Bridge()]
        source = VentunoBridgeMmWaveSource(bridge_factory=lambda: clients.pop(0))
        with self.assertRaisesRegex(ConnectionError, "router socket reset"):
            source.read()
        self.assertFalse(source.status()["available"])

        frame = source.read()
        self.assertEqual(frame.sequence, 10)
        self.assertTrue(source.status()["available"])

    def test_ventuno_bridge_source_reports_stale_frame_without_fake_obstacle(self):
        from body_runtime_host.mmwave_radar import VentunoBridgeMmWaveSource

        class Bridge:
            def connect(self, timeout):
                return True
            def call(self, method, timeout):
                return '{"available":false,"targets":[],"error":"stale_or_missing_frame"}'

        source = VentunoBridgeMmWaveSource(bridge_factory=Bridge)
        with self.assertRaisesRegex(TimeoutError, "stale_or_missing_frame"):
            source.read()
        self.assertIn("stale_or_missing_frame", source.status()["last_error"])

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
