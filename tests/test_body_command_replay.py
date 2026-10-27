"""Offline replay protection regression tests (stdlib only)."""
import tempfile
import time
import unittest
from pathlib import Path

from body_runtime_host.command_replay import CommandReplayLedger


class ReplayLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "commands.json"
        self.ledger = CommandReplayLedger(self.path)

    def test_reservation_survives_restart(self):
        deadline = time.time() + 120
        self.assertTrue(self.ledger.reserve("approved-1", deadline)[0])
        self.assertFalse(CommandReplayLedger(self.path).reserve("approved-1", deadline)[0])

    def test_missing_expiry_is_rejected(self):
        self.assertFalse(self.ledger.reserve("no-expiry", 0)[0])
        self.assertFalse(self.path.exists())

    def test_expired_command_is_rejected(self):
        self.assertFalse(self.ledger.reserve("expired", time.time() - 1)[0])

    def test_far_future_expiry_is_rejected(self):
        self.assertFalse(self.ledger.reserve("unbounded", time.time() + 90000)[0])

    def test_corrupt_ledger_fails_closed(self):
        self.path.write_text("{not-json", encoding="utf-8")
        self.assertFalse(self.ledger.reserve("approved-2", time.time() + 30)[0])
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{not-json")

    def test_disk_failure_fails_closed(self):
        self.path.mkdir()
        self.assertFalse(self.ledger.reserve("approved-3", time.time() + 30)[0])


if __name__ == "__main__":
    unittest.main()
