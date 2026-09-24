"""Permissioned Brain -> Body command path tests."""
import time
import unittest
from unittest.mock import patch


class BodyCommandQueueTest(unittest.TestCase):
    def setUp(self):
        from cognition.body_runtime import BodyRuntime
        self.body = BodyRuntime()
        # Keep this unit test isolated from the user's persisted Body config.
        self.body._config = {"BODY_COMMAND_TTL_SECONDS": 120.0}

    def test_brain_adapter_is_passive_and_never_builds_local_world_model(self):
        self.assertFalse(self.body.status()["running"])
        with patch("cognition.body_runtime.remote.RemoteWorldModel") as remote_model:
            remote_model.return_value.ping.return_value = False
            self.assertIsNone(self.body._build_worldmodel())
        remote_model.assert_called_once()

    def test_disabled_world_model_does_not_probe_body_host(self):
        self.body._config["BODY_WORLDMODEL_ENABLED"] = False
        with patch("cognition.body_runtime.runtime.BodyRuntime._build_worldmodel") as build:
            self.assertIsNone(self.body.worldmodel)
        build.assert_not_called()

    def test_approval_delivers_only_approved_command(self):
        command = self.body.enqueue_command("robot", "forward")
        self.assertEqual(self.body.snapshot_commands()[0]["status"], "queued")
        delivered = self.body.next_bridge_command(timeout=0.01)
        self.assertIsNone(delivered)

        approved = self.body.approve_command(command.command_id)
        self.assertTrue(approved["ok"])
        delivered = self.body.next_bridge_command(timeout=0.1)
        self.assertEqual(delivered["type"], "command")
        self.assertEqual(delivered["command"]["status"], "approved")

    def test_rejection_and_expiry_are_terminal(self):
        rejected = self.body.enqueue_command("robot", "forward")
        result = self.body.reject_command(rejected.command_id, "operator test")
        self.assertTrue(result["ok"])
        self.assertEqual(result["command"]["status"], "rejected")

        expired = self.body.enqueue_command("robot", "forward", ttl_seconds=1)
        expired.expires_at = time.time() - 1
        self.assertFalse(self.body.approve_command(expired.command_id)["ok"])
        self.assertEqual(self.body.snapshot_commands(include_terminal=True)[0]["status"], "expired")

    def test_outcome_becomes_body_observation(self):
        command = self.body.enqueue_command("robot", "forward")
        self.body.approve_command(command.command_id)
        self.body.next_bridge_command(timeout=0.1)
        result = self.body.record_command_outcome({
            "type": "command_result",
            "command_id": command.command_id,
            "status": "executed",
            "outcome": {"kind": "success", "reward": 1.0},
        })
        self.assertTrue(result["ok"])
        self.assertEqual(result["command"]["status"], "executed")
        events = self.body.recent_events()
        self.assertTrue(any(item["kind"] == "actuation_feedback" for item in events))


if __name__ == "__main__":
    unittest.main(verbosity=2)
