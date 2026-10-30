"""Offline Brain-approved command delivery tests.

Construct a minimal BodyHost without starting threads, sockets, or hardware.
The world model is a deterministic fake; only the command gateway is tested.
"""
import tempfile
import time
import unittest
import importlib.util
import sys
from collections import deque
from pathlib import Path
from threading import RLock
from unittest.mock import Mock

from body_runtime_host.command_replay import CommandReplayLedger
from body_runtime_host.runtime import BodyHost

_body_runtime_path = Path(__file__).resolve().parents[1] / "cognition" / "body_runtime" / "runtime.py"
_body_runtime_spec = importlib.util.spec_from_file_location("_body_runtime_command_tests", _body_runtime_path)
_body_runtime_module = importlib.util.module_from_spec(_body_runtime_spec)
sys.modules[_body_runtime_spec.name] = _body_runtime_module
_body_runtime_spec.loader.exec_module(_body_runtime_module)
BodyCommand = _body_runtime_module.BodyCommand
BodyRuntime = _body_runtime_module.BodyRuntime


class BrainBodyCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.host = BodyHost.__new__(BodyHost)
        self.host._command_replay = CommandReplayLedger(Path(self.temp.name) / "ledger.json")
        self.host._bridge_put_message = Mock()
        self.host.latest = {}
        self.host._worldmodel = Mock()
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

    def approved_brain_command(self):
        command = BodyCommand(target="robot", action="forward", status="approved")
        brain = BodyRuntime.__new__(BodyRuntime)
        brain._lock = RLock()
        brain._commands = deque([command])
        brain.organism = None
        brain.publish_observation = Mock()
        return brain, command.as_dict()

    def test_approved_command_delivered_once(self):
        result = self.host.execute_command(self.command())
        self.assertEqual(result["status"], "acknowledged")
        self.host.worldmodel.execute_external.assert_called_once()
        self.host._bridge_put_message.assert_called_once()

    def test_duplicate_delivery_after_restart_rejected(self):
        command = self.command()
        self.assertEqual(self.host.execute_command(command)["status"], "acknowledged")
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

    def test_explicit_verified_evidence_reports_executed(self):
        self.host.worldmodel.execute_external.return_value = {
            "outcome": {"kind": "success"},
            "evidence": {"state": "verified_simulation"},
        }
        result = self.host.execute_command(self.command())
        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["verification_status"], "verified_simulation")

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

    def test_brain_preserves_body_ack_as_unverified(self):
        brain, command = self.approved_brain_command()
        body_result = self.host.execute_command(command)
        self.assertEqual(body_result["status"], "acknowledged")
        result = brain.record_command_outcome(body_result)
        self.assertEqual(result["command"]["status"], "acknowledged")
        self.assertEqual(result["command"]["verification_status"], "unknown")
        self.assertIsNone(result["command"]["executed_at"])

    def test_brain_downgrades_legacy_executed_without_evidence(self):
        brain, command = self.approved_brain_command()
        legacy_result = {
            "type": "command_result", "command_id": command["command_id"],
            "status": "executed", "outcome": {"kind": "success"},
        }
        result = brain.record_command_outcome(legacy_result)
        self.assertEqual(result["command"]["status"], "acknowledged")
        self.assertIsNone(result["command"]["executed_at"])

    def test_brain_marks_execution_only_with_verified_evidence(self):
        brain, command = self.approved_brain_command()
        verified_result = {
            "type": "command_result", "command_id": command["command_id"],
            "status": "executed", "verification_status": "verified_observation",
            "outcome": {"kind": "success"},
        }
        result = brain.record_command_outcome(verified_result)
        self.assertEqual(result["command"]["status"], "executed")
        self.assertEqual(result["command"]["verification_status"], "verified_observation")

    def test_failure_status_cannot_be_overridden_by_success_outcome(self):
        brain, command = self.approved_brain_command()
        inconsistent_result = {
            "type": "command_result", "command_id": command["command_id"],
            "status": "failed", "outcome": {"kind": "success"},
        }
        result = brain.record_command_outcome(inconsistent_result)
        self.assertEqual(result["command"]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
