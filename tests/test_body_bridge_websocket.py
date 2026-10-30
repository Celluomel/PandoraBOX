"""Real loopback WebSocket delivery with a non-actuating fake world model."""
import asyncio
import json
import tempfile
import time
import unittest
from pathlib import Path
from queue import Queue
from threading import Event, Lock
from unittest.mock import Mock

try:
    import websockets
except ImportError:  # The production Body dependency is optional in dev installs.
    websockets = None

from body_command_auth import sign_approval
from body_runtime_host.command_replay import CommandReplayLedger
from body_runtime_host.runtime import BodyHost


APPROVAL_SECRET = "loopback-only-approval-key-32-bytes"


@unittest.skipIf(websockets is None, "install declared Body dependency: websockets")
class BodyBridgeWebSocketTests(unittest.IsolatedAsyncioTestCase):
    async def test_approved_command_round_trip_over_real_loopback_socket(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            host = BodyHost.__new__(BodyHost)
            host.stop_event = Event()
            host.config = {
                "BODY_BRIDGE_ENABLED": True,
                "BODY_BRIDGE_URL": "",
                "BODY_BRIDGE_TOKEN": "loopback-token",
                "BODY_BRIDGE_DEVICE_ID": "test-body",
                "BODY_BRIDGE_RECONNECT_SECONDS": 1,
                "BODY_COMMAND_APPROVAL_SECRET": APPROVAL_SECRET,
            }
            host.queue = Queue(maxsize=32)
            host._bridge_lock = Lock()
            host._bridge_connected = Event()
            host._bridge_latest = {}
            host._command_replay = CommandReplayLedger(Path(temp_dir) / "ledger.json")
            host.latest = {}
            host._worldmodel = Mock()
            host._worldmodel.execute_external.return_value = {
                "outcome": {"kind": "success", "description": "fake adapter acknowledgement"}
            }
            host.value = lambda key, default=None: host.config.get(key, default)

            now = time.time()
            command = {
                "command_id": "loopback-command-1",
                "target": "robot",
                "action": "wait",
                "payload": {"params": {}},
                "status": "approved",
                "created_at": now,
                "approved_at": now,
                "approved_by": "local_interface_confirmation",
                "expires_at": now + 45,
                "requires_confirmation": True,
                "origin": "loopback-test",
            }
            command["approval_proof"] = sign_approval(command, APPROVAL_SECRET)
            expired_command = dict(command)
            expired_command.update({
                "command_id": "loopback-expired-command",
                "created_at": now - 20,
                "approved_at": now - 20,
                "expires_at": now - 1,
            })
            expired_command["approval_proof"] = sign_approval(expired_command, APPROVAL_SECRET)
            received_result = asyncio.get_running_loop().create_future()
            expired_result = asyncio.get_running_loop().create_future()
            connections = 0

            async def fake_brain(ws, *_):
                nonlocal connections
                connections += 1
                self.assertEqual(ws.request.headers.get("Authorization"), "Bearer loopback-token")
                hello = await ws.recv()
                self.assertEqual(json.loads(hello)["type"], "hello")
                await ws.send(json.dumps({"type": "hello_ack", "protocol": 1}))
                if connections == 1:
                    await ws.send(json.dumps({"type": "command", "command": expired_command}))
                    expired = json.loads(await asyncio.wait_for(ws.recv(), 3))
                    if not expired_result.done():
                        expired_result.set_result(expired)
                    await ws.close()
                    return
                await ws.send(json.dumps({"type": "command", "command": command}))
                result = json.loads(await asyncio.wait_for(ws.recv(), 3))
                if not received_result.done():
                    received_result.set_result(result)
                host.stop_event.set()
                await ws.close()

            async with websockets.serve(fake_brain, "127.0.0.1", 0) as server:
                port = server.sockets[0].getsockname()[1]
                host.config["BODY_BRIDGE_URL"] = f"ws://127.0.0.1:{port}/bridge"
                session = asyncio.create_task(host._bridge_session(websockets))
                try:
                    refused = await asyncio.wait_for(expired_result, 5)
                    result = await asyncio.wait_for(received_result, 5)
                    await asyncio.wait_for(session, 3)
                finally:
                    host.stop_event.set()
                    if not session.done():
                        session.cancel()
                        await asyncio.gather(session, return_exceptions=True)

            self.assertEqual(refused["status"], "expired")
            self.assertEqual(refused["command_id"], "loopback-expired-command")
            self.assertEqual(connections, 2)
            self.assertEqual(result["type"], "command_result")
            self.assertEqual(result["command_id"], "loopback-command-1")
            self.assertEqual(result["status"], "acknowledged")
            host._worldmodel.execute_external.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
