"""Offline fault injection for the real-robot HTTP adapter.

No network connection or physical hardware is used. These tests mock the
protocol boundary and assert that a failed sensor link cannot send commands.
"""
import time
import unittest
from unittest.mock import patch

from body_runtime_host.worldmodel.sources import RobotHttpSource
from body_runtime_host.worldmodel.types import Action


def sensors(timestamp=None):
    return {
        "position": [0.0, 0.0, 0.0],
        "orientation": 0.0,
        "objects": [],
        "timestamp": time.time() if timestamp is None else timestamp,
    }


class RobotHttpFaultInjectionTests(unittest.TestCase):
    def setUp(self):
        self.robot = RobotHttpSource("http://127.0.0.1:65534", actuation_enabled=True)
        self.action = Action(type="forward")

    def test_network_outage_after_successful_poll_blocks_actuation(self):
        calls = []

        def fake_http(method, url, **kwargs):
            calls.append((method, url))
            if method == "GET" and len(calls) == 1:
                return sensors()
            raise OSError("simulated sensor outage")

        with patch("body_runtime_host.worldmodel.sources._http_json", side_effect=fake_http):
            self.robot.observe()
            _, outcome = self.robot.execute_authorized(self.action)
        self.assertEqual(outcome.kind, "failure")
        self.assertFalse(any(method == "POST" for method, _ in calls))

    def test_stale_sensor_frame_blocks_actuation(self):
        calls = []

        def fake_http(method, url, **kwargs):
            calls.append(method)
            if method == "GET":
                return sensors(timestamp=time.time() - 30)
            raise AssertionError("stale geometry must not actuate")

        with patch("body_runtime_host.worldmodel.sources._http_json", side_effect=fake_http):
            _, outcome = self.robot.execute_authorized(self.action)
        self.assertEqual(outcome.kind, "failure")
        self.assertNotIn("POST", calls)

    def test_future_sensor_frame_blocks_actuation(self):
        calls = []

        def fake_http(method, url, **kwargs):
            calls.append(method)
            if method == "GET":
                return sensors(timestamp=time.time() + 30)
            raise AssertionError("future-dated geometry must not actuate")

        with patch("body_runtime_host.worldmodel.sources._http_json", side_effect=fake_http):
            _, outcome = self.robot.execute_authorized(self.action)
        self.assertEqual(outcome.kind, "failure")
        self.assertNotIn("POST", calls)

    def test_zero_robot_timestamp_blocks_actuation(self):
        with patch("body_runtime_host.worldmodel.sources._http_json", return_value=sensors(timestamp=0)) as transport:
            _, outcome = self.robot.execute_authorized(self.action)
        self.assertEqual(outcome.kind, "failure")
        self.assertFalse(any(call.args[0] == "POST" for call in transport.call_args_list))

    def test_missing_robot_timestamp_blocks_actuation(self):
        payload = sensors()
        payload.pop("timestamp")
        with patch("body_runtime_host.worldmodel.sources._http_json", return_value=payload) as transport:
            _, outcome = self.robot.execute_authorized(self.action)
        self.assertEqual(outcome.kind, "failure")
        self.assertFalse(any(call.args[0] == "POST" for call in transport.call_args_list))

    def test_disabled_actuation_never_posts(self):
        self.robot.actuation_enabled = False
        with patch("body_runtime_host.worldmodel.sources._http_json", return_value=sensors()) as transport:
            _, outcome = self.robot.execute_authorized(self.action)
        self.assertEqual(outcome.kind, "neutral")
        self.assertFalse(any(call.args[0] == "POST" for call in transport.call_args_list))


if __name__ == "__main__":
    unittest.main()
