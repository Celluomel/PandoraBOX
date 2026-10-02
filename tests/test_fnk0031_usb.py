import unittest

from body_runtime_host.fnk0031_usb import FNK0031USBSource
from body_runtime_host.worldmodel.types import Action


class FakeSerial:
    def __init__(self, port, baudrate, timeout, write_timeout):
        self.buffer = bytearray()
        self.writes = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def reset_input_buffer(self):
        self.buffer.clear()

    def write(self, data):
        self.writes.append(bytes(data))
        order = data[1]
        replies = {
            0: (1,),
            10: (11, 9, 48),  # 12.00 V in the FNHR base-128 encoding
            92: (21, 23),
            80: (21,),
            82: (21,),
            88: (21,),
            90: (21,),
            94: (21,),
        }
        if order in {80, 82, 88, 90, 94}:
            replies = {**replies, order: (21, 23)}
        response = replies.get(order, ())
        if order == 10:
            self.buffer.extend((128, *response, 129))
        else:
            for item in response:
                self.buffer.extend((128, item, 129))
        return len(data)

    def flush(self):
        pass

    def read(self, size=1):
        if not self.buffer:
            return b""
        value = self.buffer[0]
        del self.buffer[0]
        return bytes((value,))


class FNK0031USBSourceTests(unittest.TestCase):
    def setUp(self):
        self.connections = []

        def factory(*args, **kwargs):
            connection = FakeSerial(*args, **kwargs)
            self.connections.append(connection)
            return connection

        self.factory = factory

    def test_echo_and_voltage_observation_use_fnhr_frames(self):
        source = FNK0031USBSource("/dev/ttyACM0", serial_factory=self.factory)
        self.assertTrue(source.ping())
        observation = source.observe()
        self.assertEqual(observation.source, "fnk0031_usb")
        self.assertAlmostEqual(observation.value["supply_voltage_v"], 12.0)
        self.assertIn("not measured", observation.text)
        self.assertEqual(self.connections[0].writes, [bytes((128, 0, 129)), bytes((128, 10, 129))])

    def test_authorized_forward_emits_firmware_order_and_reports_unverified_motion(self):
        source = FNK0031USBSource("COM5", actuation_enabled=True, serial_factory=self.factory)
        _, outcome = source.execute_authorized(Action(type="forward"))
        self.assertEqual(outcome.kind, "success")
        self.assertIn("displacement is unverified", outcome.description)
        self.assertEqual(self.connections[0].writes, [
            bytes((128, 92, 129)), bytes((128, 80, 129)), bytes((128, 10, 129)),
        ])

    def test_actuation_gate_and_unsupported_gripper_actions_do_not_send_motion(self):
        gated_source = FNK0031USBSource("COM5", actuation_enabled=False, serial_factory=self.factory)
        _, gated = gated_source.execute_authorized(Action(type="forward"))
        self.assertEqual(gated.kind, "neutral")
        source = FNK0031USBSource("COM5", actuation_enabled=True, serial_factory=self.factory)
        _, unsupported = source.execute_authorized(Action(type="grab"))
        self.assertEqual(unsupported.kind, "failure")
        self.assertIn("does not support", unsupported.description)
        self.assertTrue(all(all(write[1] != 80 for write in connection.writes) for connection in self.connections))

    def test_no_pose_or_gripper_is_fabricated_for_stock_firmware(self):
        source = FNK0031USBSource("COM5", serial_factory=self.factory)
        body = source.body_state()
        self.assertEqual(body.position_source, "unavailable")
        self.assertFalse(body.posture["pose_available"])
        self.assertEqual(body.capabilities["gripper"], 0.0)

    def test_source_resolver_selects_usb_without_gateway_url(self):
        from body_runtime_host.worldmodel import resolve_source

        source = resolve_source({
            "BODY_PLUGIN_ROBOT_ENABLED": True,
            "FNK0031_PLATFORM": "usb_serial",
            "FNK0031_SERIAL_PORT": "/dev/ttyACM0",
            "FNK0031_ACTUATION_ENABLED": False,
        })
        self.assertEqual(source.name, "fnk0031_usb")
        self.assertEqual(source.port, "/dev/ttyACM0")
        self.assertFalse(source.actuation_enabled)


if __name__ == "__main__":
    unittest.main()
