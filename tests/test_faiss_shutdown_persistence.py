"""FAISS index writes must survive a normal Lumina shutdown."""
from pathlib import Path
from threading import Lock, RLock, Thread
from queue import Queue
from types import SimpleNamespace
from unittest.mock import Mock

import cognition.ai_system as ai_system_module
from cognition.ai_system import BackgroundWorker, EnhancedAISystem, EnhancedMemorySystem
from cognition.cognitive_organism import CognitiveOrganism


def test_save_index_atomically_replaces_the_persisted_file(tmp_path, monkeypatch):
    target = tmp_path / "faiss_index.bin"
    target.write_bytes(b"old-index")

    class FakeFaiss:
        @staticmethod
        def write_index(index, path):
            assert index == "updated-index"
            Path(path).write_bytes(b"updated-index")

    memory = EnhancedMemorySystem.__new__(EnhancedMemorySystem)
    memory._lock = RLock()
    memory.faiss_index = "updated-index"
    memory.config = SimpleNamespace(
        faiss=SimpleNamespace(index_path=str(target)),
    )
    monkeypatch.setattr(ai_system_module, "faiss", FakeFaiss)

    assert memory._save_index() is True
    assert target.read_bytes() == b"updated-index"
    assert list(tmp_path.iterdir()) == [target]


def test_failed_index_write_preserves_previous_persisted_file(tmp_path, monkeypatch):
    target = tmp_path / "faiss_index.bin"
    target.write_bytes(b"known-good-index")

    class BrokenFaiss:
        @staticmethod
        def write_index(index, path):
            Path(path).write_bytes(b"partial")
            raise OSError("simulated disk error")

    memory = EnhancedMemorySystem.__new__(EnhancedMemorySystem)
    memory._lock = RLock()
    memory.faiss_index = "updated-index"
    memory.config = SimpleNamespace(
        faiss=SimpleNamespace(index_path=str(target)),
    )
    monkeypatch.setattr(ai_system_module, "faiss", BrokenFaiss)

    assert memory._save_index() is False
    assert target.read_bytes() == b"known-good-index"
    assert list(tmp_path.iterdir()) == [target]


def test_organism_shutdown_flushes_index_after_stopping_internal_loop():
    organism = CognitiveOrganism.__new__(CognitiveOrganism)
    organism.thought_stream = SimpleNamespace(flush=Mock())
    events = []
    organism._loop = SimpleNamespace(shutdown=lambda: events.append("loop"))
    organism.ai_system = SimpleNamespace(
        background_worker=SimpleNamespace(
            shutdown=lambda: events.append("background_worker") or True
        ),
        flush_memory_index=lambda: events.append("flush_index") or True,
    )

    organism.shutdown()

    assert events == ["loop", "background_worker", "flush_index"]


def test_organism_skips_index_flush_if_background_worker_did_not_stop():
    organism = CognitiveOrganism.__new__(CognitiveOrganism)
    organism.thought_stream = SimpleNamespace(flush=Mock())
    organism._loop = SimpleNamespace(shutdown=Mock())
    flush = Mock(return_value=True)
    organism.ai_system = SimpleNamespace(
        background_worker=SimpleNamespace(shutdown=Mock(return_value=False)),
        flush_memory_index=flush,
    )

    organism.shutdown()

    organism.ai_system.background_worker.shutdown.assert_called_once_with()
    flush.assert_not_called()


def test_background_worker_drains_accepted_tasks_and_rejects_work_after_stop():
    completed = []
    worker = BackgroundWorker.__new__(BackgroundWorker)
    worker.ai_system = SimpleNamespace()
    worker._queue = Queue()
    worker._state_lock = Lock()
    worker._stopping = False
    worker._thread = Thread(target=worker._run, daemon=True)
    worker._execute = completed.append
    worker._thread.start()

    assert worker.submit("accepted-before-stop") is True
    assert worker.shutdown(timeout=1.0) is True

    assert completed == ["accepted-before-stop"]
    assert worker.submit("rejected-after-stop") is False


def test_enhanced_ai_system_delegates_index_flush():
    system = EnhancedAISystem.__new__(EnhancedAISystem)
    system.memory_system = SimpleNamespace(_save_index=Mock(return_value=True))

    assert system.flush_memory_index() is True
    system.memory_system._save_index.assert_called_once_with()
