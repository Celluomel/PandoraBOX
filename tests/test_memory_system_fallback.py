import sys
import unittest
from datetime import datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace
from contextlib import contextmanager
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
package = ModuleType("cognition")
package.__path__ = [str(ROOT / "cognition")]
sys.modules.setdefault("cognition", package)

import cognition.ai_system as ai_system_module
from cognition.ai_system import EnhancedMemorySystem
from cognition.memory_retrieval import (
    extract_explicit_recall_topic,
    filter_recall_query_records,
    filter_memories_by_modality,
    is_explicit_memory_recall_query,
    is_visual_memory_query,
    merge_user_authored_memories,
)
from cognition.turn_context_evidence import format_memory_for_prompt


class _Persistence:
    def __init__(self, rows):
        self.rows = rows
        self.all_memory_queries = []

    def get_all_memories(self, tier=None, memory_type=None, limit=None):
        self.all_memory_queries.append((tier, memory_type, limit))
        if tier is None:
            selected = list(self.rows)
        else:
            selected = [row for row in self.rows if row["memory_tier"] == tier]
        if memory_type is not None:
            selected = [row for row in selected if row["memory_type"] == memory_type]
        if limit is not None:
            selected = selected[:limit]
        return selected

    def get_memories_by_ids(self, ids):
        return [row for row in self.rows if row.get("faiss_id") in ids]

    def add_memory(self, memory):
        next_id = max((int(row.get("id", 0)) for row in self.rows), default=0) + 1
        row = dict(memory, id=next_id, faiss_id=next_id)
        self.rows.append(row)
        return next_id

    @contextmanager
    def get_connection(self):
        class _Connection:
            def execute(self, _query):
                return self

            def fetchall(self):
                return [(row.get("faiss_id"),) for row in self_rows if row.get("faiss_id") is not None]

        self_rows = self.rows
        yield _Connection()


class _BrokenEmbedder:
    def encode(self, _text):
        raise RuntimeError("encoder unavailable")


class _Index:
    ntotal = 3

    def search(self, *_args):
        raise AssertionError("lexical fallback should run before vector search")


class _UserSourceIndex:
    ntotal = 2

    def search(self, _query, count):
        assert count == 2
        return np.array([[0.1, 0.2]], dtype="float32"), np.array([[2, 1]], dtype="int64")


class _WorkingIndex:
    ntotal = 2

    def search(self, _query, count):
        return (
            np.array([[0.2, 0.8]], dtype="float32")[:, :count],
            np.array([[1, 2]], dtype="int64")[:, :count],
        )


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
        system.config = SimpleNamespace(
            max_memory_retrieval=5,
            faiss=SimpleNamespace(save_interval=100),
        )
        system.embedding_dim = 3
        system.embedding_model = embedder
        system.faiss_index = index
        system._counter = 0
        import threading
        system._lock = threading.RLock()
        return system

    def test_persisted_faiss_index_must_match_unique_database_ids(self):
        system = self._system()
        vector_api = SimpleNamespace(vector_to_array=lambda ids: np.asarray(ids))
        with patch.object(ai_system_module, "faiss", vector_api):
            valid = SimpleNamespace(id_map=np.array([1, 2]), ntotal=2)
            duplicate = SimpleNamespace(id_map=np.array([1, 1]), ntotal=2)
            stale = SimpleNamespace(id_map=np.array([1, 999]), ntotal=2)

            self.assertTrue(system._index_matches_memory_db(valid))
            self.assertFalse(system._index_matches_memory_db(duplicate))
            self.assertFalse(system._index_matches_memory_db(stale))

    def test_no_embedder_still_recalls_persisted_memory_and_filters_tier(self):
        system = self._system()

        general = system.retrieve_memories("How can I move the Arduino camera?")
        personal = system.retrieve_by_tier("Arduino camera movement", "personal")

        self.assertEqual(general[0]["id"], 1)
        self.assertGreater(general[0]["relevance"], 0)
        self.assertEqual([row["id"] for row in personal], [1])

    def test_retrieval_receipt_names_faiss_when_vector_search_runs(self):
        system = self._system(embedder=_Embedder(), index=_WorkingIndex())

        memories, receipt = system.retrieve_memories_with_receipt(
            "Arduino camera movement"
        )

        self.assertEqual(len(memories), 2)
        self.assertEqual(receipt["backend"], "faiss")
        self.assertIsNone(receipt["fallback_reason"])
        self.assertEqual(receipt["vector_candidate_count"], 2)
        self.assertEqual(receipt["returned_count"], 2)

    def test_retrieval_receipt_names_lexical_fallback_and_reason_when_vectors_unavailable(self):
        system = self._system()

        memories, receipt = system.retrieve_memories_with_receipt(
            "configured Coqui speaker file"
        )

        self.assertTrue(memories)
        self.assertEqual(receipt["backend"], "lexical")
        self.assertEqual(receipt["fallback_reason"], "embedding_or_index_unavailable")

    def test_explicit_recall_extracts_topic_instead_of_current_request(self):
        self.assertEqual(
            extract_explicit_recall_topic(
                "Rappelle uniquement ce que je t’ai demandé concernant la manière de conduire l’audit du harnais cognitif."
            ),
            "la manière de conduire l’audit du harnais cognitif",
        )
        self.assertEqual(
            extract_explicit_recall_topic("What do you remember about my audit priorities?"),
            "my audit priorities",
        )
        self.assertEqual(
            extract_explicit_recall_topic(
                "Tu te rappelles ce qu'on a dit à propos du format des données du Body ?"
            ),
            "format des données du Body",
        )
        self.assertEqual(
            extract_explicit_recall_topic("On a parlé de la pondération de l'attention ?"),
            "la pondération de l'attention",
        )
        self.assertEqual(
            extract_explicit_recall_topic("Do you remember what we discussed about memory recall?"),
            "memory recall",
        )

    def test_visual_tier_is_not_implied_by_recall_language(self):
        query = "Rappelle ce que je t’ai demandé concernant la manière de conduire l’audit"
        self.assertNotIn("image", extract_explicit_recall_topic(query).casefold())

    def test_prior_request_question_routes_to_explicit_recall(self):
        query = (
            "Pour l’audit du harnais, quel résultat final ai-je demandé ? "
            "Réponds depuis un échange antérieur retrouvé, sinon dis que tu ne retrouves pas de source."
        )
        self.assertTrue(is_explicit_memory_recall_query(query))
        topic = extract_explicit_recall_topic(query).casefold()
        self.assertIn("audit du harnais", topic)
        self.assertIn("résultat final", topic)
        self.assertNotIn("échange antérieur", topic)

    def test_historical_request_router_handles_tense_variants(self):
        queries = (
            "Pour l audit du harnais, quel resultat final avais-je demande ?",
            "Pour l’audit, quel résultat ai-je demandé ?",
            "For the audit, what final outcome had I asked you to provide?",
            "For the audit, what final outcome did I ask you to provide?",
        )
        for query in queries:
            with self.subTest(query=query):
                self.assertTrue(is_explicit_memory_recall_query(query))
                topic = extract_explicit_recall_topic(query).casefold()
                self.assertTrue(
                    any(term in topic for term in ("final", "résultat", "resultat", "outcome")),
                    topic,
                )

    def test_explicit_recall_discards_prior_recall_prompt_self_matches(self):
        repeated_recall = {
            "memory_type": "user_message",
            "text": (
                "Pour l’audit du harnais, quel résultat final ai-je demandé ? "
                "Réponds depuis un échange antérieur retrouvé."
            ),
        }
        factual_source = {
            "memory_type": "user_message",
            "text": "La preuve utile est de définir les modules requis par scénario, puis vérifier sorties et effets en aval.",
        }
        historical_exchange = {
            "memory_type": "episodic",
            "text": "User: Pour l'audit, quel résultat final ai-je demandé? | Lumina: Je ne retrouve pas la source.",
        }

        self.assertEqual(
            filter_recall_query_records([repeated_recall, factual_source, historical_exchange]),
            [factual_source],
        )

    def test_explicit_recall_filters_neighboring_status_and_prior_recall_episodes(self):
        query = (
            "Pour l’audit du harnais, quel résultat final ai-je demandé ? "
            "Réponds depuis un échange antérieur retrouvé."
        )
        neighboring_status = {
            "memory_type": "user_message",
            "text": (
                "Reprenons l’audit du harnais après ce redémarrage. Quel est le dernier "
                "point vérifié avec preuve, quelle prochaine étape reste à examiner ?"
            ),
        }
        previous_recall = {
            "memory_type": "episodic",
            "text": (
                "Conversation — User: Pour l’audit du harnais, quel résultat final ai-je "
                "demandé ? | Lumina: Je ne retrouve pas la source demandée."
            ),
        }
        relevant_source = {
            "memory_type": "user_message",
            "text": (
                "Pour le résultat final de l’audit du harnais, j’ai demandé d’évaluer "
                "les sorties et effets aval sur des scénarios représentatifs, puis "
                "de classer les modules."
            ),
        }

        selected = filter_recall_query_records(
            [neighboring_status, previous_recall, relevant_source], query=query,
        )

        self.assertEqual(selected, [relevant_source])
        # This reproduces the live turn's actual retrieval failure: when only
        # neighboring audit-status prompts and earlier retries are available,
        # none may be passed to generation as evidence for the requested result.
        self.assertEqual(
            filter_recall_query_records(
                [neighboring_status, previous_recall], query=query,
            ),
            [],
        )

    def test_explicit_recall_focus_keeps_english_source_and_rejects_unrelated(self):
        query = "For the audit, what final outcome did I ask you to provide?"
        source = {
            "memory_type": "user_message",
            "text": "The final outcome I asked for was a conclusive audit of the cognitive harness modules and their outputs.",
        }
        unrelated = {"memory_type": "user_message", "text": "What color is the camera status LED?"}

        self.assertEqual(
            filter_recall_query_records([unrelated, source], query=query),
            [source],
        )

    def test_prior_request_question_english_routes_to_explicit_recall(self):
        query = "For the audit, what final outcome did I ask you to provide?"
        self.assertTrue(is_explicit_memory_recall_query(query))
        topic = extract_explicit_recall_topic(query).casefold()
        self.assertIn("audit", topic)
        self.assertIn("final outcome", topic)

    def test_text_recall_excludes_visual_results_from_mixed_retrieval_pool(self):
        records = [
            {"memory_tier": "interaction", "memory_type": "user_message", "text": "audit priority"},
            {"memory_tier": "visual", "memory_type": "visual_perception", "text": "camera scene"},
        ]
        self.assertEqual(
            filter_memories_by_modality(records, include_visual=False),
            [records[0]],
        )
        self.assertEqual(
            filter_memories_by_modality(records, include_visual=True),
            records,
        )

    def test_visual_memory_routing_uses_current_utterance_not_learned_topic(self):
        self.assertFalse(is_visual_memory_query("Quel correctif récent est chargé ?"))
        self.assertTrue(is_visual_memory_query("Que vois-tu dans cette image ?"))
        self.assertTrue(is_visual_memory_query("What does the camera see?"))

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

    def test_persisted_user_message_is_retrievable_for_a_later_turn(self):
        system = self._system()
        stored = system.add_memory(
            "User message: Lumina sends commands to Flux in one direction.",
            memory_type="user_message",
        )

        recalled = system.retrieve_user_authored_memories(
            "How does the Lumina Flux command flow work?", limit=1,
        )

        self.assertTrue(stored)
        self.assertEqual(len(recalled), 1)
        self.assertEqual(recalled[0]["memory_type"], "user_message")
        self.assertIn("one direction", recalled[0]["text"])
        self.assertGreater(recalled[0]["relevance"], 0)

    def test_user_source_lane_uses_semantic_neighbours_before_bounded_lexical_fallback(self):
        self.rows = [
            {"id": 1, "faiss_id": 1,
             "text": "User message: Lumina is the master brain; communication goes to Flux in one direction.",
             "timestamp": datetime.now().isoformat(), "impact_score": 0.5,
             "memory_type": "user_message", "memory_tier": "interaction",
             "emotional_valence": "Neutral", "access_count": 0},
            {"id": 2, "faiss_id": 2,
             "text": "Conversation — User: How should Lumina and Flux work? | Lumina: Flux is the master and communication is bidirectional.",
             "timestamp": datetime.now().isoformat(), "impact_score": 0.9,
             "memory_type": "episodic", "memory_tier": "interaction",
             "emotional_valence": "Neutral", "access_count": 0},
        ]
        system = self._system(embedder=_Embedder(), index=_UserSourceIndex())

        result = system.retrieve_user_authored_memories(
            "Who leads and is the dialogue one-way or reciprocal?", limit=1
        )

        self.assertEqual([row["id"] for row in result], [1])
        self.assertGreater(result[0]["relevance"], 0)
        self.assertEqual(system.persistence.all_memory_queries, [])


if __name__ == "__main__":
    unittest.main()
