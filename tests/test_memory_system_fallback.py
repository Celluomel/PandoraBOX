import sys
import sqlite3
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
from cognition.ai_system import EnhancedMemorySystem, EnhancedPersistence
from cognition.ai_system import retrieve_memories_for_user
from cognition.memory_retrieval import (
    extract_explicit_recall_topic,
    explicit_recall_source_result,
    explicit_recall_abstention_result,
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
        self.conversation_source_queries = []

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

    def get_conversation_source_memories(self, query=None, limit=2000):
        self.conversation_source_queries.append((query, limit))
        return [
            row for row in self.rows
            if row.get("memory_type") in {"user_message", "episodic"}
        ][:limit]

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


class _UnexpectedExplicitRecallSearchIndex:
    # Explicit recall should use the source archive, not let a recent
    # nearest-neighbor window determine which historical user turns exist.
    ntotal = 240

    def search(self, *_args):
        raise AssertionError("explicit recall must search source conversation records")


class _SemanticExplicitRecallSearchIndex:
    ntotal = 240

    def __init__(self, faiss_id):
        self.faiss_id = faiss_id
        self.calls = 0

    def search(self, _query, count):
        self.calls += 1
        distances = np.full((1, count), np.float32(2.0), dtype="float32")
        indices = np.full((1, count), -1, dtype="int64")
        distances[0, 0] = np.float32(0.2)
        indices[0, 0] = self.faiss_id
        return distances, indices


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
            embedding_model_name="test-embedder",
        )
        system.embedding_dim = 3
        system.embedding_model = embedder
        system.faiss_index = index
        system._counter = 0
        import threading
        system._lock = threading.RLock()
        return system

    def test_persisted_memory_scope_isolates_users_and_quarantines_legacy_dialogue(self):
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            persistence = EnhancedPersistence(SimpleNamespace(
                name=str(Path(folder) / "memory.sqlite3"), timeout=5.0,
                check_same_thread=False, max_backups=2,
            ))
            entries = [
                ("Fred private statement", "user_message", "interaction", "fred"),
                ("Other private statement", "user_message", "interaction", "other"),
                ("Legacy unowned statement", "episodic", "interaction", None),
                ("Shared cognitive principle", "principle", "cognitive", None),
            ]
            for text, memory_type, tier, owner in entries:
                assert persistence.add_memory({
                    "text": text, "timestamp": datetime.now().isoformat(),
                    "impact_score": 0.5, "emotional_valence": "Neutral",
                    "arousal_level": "Low", "memory_type": memory_type,
                    "memory_tier": tier, "owner_user_id": owner,
                    "access_count": 0, "last_accessed": datetime.now().isoformat(),
                    "semantic_hash": ai_system_module.generate_semantic_hash(text, owner),
                }) is not None

            fred_rows = persistence.get_all_memories(owner_user_id="fred")
            fred_texts = {row["text"] for row in fred_rows}
            self.assertIn("Fred private statement", fred_texts)
            self.assertNotIn("Shared cognitive principle", fred_texts)
            self.assertNotIn("Other private statement", fred_texts)
            self.assertNotIn("Legacy unowned statement", fred_texts)
            scoped_system = EnhancedMemorySystem.__new__(EnhancedMemorySystem)
            scoped_system.persistence = persistence
            scoped_system.config = SimpleNamespace(max_memory_retrieval=8)
            scoped_system.embedding_model = None
            scoped_system.faiss_index = None
            scoped_system.embedding_dim = 3
            retrieved = scoped_system.retrieve_memories(
                "private statement", owner_user_id="fred",
            )
            self.assertEqual([row["text"] for row in retrieved], ["Fred private statement"])
            self.assertEqual(
                [row["text"] for row in persistence.get_conversation_source_memories(
                    owner_user_id="fred"
                )],
                ["Fred private statement"],
            )
            self.assertEqual(
                {row["text"] for row in persistence.get_memories_by_ids(
                    [1, 2, 3, 4], owner_user_id="fred"
                )},
                {"Fred private statement"},
            )
            self.assertNotEqual(
                ai_system_module.generate_semantic_hash("same fact", "fred"),
                ai_system_module.generate_semantic_hash("same fact", "other"),
            )
            persistence.close_thread_connection()

    def test_user_scope_is_enforced_for_legacy_memory_adapters(self):
        class LegacyAdapter:
            def retrieve_memories(self, query, limit=None):
                return [
                    {"text": "Fred fact", "owner_user_id": "fred"},
                    {"text": "Other user's fact", "owner_user_id": "other"},
                    {"text": "Legacy ownerless fact", "owner_user_id": None},
                ]

        rows = retrieve_memories_for_user(LegacyAdapter(), "fact", "fred", limit=3)
        self.assertEqual([row["text"] for row in rows], ["Fred fact"])

    def test_legacy_database_migration_adds_owner_without_claiming_old_dialogue(self):
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            db_path = Path(folder) / "legacy.sqlite3"
            connection = sqlite3.connect(db_path)
            connection.execute("""
                CREATE TABLE memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, faiss_id INTEGER UNIQUE,
                    text TEXT NOT NULL, timestamp TEXT NOT NULL, impact_score REAL,
                    emotional_valence TEXT, arousal_level TEXT, memory_type TEXT,
                    memory_tier TEXT, access_count INTEGER, last_accessed TEXT,
                    semantic_hash TEXT UNIQUE, created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.execute(
                "INSERT INTO memories (faiss_id,text,timestamp,memory_type,memory_tier,semantic_hash) "
                "VALUES (1,'User message: legacy secret','2026-11-01','user_message','interaction','legacy-hash')"
            )
            connection.commit()
            connection.close()

            persistence = EnhancedPersistence(SimpleNamespace(
                name=str(db_path), timeout=5.0,
                check_same_thread=False, max_backups=2,
            ))
            with persistence.get_connection() as conn:
                columns = {
                    row[1] for row in conn.execute("PRAGMA table_info(memories)").fetchall()
                }
            self.assertIn("owner_user_id", columns)
            self.assertEqual(
                persistence.get_conversation_source_memories(owner_user_id="fred"), []
            )
            persistence.close_thread_connection()

    def test_personal_tier_recall_requires_matching_owner(self):
        system = self._system()
        system.persistence.rows = [
            {"id": 1, "faiss_id": 1, "text": "Fred's family fact", "timestamp": datetime.now().isoformat(),
             "impact_score": 0.9, "memory_type": "personal_fact", "memory_tier": "personal",
             "owner_user_id": "fred"},
            {"id": 2, "faiss_id": 2, "text": "Other user's family fact", "timestamp": datetime.now().isoformat(),
             "impact_score": 0.9, "memory_type": "personal_fact", "memory_tier": "personal",
             "owner_user_id": "other"},
        ]

        assert [row["id"] for row in system.retrieve_by_tier(
            "family fact", "personal", owner_user_id="fred",
        )] == [1]

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
        self.assertEqual(receipt["embedding_model"], "test-embedder")
        self.assertEqual(receipt["embedding_dim"], 3)
        self.assertIsNone(receipt["fallback_reason"])
        self.assertEqual(receipt["vector_candidate_count"], 2)
        self.assertEqual(receipt["returned_count"], 2)

    def test_faiss_widens_shared_index_search_until_owner_scoped_rows_appear(self):
        now = datetime.now().isoformat()
        rows = [
            {"id": i, "faiss_id": i, "text": f"Other profile memory {i}",
             "timestamp": now, "impact_score": 0.5, "memory_type": "project",
             "memory_tier": "personal", "owner_user_id": "other"}
            for i in range(1, 20)
        ]
        rows.append({
            "id": 20, "faiss_id": 20, "text": "Fred audit objective",
            "timestamp": now, "impact_score": 0.9, "memory_type": "user_message",
            "memory_tier": "personal", "owner_user_id": "fred",
        })

        class _SharedIndex:
            ntotal = 20

            def __init__(self):
                self.requested_counts = []

            def search(self, _query, count):
                self.requested_counts.append(count)
                ids = np.arange(1, count + 1, dtype="int64")
                return np.full((1, count), 0.2, dtype="float32"), ids.reshape(1, -1)

        index = _SharedIndex()
        system = self._system(embedder=_Embedder(), index=index)
        system.persistence = _Persistence(rows)

        memories, receipt = system.retrieve_memories_with_receipt(
            "audit objective", owner_user_id="fred",
        )

        self.assertEqual(index.requested_counts, [15, 20])
        self.assertEqual([row["owner_user_id"] for row in memories], ["fred"])
        self.assertEqual(receipt["backend"], "faiss")
        self.assertEqual(receipt["fallback_reason"], None)

    def test_explicit_recall_accepts_determiner_led_french_topic(self):
        query = "Rappelle-moi l’objectif principal de notre audit du harnais cognitif."

        self.assertTrue(is_explicit_memory_recall_query(query))
        self.assertIn("objectif principal", extract_explicit_recall_topic(query).casefold())
        self.assertIn("audit du harnais cognitif", extract_explicit_recall_topic(query).casefold())

    def test_generic_history_recall_discards_tangential_user_source_and_abstains(self):
        query = "Rappelle-moi l’objectif principal de notre audit du harnais cognitif."
        tangential_source = {
            "id": 9768,
            "memory_type": "user_message",
            "text": "User message: n'est-ce pas la structure même de ton harnais cognitif",
            "relevance": 0.632,
        }

        filtered = filter_recall_query_records([tangential_source], query=query)
        result = explicit_recall_abstention_result(query, filtered)

        self.assertEqual(filtered, [])
        self.assertEqual(result["status"], "abstained_no_source")

    def test_generic_history_recall_keeps_a_source_with_subject_coverage(self):
        query = "Rappelle-moi l’objectif principal de notre audit du harnais cognitif."
        source = {
            "memory_type": "user_message",
            "text": "L'objectif principal de notre audit du harnais cognitif est de corriger le harnais cognitif dans l'exécution de son code.",
            "relevance": 0.9,
        }

        filtered = filter_recall_query_records([source], query=query)

        self.assertEqual(filtered, [source])

    def test_direct_recall_grammar_does_not_match_a_recall_infinitive(self):
        self.assertFalse(is_explicit_memory_recall_query("Rappelle-moi de vérifier demain."))

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

    def test_relative_clause_recall_routes_to_historical_source(self):
        cases = (
            (
                "Rappelle-moi le dernier objectif cognitif dont nous avons parlé.",
                "le dernier objectif cognitif",
            ),
            (
                "Remind me the last goal we discussed.",
                "the last goal",
            ),
        )
        for query, expected_topic in cases:
            with self.subTest(query=query):
                self.assertTrue(is_explicit_memory_recall_query(query))
                self.assertEqual(
                    extract_explicit_recall_topic(query).casefold(),
                    expected_topic,
                )

    def test_memory_write_instruction_is_not_misclassified_as_recall(self):
        instruction = (
            "For this audit only, remember the test phrase amber kite 731 "
            "so I can ask for it in my next message."
        )
        historical_question = (
            "What exact test phrase did I ask you to remember for this audit?"
        )

        self.assertFalse(is_explicit_memory_recall_query(instruction))
        self.assertTrue(is_explicit_memory_recall_query(historical_question))
        self.assertEqual(
            filter_recall_query_records(
                [{"memory_type": "user_message", "text": instruction}],
                query=historical_question,
            ),
            [{"memory_type": "user_message", "text": instruction}],
        )
        topic = extract_explicit_recall_topic(historical_question).casefold()
        self.assertIn("test phrase", topic)
        self.assertIn("audit", topic)

    def test_ask_for_exact_instructions_given_routes_to_source_recall(self):
        query = (
            "What exact instructions did I give you for the ongoing cognitive harness audit? "
            "Quote the exact wording from my message."
        )
        self.assertTrue(is_explicit_memory_recall_query(query))
        topic = extract_explicit_recall_topic(query).casefold()
        self.assertIn("cognitive harness audit", topic)
        self.assertNotIn("quote", topic)

        source = {
            "id": 874,
            "memory_type": "user_message",
            "text": (
                "User message: Continue the cognitive harness audit, identify issues, "
                "fix them and commit the repairs."
            ),
            "relevance": 0.91,
        }
        recalled = explicit_recall_source_result(query, [source])
        self.assertEqual(recalled["status"], "supported_verbatim_source")
        self.assertIn("Continue the cognitive harness audit", recalled["answer"])

    def test_repeated_instruction_recall_accepts_adverbial_historical_verb(self):
        query = (
            "Which instruction have I repeatedly given you about using a dictionary "
            "to route or answer questions?"
        )
        self.assertTrue(is_explicit_memory_recall_query(query))
        topic = extract_explicit_recall_topic(query).casefold()
        self.assertIn("dictionary", topic)
        self.assertIn("route", topic)

    def test_explicit_recall_can_retrieve_a_remember_instruction_as_source(self):
        self.rows = [{
            "id": 73, "faiss_id": 73,
            "text": (
                "User message: For this audit only, remember the test phrase "
                "amber kite 731 so I can ask for it in my next message."
            ),
            "timestamp": datetime.now().isoformat(), "impact_score": 0.5,
            "memory_type": "user_message", "memory_tier": "interaction",
            "emotional_valence": "Neutral", "access_count": 0,
        }]

        recalled = self._system().retrieve_user_authored_memories(
            "Conversation exact test phrase for this audit",
            limit=6, explicit_recall=True,
        )

        self.assertEqual([memory["id"] for memory in recalled], [73])
        self.assertIn("amber kite 731", recalled[0]["text"])

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

    def test_sensor_value_given_in_prior_turn_routes_to_source_recall(self):
        queries = (
            "Peux-tu rappeler quelle valeur du capteur je t’ai donnée au tour précédent ?",
            "Quelle valeur du capteur t’ai-je indiquée dans mon message précédent ?",
            "What sensor reading did I give you in the previous turn?",
            "Which value did I tell you in my last message?",
            "Can you recall the exact sensor value I gave you in my previous message?",
        )
        for query in queries:
            with self.subTest(query=query):
                self.assertTrue(is_explicit_memory_recall_query(query))
                topic = extract_explicit_recall_topic(query).casefold()
                self.assertTrue(
                    any(term in topic for term in ("capteur", "sensor", "value", "reading")),
                    topic,
                )

        query = queries[0]
        source = {
            "memory_type": "user_message",
            "text": "User message: La dernière valeur du capteur que je t’ai donnée est 0,8 m.",
            "relevance": 0.9,
        }
        eligible = filter_recall_query_records([source], query=query)
        self.assertEqual(eligible, [source])
        self.assertIsNone(explicit_recall_abstention_result(query, eligible))
        self.assertEqual(
            explicit_recall_abstention_result(query, [])["status"],
            "abstained_no_source",
        )

    def test_feminine_french_historical_participle_routes_to_explicit_recall(self):
        query = "Dans nos échanges, quelle règle ai-je posée pour les informations des capteurs ?"
        self.assertTrue(is_explicit_memory_recall_query(query))
        topic = extract_explicit_recall_topic(query).casefold()
        self.assertIn("règle", topic)
        self.assertIn("capteurs", topic)

    def test_object_of_what_did_i_ask_you_to_is_routed_as_explicit_recall(self):
        queries = (
            "From my historical exchanges stored in memory, what did I ask you to fix "
            "about the UnboundLocalError involving _deterministic_response?",
            "What did I ask you to fix about the UnboundLocalError involving _deterministic_response?",
            "Which plan did I ask you to summarize earlier in this chat?",
            "Qu’est-ce que je t’ai demandé de corriger à propos de l’erreur UnboundLocalError ?",
        )
        for query in queries:
            with self.subTest(query=query):
                self.assertTrue(is_explicit_memory_recall_query(query))
                topic = extract_explicit_recall_topic(query).casefold()
                self.assertTrue(
                    any(term in topic for term in ("unboundlocalerror", "corriger", "plan")),
                    topic,
                )
                self.assertNotIn("historical exchanges", topic)

    def test_explicit_recall_does_not_accept_neighboring_audit_records_on_one_word(self):
        query = (
            "From my historical exchanges stored in memory, what did I ask you to fix "
            "about the UnboundLocalError involving _deterministic_response?"
        )
        neighbors = [
            {
                "memory_type": "user_message",
                "text": (
                    "User message: For this audit only, remember the test phrase "
                    "amber kite 731 so I can ask for it in my next message."
                ),
            },
            {
                "memory_type": "episodic",
                "text": (
                    "Conversation — User: For this audit, report the cognitive "
                    "module counts. | Lumina: I will check the audit status."
                ),
            },
        ]
        source = {
            "memory_type": "user_message",
            "text": (
                "User message: Please fix the UnboundLocalError involving "
                "_deterministic_response in the response stream."
            ),
        }

        self.assertEqual(filter_recall_query_records(neighbors, query=query), [])
        self.assertEqual(filter_recall_query_records([*neighbors, source], query=query), [source])

    def test_explicit_recall_abstains_instead_of_completing_from_question_when_source_missing(self):
        query = (
            "From my historical exchanges stored in memory, what did I ask you to fix "
            "about the UnboundLocalError involving _deterministic_response?"
        )
        neighbors = [
            {
                "memory_type": "user_message",
                "text": "User message: For this audit only, remember the phrase amber kite 731.",
            },
            {
                "memory_type": "episodic",
                "text": "Conversation — User: For this audit, report module counts. | Lumina: Done.",
            },
        ]
        eligible = filter_recall_query_records(neighbors, query=query)

        result = explicit_recall_abstention_result(query, eligible)

        self.assertEqual(eligible, [])
        self.assertEqual(result["status"], "abstained_no_source")
        self.assertIsNone(result["source_ref"])
        self.assertIn("couldn't retrieve", result["answer"])

    def test_exact_historical_value_abstains_when_only_semantic_neighbors_exist(self):
        query = "What exact checksum string did I give you for the Moonbase regression test?"
        semantic_neighbor = {
            "memory_type": "user_message",
            "text": "User message: For the cognitive harness audit, my test marker for the next turn is cobalt fox 8421.",
            "relevance": 0.99,
        }

        result = explicit_recall_abstention_result(query, [semantic_neighbor])

        self.assertEqual(result["status"], "abstained_insufficient_source_match")
        self.assertIsNone(result["source_ref"])
        self.assertNotIn("cobalt fox 8421", result["answer"])

    def test_explicit_recall_does_not_abstain_when_a_relevant_user_source_exists(self):
        query = "What did I ask you to fix about the UnboundLocalError involving _deterministic_response?"
        source = {
            "memory_type": "user_message",
            "text": "User message: Please fix the UnboundLocalError involving _deterministic_response in the response stream.",
        }
        eligible = filter_recall_query_records([source], query=query)

        self.assertEqual(eligible, [source])
        self.assertIsNone(explicit_recall_abstention_result(query, eligible))

    def test_exact_phrase_recall_returns_the_retrieved_user_source_verbatim(self):
        query = "What exact test phrase did I ask you to remember for this audit?"
        source = {
            "id": 42,
            "memory_type": "user_message",
            "text": (
                "User message: For this audit only, remember the test phrase "
                "amber kite 731 so I can ask for it in my next message."
            ),
            "relevance": 0.91,
        }

        result = explicit_recall_source_result(query, [source])

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "supported_verbatim_source")
        self.assertIn("amber kite 731", result["answer"])
        self.assertIn("Retrieved user-authored source", result["answer"])
        self.assertEqual(result["source_type"], "user_message")

    def test_exact_phrase_recall_never_uses_an_assistant_only_record(self):
        query = "What exact test phrase did I ask you to remember for this audit?"
        assistant_only = {
            "memory_type": "cognitive",
            "text": "Lumina replied: the phrase was amber kite 731.",
            "relevance": 1.0,
        }

        result = explicit_recall_source_result(query, [assistant_only])

        self.assertIsNone(result)

    def test_one_phrase_response_format_does_not_request_verbatim_recall(self):
        query = (
            "Quelle règle ai-je formulée pour les informations des capteurs ? "
            "Réponds en une phrase, sans exemple."
        )
        source = {
            "memory_type": "user_message",
            "text": "User message: Le Body doit interpréter les données brutes de chaque capteur avant de les transmettre au Brain.",
            "relevance": 0.9,
        }

        self.assertIsNone(explicit_recall_source_result(query, [source]))

    def test_imperative_historical_recall_prompt_is_not_a_source(self):
        prompt = {
            "memory_type": "user_message",
            "text": (
                "Rappelle la règle que je t’ai donnée sur la responsabilité du Body "
                "et du Brain quand les capteurs envoient leurs mesures. Explique ce "
                "que le Body doit transmettre et ce que le Brain doit en faire."
            ),
        }

        self.assertTrue(is_explicit_memory_recall_query(prompt["text"]))
        self.assertEqual(filter_recall_query_records([prompt]), [])

    def test_french_recall_of_what_i_asked_is_source_backed_and_filters_prior_prompt(self):
        queries = (
            "Rappelle uniquement ce que je t’ai demandé concernant la manière de conduire l’audit du harnais cognitif.",
            "Rappelle ce que je t'ai demandé concernant la manière de conduire l'audit du harnais cognitif.",
        )
        for query in queries:
            with self.subTest(query=query):
                self.assertTrue(is_explicit_memory_recall_query(query))
                topic = extract_explicit_recall_topic(query).casefold()
                self.assertIn("audit du harnais cognitif", topic)
                prior_prompt = {"memory_type": "user_message", "text": query}
                self.assertEqual(filter_recall_query_records([prior_prompt], query=query), [])

    def test_source_only_french_recall_quotes_relevant_statement_and_skips_old_recall_prompt(self):
        query = "Rappelle uniquement ce que je t’ai demandé concernant la manière de conduire l’audit du harnais cognitif."
        prior_prompt = {"memory_type": "user_message", "text": query, "relevance": 1.0}
        source = {
            "memory_type": "user_message",
            "text": "Pour la manière de conduire l’audit du harnais cognitif, tu m’as demandé de poursuivre, corriger les causes et vérifier les effets en aval.",
            "relevance": 0.82,
        }
        same_topic_but_wrong_instruction = {
            "memory_type": "user_message",
            "text": "Audit technique: donne une phrase sur la fonction du harnais cognitif. Aucune recherche web et aucune action externe.",
            "relevance": 1.0,
        }

        result = explicit_recall_source_result(query, [prior_prompt, same_topic_but_wrong_instruction, source])

        self.assertEqual(result["status"], "supported_verbatim_source")
        self.assertIn(source["text"], result["answer"])
        self.assertNotIn(prior_prompt["text"], result["answer"])

    def test_source_only_french_recall_abstains_when_no_relevant_source_remains(self):
        query = "Rappelle uniquement ce que je t’ai demandé concernant la manière de conduire l’audit du harnais cognitif."
        prior_prompt = {"memory_type": "user_message", "text": query, "relevance": 1.0}
        topic_neighbor = {
            "memory_type": "user_message",
            "text": "Audit technique: donne une phrase sur la fonction du harnais cognitif.",
            "relevance": 1.0,
        }
        filtered = filter_recall_query_records([prior_prompt, topic_neighbor], query=query)

        self.assertEqual(filtered, [topic_neighbor])
        result = explicit_recall_abstention_result(query, filtered)
        self.assertEqual(result["status"], "abstained_insufficient_source_match")

    def test_french_recall_of_instruction_with_only_modifier_uses_prior_source(self):
        query = (
            "Rappelle uniquement la consigne que je t’ai donnée : poursuivre l’audit "
            "sans redémarrer Lumina après chaque correctif, puis vérifier en live à la fin."
        )
        prior_recall_prompt = {"memory_type": "user_message", "text": query, "relevance": 1.0}
        historical_source = {
            "memory_type": "user_message",
            "text": (
                "On va procéder autrement, tu poursuis l’audit, évalues les problèmes "
                "et les fixes, commit sur git les fix, poursuis l’audit sans redémarrer "
                "Lumina sans t’arrêter et ainsi de suite; puis en toute fin on redémarre "
                "Lumina pour vérifier les fixs appliqués."
            ),
            "relevance": 0.86,
        }

        self.assertTrue(is_explicit_memory_recall_query(query))
        filtered = filter_recall_query_records([prior_recall_prompt, historical_source], query=query)
        self.assertEqual(filtered, [historical_source])
        result = explicit_recall_source_result(query, filtered)
        self.assertEqual(result["status"], "supported_verbatim_source")
        self.assertIn(historical_source["text"], result["answer"])

    def test_source_only_instruction_recall_uses_description_after_colon_as_focus(self):
        query = (
            "Rappelle uniquement la consigne que je t’ai donnée : poursuivre l’audit "
            "sans redémarrer Lumina après chaque correctif, puis vérifier en live à la fin."
        )
        prior_prompt = {"memory_type": "user_message", "text": query, "relevance": 1.0}
        source = {
            "memory_type": "user_message",
            "text": (
                "On va procéder autrement : tu poursuis l’audit, évalue les problèmes et "
                "les fixes, commit sur git les fix, poursuis l’audit sans redémarrer "
                "Lumina sans t’arrêter; puis en toute fin on redémarre Lumina pour "
                "vérifier les fixs appliqués."
            ),
            "relevance": 0.86,
        }

        topic = extract_explicit_recall_topic(query).casefold()
        self.assertIn("poursuivre l’audit", topic)
        self.assertNotIn("rappelle", topic)
        self.assertTrue(is_explicit_memory_recall_query(query))
        filtered = filter_recall_query_records([prior_prompt, source], query=query)
        self.assertEqual(filtered, [source])
        result = explicit_recall_source_result(query, filtered)
        self.assertEqual(result["status"], "supported_verbatim_source")
        self.assertIn(source["text"], result["answer"])

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

    def test_explicit_recall_filter_is_reapplied_after_event_and_secondary_lanes(self):
        query = (
            "Pour l’audit du harnais, quel résultat final avais-je demandé ? "
            "Réponds seulement si un souvenir utilisateur pertinent le confirme."
        )
        current_question = {
            "memory_type": "user_message",
            "text": query,
            "source": "faiss_primary",
        }
        prior_answer_episode = {
            "memory_type": "episodic",
            "text": (
                "User: Pour l’audit du harnais, quel résultat final avais-je demandé ? "
                "| Lumina: Je ne retrouve pas la source."
            ),
            "source": "event_tier",
        }
        prior_recall_question = {
            "memory_type": "user_message",
            "text": "Pour l’audit, quel résultat final avais-je demandé auparavant ?",
            "source": "explicit_recall_secondary",
        }
        source_statement = {
            "memory_type": "user_message",
            "text": (
                "Pour l’audit du harnais, la preuve utile est de définir les "
                "modules requis par scénario, puis de vérifier leurs sorties "
                "et effets en aval."
            ),
            "source": "primary",
        }

        # The primary and user-authored pools are filtered first. The event
        # and explicit-recall secondary lanes are appended later in
        # persona_bridge; the final assembly boundary must filter them too.
        primary = filter_recall_query_records(
            [current_question, source_statement], query=query,
        )
        assembled = [*primary, prior_answer_episode, prior_recall_question]
        final_pool = filter_recall_query_records(assembled, query=query)

        self.assertEqual(final_pool, [source_statement])

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

    def test_prior_question_recall_matches_and_quotes_the_previous_user_question(self):
        query = "Rappelle-moi la question que je viens de poser au sujet de tes objectifs actifs."
        previous_question = {
            "id": 9866,
            "memory_type": "user_message",
            "text": "User message: Quels sont tes objectifs actifs ?",
            "relevance": 0.9,
        }
        duplicate_episode = {
            "id": 9865,
            "memory_type": "episodic",
            "text": "Conversation — User: Quels sont tes objectifs actifs ? | Lumina: 5 objectifs enregistrés.",
            "relevance": 0.95,
        }
        unrelated_question = {
            "id": 9867,
            "memory_type": "user_message",
            "text": "User message: Quelle est la couleur de la caméra ?",
            "relevance": 1.0,
        }
        current_recall_prompt = {
            "id": 9868,
            "memory_type": "user_message",
            "text": f"User message: {query}",
            "relevance": 1.0,
        }

        self.assertTrue(is_explicit_memory_recall_query(query))
        self.assertEqual(
            extract_explicit_recall_topic(query).casefold(),
            "tes objectifs actifs",
        )
        eligible = filter_recall_query_records(
            [duplicate_episode, unrelated_question, current_recall_prompt, previous_question],
            query=query,
        )
        self.assertEqual(eligible, [previous_question])
        result = explicit_recall_source_result(query, eligible)
        self.assertEqual(result["status"], "supported_verbatim_source")
        self.assertIn("Quels sont tes objectifs actifs ?", result["answer"])

    def test_unscoped_previous_question_recall_uses_most_recent_question_not_statement(self):
        query = "Quelle était ma question précédente ?"
        older_question = {
            "id": 20,
            "memory_type": "user_message",
            "text": "User message: Quel est le statut du projet ?",
        }
        latest_statement = {
            "id": 22,
            "memory_type": "user_message",
            "text": "User message: Le système est maintenant prêt.",
        }
        latest_question = {
            "id": 23,
            "memory_type": "user_message",
            "text": "User message: Est-ce que la mémoire est restaurée ?",
        }

        eligible = filter_recall_query_records(
            [older_question, latest_statement, latest_question], query=query,
        )

        self.assertEqual(eligible, [latest_question])
        result = explicit_recall_source_result(query, eligible)
        self.assertIn("Est-ce que la mémoire est restaurée ?", result["answer"])

    def test_english_prior_question_recall_routes_to_source_text(self):
        query = "What exact question did I just ask about memory recall?"
        source = {
            "id": 31,
            "memory_type": "user_message",
            "text": "User message: Why did the recent memory recall fail?",
        }

        self.assertTrue(is_explicit_memory_recall_query(query))
        self.assertIn("memory recall", extract_explicit_recall_topic(query).casefold())
        eligible = filter_recall_query_records([source], query=query)
        self.assertEqual(eligible, [source])
        self.assertIn("Why did the recent memory recall fail?", explicit_recall_source_result(query, eligible)["answer"])

    def test_english_prior_question_recall_accepts_unmodified_question_form(self):
        query = "What question did I just ask about memory recall?"
        source = {
            "id": 32,
            "memory_type": "user_message",
            "text": "User message: Why did the recent memory recall fail?",
        }

        self.assertTrue(is_explicit_memory_recall_query(query))
        self.assertIn("memory recall", extract_explicit_recall_topic(query).casefold())
        eligible = filter_recall_query_records([source], query=query)
        self.assertEqual(eligible, [source])
        self.assertIn("Why did the recent memory recall fail?", explicit_recall_source_result(query, eligible)["answer"])

    def test_copular_marker_recall_routes_to_the_matching_user_source(self):
        query = "What was the test marker I gave you for the next turn in the cognitive harness audit?"
        source = {
            "memory_type": "user_message",
            "text": "User message: For the cognitive harness audit, my test marker for the next turn is cobalt fox 8421.",
            "relevance": 0.9,
        }
        unrelated = {
            "memory_type": "user_message",
            "text": "User message: The next audit operation is web_search.",
            "relevance": 1.0,
        }

        self.assertTrue(is_explicit_memory_recall_query(query))
        focus = extract_explicit_recall_topic(query).casefold()
        self.assertIn("test marker", focus)
        self.assertIn("cognitive harness audit", focus)
        self.assertEqual(
            filter_recall_query_records([unrelated, source], query=query),
            [source],
        )
        result = explicit_recall_source_result(query, [unrelated, source])
        self.assertEqual(result["status"], "supported_verbatim_source")
        self.assertIn("cobalt fox 8421", result["answer"])
        self.assertNotIn("web_search", result["answer"])

    def test_exact_marker_recall_rejects_a_recent_source_missing_distinguishing_context(self):
        query = "What was the test marker I gave you for the next turn in the cognitive harness audit?"
        near_match = {
            "memory_type": "user_message",
            "text": (
                "User message: For the cognitive harness audit, the marker "
                "I used was LUMINA-MEMORY-8B2R."
            ),
            "relevance": 0.99,
        }

        eligible = filter_recall_query_records([near_match], query=query)

        self.assertEqual(eligible, [])
        abstention = explicit_recall_abstention_result(query, eligible)
        self.assertEqual(abstention["status"], "abstained_insufficient_source_match")
        self.assertNotIn("LUMINA-MEMORY-8B2R", abstention["answer"])

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

    def test_explicit_recall_does_not_depend_on_recent_faiss_prompt_neighbors(self):
        query = (
            "For the cognitive harness audit, what did I ask you to verify "
            "about module outputs?"
        )
        self.rows = [
            {
                "id": 1, "faiss_id": 1,
                "text": (
                    "For the cognitive harness audit, verify each module's "
                    "outputs and downstream effects against the expected role."
                ),
                "timestamp": datetime.now().isoformat(), "impact_score": 0.5,
                "memory_type": "user_message", "memory_tier": "interaction",
                "emotional_valence": "Neutral", "access_count": 0,
            },
            {
                "id": 2, "faiss_id": 2,
                "text": "For the cognitive harness audit, what did I ask you to verify?",
                "timestamp": datetime.now().isoformat(), "impact_score": 0.5,
                "memory_type": "user_message", "memory_tier": "interaction",
                "emotional_valence": "Neutral", "access_count": 0,
            },
            {
                "id": 3, "faiss_id": 3,
                "text": "Do you remember what I asked about the harness audit?",
                "timestamp": datetime.now().isoformat(), "impact_score": 0.5,
                "memory_type": "user_message", "memory_tier": "interaction",
                "emotional_valence": "Neutral", "access_count": 0,
            },
        ]
        system = self._system(
            embedder=_Embedder(), index=_UnexpectedExplicitRecallSearchIndex(),
        )

        recalled = system.retrieve_user_authored_memories(
            query, limit=1, explicit_recall=True,
        )

        self.assertEqual([memory["id"] for memory in recalled], [1])
        self.assertTrue(
            not system.persistence.all_memory_queries,
            "explicit recall must use the dedicated source archive query",
        )

    def test_explicit_recall_supplements_faiss_with_exact_source_outside_neighbor_window(self):
        query = "What was the test marker I gave you for the next turn in the cognitive harness audit?"
        self.rows = [
            {
                "id": 1, "faiss_id": 1,
                "text": "User message: In the cognitive harness audit, keep focus on Global Workspace outputs.",
                "timestamp": datetime.now().isoformat(), "impact_score": 0.5,
                "memory_type": "user_message", "memory_tier": "interaction",
                "emotional_valence": "Neutral", "access_count": 0,
            },
            {
                "id": 2, "faiss_id": 2,
                "text": "User message: The next audit operation is web_search.",
                "timestamp": datetime.now().isoformat(), "impact_score": 0.5,
                "memory_type": "user_message", "memory_tier": "interaction",
                "emotional_valence": "Neutral", "access_count": 0,
            },
            {
                "id": 3, "faiss_id": 3,
                "text": "User message: For the cognitive harness audit, my test marker for the next turn is cobalt fox 8421.",
                "timestamp": datetime.now().isoformat(), "impact_score": 0.5,
                "memory_type": "user_message", "memory_tier": "interaction",
                "emotional_valence": "Neutral", "access_count": 0,
            },
        ]

        class _IncompleteSemanticWindow:
            ntotal = 240

            def search(self, _query, _count):
                return (
                    np.array([[0.1, 0.2]], dtype="float32"),
                    np.array([[1, 2]], dtype="int64"),
                )

        system = self._system(embedder=_Embedder(), index=_IncompleteSemanticWindow())
        recalled = system.retrieve_user_authored_memories(
            query, limit=6, explicit_recall=True,
        )

        self.assertEqual([memory["id"] for memory in recalled], [3])
        self.assertIn("cobalt fox 8421", recalled[0]["text"])
        self.assertEqual(system.persistence.conversation_source_queries, [(query, 128)])

    def test_explicit_recall_recovers_user_segment_from_legacy_episodic_dialogue(self):
        query = "For the cognitive harness audit, what did I say about module outputs?"
        assistant_reply = "Lumina invented a long answer about quantum cognition."
        self.rows = [{
            "id": 7, "faiss_id": 7,
            "text": (
                "Conversation — User: For the cognitive harness audit, "
                "verify each module's outputs and downstream effects. "
                "(felt neutral) | Lumina: " + assistant_reply
            ),
            "timestamp": datetime.now().isoformat(), "impact_score": 0.5,
            "memory_type": "episodic", "memory_tier": "interaction",
            "emotional_valence": "Neutral", "access_count": 0,
        }]
        system = self._system(embedder=_Embedder(), index=_UnexpectedExplicitRecallSearchIndex())

        recalled = system.retrieve_user_authored_memories(
            query, limit=1, explicit_recall=True,
        )
        rendered = format_memory_for_prompt(recalled[0])

        self.assertEqual(len(recalled), 1)
        self.assertEqual(recalled[0]["source"], "legacy_episodic_user_source")
        self.assertIn("verify each module's outputs", rendered)
        self.assertIn("assistant reply omitted", rendered)
        self.assertNotIn(assistant_reply, rendered)
        merged = merge_user_authored_memories(
            [{"id": 99, "memory_type": "episodic", "text": "unrelated"}],
            recalled,
            limit=2,
        )
        self.assertEqual(merged[0]["id"], 7)

    def test_explicit_recall_uses_semantic_source_fallback_for_paraphrase(self):
        query = (
            "Quel principe général avais-je demandé pour le parcours des mesures, "
            "du capteur jusqu’à l’analyse cognitive ?"
        )
        self.rows = [{
            "id": 31, "faiss_id": 31,
            "text": (
                "User message: un capteur renvoie une donnée brute; le Body doit "
                "renvoyer une interprétation claire pour tous les capteurs."
            ),
            "timestamp": datetime.now().isoformat(), "impact_score": 0.5,
            "memory_type": "user_message", "memory_tier": "interaction",
            "emotional_valence": "Neutral", "access_count": 0,
        }]
        index = _SemanticExplicitRecallSearchIndex(faiss_id=31)
        system = self._system(embedder=_Embedder(), index=index)

        recalled = system.retrieve_user_authored_memories(
            query, limit=6, explicit_recall=True,
        )

        self.assertEqual(index.calls, 1)
        self.assertEqual([memory["id"] for memory in recalled], [31])
        self.assertEqual(recalled[0]["memory_type"], "user_message")
        self.assertIn("interprétation claire", recalled[0]["text"])
        self.assertEqual(system.persistence.conversation_source_queries, [(query, 128)])

    def test_explicit_recall_deduplicates_user_message_and_episodic_copy(self):
        query = "For the cognitive harness audit, what did I ask about module outputs?"
        user_text = (
            "For the cognitive harness audit, verify module outputs and downstream effects."
        )
        self.rows = [
            {
                "id": 8, "faiss_id": 8,
                "text": "User message: " + user_text,
                "timestamp": datetime.now().isoformat(), "impact_score": 0.5,
                "memory_type": "user_message", "memory_tier": "interaction",
                "emotional_valence": "Neutral", "access_count": 0,
            },
            {
                "id": 7, "faiss_id": 7,
                "text": (
                    "Conversation — User: " + user_text + " (felt neutral) "
                    "| Lumina: A duplicate assistant response."
                ),
                "timestamp": datetime.now().isoformat(), "impact_score": 0.5,
                "memory_type": "episodic", "memory_tier": "interaction",
                "emotional_valence": "Neutral", "access_count": 0,
            },
        ]

        recalled = self._system().retrieve_user_authored_memories(
            query, limit=6, explicit_recall=True,
        )

        self.assertEqual(len(recalled), 1)
        self.assertEqual(recalled[0]["id"], 8)
        self.assertEqual(recalled[0]["memory_type"], "user_message")

    def test_conversation_source_reader_ranks_and_bounds_rows_in_sql(self):
        persistence = EnhancedPersistence.__new__(EnhancedPersistence)
        connection = sqlite3.connect(":memory:")
        connection.execute("""
            CREATE TABLE memories (
                id INTEGER, faiss_id INTEGER, text TEXT, timestamp TEXT,
                impact_score REAL, emotional_valence TEXT, arousal_level TEXT,
                memory_type TEXT, memory_tier TEXT, access_count INTEGER,
                owner_user_id TEXT
            )
        """)
        records = [
            (1, 1, "User message: valeur du capteur = 0,8 m pendant l’audit",
             "2026-11-01", 0.5, "Neutral", "Low", "user_message", "interaction", 0),
            (2, 2, "User message: conversation sur le harnais cognitif",
             "2026-11-02", 0.5, "Neutral", "Low", "user_message", "interaction", 0),
            (3, 3, "Conversation — User: la valeur du capteur était 0,8 m | Lumina: reçu",
             "2026-11-03", 0.5, "Neutral", "Low", "episodic", "interaction", 0),
            (4, 4, "Assistant: valeur du capteur reçue", "2026-11-04", 0.5,
             "Neutral", "Low", "assistant_message", "interaction", 0),
        ]
        records = [record + (None,) for record in records]
        connection.executemany("INSERT INTO memories VALUES (?,?,?,?,?,?,?,?,?,?,?)", records)

        @contextmanager
        def get_connection():
            yield connection

        persistence.get_connection = get_connection
        results = persistence.get_conversation_source_memories(
            query="Quelle valeur du capteur m’as-tu rappelée ?", limit=1,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 3)
        self.assertEqual(results[0]["memory_type"], "episodic")

    def test_cross_pool_merge_deduplicates_same_user_turn(self):
        user_message = {
            "id": 8,
            "memory_type": "user_message",
            "text": "User message: Keep the audit focused on causal module execution.",
        }
        episodic_copy = {
            "id": 7,
            "memory_type": "episodic",
            "text": (
                "Conversation — User: Keep the audit focused on causal module execution. "
                "(felt neutral) | Lumina: Historical assistant text."
            ),
        }
        distinct_episode = {
            "id": 6,
            "memory_type": "episodic",
            "text": "Conversation — User: Check memory recall next. | Lumina: Done.",
        }

        merged = merge_user_authored_memories(
            [episodic_copy, distinct_episode], [user_message], limit=5,
        )

        self.assertEqual([memory["id"] for memory in merged], [8, 6])
        self.assertEqual(merged[0]["memory_type"], "user_message")

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

