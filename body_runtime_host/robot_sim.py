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
            return {
                "position": [self.room.px, self.room.py, 0.0],
                "orientation": self.room.heading,
                "capabilities": {
                    "reach": REACH, "speed": 1.0, "strength": STRENGTH, "gripper": 1.0,
                },
                "objects": objs,
                "carrying": self.room.carrying,
                "battery": self.battery,
                "timestamp": time.time(),
                "confidence": 1.0,
            }

    def command(self, action: Dict[str, Any]) -> Dict[str, Any]:
        act = Action.from_dict(action)
        with self._lock:
            # a tiny battery drain per command, like a real robot
            self.battery = max(0.05, self.battery - 0.001)
            _obs, outcome = self.room.step(act)
            return {
                "outcome": outcome.kind,
                "reward": outcome.reward,
                "description": outcome.description,
                "room": self.room.status(),
            }

    def reset(self) -> Dict[str, Any]:
        with self._lock:
            self.room.reset()
            self.battery = 0.9
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
                    self._send({"status": "robot-sim", "room": owner.room.status()})
                elif path == "/sensors":
                    self._send(owner.sensors())
                else:
                    self._send({"error": "not found"}, 404)

            def do_POST(self):  # noqa: N802
                path = self.path.split("?", 1)[0].rstrip("/")
                if path == "/command":
                    self._send(owner.command(self._body()))
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
