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
        embedding_model_name="all-MiniLM-L6-v2",
    )
    memory.embedding_dim = 384
    monkeypatch.setattr(ai_system_module, "faiss", FakeFaiss)

    assert memory._save_index() is True
    assert target.read_bytes() == b"updated-index"
    manifest = target.with_suffix(target.suffix + ".meta.json")
    assert manifest.exists()
    assert memory._index_manifest_matches(target)
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(
        [target.name, manifest.name]
    )


def test_faiss_manifest_rejects_model_change_and_index_tampering(tmp_path, monkeypatch):
    target = tmp_path / "faiss_index.bin"

    class FakeFaiss:
        @staticmethod
        def write_index(index, path):
            Path(path).write_bytes(index)

    memory = EnhancedMemorySystem.__new__(EnhancedMemorySystem)
    memory._lock = RLock()
    memory.faiss_index = b"index-for-minilm"
    memory.embedding_dim = 384
    memory.config = SimpleNamespace(
        faiss=SimpleNamespace(index_path=str(target)),
        embedding_model_name="all-MiniLM-L6-v2",
    )
    monkeypatch.setattr(ai_system_module, "faiss", FakeFaiss)

    assert memory._save_index() is True
    assert memory._index_manifest_matches(target)

    memory.config.embedding_model_name = "some-other-384d-model"
    assert memory._index_manifest_matches(target) is False

    memory.config.embedding_model_name = "all-MiniLM-L6-v2"
    target.write_bytes(b"tampered-index")
    assert memory._index_manifest_matches(target) is False


def test_legacy_faiss_index_without_manifest_is_not_trusted(tmp_path):
    target = tmp_path / "legacy.bin"
    target.write_bytes(b"old-index-without-model-provenance")
    memory = EnhancedMemorySystem.__new__(EnhancedMemorySystem)
    memory.embedding_dim = 384
    memory.config = SimpleNamespace(
        embedding_model_name="all-MiniLM-L6-v2",
    )

    assert memory._index_manifest_matches(target) is False


def test_rebuilding_faiss_index_batch_encodes_memories_and_preserves_ids(monkeypatch):
    rows = [(11, "User message: remember this"), (12, "A stored observation")]

    class Cursor:
        def execute(self, query):
            assert "SELECT faiss_id, text FROM memories" in query

        def fetchall(self):
            return rows

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def cursor(self):
            return Cursor()

    class Index:
        def __init__(self):
            self.added_vectors = None
            self.added_ids = None

        def add_with_ids(self, vectors, ids):
            self.added_vectors = vectors.copy()
            self.added_ids = ids.copy()

    index = Index()

    class FakeFaiss:
        @staticmethod
        def IndexIDMap(_flat_index):
            return index

        @staticmethod
        def IndexFlatL2(dim):
            assert dim == 3
            return "flat-index"

    class Embedder:
        def __init__(self):
            self.calls = []

        def encode(self, texts, **kwargs):
            self.calls.append((texts, kwargs))
            return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]

    embedder = Embedder()
    memory = EnhancedMemorySystem.__new__(EnhancedMemorySystem)
    memory.embedding_dim = 3
    memory.embedding_model = embedder
    memory.faiss_index = None
    memory.persistence = SimpleNamespace(get_connection=Connection)
    memory._save_index = Mock(return_value=True)
    monkeypatch.setattr(ai_system_module, "faiss", FakeFaiss)

    built = memory._build_index_from_db()

    assert built is index
    assert len(embedder.calls) == 1
    encoded_texts, kwargs = embedder.calls[0]
    assert encoded_texts == [
        ai_system_module.memory_embedding_text(rows[0][1], "user_message"),
        ai_system_module.memory_embedding_text(rows[1][1], ""),
    ]
    assert kwargs == {"show_progress_bar": False, "batch_size": 128}
    assert index.added_ids.tolist() == [11, 12]
    assert index.added_vectors.tolist() == [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    memory._save_index.assert_called_once_with(index)


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
        embedding_model_name="all-MiniLM-L6-v2",
    )
    memory.embedding_dim = 384
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
            shutdown=lambda timeout=10.0: events.append(("background_worker", timeout)) or True
        ),
        flush_memory_index=lambda: events.append("flush_index") or True,
    )

    organism.shutdown()

    assert events == ["loop", ("background_worker", 60.0), "flush_index"]


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

    organism.ai_system.background_worker.shutdown.assert_called_once_with(timeout=60.0)
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
