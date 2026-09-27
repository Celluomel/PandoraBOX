"""Simulated robot — implements the Lumina robot protocol over HTTP.

This is the "robot" you plug the Body into when no physical robot is present.
It wraps the ``SimulatedRoom`` sandbox and exposes exactly the endpoints a
real robot would:

    GET  /health
    GET  /sensors   -> body pose + scene + capabilities
    POST /command   -> execute one action, returns outcome + reward
    POST /reset     -> reset the room

Running it standalone:

    venv/Scripts/python.exe -m body_runtime_host.robot_sim --port 9100

The Body (BodyHost) then uses ``RobotHttpSource`` pointed at
``http://127.0.0.1:9100`` — the *exact same code path* as a real robot.
So the whole embodied loop (perceive -> encode -> imagine -> act -> learn)
is exercised over the real sensor/actuator boundary, not just in-process.

Only the standard library is required (plus numpy, which the world model
package already pulls in for its sim_world import).
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

from .worldmodel.sim_world import REACH, STRENGTH, SimulatedRoom
from .worldmodel.types import Action
from .fnk0031_protocol import PROTOCOL_VERSION, normalize_command, normalize_sensors

LOG = logging.getLogger("lumina.robot_sim")


class RobotSimServer:
    """An HTTP robot whose sensors + actuators back onto a SimulatedRoom."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9100):
        self.host = host
        self.port = port
        self.room = SimulatedRoom()
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.battery = 0.9
        self.gait = "idle"
        self._gait_phase = 0.0
        self._last_command = ""
        self._last_command_at = 0.0
        self._servo_targets = [0.0] * 18

    # ── protocol payloads ───────────────────────────────────────────────────

    def sensors(self) -> Dict[str, Any]:
        with self._lock:
            objs = []
            for o in self.room.objects.values():
                objs.append({
                    "id": o["id"], "label": o["label"], "kind": o["kind"],
                    "x": o["x"], "y": o["y"], "z": 0.0,
                    "mass": o["mass"], "size": o["size"],
                })
            payload = {
                "protocol_version": PROTOCOL_VERSION,
                "position": [self.room.px, self.room.py, 0.0],
                "orientation": self.room.heading,
                "coordinate_frame": "local_map",
                "position_source": "simulated_odometry",
                "position_accuracy_m": 0.02,
                "capabilities": {
                    "reach": REACH, "speed": 1.0, "strength": STRENGTH, "gripper": 1.0,
                    "max_speed": 2.0, "servo_count": 18, "leg_count": 6,
                },
                "objects": objs,
                "carrying": self.room.carrying,
                "battery": self.battery,
                "imu": {"pitch": 0.0, "roll": 0.0, "yaw": self.room.heading, "source": "simulated_imu"},
                "actuators": {
                    "servo_count": 18,
                    "targets": list(self._servo_targets),
                    "gait": self.gait,
                    "phase": round(self._gait_phase, 4),
                },
                "last_command": self._last_command,
                "last_command_at": self._last_command_at,
                "timestamp": time.time(),
                "confidence": 1.0,
            }
            return normalize_sensors(payload)

    def command(self, action: Dict[str, Any]) -> Dict[str, Any]:
        action = normalize_command(action)
        act = Action.from_dict(action)
        with self._lock:
            # a tiny battery drain per command, like a real robot
            self.battery = max(0.05, self.battery - 0.001)
            _obs, outcome = self.room.step(act)
            self._last_command = act.type
            self._last_command_at = time.time()
            self.gait = act.type if act.type in {"forward", "backward", "turn_left", "turn_right"} else "idle"
            if self.gait != "idle":
                self._gait_phase = (self._gait_phase + 0.12) % (2 * math.pi)
                direction = -1.0 if self.gait in {"backward", "turn_right"} else 1.0
                turning = self.gait in {"turn_left", "turn_right"}
                for leg in range(6):
                    tripod = 1.0 if leg % 2 == int(self._gait_phase > math.pi) else -1.0
                    stride = math.sin(self._gait_phase + leg * math.pi) * direction
                    for joint in range(3):
                        value = stride * (0.32 if joint == 0 else 0.18)
                        if turning:
                            value *= -1.0 if leg < 3 else 1.0
                        self._servo_targets[leg * 3 + joint] = round(value * tripod, 4)
            else:
                self._servo_targets = [0.0] * 18
            return {
                "protocol_version": PROTOCOL_VERSION,
                "outcome": outcome.kind,
                "reward": outcome.reward,
                "description": outcome.description,
                "room": self.room.status(),
                "gait": self.gait,
                "servo_count": 18,
                "servo_targets": list(self._servo_targets),
            }

    def emergency_stop(self, reason: str = "operator stop") -> Dict[str, Any]:
        with self._lock:
            self.gait = "idle"
            self._servo_targets = [0.0] * 18
            self._last_command = "stop"
            self._last_command_at = time.time()
            return {"ok": True, "stopped": True, "reason": reason, "servo_targets": list(self._servo_targets)}

    def capabilities(self) -> Dict[str, Any]:
        return {
            "protocol_version": PROTOCOL_VERSION,
            "platform": "fnk0031_simulator",
            "servo_count": 18,
            "leg_count": 6,
            "actuator": "fnk0031_servo_board",
            "commands": ["forward", "backward", "turn_left", "turn_right", "wait", "grab", "release", "stop"],
            "sensors": ["odometry", "imu", "battery", "scene"],
            "modules": [
                {"id": "imu", "label": "Simulated IMU", "kind": "inertial"},
                {"id": "odometry", "label": "Simulated odometry", "kind": "localization"},
                {"id": "actuators", "label": "FNK0031 simulated servos", "kind": "actuation", "servo_count": 18},
            ],
        }

    def module_status(self) -> Dict[str, Any]:
        now = time.time()
        return {
            "timestamp": now,
            "modules": {
                "imu": {"status": "online", "timestamp": now, "data": {"pitch": 0.0, "roll": 0.0, "yaw": self.room.heading}},
                "odometry": {"status": "online", "timestamp": now, "data": {"position": [self.room.px, self.room.py, 0.0]}},
                "actuators": {"status": "online", "timestamp": now, "data": {"gait": self.gait, "servo_count": 18}},
            },
        }

    def reset(self) -> Dict[str, Any]:
        with self._lock:
            self.room.reset()
            self.battery = 0.9
            self.gait = "idle"
            self._gait_phase = 0.0
            self._last_command = "reset"
            self._servo_targets = [0.0] * 18
            return {"ok": True, "room": self.room.status()}

    # ── server lifecycle ────────────────────────────────────────────────────

    def start(self) -> None:
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def _send(self, payload: Dict[str, Any], status: int = 200) -> None:
                data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _body(self) -> Dict[str, Any]:
                length = int(self.headers.get("Content-Length") or 0)
                if length <= 0:
                    return {}
                try:
                    return json.loads(self.rfile.read(length).decode("utf-8"))
                except Exception:
                    return {}

            def do_GET(self):  # noqa: N802
                path = self.path.split("?", 1)[0].rstrip("/")
                if path == "/health":
                    self._send({"status": "robot-sim", "protocol_version": PROTOCOL_VERSION, "platform": "fnk0031_simulator", "room": owner.room.status(), "gait": owner.gait})
                elif path == "/sensors":
                    self._send(owner.sensors())
                elif path == "/capabilities":
                    self._send(owner.capabilities())
                elif path == "/modules/status":
                    self._send(owner.module_status())
                else:
                    self._send({"error": "not found"}, 404)

            def do_POST(self):  # noqa: N802
                path = self.path.split("?", 1)[0].rstrip("/")
                if path == "/command":
                    self._send(owner.command(self._body()))
                elif path == "/stop":
                    body = self._body()
                    self._send(owner.emergency_stop(str(body.get("reason") or "operator stop")))
                elif path == "/reset":
                    self._send(owner.reset())
                else:
                    self._send({"error": "not found"}, 404)

            def log_message(self, fmt, *args):
                LOG.debug("Robot sim HTTP: " + fmt, *args)

        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        if self.port == 0:
            self.port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, name="robot-sim", daemon=True)
        self._thread.start()
        LOG.info("Robot sim listening on http://%s:%d", self.host, self.port)

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None


def main() -> int:
    parser = argparse.ArgumentParser(description="Lumina simulated robot (robot protocol over HTTP)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9100)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    server = RobotSimServer(host=args.host, port=args.port)
    server.start()
    print(f"Robot sim ready at http://{args.host}:{server.port}")
    print("  GET  /health   GET  /sensors   POST /command   POST /reset")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
