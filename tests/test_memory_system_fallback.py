import sys
import unittest
from datetime import datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
package = ModuleType("cognition")
package.__path__ = [str(ROOT / "cognition")]
sys.modules.setdefault("cognition", package)

from cognition.ai_system import EnhancedMemorySystem
from cognition.memory_retrieval import merge_user_authored_memories
from cognition.turn_context_evidence import format_memory_for_prompt


class _Persistence:
    def __init__(self, rows):
        self.rows = rows

    def get_all_memories(self, tier=None):
        if tier is None:
            return list(self.rows)
        return [row for row in self.rows if row["memory_tier"] == tier]

    def get_memories_by_ids(self, _ids):
        return []


class _BrokenEmbedder:
    def encode(self, _text):
        raise RuntimeError("encoder unavailable")


class _Index:
    ntotal = 3

    def search(self, *_args):
        raise AssertionError("lexical fallback should run before vector search")


class _StaleIndex:
    ntotal = 1

    def search(self, *_args):
        return np.array([[0.1]], dtype="float32"), np.array([[999]], dtype="int64")


class _Embedder:
    def encode(self, _text):
        return np.ones(3, dtype="float32")


class MemorySystemFallbackTests(unittest.TestCase):
    def setUp(self):
        now = datetime.now().isoformat()
        self.rows = [
            {"id": 1, "faiss_id": 1, "text": "Arduino Q camera movement and future embodiment",
             "timestamp": now, "impact_score": 0.5, "memory_type": "project",
             "memory_tier": "personal", "emotional_valence": "Neutral", "access_count": 0},
            {"id": 2, "faiss_id": 2, "text": "Coqui voice selection needs the configured speaker file",
             "timestamp": now, "impact_score": 0.5, "memory_type": "settings",
             "memory_tier": "interaction", "emotional_valence": "Neutral", "access_count": 0},
        ]

    def _system(self, embedder=None, index=None):
        system = EnhancedMemorySystem.__new__(EnhancedMemorySystem)
        system.persistence = _Persistence(self.rows)
        system.config = SimpleNamespace(max_memory_retrieval=5)
        system.embedding_dim = 3
        system.embedding_model = embedder
        system.faiss_index = index
        return system

    def test_no_embedder_still_recalls_persisted_memory_and_filters_tier(self):
        system = self._system()

        general = system.retrieve_memories("How can I move the Arduino camera?")
        personal = system.retrieve_by_tier("Arduino camera movement", "personal")

        self.assertEqual(general[0]["id"], 1)
        self.assertGreater(general[0]["relevance"], 0)
        self.assertEqual([row["id"] for row in personal], [1])

    def test_empty_vector_index_does_not_hide_database_memories(self):
        system = self._system(embedder=object(), index=SimpleNamespace(ntotal=0))

        result = system.retrieve_memories("configured Coqui speaker file")

        self.assertEqual(result[0]["id"], 2)

    def test_stale_vector_ids_do_not_hide_sqlite_memories(self):
        system = self._system(embedder=_Embedder(), index=_StaleIndex())

        result = system.retrieve_memories("configured Coqui speaker file")

        self.assertEqual(result[0]["id"], 2)

    def test_encoder_failure_disables_broken_vector_path_and_falls_back(self):
        system = self._system(embedder=_BrokenEmbedder(), index=_Index())

        result = system.retrieve_memories("configured Coqui speaker file")

        self.assertEqual(result[0]["id"], 2)
        self.assertIsNone(system.embedding_model)
        self.assertIsNone(system.faiss_index)

    def test_source_recall_preserves_user_statement_over_conflicting_lumina_reply(self):
        query = "What relationship and direction did we define between Lumina and Flux?"
        self.rows = [
            {"id": 1, "faiss_id": 1,
             "text": "User message: Lumina is the master brain; conversation goes one way from Lumina to Flux.",
             "timestamp": datetime.now().isoformat(), "impact_score": 0.5,
             "memory_type": "user_message", "memory_tier": "interaction",
             "emotional_valence": "Neutral", "access_count": 0},
            {"id": 2, "faiss_id": 2,
             "text": "Conversation — User: How should Lumina and Flux work? | Lumina: Flux is master and the dialogue is bidirectional.",
             "timestamp": datetime.now().isoformat(), "impact_score": 1.0,
             "memory_type": "episodic", "memory_tier": "interaction",
             "emotional_valence": "Neutral", "access_count": 0},
        ]
        system = self._system()

        # Reproduce the actual failure: the shared fallback ranks the false,
        # longer assistant reply above the user's source statement.
        primary = system.retrieve_memories(query, limit=2)
        self.assertEqual(primary[0]["id"], 2)

        source = system.retrieve_user_authored_memories(query, limit=2)
        recalled = merge_user_authored_memories(primary, source, limit=2)

        self.assertEqual(recalled[0]["id"], 1)
        rendered = format_memory_for_prompt(recalled[0])
        self.assertIn("separately indexed, user-authored message", rendered)
        self.assertIn("a question alone does not establish its answer", rendered)
        self.assertIn("one way from Lumina to Flux", rendered)

    def test_source_recall_does_not_inject_unrelated_user_message(self):
        self.rows = [{
            "id": 3, "faiss_id": 3, "text": "User message: My favorite color is green.",
            "timestamp": datetime.now().isoformat(), "impact_score": 0.5,
            "memory_type": "user_message", "memory_tier": "interaction",
            "emotional_valence": "Neutral", "access_count": 0,
        }]

        result = self._system().retrieve_user_authored_memories(
            "How does the cognitive planner select actions?", limit=2
        )

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
