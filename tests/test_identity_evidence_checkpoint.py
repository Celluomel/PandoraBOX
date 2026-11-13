import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from cognition.ai_identity import IdentityAnalyzer


class MemoryStore:
    def __init__(self, database_path):
        self.database_path = database_path

    @contextmanager
    def get_connection(self):
        connection = sqlite3.connect(self.database_path)
        try:
            yield connection
        finally:
            connection.close()


def add_memory(connection, memory_id, text, memory_type="reflection", impact=0.8, valence="Positive"):
    connection.execute(
        """INSERT INTO memories
           (id, faiss_id, text, timestamp, impact_score, emotional_valence,
            arousal_level, memory_type, access_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (memory_id, str(memory_id), text, str(memory_id), impact, valence, 0.1, memory_type, 0),
    )
    connection.commit()


class IdentityEvidenceCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        self.db_path = str(Path(self.temp_dir.name, "memories.sqlite3"))
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute(
                """CREATE TABLE memories (
                   id INTEGER PRIMARY KEY, faiss_id TEXT, text TEXT, timestamp TEXT,
                   impact_score REAL, emotional_valence TEXT, arousal_level REAL,
                   memory_type TEXT, access_count INTEGER)"""
            )
            connection.commit()
        finally:
            connection.close()
        self.store = MemoryStore(self.db_path)

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()

    def analyzer(self):
        instance = IdentityAnalyzer(self.store, llm=None, persistence=self.store)
        instance.BATCH_SIZE = 2
        instance.REBUILD_PAGE_SIZE = 2
        instance.MAX_REBUILD_PER_REFRESH = 2
        instance._build_identity_from_accumulators = lambda _recent: None
        return instance

    def test_checkpoint_restores_accumulators_and_cursor_without_raw_text(self):
        with self.store.get_connection() as connection:
            add_memory(connection, 1, "curious and honest", valence="Positive")
            add_memory(connection, 2, "curious and honest", valence="Positive")
            add_memory(connection, 3, "curious and honest", valence="Positive")

        first = self.analyzer()
        first.analyze_identity()
        self.assertEqual(first._last_processed_id, 2)
        self.assertEqual(first._trait_evidence["curiosity"]["count"], 2)

        checkpoint_path = Path("data/identity_evidence_state.json")
        saved = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        self.assertNotIn("curious and honest", checkpoint_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["last_processed_id"], 2)

        resumed = self.analyzer()
        self.assertEqual(resumed._trait_evidence["curiosity"]["count"], 2)
        resumed.analyze_identity()
        self.assertEqual(resumed._last_processed_id, 3)
        self.assertEqual(resumed._trait_evidence["curiosity"]["count"], 3)

    def test_filtered_records_advance_cursor_and_do_not_block_later_evidence(self):
        with self.store.get_connection() as connection:
            add_memory(connection, 1, "ordinary low signal", memory_type="interaction", impact=0.1)
            add_memory(connection, 2, "ordinary low signal", memory_type="interaction", impact=0.1)
            add_memory(connection, 3, "curious about evidence", memory_type="reflection")

        analyzer = self.analyzer()
        analyzer.analyze_identity()
        self.assertEqual(analyzer._last_processed_id, 2)
        self.assertEqual(analyzer._trait_evidence, {})

        analyzer.analyze_identity()
        self.assertEqual(analyzer._last_processed_id, 3)
        self.assertEqual(analyzer._trait_evidence["curiosity"]["count"], 1)

    def test_legacy_cursor_without_evidence_checkpoint_rebuilds_from_zero(self):
        Path("data").mkdir()
        Path("data/identity_cursor.json").write_text(
            json.dumps({"last_processed_id": 9000}), encoding="utf-8"
        )
        analyzer = self.analyzer()
        self.assertEqual(analyzer._last_processed_id, 0)
        self.assertTrue(analyzer._rebuild_required)


if __name__ == "__main__":
    unittest.main()
