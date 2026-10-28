"""Loopback-only HTTP integration test for the robot protocol.

Starts an in-process fake robot server on 127.0.0.1. Never connects to
VENTUNO, any external network, or real actuators.
"""
import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from body_runtime_host.worldmodel.sources import RobotHttpSource
from body_runtime_host.worldmodel.types import Action


class FakeRobot(BaseHTTPRequestHandler):
    sensor_failure = False
    posts = 0

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path != "/sensors":
            self.send_error(404)
            return
        if type(self).sensor_failure:
            self.send_error(503)
            return
        data = {"timestamp": time.time(), "position": [0, 0, 0],
                "orientation": 0, "objects": [], "capabilities": {"speed": 0.3}}
        encoded = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self):
        if self.path != "/command":
            self.send_error(404)
            return
        type(self).posts += 1
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        if payload.get("type") != "forward":
            self.send_error(400)
            return
        encoded = json.dumps({"outcome": "success", "description": "fake controller ACK"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class RobotHttpLoopbackTests(unittest.TestCase):
    def setUp(self):
        FakeRobot.sensor_failure = False
        FakeRobot.posts = 0
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeRobot)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.robot = RobotHttpSource(
            f"http://127.0.0.1:{self.server.server_port}",
            timeout=1.5, actuation_enabled=False,
        )

    def test_disabled_actuation_does_not_post(self):
        _, outcome = self.robot.execute_authorized(Action(type="forward"))
        self.assertEqual(outcome.kind, "neutral")
        self.assertEqual(FakeRobot.posts, 0)

    def test_successful_fake_controller_ack(self):
        self.robot.actuation_enabled = True
        _, outcome = self.robot.execute_authorized(Action(type="forward"))
        self.assertEqual(outcome.kind, "success")
        self.assertEqual(FakeRobot.posts, 1)
        # Adapter success is only a fake controller ACK, not proof of motion.

    def test_sensor_outage_blocks_post(self):
        self.robot.actuation_enabled = True
        FakeRobot.sensor_failure = True
        _, outcome = self.robot.execute_authorized(Action(type="forward"))
        self.assertEqual(outcome.kind, "failure")
        self.assertEqual(FakeRobot.posts, 0)


if __name__ == "__main__":
    unittest.main()
