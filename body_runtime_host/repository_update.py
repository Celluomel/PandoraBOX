"""Guarded fast-forward updates for the standalone Body checkout."""
from __future__ import annotations

import subprocess
from pathlib import Path


class RepositoryUpdater:
    def __init__(self, repository: Path) -> None:
        self.repository = Path(repository).resolve()

    def _git(self, *args: str, timeout: float = 20.0) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repository), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode:
            message = (result.stderr or result.stdout or "git command failed").strip()
            raise RuntimeError(message)
        return result.stdout.rstrip("\r\n")

    def status(self) -> dict:
        branch = self._git("rev-parse", "--abbrev-ref", "HEAD").strip()
        commit = self._git("rev-parse", "--short", "HEAD").strip()
        porcelain = self._git("status", "--porcelain", "--untracked-files=normal")
        changed_files = [line[3:].strip() for line in porcelain.splitlines() if line]
        try:
            upstream = self._git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}").strip()
        except RuntimeError:
            upstream = ""
        ahead = behind = 0
        if upstream:
            counts = self._git("rev-list", "--left-right", "--count", f"HEAD...{upstream}").split()
            if len(counts) == 2:
                ahead, behind = map(int, counts)
        return {
            "available": True,
            "repository": str(self.repository),
            "branch": branch,
            "commit": commit,
            "upstream": upstream,
            "dirty": bool(changed_files),
            "changed_files": changed_files,
            "ahead": ahead,
            "behind": behind,
            "update_available": bool(upstream and behind and not ahead and not changed_files),
            "restart_required": False,
        }

    def check(self) -> dict:
        self._git("fetch", timeout=120.0)
        return {"ok": True, **self.status()}

    def pull(self) -> dict:
        before = self.status()
        if before["dirty"]:
            return {"ok": False, "reason": "dirty_worktree", **before}
        if not before["upstream"]:
            return {"ok": False, "reason": "no_upstream", **before}
        self._git("pull", "--ff-only", "--no-rebase", timeout=300.0)
        after = self.status()
        after["restart_required"] = before["commit"] != after["commit"]
        return {"ok": True, "pulled": after["restart_required"], **after}
