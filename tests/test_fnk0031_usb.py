import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from body_runtime_host.fnk0031_usb import (
    FNK0031CustomUSBSource,
    FNK0031USBSource,
    FRAME_END,
    FRAME_START,
    ORDER_DONE,
    ORDER_ECHO_REQUEST,
    ORDER_ECHO_RESPONSE,
    ORDER_STARTED,
    ORDER_VOLTAGE_REQUEST,
    ORDER_VOLTAGE_RESPONSE,
    SERIAL_STARTUP_SETTLE_SECONDS,
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


class FakeHardwareSerial(FakeSerial):
    def __init__(self, port, baudrate, timeout, write_timeout):
        super().__init__(port, baudrate, timeout, write_timeout)
        self.is_open = False
        self.dtr = True

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False


class FakeCustomSerial:
    def __init__(self, port, baudrate, timeout, write_timeout):
        self.buffer = bytearray()
        self.writes = []
        self.z = [0.0] * 6

    def reset_input_buffer(self):
        self.buffer.clear()

    def write(self, data):
        line = bytes(data).decode("ascii").strip()
        self.writes.append(line)
        if line == "PING":
            self.buffer.extend(b"PONG FNK0031_NAV_V2\n")
        elif line.startswith("CMD leg "):
            _, _, leg_text, delta_text = line.split()
            leg = int(leg_text)
            self.buffer.extend(f"STARTED leg {leg}\n".encode())
            self.z[leg - 1] += float(delta_text)
            self.buffer.extend(f"DONE leg {leg}\n".encode())
        elif line == "CMD state":
            values = " ".join(
                str(value)
                for index, z in enumerate(self.z)
                for value in (index, index + 1, z, 10 + index, 20 + index, 30 + index)
            )
            self.buffer.extend(f"STATE 123 {values}\n".encode())
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

    def test_real_serial_open_waits_for_fnhr_controller_startup(self):
        connection = FakeHardwareSerial(None, 115200, 0.1, 5)
        serial_module = SimpleNamespace(Serial=lambda *args, **kwargs: connection)
        source = FNK0031USBSource("/dev/test-fnk0031-startup")
        with patch.dict("sys.modules", {"serial": serial_module}), patch(
            "body_runtime_host.fnk0031_usb.time.sleep"
        ) as sleep:
            with source._open() as opened:
                self.assertIs(opened, connection)
                self.assertTrue(opened.is_open)
                self.assertFalse(opened.dtr)
            sleep.assert_called_once_with(SERIAL_STARTUP_SETTLE_SECONDS)
        connection.close()

    def test_observation_reports_stock_protocol_and_no_fabricated_pose(self):
        source = FNK0031USBSource("/dev/ttyUSB0", serial_factory=self.factory)
        observation = source.observe()
        self.assertEqual(observation.source, "fnk0031_usb")
        self.assertEqual(observation.value["protocol"], "fnhr_framed_serial")
        self.assertEqual(observation.value["supply_voltage_v"], 7.68)
        self.assertFalse(observation.value["pose_available"])
        self.assertEqual(observation.value["controller_model"], "Freenove Crawling Robot Controller V3.2")
        status = source.status()
        self.assertFalse(status["continuous_cmd_vel"])
        self.assertEqual(status["control_mode"], "blocking_gait_actions")
        self.assertIn("not an emergency stop", status["stop_behavior"])
        self.assertIn("RF remote", observation.text)

    def test_custom_controller_profile_uses_ascii_handshake_and_crawl(self):
        connections = []

        def custom_factory(*args, **kwargs):
            connection = FakeSerial(*args, **kwargs)
            original_write = connection.write

            def write(data):
                data = bytes(data)
                connection.writes.append(data)
                command = data.decode("ascii").strip()
                if command == "PING":
                    connection.buffer.extend(b"PONG FNK0031_NAV_V2\n")
                elif command == "CMD state":
                    values = " ".join(str(value) for leg in range(6)
                                      for value in (leg, leg + 1, leg + 2, 10 + leg, 20 + leg, 30 + leg))
                    connection.buffer.extend(f"STATE 1234 {values}\n".encode())
                elif command.startswith("CMD crawl "):
                    connection.buffer.extend(b"STARTED crawl\nDONE crawl\n")
                elif command == "CMD stop":
                    connection.buffer.extend(b"DONE stop\n")
                else:
                    action = command.removeprefix("CMD ")
                    connection.buffer.extend(f"STARTED {action}\nDONE {action}\n".encode())
                return len(data)

            connection.write = write
            connections.append(connection)
            return connection

        source = FNK0031CustomUSBSource(
            "COM8", actuation_enabled=True, serial_factory=custom_factory,
        )
        self.assertTrue(source.ping())
        _, outcome = source.execute_authorized(Action(type="crawl", params={"x": 12, "y": -3, "angle": 4}))
        self.assertEqual(outcome.kind, "success")
        self.assertIn(b"CMD crawl 12.000 -3.000 4.000\n", connections[0].writes)
        self.assertFalse(source.status()["continuous_cmd_vel"])
        self.assertFalse(source.status()["remote_preserved"])

    def test_custom_state_parser_labels_six_leg_values_as_estimates(self):
        values = " ".join(str(value) for leg in range(6)
                          for value in (leg, leg + 1, leg + 2, 10 + leg, 20 + leg, 30 + leg))
        state = FNK0031CustomUSBSource._parse_estimated_state(f"STATE 1234 {values}")
        self.assertEqual(state["source"], "fnhr_internal_command_estimate")
        self.assertFalse(state["measured_feedback"])
        self.assertEqual(state["board_uptime_ms"], 1234)
        self.assertEqual(len(state["legs"]), 6)
        self.assertEqual(state["legs"][0]["foot_position_mm"], [0.0, 1.0, 2.0])
        self.assertEqual(state["legs"][5]["joint_angles_deg"], [15.0, 25.0, 35.0])

    def test_custom_board_leg_test_is_acknowledged_and_reads_updated_estimate(self):
        connection = FakeCustomSerial("COM-LEG", 115200, 0.1, 5)
        source = FNK0031CustomUSBSource(
            "COM-LEG", actuation_enabled=False,
            serial_factory=lambda *args, **kwargs: connection,
        )
        state = source.execute_leg_test(2, 5)
        self.assertEqual(connection.writes, ["CMD leg 2 5", "CMD state"])
        self.assertEqual(state["legs"][1]["foot_position_mm"][2], 5.0)
        self.assertFalse(state["measured_feedback"])

    def test_custom_board_leg_test_rejects_large_or_invalid_moves_before_serial(self):
        connection = FakeCustomSerial("COM-LEG-INVALID", 115200, 0.1, 5)
        source = FNK0031CustomUSBSource(
            "COM-LEG-INVALID", serial_factory=lambda *args, **kwargs: connection,
        )
        for leg, delta in ((0, 5), (7, 5), (True, 5), (1, 6), (1, -6)):
            with self.subTest(leg=leg, delta=delta), self.assertRaises(ValueError):
                source.execute_leg_test(leg, delta)
        self.assertEqual(connection.writes, [])

    def test_body_leg_test_requires_board_only_confirmation_and_reports_readback(self):
        from body_runtime_host.runtime import BodyHost

        host = BodyHost()
        host.fnk0031_settings = lambda: {
            "platform": "usb_serial_custom", "serial_port": "COM-TEST", "timeout": 2.0,
        }
        before = FNK0031CustomUSBSource._parse_estimated_state(
            "STATE 1 " + " ".join(str(value) for leg in range(6)
                                   for value in (0, 0, 0, 0, 0, 0))
        )
        after_values = [0.0] * 36
        after_values[2] = 5.0
        after = FNK0031CustomUSBSource._parse_estimated_state(
            "STATE 2 " + " ".join(str(value) for value in after_values)
        )
        with patch("body_runtime_host.fnk0031_usb.FNK0031CustomUSBSource") as source_type:
            source = source_type.return_value
            source.ping.return_value = True
            source.read_estimated_leg_state.side_effect = [before]
            source.execute_leg_test.return_value = after
            with self.assertRaises(ValueError):
                host.fnk0031_leg_test({"leg": 1, "direction": "lift"})
            result = host.fnk0031_leg_test({
                "leg": 1, "direction": "lift", "board_only_confirmed": True,
            })
        source.execute_leg_test.assert_called_once_with(1, 5)
        self.assertTrue(result["acknowledged"])
        self.assertEqual(result["ack"], "DONE leg 1")
        self.assertEqual(result["reported_delta_z_mm"], 5.0)

    def test_custom_controller_rejects_unbounded_crawl_before_motion(self):
        source = FNK0031CustomUSBSource("COM9", actuation_enabled=True, serial_factory=self.factory)
        _, outcome = source.execute_authorized(Action(type="crawl", params={"x": 43, "y": 0, "angle": 0}))
        self.assertEqual(outcome.kind, "failure")
        self.assertTrue(all(write == b"PING\n" for write in self.connections[0].writes))

    def test_source_resolver_selects_opt_in_custom_firmware_by_platform(self):
        from body_runtime_host.worldmodel.sources import resolve_source

        source = resolve_source({
            "BODY_PLUGIN_ROBOT_ENABLED": True,
            "FNK0031_PLATFORM": "usb_serial_custom",
            "FNK0031_SERIAL_PORT": "COM10",
            "FNK0031_ACTUATION_ENABLED": False,
        })
        self.assertIsInstance(source, FNK0031CustomUSBSource)
        self.assertFalse(source.actuation_enabled)

    def test_body_runtime_keeps_custom_usb_robot_selected_in_sim_default_mode(self):
        from body_runtime_host.runtime import BodyHost

        host = BodyHost()
        host.config = {
            "BODY_PLUGIN_ROBOT_ENABLED": True,
            "FNK0031_PLATFORM": "usb_serial_custom",
            "FNK0031_SERIAL_PORT": "COM10",
            "FNK0031_ACTUATION_ENABLED": False,
        }
        with patch("body_runtime_host.runtime.ROOT", Path("Z:/missing-body-test-root")):
            source = host._resolve_worldmodel_source()
        self.assertIsInstance(source, FNK0031CustomUSBSource)
        self.assertEqual(source.port, "COM10")

    def test_custom_usb_health_and_estimated_state_are_forwarded_to_brain(self):
        from body_runtime_host.runtime import BodyHost

        host = BodyHost()
        host.config = {
            "BODY_PLUGIN_ROBOT_ENABLED": True,
            "FNK0031_PLATFORM": "usb_serial_custom",
            "FNK0031_SERIAL_PORT": "COM10",
            "FNK0031_ACTUATION_ENABLED": False,
            "FNK0031_POLL_INTERVAL": 1,
        }
        estimate = {"source": "fnhr_internal_command_estimate", "measured_feedback": False, "legs": []}
        host.fnk0031_usb_status = lambda: {
            "connected": True,
            "configured_port": "COM10",
            "protocol": "custom_fnhr_ascii_v2",
            "firmware_profile": "custom_fnhr_ascii_v2",
            "transport": "USB serial / custom FNHR ASCII controller",
            "actuation_enabled": False,
            "pose_available": False,
            "estimated_leg_state": estimate,
            "estimated_state_is_measured": False,
            "supported_actions": ["crawl", "stop"],
            "remote_preserved": False,
        }

        self.assertTrue(host.publish_fnk0031_usb_status())
        value = host._bridge_latest["robot.fnk0031.usb_status"]["observation"]["value"]
        self.assertEqual(value["protocol"], "custom_fnhr_ascii_v2")
        self.assertEqual(value["estimated_leg_state"], estimate)
        self.assertFalse(value["estimated_state_is_measured"])
        self.assertFalse(value["actuation_enabled"])
        self.assertIn("not servo feedback or odometry",
                      host._bridge_latest["robot.fnk0031.usb_status"]["observation"]["provenance"]["state_semantics"])

    def test_body_runtime_routes_approved_command_into_worldmodel(self):
        from body_runtime_host.runtime import BodyHost

        host = BodyHost()
        received = []

        def execute_external(action):
            received.append(action)
            return {"outcome": {"kind": "success", "description": "test acknowledgement"}}

        host._worldmodel = SimpleNamespace(execute_external=execute_external)
        result = host.execute_command({
            "command_id": "fnk-approved-test",
            "status": "approved",
            "action": "crawl",
            "target": "fnk0031",
            "payload": {"params": {"x": 12, "y": -3, "angle": 4}},
        })
        self.assertEqual(result["status"], "executed")
        self.assertEqual(received[0].type, "crawl")
        self.assertEqual(received[0].params, {"x": 12, "y": -3, "angle": 4})

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

    def test_usb_health_is_forwarded_to_brain_without_enabling_actuation(self):
        from body_runtime_host.runtime import BodyHost

        host = BodyHost()
        host.config = {
            "BODY_PLUGIN_ROBOT_ENABLED": True,
            "FNK0031_PLATFORM": "usb_serial",
            "FNK0031_SERIAL_PORT": "/dev/ttyUSB0",
            "FNK0031_ACTUATION_ENABLED": False,
            "FNK0031_POLL_INTERVAL": 5,
        }
        host.fnk0031_usb_status = lambda: {
            "connected": False,
            "configured_port": "/dev/ttyUSB0",
            "protocol": "fnhr_framed_serial",
            "transport": "USB serial / stock FNHR framed protocol",
            "actuation_enabled": False,
            "pose_available": False,
            "supply_voltage_v": None,
            "last_error": "read-only echo timeout",
            "supported_actions": ["forward"],
            "unsupported_actions": ["set_action_speed"],
            "remote_preserved": True,
        }

        self.assertTrue(host.publish_fnk0031_usb_status())
        message = host._bridge_latest["robot.fnk0031.usb_status"]
        value = message["observation"]["value"]
        self.assertFalse(value["connected"])
        self.assertFalse(value["actuation_enabled"])
        self.assertEqual(value["port"], "/dev/ttyUSB0")
        self.assertEqual(value["last_error"], "read-only echo timeout")
        self.assertFalse(host.publish_fnk0031_usb_status())


if __name__ == "__main__":
    unittest.main()
