"""Offline Brain-approved command delivery tests.

Construct a minimal BodyHost without starting threads, sockets, or hardware.
The world model is a deterministic fake; only the command gateway is tested.
"""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock

from body_runtime_host.command_replay import CommandReplayLedger
from body_runtime_host.runtime import BodyHost


class BrainBodyCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.host = BodyHost.__new__(BodyHost)
        self.host._command_replay = CommandReplayLedger(Path(self.temp.name) / "ledger.json")
        self.host._bridge_put_message = Mock()
        self.host.latest = {}
        self.host.worldmodel = Mock()
        self.host.worldmodel.execute_external.return_value = {
            "outcome": {"kind": "success", "description": "simulated"}
        }

    def command(self, command_id="cmd-1", **overrides):
        value = {
            "command_id": command_id, "status": "approved",
            "action": "wait", "expires_at": time.time() + 30,
            "payload": {"params": {}},
        }
        value.update(overrides)
        return value

    def test_approved_command_delivered_once(self):
        result = self.host.execute_command(self.command())
        self.assertEqual(result["status"], "executed")
        self.host.worldmodel.execute_external.assert_called_once()
        self.host._bridge_put_message.assert_called_once()

    def test_duplicate_delivery_after_restart_rejected(self):
        command = self.command()
        self.assertEqual(self.host.execute_command(command)["status"], "executed")
        self.host._command_replay = CommandReplayLedger(Path(self.temp.name) / "ledger.json")
        duplicate = self.host.execute_command(command)
        self.assertEqual(duplicate["status"], "rejected")
        self.host.worldmodel.execute_external.assert_called_once()

    def test_unapproved_command_never_reaches_world_model(self):
        result = self.host.execute_command(self.command(status="pending"))
        self.assertEqual(result["status"], "rejected")
        self.host.worldmodel.execute_external.assert_not_called()

    def test_missing_expiry_never_reaches_world_model(self):
        result = self.host.execute_command(self.command(expires_at=None))
        self.assertEqual(result["status"], "rejected")
        self.host.worldmodel.execute_external.assert_not_called()

    def test_expired_command_never_reaches_world_model(self):
        result = self.host.execute_command(self.command(expires_at=time.time() - 10))
        self.assertEqual(result["status"], "expired")
        self.host.worldmodel.execute_external.assert_not_called()

    def test_neutral_outcome_not_reported_executed(self):
        self.host.worldmodel.execute_external.return_value = {
            "outcome": {"kind": "neutral", "description": "actuation disabled"}
        }
        result = self.host.execute_command(self.command())
        self.assertEqual(result["status"], "failed")

    def test_world_model_exception_does_not_allow_retry(self):
        self.host.worldmodel.execute_external.side_effect = RuntimeError("simulated timeout")
        command = self.command()
        self.assertEqual(self.host.execute_command(command)["status"], "failed")
        self.assertEqual(self.host.execute_command(command)["status"], "rejected")
        self.host.worldmodel.execute_external.assert_called_once()


if __name__ == "__main__":
    unittest.main()
