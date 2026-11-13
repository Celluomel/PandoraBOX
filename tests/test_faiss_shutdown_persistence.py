"""FAISS index writes must survive a normal Lumina shutdown."""
from pathlib import Path
from threading import RLock
from types import SimpleNamespace
from unittest.mock import Mock

import cognition.ai_system as ai_system_module
from cognition.ai_system import EnhancedAISystem, EnhancedMemorySystem
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
    organism._loop = Mock()
    organism.ai_system = Mock()
    organism.ai_system.flush_memory_index.return_value = True

    organism.shutdown()

    organism._loop.shutdown.assert_called_once_with()
    organism.ai_system.flush_memory_index.assert_called_once_with()


def test_enhanced_ai_system_delegates_index_flush():
    system = EnhancedAISystem.__new__(EnhancedAISystem)
    system.memory_system = SimpleNamespace(_save_index=Mock(return_value=True))

    assert system.flush_memory_index() is True
    system.memory_system._save_index.assert_called_once_with()
