import json
from pathlib import Path
from unittest.mock import patch

from core.data.access import DataAccess
from cognition.thread_resolver import ThreadResolver


def _write_thread_file(path: Path, threads):
    path.mkdir(parents=True, exist_ok=True)
    (path / "thought_threads.json").write_text(
        json.dumps({thread["id"]: thread for thread in threads}), encoding="utf-8"
    )
    (path / "tensions.json").write_text(
        json.dumps({"current": {}}), encoding="utf-8"
    )


def _thread(thread_id, **overrides):
    result = {
        "id": thread_id,
        "topic": "cognitive audit",
        "object": "cognitive audit",
        "action": "resolve tension",
        "status": "active",
        "history": [],
        "iteration_count": 1,
        "current_tension": 0.5,
    }
    result.update(overrides)
    return result


def test_resolver_does_not_rewrite_unchanged_thread_file(tmp_path):
    threads = [_thread(f"thread-{i}") for i in range(40)]
    _write_thread_file(tmp_path, threads)
    writes = []
    original_save = DataAccess._save

    def count_thread_writes(self, filename, data):
        if filename == "thought_threads.json":
            writes.append(filename)
        return original_save(self, filename, data)

    with patch.object(DataAccess, "_save", count_thread_writes):
        assert ThreadResolver(tmp_path).resolve_stuck_threads() == (0, 0)

    assert writes == []


def test_resolver_persists_changed_threads_with_one_atomic_batch_write(tmp_path):
    threads = [_thread(f"thread-{i}", current_tension=None) for i in range(40)]
    _write_thread_file(tmp_path, threads)
    writes = []
    original_save = DataAccess._save

    def count_thread_writes(self, filename, data):
        if filename == "thought_threads.json":
            writes.append(filename)
        return original_save(self, filename, data)

    with patch.object(DataAccess, "_save", count_thread_writes):
        assert ThreadResolver(tmp_path).resolve_stuck_threads() == (0, 0)

    assert writes == ["thought_threads.json"]
    saved = json.loads((tmp_path / "thought_threads.json").read_text(encoding="utf-8"))
    assert len(saved) == 40
    assert all(thread["current_tension"] == 0.5 for thread in saved.values())


def test_resolver_reads_wrapped_current_tension_and_resolves_low_tension(tmp_path):
    thread = _thread("thread-low-tension", current_tension=0.5)
    _write_thread_file(tmp_path, [thread])
    (tmp_path / "tensions.json").write_text(
        json.dumps({"current": {"cognitive audit": 0.1}}), encoding="utf-8"
    )

    assert ThreadResolver(tmp_path).resolve_stuck_threads() == (1, 0)

    saved = json.loads((tmp_path / "thought_threads.json").read_text(encoding="utf-8"))
    result = saved["thread-low-tension"]
    assert result["status"] == "resolved"
    assert result["resolution_criteria_met"] is True
    assert "Tension below threshold (0.10 < 0.2)" in result["resolution_reason"]
