import unittest

from body_runtime_host.fnk0031_usb import (
    FNK0031USBSource,
    FRAME_END,
    FRAME_START,
    ORDER_DONE,
    ORDER_ECHO_REQUEST,
    ORDER_ECHO_RESPONSE,
    ORDER_STARTED,
    ORDER_VOLTAGE_REQUEST,
    ORDER_VOLTAGE_RESPONSE,
)
from body_runtime_host.worldmodel.types import Action


def frame(order, *payload):
    return bytes((FRAME_START, order, *payload, FRAME_END))


class FakeSerial:
    def __init__(self, port, baudrate, timeout, write_timeout):
        self.buffer = bytearray()
        self.writes = []

    def reset_input_buffer(self):
        self.buffer.clear()

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        order = data[1]
        if order == ORDER_ECHO_REQUEST:
            self.buffer.extend(frame(ORDER_ECHO_RESPONSE))
        elif order == ORDER_VOLTAGE_REQUEST:
            # 7.68 V encoded as (voltage * 100) split into base-128 bytes.
            self.buffer.extend(frame(ORDER_VOLTAGE_RESPONSE, 6, 0))
        elif order == 30:
            self.buffer.extend(frame(ORDER_DONE))
        elif 64 <= order <= 127:
            self.buffer.extend(frame(ORDER_STARTED))
            self.buffer.extend(frame(ORDER_DONE))
        return len(data)

    def flush(self):
        pass

    def read(self, size=1):
        if not self.buffer:
            return b""
        value = bytes(self.buffer[:size])
        del self.buffer[:size]
        return value


class FNK0031USBSourceTests(unittest.TestCase):
    def setUp(self):
        self.connections = []

        def factory(*args, **kwargs):
            connection = FakeSerial(*args, **kwargs)
            self.connections.append(connection)
            return connection

        self.factory = factory

    def test_native_echo_and_voltage_use_fnhr_framing(self):
        source = FNK0031USBSource("/dev/ttyUSB0", serial_factory=self.factory)
        self.assertTrue(source.ping())
        self.assertEqual(source.read_supply_voltage(), 7.68)
        self.assertEqual(
            self.connections[0].writes,
            [frame(ORDER_ECHO_REQUEST), frame(ORDER_VOLTAGE_REQUEST)],
        )

    def test_observation_reports_stock_protocol_and_no_fabricated_pose(self):
        source = FNK0031USBSource("/dev/ttyUSB0", serial_factory=self.factory)
        observation = source.observe()
        self.assertEqual(observation.source, "fnk0031_usb")
        self.assertEqual(observation.value["protocol"], "fnhr_framed_serial")
        self.assertEqual(observation.value["supply_voltage_v"], 7.68)
        self.assertFalse(observation.value["pose_available"])
        self.assertIn("RF remote", observation.text)

    def test_actuation_gate_prevents_any_motion_frame_by_default(self):
        source = FNK0031USBSource("COM5", actuation_enabled=False, serial_factory=self.factory)
        _, outcome = source.execute_authorized(Action(type="forward"))
        self.assertEqual(outcome.kind, "neutral")
        self.assertTrue(all(write[1] in (ORDER_ECHO_REQUEST, ORDER_VOLTAGE_REQUEST)
                            for write in self.connections[0].writes))

    def test_authorized_high_level_action_uses_native_order_and_start_done(self):
        source = FNK0031USBSource("COM5", actuation_enabled=True, serial_factory=self.factory)
        _, outcome = source.execute_authorized(Action(type="forward"))
        self.assertEqual(outcome.kind, "success")
        self.assertIn("displacement is unverified", outcome.description)
        self.assertEqual(self.connections[0].writes[0], frame(80))
        self.assertEqual(self.connections[0].writes[1], frame(ORDER_ECHO_REQUEST))

    def test_parameterized_fnhr_movements_encode_arguments(self):
        cases = (
            ("active_mode", {}, frame(92)),
            ("sleep_mode", {}, frame(94)),
            ("switch_mode", {}, frame(96)),
            ("crawl_forward", {}, frame(80)),
            ("crawl_backward", {}, frame(82)),
            ("crawl_left", {}, frame(84)),
            ("crawl_right", {}, frame(86)),
            ("turn_left", {}, frame(88)),
            ("turn_right", {}, frame(90)),
            ("crawl", {"x": 1, "y": -2, "angle": 3}, frame(110, 65, 62, 67)),
            ("change_body_height", {"height": 4}, frame(112, 68)),
            ("move_body", {"x": 1, "y": 2, "z": 3}, frame(114, 65, 66, 67)),
            ("rotate_body", {"x": -1, "y": 0, "z": 1}, frame(116, 63, 64, 65)),
            ("twist_body", {"x_move": 1, "y_move": 2, "z_move": 3,
                             "x_rotate": -1, "y_rotate": -2, "z_rotate": -3},
             frame(118, 65, 66, 67, 63, 62, 61)),
            ("leg_move_to_relatively", {"leg": 6, "x": 1, "y": 0, "z": -1},
             frame(30, 6, 65, 64, 63)),
        )
        for index, (action_type, params, expected) in enumerate(cases):
            with self.subTest(action=action_type):
                source = FNK0031USBSource(f"COM{100 + index}", actuation_enabled=True, serial_factory=self.factory)
                _, outcome = source.execute_authorized(Action(type=action_type, params=params))
                self.assertEqual(outcome.kind, "success")
                self.assertEqual(self.connections[-1].writes[0], expected)

    def test_parameter_validation_and_unexposed_settings_fail_without_motion(self):
        cases = (
            ("crawl", {"x": 64, "y": 0, "angle": 0}),
            ("leg_move_to_relatively", {"leg": 0, "x": 0, "y": 0, "z": 0}),
            ("set_action_speed", {"speed": 50}),
            ("set_action_group", {"group": 1}),
        )
        for index, (action_type, params) in enumerate(cases):
            with self.subTest(action=action_type):
                source = FNK0031USBSource(f"COM{200 + index}", actuation_enabled=True, serial_factory=self.factory)
                _, outcome = source.execute_authorized(Action(type=action_type, params=params))
                self.assertEqual(outcome.kind, "failure")
                self.assertTrue(all(write[1] in (ORDER_ECHO_REQUEST, ORDER_VOLTAGE_REQUEST)
                                    for connection in self.connections for write in connection.writes))

    def test_wait_and_unsupported_manipulation_do_not_send_motion(self):
        source = FNK0031USBSource("COM5", actuation_enabled=True, serial_factory=self.factory)
        _, waiting = source.execute_authorized(Action(type="wait"))
        _, unsupported = source.execute_authorized(Action(type="grab"))
        self.assertEqual(waiting.kind, "neutral")
        self.assertEqual(unsupported.kind, "failure")
        self.assertTrue(all(write[1] in (ORDER_ECHO_REQUEST, ORDER_VOLTAGE_REQUEST)
                            for connection in self.connections for write in connection.writes))

    def test_stock_fnhr_remote_support_is_not_replaced_by_custom_sketch(self):
        source = FNK0031USBSource("COM5", serial_factory=self.factory)
        self.assertTrue(source.status()["remote_preserved"])

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
            "FNK0031_SERIAL_PORT": "/dev/ttyUSB0",
            "FNK0031_ACTUATION_ENABLED": False,
        })
        self.assertEqual(source.name, "fnk0031_usb")
        self.assertEqual(source.port, "/dev/ttyUSB0")
        self.assertFalse(source.actuation_enabled)


if __name__ == "__main__":
    unittest.main()
