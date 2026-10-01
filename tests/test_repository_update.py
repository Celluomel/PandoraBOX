import unittest
from pathlib import Path
from unittest.mock import patch

from body_runtime_host.repository_update import RepositoryUpdater


class RepositoryUpdaterTests(unittest.TestCase):
    def test_status_reports_worktree_and_upstream_divergence(self):
        outputs = {
            ("rev-parse", "--abbrev-ref", "HEAD"): "main",
            ("rev-parse", "--short", "HEAD"): "abc1234",
            ("status", "--porcelain", "--untracked-files=normal"): " M body.py\n?? notes.txt",
            ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"): "origin/main",
            ("rev-list", "--left-right", "--count", "HEAD...origin/main"): "0\t2",
        }

        def git(command, **kwargs):
            self.assertEqual(command[:2], ["git", "-C"])
            return type("Completed", (), {"returncode": 0, "stdout": outputs[tuple(command[3:])], "stderr": ""})()

        updater = RepositoryUpdater(Path("/repo"))
        with patch("body_runtime_host.repository_update.subprocess.run", side_effect=git):
            result = updater.status()

        self.assertEqual(result["branch"], "main")
        self.assertEqual(result["commit"], "abc1234")
        self.assertEqual(result["changed_files"], ["body.py", "notes.txt"])
        self.assertTrue(result["dirty"])
        self.assertEqual(result["behind"], 2)
        self.assertFalse(result["update_available"], "dirty worktree must never advertise a safe pull")

    def test_pull_refuses_to_overwrite_local_changes(self):
        updater = RepositoryUpdater(Path("/repo"))
        dirty_status = {
            "available": True,
            "branch": "main",
            "commit": "abc1234",
            "upstream": "origin/main",
            "dirty": True,
            "changed_files": ["runtime.py"],
            "ahead": 0,
            "behind": 1,
            "update_available": False,
            "restart_required": False,
        }
        with patch.object(updater, "status", return_value=dirty_status), patch.object(updater, "_git") as git:
            result = updater.pull()
        git.assert_not_called()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "dirty_worktree")


if __name__ == "__main__":
    unittest.main()
