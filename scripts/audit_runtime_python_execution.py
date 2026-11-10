"""Opt-in, path-only Python execution audit for one Lumina process session.

Enable through start.bat with LUMINA_MODULE_EXECUTION_AUDIT=1. This records
which repository .py files execute Python code, not source text, arguments,
locals, prompts, sensor payloads, or return values.
"""
from __future__ import annotations

import atexit
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import threading
import time
from collections import Counter


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ.get(
    "LUMINA_MODULE_AUDIT_OUTPUT", str(ROOT / "logs" / "runtime_python_execution.json")
)).resolve()
EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "body_venv", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
}
TEST_OR_TOOL_DIRS = {"tests", "scripts", "tools", "archive", "artifacts"}
file_calls: Counter[str] = Counter()
module_calls: Counter[str] = Counter()
relative_path_cache: dict[str, str | None] = {}
last_flush = 0.0


def _repo_relative(filename: str) -> str | None:
    cached = relative_path_cache.get(filename)
    if filename in relative_path_cache:
        return cached
    try:
        absolute = Path(os.path.abspath(filename))
        relative = absolute.relative_to(ROOT)
    except (OSError, ValueError):
        relative_path_cache[filename] = None
        return None
    if relative.suffix.lower() != ".py" or {
        part.casefold() for part in relative.parts
    }.intersection(EXCLUDED_DIRS):
        relative_path_cache[filename] = None
        return None
    value = relative.as_posix()
    relative_path_cache[filename] = value
    return value


def _repository_python_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--", "*.py"],
            cwd=ROOT, capture_output=True, text=True, timeout=10, check=True,
        )
        files = {
            line.strip().replace("\\", "/")
            for line in result.stdout.splitlines()
            if line.strip().lower().endswith(".py")
        }
    except (OSError, subprocess.SubprocessError):
        # Fallback for exported source trees without Git metadata. Prune
        # generated environments and caches before descending into them.
        files = set()
        excluded = {item.casefold() for item in EXCLUDED_DIRS}
        for current, directories, filenames in os.walk(ROOT, topdown=True):
            directories[:] = [name for name in directories if name.casefold() not in excluded]
            for filename in filenames:
                if filename.casefold().endswith(".py"):
                    files.add(Path(current, filename).relative_to(ROOT).as_posix())
    return sorted(files | set(file_calls))


def _scope(path: str) -> str:
    parts = {part.casefold() for part in Path(path).parts}
    if "body_runtime_host" in parts:
        return "body_runtime_code"
    if TEST_OR_TOOL_DIRS.intersection(parts):
        return "test_or_tool"
    return "brain_or_shared_library"


def _profile(frame, event, arg):
    del arg
    if event != "call":
        return
    relative = _repo_relative(frame.f_code.co_filename)
    if relative is None:
        return
    file_calls[relative] += 1
    if frame.f_code.co_name == "<module>":
        module_calls[relative] += 1
    global last_flush
    now = time.monotonic()
    if now - last_flush >= 30:
        last_flush = now
        _write_report()


def _write_report() -> None:
    files = _repository_python_files()
    executed = sorted(file_calls)
    unexecuted = sorted(set(files) - set(executed))
    report = {
        "schema": "lumina_python_execution_audit.v1",
        "scope": "current app.py process and its Python threads; subprocesses are separate",
        "created_at_unix": time.time(),
        "pid": os.getpid(),
        "profiling_enabled": True,
        "overhead_note": "sys.setprofile observes Python function/module calls; use for audit sessions only",
        "scope_note": "Scope labels classify source paths; every listed execution occurred in this app.py process and its Python threads.",
        "repository_python_files": len(files),
        "executed_file_count": len(executed),
        "unexecuted_file_count": len(unexecuted),
        "executed_files": [
            {"path": path, "module_body_executions": module_calls.get(path, 0),
             "python_call_events": file_calls[path],
             "scope": _scope(path)}
            for path in executed
        ],
        "unexecuted_files": unexecuted,
        "limitations": [
            "A file absent from this report may be optional, platform-specific, or scenario-gated; absence alone is not a defect.",
            "A call event proves code execution, not correct output or useful downstream effect.",
            "The module body count distinguishes module import/execution from calls into an already imported module.",
        ],
    }
    try:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        temporary = OUTPUT.with_suffix(OUTPUT.suffix + ".tmp")
        temporary.write_text(json.dumps(report, indent=2), encoding="utf-8")
        os.replace(temporary, OUTPUT)
    except OSError as exc:
        print(f"[module-audit] Could not write report: {type(exc).__name__}", file=sys.stderr)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: audit_runtime_python_execution.py app.py [app args...]", file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).resolve()
    if not target.is_file() or target.suffix.lower() != ".py":
        print("Audit target must be an existing Python file.", file=sys.stderr)
        return 2

    atexit.register(_write_report)
    sys.path.insert(0, str(ROOT))
    sys.argv = [str(target), *sys.argv[2:]]
    sys.setprofile(_profile)
    threading.setprofile(_profile)
    try:
        runpy.run_path(str(target), run_name="__main__")
    finally:
        sys.setprofile(None)
        threading.setprofile(None)
        _write_report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
