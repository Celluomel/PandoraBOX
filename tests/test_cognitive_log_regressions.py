"""Regression tests for concrete cognitive defects found in the Nov 9 log."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import threading
import tempfile
import time
import types
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

# Import focused modules without executing the package-level application
# bootstrap (`cognition.__init__` imports the full model/ML dependency stack).
ROOT = Path(__file__).parents[1]
_modules_before = set(sys.modules)
for package_name, package_path in (
    ("cognition", ROOT / "cognition"),
    ("core", ROOT / "core"),
    ("core.data", ROOT / "core" / "data"),
):
    if package_name not in sys.modules:
        package = types.ModuleType(package_name)
        package.__path__ = [str(package_path)]
        sys.modules[package_name] = package

from cognition.goal_engine import GoalEngine, Motivation
from cognition.goal_quality_filter import GoalQualityFilter
from cognition.profile_flow import update_behavioral_user_profile
from cognition.belief_bootstrapper import BeliefBootstrapper
from cognition.tension_topics import generate_identity_topic
from cognition.grounded_introspection import GroundedIntrospectionGenerator
from cognition.semantic_extractor import SemanticExtractor
from cognition.semantic_memory import SemanticMemory
from cognition.self_concept_synchronizer import SelfConceptSynchronizer
from cognition.self_concept import SelfConceptSystem
from cognition.cognitive_attention_engine import CognitiveAttentionEngine, MODULES
from cognition.contextual_attention_memory import ContextualAttentionMemory
from cognition.decision_commitment import Commitment, DecisionCommitmentLayer
from cognition.ai_identity import (
    AIIdentity, CoreValues, IdentityAnalyzer, IdentityComponent, IdentitySystem,
    measured_identity_coherence_below,
)
from cognition.self_description import SelfDescription
from cognition.simple_thought_evaluator import SimpleThoughtEvaluator
from cognition.turn_context_evidence import (
    USER_PROFILE_PROVENANCE_POLICY,
    audit_safe_turn_summary,
    format_memory_for_prompt,
    memory_embedding_text,
    memory_prompt_injection_evidence,
    memory_retrieval_evidence,
    profile_context_evidence,
)
from cognition.thought_thread_engine import ThoughtThreadEngine
from managers.user_manager import UserManager

# Keep the package namespace clean for the rest of unittest discovery. The
# imported class objects remain usable by these isolated tests.
for _name in list(sys.modules):
    if _name not in _modules_before and (
        _name == "cognition" or _name.startswith("cognition.")
        or _name in {"core", "core.data"} or _name.startswith("core.data.")
    ):
        sys.modules.pop(_name, None)


class CognitiveLogRegressionTests(unittest.TestCase):
    def test_user_profile_sources_are_kept_epistemically_separate(self):
        self.assertIn("named UserManager profile", USER_PROFILE_PROVENANCE_POLICY)
        self.assertIn("WorldModel behavioral interaction model", USER_PROFILE_PROVENANCE_POLICY)
        self.assertIn("if the count is zero, say there are none", USER_PROFILE_PROVENANCE_POLICY)

    def test_behavioral_profile_updates_only_on_human_turns_and_returns_receipt(self):
        calls = []

        class _WorldModel:
            def update_from_interaction(self, **kwargs):
                calls.append(kwargs)
                return SimpleNamespace(interaction_count=12)

        peer = update_behavioral_user_profile(
            _WorldModel(), user_id="flux", user_text="peer text", response="peer reply",
            emotion="neutral", human_interaction=False,
        )
        human = update_behavioral_user_profile(
            _WorldModel(), user_id="fred", user_text="human text", response="answer",
            emotion="neutral", human_interaction=True,
        )

        self.assertEqual(peer["status"], "skipped_by_scope")
        self.assertFalse(peer["changed"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["user_id"], "fred")
        self.assertEqual(human["status"], "updated")
        self.assertEqual(human["interaction_count"], 12)

    def test_memory_and_profile_trace_receipts_link_context_without_exposing_text(self):
        memories = [{
            "id": "memory-private-17",
            "text": "A private remembered conversation detail",
            "memory_tier": "personal",
            "memory_type": "conversation",
            "timestamp": "2026-11-01T12:00:00",
        }]
        evidence = memory_retrieval_evidence("what did we discuss?", memories)
        profile = profile_context_evidence(
            "injected", "named_profile", "Preferences: private preference."
        )

        self.assertEqual(evidence["candidate_count"], 1)
        self.assertEqual(evidence["candidates"][0]["memory_tier"], "personal")
        self.assertEqual(len(evidence["candidates"][0]["ref"]), 20)
        self.assertNotIn("private remembered conversation detail", str(evidence))
        self.assertNotIn("private preference", str(profile))
        self.assertEqual(profile["status"], "injected")
        self.assertEqual(profile["quality"], "present")

        counted_profile = profile_context_evidence(
            "injected", "named_profile", "hashed context", {
                "explicit_user_stated_entries": 0,
                "legacy_unverified_entries": 1,
                "display_name_source": "source_not_recorded",
                "categories": {"preferences": {"explicit_user_stated": 0, "legacy_unverified": 1}},
            },
        )
        counted = audit_safe_turn_summary(counted_profile)
        self.assertEqual(counted["provenance_summary"]["explicit_user_stated_entries"], 0)
        self.assertEqual(counted["provenance_summary"]["display_name_source"], "source_not_recorded")
        self.assertEqual(counted["provenance_summary"]["categories"]["preferences"]["legacy_unverified"], 1)
        empty_profile = profile_context_evidence("empty", "no_named_profile", "")
        self.assertEqual(empty_profile["quality"], "empty")
        self.assertEqual(audit_safe_turn_summary(empty_profile)["quality"], "empty")

    def test_memory_retrieval_keeps_user_query_separate_from_attention_mode(self):
        query = "Quelle règle avons-nous définie pour Lumina et Flux ?"
        evidence = memory_retrieval_evidence(
            query,
            [{"id": "memory-1", "text": "decision", "relevance": 0.82}],
            query_source="user_input",
            attention_mode="relational",
            retrieval_receipt={
                "backend": "lexical",
                "fallback_reason": "empty_vector_index",
                "vector_candidate_count": 0,
                "returned_count": 1,
                "elapsed_ms": 2.5,
            },
        )

        self.assertEqual(evidence["query_sha256"], hashlib.sha256(query.encode()).hexdigest())
        summary = audit_safe_turn_summary(evidence)
        self.assertEqual(summary["query_source"], "user_input")
        self.assertEqual(summary["attention_mode"], "relational")
        self.assertEqual(summary["candidates"][0]["relevance"], 0.82)
        self.assertEqual(summary["retrieval"]["backend"], "lexical")
        self.assertEqual(summary["retrieval"]["fallback_reason"], "empty_vector_index")
        self.assertEqual(summary["retrieval"]["primary_returned_count"], 1)
        self.assertEqual(summary["retrieval"]["final_pool_count"], 1)

    def test_memory_trace_reports_actual_faiss_model_without_local_path(self):
        evidence = memory_retrieval_evidence(
            "question", [], retrieval_receipt={
                "backend": "faiss",
                "embedding_model": r"C:\Users\private\models\text-embedding-nomic-embed-text-v1.5",
                "embedding_dim": 768,
                "vector_candidate_count": 3,
                "returned_count": 1,
                "elapsed_ms": 12.0,
            },
        )

        assert evidence["retrieval"]["embedding_model"] == "text-embedding-nomic-embed-text-v1.5"
        assert evidence["retrieval"]["embedding_dim"] == 768
        summary = audit_safe_turn_summary(evidence)
        assert summary["retrieval"]["embedding_model"] == "text-embedding-nomic-embed-text-v1.5"
        assert summary["retrieval"]["embedding_dim"] == 768
        assert "C:\\Users" not in repr(summary)

    def test_prompt_memory_keeps_user_message_separate_from_unverified_lumina_reply(self):
        rendered = format_memory_for_prompt({
            "memory_type": "episodic",
            "text": (
                "Conversation — User: Quelle règle avons-nous définie ? "
                "| Lumina: Nous avons défini que les échanges sont bidirectionnels."
            ),
        })

        self.assertIn("USER MESSAGE", rendered)
        self.assertIn("a question alone does not establish its answer", rendered)
        self.assertIn("LUMINA REPLY", rendered)
        self.assertIn("unverified and not proof", rendered)

    def test_user_message_memory_gets_clean_embedding_and_explicit_prompt_provenance(self):
        self.assertEqual(
            memory_embedding_text("User message: Lumina is primary; messages go to Flux.", "user_message"),
            "Lumina is primary; messages go to Flux.",
        )
        rendered = format_memory_for_prompt({
            "memory_type": "user_message",
            "text": "User message: Lumina is primary; Flux is the secondary child brain.",
        })
        self.assertIn("USER MESSAGE", rendered)
        self.assertIn("separately indexed, user-authored", rendered)
        self.assertIn("a question alone does not establish its answer", rendered)
        evidence = memory_retrieval_evidence("who is primary?", [{
            "id": "user-message-1", "text": "User message: Lumina is primary.",
            "memory_type": "user_message", "memory_tier": "interaction",
        }])
        self.assertTrue(evidence["candidates"][0]["has_user_message"])

    def test_turn_trace_exposes_memory_provenance_without_memory_text(self):
        evidence = memory_retrieval_evidence("what did we decide?", [{
            "id": "decision-42", "text": "Private decision content",
            "memory_tier": "episodic", "memory_type": "conversation",
            "source": "faiss", "timestamp": "2026-11-10T10:00:00",
        }])

        summary = audit_safe_turn_summary(evidence)

        self.assertEqual(summary["candidate_count"], 1)
        self.assertEqual(summary["candidates"][0]["memory_tier"], "episodic")
        self.assertEqual(summary["candidates"][0]["source"], "faiss")
        self.assertEqual(summary["candidates"][0]["retrieval_lane"], "unattributed")
        self.assertNotIn("Private decision content", str(summary))

    def test_memory_lane_provenance_survives_trace_sanitization(self):
        recalled = audit_safe_turn_summary(memory_retrieval_evidence(
            "private query", [{
                "id": "private-1", "text": "private text", "memory_type": "fact",
                "memory_tier": "personal", "retrieval_lane": "personal",
            }],
        ))
        injected = audit_safe_turn_summary(memory_prompt_injection_evidence([{
            "id": "private-1", "text": "private text", "memory_type": "fact",
            "memory_tier": "personal", "retrieval_lane": "personal",
        }]))

        self.assertEqual(recalled["candidates"][0]["retrieval_lane"], "personal")
        self.assertEqual(injected["records"][0]["retrieval_lane"], "personal")
        self.assertNotIn("private text", str(recalled))
        self.assertNotIn("private text", str(injected))

        invalid = audit_safe_turn_summary(memory_prompt_injection_evidence([{
            "id": "private-2", "retrieval_lane": "forged/private/path",
        }]))
        self.assertEqual(invalid["records"][0]["retrieval_lane"], "unattributed")

    def test_memory_injection_receipt_distinguishes_recalled_from_prompted_records(self):
        memories = [{
            "id": "injected-1", "text": "private included record",
            "memory_tier": "personal", "memory_type": "fact",
        }]
        receipt = memory_prompt_injection_evidence(memories)
        summary = audit_safe_turn_summary(receipt)

        self.assertEqual(summary["injected_count"], 1)
        self.assertEqual(summary["records"][0]["memory_tier"], "personal")
        self.assertNotIn("private included record", str(summary))

    def test_turn_trace_exposes_profile_receipt_without_profile_values(self):
        summary = audit_safe_turn_summary({
            "status": "updated", "changed": True, "quarantined_count": 2,
            "persisted": True, "categories_updated": ["preference"],
            "private_profile_value": "do not expose",
        })

        self.assertEqual(summary["status"], "updated")
        self.assertTrue(summary["changed"])
        self.assertTrue(summary["persisted"])
        self.assertEqual(summary["categories_updated"], ["preference"])
        self.assertIsNone(summary["extracted_count"])
        self.assertEqual(summary["quality"], "present")
        self.assertEqual(summary["quarantined_count"], 2)
        self.assertNotIn("private_profile_value", str(summary))
        self.assertNotIn("do not expose", str(summary))

        failed = audit_safe_turn_summary({
            "status": "persistence_failed", "changed": True,
            "persisted": False, "interaction_count": 12,
        })
        self.assertEqual(failed["quality"], "failed")
        self.assertFalse(failed["persisted"])
        self.assertEqual(failed["interaction_count"], 12)

        unknown = audit_safe_turn_summary({
            "status": "updated", "changed": True, "persisted": True,
        })
        self.assertIsNone(unknown["categories_updated"])
        self.assertIsNone(unknown["extracted_count"])

        opted_out = audit_safe_turn_summary({
            "status": "skipped_explicit_opt_out", "changed": False,
            "persisted": False, "learning_scope": "none",
            "categories_updated": [], "extracted_count": 0,
        })
        self.assertEqual(opted_out["quality"], "skipped")
        self.assertFalse(opted_out["changed"])
        self.assertEqual(opted_out["learning_scope"], "none")

    def test_turn_trace_exposes_routing_decisions_without_user_text(self):
        summary = audit_safe_turn_summary({
            "factual_plan_query": True,
            "closed_world_report": True,
            "architecture_query": False,
            "cognitive_trace_query": False,
            "runtime_execution_query": False,
            "explicit_memory_recall": False,
            "api_route_query": False,
            "api_route_intent_status": "non_api_route_intent",
            "api_route_intent_positive_similarity": 0.5375,
            "api_route_intent_negative_similarity": 0.626,
            "api_route_intent_margin": -0.0884,
            "api_route_intent_space": "nomic_v1.5",
            "api_route_intent_reason": "cross_lingual_semantic_centroid_margin",
            "private_embedding_space": "http://sensitive-host/v1",
            "private_query": "do not expose",
        })

        self.assertEqual(summary["type"], "turn_evidence_routing_receipt")
        self.assertTrue(summary["factual_plan_query"])
        self.assertTrue(summary["closed_world_report"])
        self.assertFalse(summary["explicit_memory_recall"])
        self.assertFalse(summary["prompt_source_provenance_query"])
        self.assertEqual(summary["api_route_intent_status"], "non_api_route_intent")
        self.assertEqual(summary["api_route_intent_margin"], -0.0884)
        self.assertEqual(summary["api_route_intent_space"], "nomic_v1.5")
        self.assertNotIn("private_embedding_space", str(summary))
        self.assertNotIn("private_query", str(summary))
        self.assertNotIn("do not expose", str(summary))

    def test_simple_thought_evaluator_can_timestamp_a_fresh_goal_candidate(self):
        class _Dal:
            def get_thoughts(self, **kwargs):
                return [{
                    "id": "thought-1", "content": "fresh thought",
                    "source": "cognitive_loop", "thought_type": "tension_awareness",
                    "timestamp": "2026-11-11T20:00:00Z",
                }]

            def get_goals(self):
                return []

            def add_thought(self, thought):
                return None

        with tempfile.TemporaryDirectory() as temp_dir:
            evaluator = SimpleThoughtEvaluator(temp_dir)
            evaluation = {
                "type": "uncertainty", "concept": "robot capabilities",
                "priority": 0.7, "actionability": 0.6,
                "friction": "unknown", "goal_type": "learn",
                "hypothesis": None, "should_create_goal": True,
                "concept_source": "legacy_text_extraction",
            }
            with (
                patch("core.data.access.DataAccess", return_value=_Dal()),
                patch.object(evaluator, "_evaluate_thought", return_value=evaluation),
                patch.object(evaluator, "_has_existing_goal", return_value=False),
                patch.object(evaluator, "_inject_followup_thoughts"),
            ):
                suggestions = evaluator.evaluate_recent_thoughts()

        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["concept"], "robot capabilities")
        self.assertTrue(suggestions[0]["created_at"])
        self.assertEqual(suggestions[0]["origin_thought_source"], "cognitive_loop")
        self.assertEqual(suggestions[0]["origin_thought_type"], "tension_awareness")

    def test_self_description_prompt_is_factual_and_marks_registry_partial(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            description = SelfDescription(str(Path(temp_dir) / "self.json"))
            description.register_or_update(
                "ExampleModule", "cognition/example.py", "bounded evidence tracking",
                {"enabled": True},
            )

            block = description.prompt_context()

        self.assertIn("partial registry", block)
        self.assertIn("ExampleModule", block)
        self.assertIn("bounded evidence tracking", block)
        self.assertIn("Do not invent equations", block)

    def test_self_description_prompt_does_not_claim_unregistered_mechanisms(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            description = SelfDescription(str(Path(temp_dir) / "self.json"))
            block = description.prompt_context()

        self.assertIn("no components are registered", block)
        self.assertIn("Do not infer", block)

    def test_semantic_extractor_discards_french_filler_topics(self):
        extractor = SemanticExtractor(SimpleNamespace())
        concepts = extractor._keyword_extract(
            "Je suis curieux de savoir quelles choses tu sais toujours."
        )
        self.assertFalse(set(concepts) & {
            "curieux", "savoir", "quelles", "choses", "toujours"
        })

    def test_peer_semantics_are_not_recorded_as_human_goal_evidence(self):
        class _Memory:
            def __init__(self):
                self.observations = []

            def upsert_concept(self, *_args, **_kwargs):
                return 1

            def record_observation(self, *args, **kwargs):
                self.observations.append((args, kwargs))

            def upsert_relation(self, *_args, **_kwargs):
                pass

        class _Workspace:
            def __init__(self):
                self.events = []

            def broadcast(self, **kwargs):
                self.events.append(kwargs)

        memory = _Memory()
        workspace = _Workspace()
        extractor = SemanticExtractor(memory, llm_fn=lambda _prompt: json.dumps({
            "turn_kind": "topic",
            "concepts": [{"name": "robot cognition", "evidence": "robot cognition"}],
            "relations": [],
            "dominant_topic": "robot cognition",
            "cognitive_load": 0.2,
        }))
        extractor._extract(
            "shared robot cognition", "A peer reply", None, workspace,
            observation_role="peer_topic",
        )

        self.assertTrue(memory.observations)
        self.assertTrue(all(
            kwargs["role"] == "peer_topic"
            and kwargs["source"] == "peer_dialogue"
            for _, kwargs in memory.observations
        ))
        self.assertEqual(workspace.events[0]["source"], "peer_semantic_extractor")
        self.assertIn("peer hypothesis:", workspace.events[0]["content"])

    def test_autonomous_user_topics_need_repeated_observations(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = SemanticMemory(str(Path(directory) / "semantic.sqlite"))
            memory.record_observation(
                "visual odometry", "conversation", "user_topic", 0.8,
                turn_id="odometry-turn-1", goal_signal="continuing_commitment",
                goal_signal_evidence="I am continuing work on visual odometry",
            )
            self.assertNotIn("visual odometry", memory.recent_user_topics())
            memory.record_observation(
                "visual odometry", "conversation", "user_topic", 0.8,
                turn_id="odometry-turn-2", goal_signal="continuing_commitment",
                goal_signal_evidence="I am continuing work on visual odometry",
            )
            self.assertIn("visual odometry", memory.recent_user_topics())

    def test_repeated_extraction_of_one_turn_is_not_independent_goal_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = SemanticMemory(str(Path(directory) / "semantic.sqlite"))
            for _ in range(4):
                memory.record_observation(
                    "camera calibration", "conversation", "user_topic", 0.8,
                    turn_id="same-turn", goal_signal="continuing_commitment",
                    goal_signal_evidence="I will keep working on camera calibration",
                )
            self.assertNotIn("camera calibration", memory.recent_user_topics())

            memory.record_observation(
                "camera calibration", "conversation", "user_topic", 0.8,
                turn_id="second-turn", goal_signal="continuing_commitment",
                goal_signal_evidence="I will keep working on camera calibration",
            )
            evidence = memory.recent_user_topic_evidence()
            self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0]["turn_count"], 2)
            self.assertEqual(set(evidence[0]["turn_ids"]), {"same-turn", "second-turn"})

    def test_repeated_topic_only_mentions_do_not_become_autonomous_goal_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = SemanticMemory(str(Path(directory) / "semantic.sqlite"))
            memory.record_observation(
                "camera calibration", "conversation", "user_topic", 0.8,
                turn_id="question-1", goal_signal="topic_only",
            )
            memory.record_observation(
                "camera calibration", "conversation", "user_topic", 0.8,
                turn_id="question-2", goal_signal="topic_only",
            )
            self.assertNotIn("camera calibration", memory.recent_user_topics())

    def test_continuing_commitment_without_quote_is_not_goal_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = SemanticMemory(str(Path(directory) / "semantic.sqlite"))
            memory.record_observation(
                "camera calibration", "conversation", "user_topic", 0.8,
                turn_id="unquoted-commitment", goal_signal="continuing_commitment",
            )
            self.assertNotIn("camera calibration", memory.recent_user_topics(min_observations=1))
            with memory._conn() as conn:
                row = conn.execute(
                    "SELECT goal_signal, goal_signal_evidence FROM concept_observations"
                ).fetchone()
            self.assertEqual(row["goal_signal"], "topic_only")
            self.assertEqual(row["goal_signal_evidence"], "")

    def test_legacy_commitment_rows_migrate_without_becoming_qualified(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "semantic.sqlite")
            conn = sqlite3.connect(path)
            try:
                conn.executescript("""
                    CREATE TABLE concepts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        strength REAL DEFAULT 0.5,
                        last_used REAL DEFAULT 0,
                        use_count INTEGER DEFAULT 1,
                        created_at REAL DEFAULT 0
                    );
                    CREATE TABLE concept_observations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        concept_id INTEGER NOT NULL REFERENCES concepts(id),
                        source TEXT NOT NULL,
                        role TEXT NOT NULL,
                        confidence REAL DEFAULT 0.5,
                        observed_at REAL NOT NULL,
                        turn_id TEXT NOT NULL DEFAULT '',
                        goal_signal TEXT NOT NULL DEFAULT 'topic_only'
                    );
                    INSERT INTO concepts(name, strength) VALUES ('camera calibration', 0.9);
                    INSERT INTO concept_observations
                        (concept_id, source, role, confidence, observed_at, turn_id, goal_signal)
                    VALUES (1, 'conversation', 'user_topic', 0.8, 1, 'legacy-a', 'continuing_commitment'),
                           (1, 'conversation', 'user_topic', 0.8, 2, 'legacy-b', 'continuing_commitment');
                """)
            finally:
                conn.close()
            memory = SemanticMemory(path)
            self.assertNotIn("camera calibration", memory.recent_user_topics(min_observations=2))
            with memory._conn() as conn:
                rows = conn.execute(
                    "SELECT goal_signal_evidence FROM concept_observations ORDER BY id"
                ).fetchall()
            self.assertEqual([row["goal_signal_evidence"] for row in rows], ["", ""])

    def test_legacy_observations_without_turn_ids_do_not_count_as_repeated_user_intent(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = SemanticMemory(str(Path(directory) / "semantic.sqlite"))
            memory.record_observation("camera calibration", "conversation", "user_topic", 0.8)
            memory.record_observation("camera calibration", "conversation", "user_topic", 0.8)
            self.assertNotIn("camera calibration", memory.recent_user_topics())

    def test_semantic_extractor_persists_the_originating_turn_on_observations(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = SemanticMemory(str(Path(directory) / "semantic.sqlite"))
            extractor = SemanticExtractor(memory)
            extractor._parse = lambda *_args: (
                ["camera calibration"], [], "camera calibration", 0.2, "topic",
                "continuing_commitment", "Camera calibration is the current topic",
            )
            receipt = extractor._extract(
                "Camera calibration is the current topic", "bounded answer",
                None, None, turn_id="camera-turn-42",
            )
            self.assertEqual(receipt["status"], "completed")
            self.assertTrue(receipt["goal_signal_evidence_valid"])
            with memory._conn() as conn:
                rows = conn.execute(
                    "SELECT turn_id, goal_signal, goal_signal_evidence "
                    "FROM concept_observations WHERE role='user_topic'"
                ).fetchall()
            self.assertEqual([row["turn_id"] for row in rows], ["camera-turn-42"])
            self.assertEqual(rows[0]["goal_signal"], "continuing_commitment")
            self.assertEqual(
                rows[0]["goal_signal_evidence"],
                "Camera calibration is the current topic",
            )
            self.assertIn("camera calibration", memory.recent_user_topics(min_observations=1))

    def test_semantic_extractor_classifies_continuing_intent_in_its_existing_llm_call(self):
        calls = []
        extractor = SemanticExtractor(
            SimpleNamespace(),
            llm_fn=lambda prompt: calls.append(prompt) or json.dumps({
                "turn_kind": "topic",
                "goal_signal": "continuing_commitment",
                "goal_signal_evidence": "I want us to keep improving the cognitive harness",
                "concepts": [{
                    "name": "cognitive harness",
                    "evidence": "cognitive harness",
                }],
                "relations": [],
                "dominant_topic": "cognitive harness",
                "cognitive_load": 0.3,
            }),
        )
        parsed = extractor._parse(
            "I want us to keep improving the cognitive harness", "acknowledged"
        )
        self.assertEqual(parsed[4], "topic")
        self.assertEqual(parsed[5], "continuing_commitment")
        self.assertEqual(parsed[6], "I want us to keep improving the cognitive harness")
        self.assertEqual(len(calls), 1)
        self.assertIn("goal_signal", calls[0])

    def test_continuing_goal_signal_requires_exact_user_evidence(self):
        for evidence in ("", "I want to explore another topic"):
            extractor = SemanticExtractor(
                SimpleNamespace(),
                llm_fn=lambda _prompt, evidence=evidence: json.dumps({
                    "turn_kind": "topic",
                    "goal_signal": "continuing_commitment",
                    "goal_signal_evidence": evidence,
                    "concepts": [{
                        "name": "cognitive harness",
                        "evidence": "cognitive harness",
                    }],
                    "relations": [],
                    "dominant_topic": "cognitive harness",
                    "cognitive_load": 0.3,
                }),
            )
            parsed = extractor._parse("Explain the cognitive harness", "acknowledged")
            self.assertEqual(parsed[5], "topic_only")
            self.assertEqual(parsed[6], "")

    def test_exact_goal_evidence_is_accepted_in_french(self):
        message = "Je veux continuer ce projet de mémoire avec toi."
        extractor = SemanticExtractor(
            SimpleNamespace(),
            llm_fn=lambda _prompt: json.dumps({
                "turn_kind": "topic",
                "goal_signal": "continuing_commitment",
                "goal_signal_evidence": "continuer ce projet de mémoire",
                "concepts": [{
                    "name": "projet mémoire",
                    "evidence": "projet de mémoire",
                }],
                "relations": [],
                "dominant_topic": "projet mémoire",
                "cognitive_load": 0.3,
            }),
        )
        parsed = extractor._parse(message, "acknowledged")
        self.assertEqual(parsed[5], "continuing_commitment")
        self.assertEqual(parsed[6], "continuer ce projet de mémoire")

    def test_goal_created_from_user_topic_keeps_all_evidence_turn_ids(self):
        engine = GoalEngine.__new__(GoalEngine)
        engine._goals = {}
        engine._cycle_counter = 1
        engine._recently_abandoned = {}
        engine.MAX_ACTIVE_GOALS = 10
        engine._external_tasks = []
        engine._topic_quality_cache = {}
        engine._lock = threading.RLock()
        with patch.object(engine, "_is_valid_goal_topic", return_value=True):
            goals = engine.generate_candidates(
                [Motivation("explore", 0.7, "test")],
                ["camera calibration"],
                topic_source_turns={"camera calibration": ["turn-a", "turn-b"]},
                topic_source_provenance={"camera calibration": {
                    "kind": "user_semantic_commitment",
                    "method": "semantic_memory.recent_user_topic_evidence",
                    "ref": "concept:camera-calibration",
                }},
            )
        self.assertEqual(len(goals), 1)
        self.assertEqual(goals[0].source_turn_id, "turn-b")
        self.assertEqual(goals[0].source_evidence_turn_ids, ["turn-a", "turn-b"])

    def test_goal_candidate_persists_source_kind_method_and_reference(self):
        engine = GoalEngine.__new__(GoalEngine)
        engine._goals = {}
        engine._cycle_counter = 1
        engine._recently_abandoned = {}
        engine.MAX_ACTIVE_GOALS = 10
        engine._external_tasks = []
        engine._topic_quality_cache = {}
        engine._lock = threading.RLock()
        with patch.object(engine, "_is_valid_goal_topic", return_value=True):
            goals = engine.generate_candidates(
                [Motivation("explore", 0.7, "test")],
                ["cognitive architecture"],
                topic_source_turns={"cognitive architecture": ["turn-a", "turn-b"]},
                topic_source_provenance={
                    "cognitive architecture": {
                        "kind": "user_semantic_commitment",
                        "method": "semantic_memory.recent_user_topic_evidence",
                        "ref": "concept:42",
                    },
                },
            )

        assert len(goals) == 1
        assert goals[0].source_concept_kind == "user_semantic_commitment"
        assert goals[0].source_concept_method == "semantic_memory.recent_user_topic_evidence"
        assert goals[0].source_concept_ref == "concept:42"

    def test_goal_admission_uses_semantic_verdict_not_token_dictionary(self):
        engine = GoalEngine.__new__(GoalEngine)
        engine._topic_quality_cache = {}
        engine._lock = threading.RLock()
        scores = {
            "module": (0.40, 0.50, False),
            "cognitive architecture": (0.62, 0.49, True),
        }
        with patch("cognition.goal_semantics.batch_topic_quality",
                   side_effect=lambda topics: {topic: scores[topic] for topic in topics}):
            self.assertFalse(engine._is_valid_goal_topic("module"))
            self.assertTrue(engine._is_valid_goal_topic("cognitive architecture"))

    def test_goal_quality_filter_uses_semantic_verdict_without_lexical_veto(self):
        quality = GoalQualityFilter.__new__(GoalQualityFilter)
        quality_verdicts = {
            "soory": (0.40, 0.51, False),
            "improve cognitive architecture": (0.62, 0.49, True),
        }
        with patch("cognition.goal_semantics.batch_topic_quality",
                   side_effect=lambda topics: {
                       topic: quality_verdicts[topic] for topic in topics
                   }):
            score, reasons = quality._score_goal(
                {"name": "soory", "origin": "thought_goal_linker", "priority": 0.95,
                 "origin_thoughts": ["supporting thought", "another thought"]},
                tensions={"curiosity_drive": 1.0}, emotions={"curiosity": 1.0},
            )
            real_score, _ = quality._score_goal(
                {"name": "improve cognitive architecture", "origin": "manual", "priority": 0.5},
                tensions={}, emotions={},
            )
        self.assertEqual(score, 0.0)
        self.assertTrue(reasons[0].startswith("semantic topic-quality gate rejected"))
        self.assertGreater(real_score, score)

    def test_tte_migrates_iteration_count_and_keeps_valid_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "thought_threads.json"
            path.write_text(json.dumps({
                "thread-a": {
                    "topic": "cognitive architecture", "goal": "understand it",
                    "iteration_count": 7, "status": "active",
                },
                "broken": {"topic": "incomplete", "status": "not-a-status"},
            }), encoding="utf-8")

            engine = ThoughtThreadEngine(str(path))

            self.assertEqual(len(engine.all_threads()), 1)
            self.assertEqual(engine.get_thread("thread-a").iteration_count, 7)
            self.assertTrue(path.exists())

    def test_introspection_does_not_present_other_as_a_real_orientation(self):
        generator = GroundedIntrospectionGenerator(organism=None)
        question = generator._derive_question({
            "idx": 0.31, "consistency": 0.60,
            "dominant_orientation": "other",
        }, "self description", 0)
        self.assertNotIn("'other'", question)
        self.assertNotIn("tendency toward", question)

    def test_unknown_belief_categories_do_not_inflate_confidence_proxy(self):
        synchronizer = SelfConceptSynchronizer.__new__(SelfConceptSynchronizer)
        score = synchronizer._compute_belief_confidence_proxy({"beliefs": {
            "known": {"category": "expressed_belief", "confidence": 0.6},
            "unknown-a": {"category": "noise_a", "confidence": 1.0},
            "unknown-b": {"category": "noise_b", "confidence": 1.0},
            "unknown-c": {"category": "noise_c", "confidence": 1.0},
            "unknown-d": {"category": "noise_d", "confidence": 1.0},
        }})
        self.assertAlmostEqual(score, 0.6)

    def test_unclassified_beliefs_produce_no_confidence_proxy_or_coherence_measurement(self):
        synchronizer = SelfConceptSynchronizer.__new__(SelfConceptSynchronizer)
        beliefs = {"beliefs": {
            f"belief-{index}": {
                "category": "",
                "confidence": 0.57,
            }
            for index in range(40)
        }}
        self.assertIsNone(synchronizer._compute_belief_confidence_proxy(beliefs))
        self.assertIsNone(synchronizer._compute_coherence(beliefs))

    def test_sync_retires_unvalidated_coherence_and_stability_proxies(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory, "self_concept.json")
            state_path.write_text(json.dumps({
                "state": {
                    "coherence": 0.2946,
                    "confidence": 0.61,
                    "stability": 0.4321,
                },
                "beliefs": {
                    f"belief-{index}": {
                        "name": f"belief-{index}",
                        "category": "",
                        "confidence": 0.57,
                    }
                    for index in range(40)
                },
            }), encoding="utf-8")
            synchronizer = SelfConceptSynchronizer(directory)
            synchronizer.dal = SimpleNamespace(get_beliefs=lambda: [])

            report = synchronizer.run()
            saved = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(report["coherence_status"], "unmeasured")
        self.assertIsNone(report["coherence_after"])
        self.assertIsNone(report["stability_after"])
        self.assertIsNone(saved["state"]["coherence"])
        self.assertIsNone(saved["state"]["stability"])
        self.assertEqual(saved["state"]["legacy_coherence_proxy"], 0.2946)
        self.assertEqual(saved["state"]["legacy_stability_proxy"], 0.4321)
        self.assertEqual(saved["state"]["coherence_status"], "unmeasured")
        self.assertEqual(saved["state"]["stability_status"], "unmeasured")

    def test_attention_does_not_use_legacy_coherence_as_identity_drive(self):
        engine = CognitiveAttentionEngine.__new__(CognitiveAttentionEngine)
        engine._o = SimpleNamespace(ai_system=SimpleNamespace(
            self_concept=SimpleNamespace(_state=SimpleNamespace(
                coherence=0.99, coherence_status="unmeasured",
                stability=None, stability_status="unmeasured",
            ))
        ))
        state = engine._read_state()
        self.assertNotIn("identity", state)

    def test_attention_accepts_only_explicitly_measured_stability(self):
        engine = CognitiveAttentionEngine.__new__(CognitiveAttentionEngine)
        engine._o = SimpleNamespace(ai_system=SimpleNamespace(
            self_concept=SimpleNamespace(_state=SimpleNamespace(
                coherence=0.2, coherence_status="unmeasured",
                stability=0.73, stability_status="measured",
            ))
        ))
        state = engine._read_state()
        self.assertEqual(state["identity"], 0.73)

    def test_decision_contradiction_does_not_mutate_unmeasured_coherence(self):
        pressure = SimpleNamespace(calls=0, record_contradiction=lambda: setattr(
            pressure, "calls", pressure.calls + 1
        ))
        self_concept = SimpleNamespace(coherence=0.61)
        ai_system = SimpleNamespace(
            pressure_system=pressure,
            self_concept=self_concept,
            liberty_contradiction=SimpleNamespace(contradictions=[]),
        )
        layer = DecisionCommitmentLayer.__new__(DecisionCommitmentLayer)
        layer._o = SimpleNamespace(ai_system=ai_system)
        layer._cycle = 4
        commitment = Commitment(
            timestamp=1.0, topic="new goal", win_type="goal", score=0.3,
            orientation="exploration", energy=0.5, cycle=4,
        )

        layer._fire_penalty(commitment, "stability", 0.2)

        self.assertEqual(pressure.calls, 1)
        self.assertEqual(self_concept.coherence, 0.61)
        self.assertEqual(len(ai_system.liberty_contradiction.contradictions), 1)

    def test_identity_analyzer_reports_coherence_unmeasured_without_evidence(self):
        analyzer = IdentityAnalyzer.__new__(IdentityAnalyzer)
        self.assertIsNone(analyzer._calc_coherence([], []))

    def test_identity_analyzer_marks_available_score_as_proxy(self):
        analyzer = IdentityAnalyzer.__new__(IdentityAnalyzer)
        trait = IdentityComponent(
            name="curiosity", description="", confidence=0.8,
            stability_score=0.75,
        )
        score = analyzer._calc_coherence([trait], [])
        self.assertAlmostEqual(score, 0.6)
        identity = AIIdentity(
            identity_coherence=score,
            identity_coherence_status="estimated_proxy",
        )
        self.assertEqual(identity.identity_coherence_status, "estimated_proxy")

    def test_identity_proxy_uses_available_values_without_missing_trait_penalty(self):
        analyzer = IdentityAnalyzer.__new__(IdentityAnalyzer)
        value = CoreValues(
            value_name="honesty", importance=0.8,
            examples=["evidence-backed example"], contradictions=[],
        )
        self.assertEqual(analyzer._calc_coherence([], [value]), 1.0)

    def test_identity_proxy_is_unmeasured_when_value_has_no_examples(self):
        analyzer = IdentityAnalyzer.__new__(IdentityAnalyzer)
        value = CoreValues(value_name="honesty", importance=0.8)
        self.assertIsNone(analyzer._calc_coherence([], [value]))

    def test_estimated_identity_coherence_proxy_does_not_create_conflict_or_development_action(self):
        proxy_identity = AIIdentity(
            identity_coherence=0.38,
            identity_coherence_status="estimated_proxy",
        )
        system = IdentitySystem.__new__(IdentitySystem)
        system.get_identity = lambda: proxy_identity

        self.assertEqual(system.analyze_identity_conflicts(), [])
        self.assertFalse(any("coherent identity" in item for item in system.suggest_identity_development()))

        self.assertFalse(measured_identity_coherence_below(proxy_identity, 0.6))

    def test_identity_prompt_context_uses_cache_and_never_waits_for_refresh(self):
        identity = AIIdentity(
            core_traits=[IdentityComponent(
                name="curiosity", description="", confidence=0.8,
                supporting_memories=[], stability_score=0.7,
            )],
            growth_trajectory="exploring",
        )
        system = IdentitySystem.__new__(IdentitySystem)
        system.current_identity = identity
        system._last_analysis_time = datetime.now() - timedelta(seconds=10)
        system._analysis_interval = timedelta(seconds=1)
        system._context_refresh_lock = threading.Lock()
        system._context_refresh_pending = False
        system._context_refresh_last_attempt = 0.0
        system._context_refresh_retry_seconds = 30.0
        refresh_started = threading.Event()
        allow_refresh_to_finish = threading.Event()
        refresh_calls = []

        def slow_refresh():
            refresh_calls.append(True)
            refresh_started.set()
            allow_refresh_to_finish.wait(2.0)
            return identity

        system.get_identity = slow_refresh
        started = time.perf_counter()
        context = system.get_identity_for_context()
        elapsed = time.perf_counter() - started

        self.assertIn("Key traits: curiosity", context)
        self.assertLess(elapsed, 0.2)
        self.assertTrue(refresh_started.wait(1.0))
        self.assertIn("Key traits: curiosity", system.get_identity_for_context())
        self.assertEqual(len(refresh_calls), 1)
        self.assertTrue(system._context_refresh_pending)
        allow_refresh_to_finish.set()
        deadline = time.perf_counter() + 1.0
        while system._context_refresh_pending and time.perf_counter() < deadline:
            time.sleep(0.005)
        self.assertFalse(system._context_refresh_pending)

    def test_identity_prompt_context_reports_pending_when_no_snapshot_exists(self):
        system = IdentitySystem.__new__(IdentitySystem)
        system.current_identity = None
        system._last_analysis_time = None
        system._analysis_interval = timedelta(hours=1)
        system._context_refresh_lock = threading.Lock()
        system._context_refresh_pending = False
        system._context_refresh_last_attempt = 0.0
        system._context_refresh_retry_seconds = 30.0
        refresh_started = threading.Event()
        allow_refresh_to_finish = threading.Event()

        def slow_refresh():
            refresh_started.set()
            allow_refresh_to_finish.wait(2.0)
            return AIIdentity()

        system.get_identity = slow_refresh
        context = system.get_identity_for_context()

        self.assertIn("Identity analysis is pending", context)
        self.assertTrue(refresh_started.wait(1.0))
        allow_refresh_to_finish.set()

    def test_measured_low_identity_coherence_remains_actionable(self):
        measured_identity = AIIdentity(
            identity_coherence=0.38,
            identity_coherence_status="measured",
        )
        system = IdentitySystem.__new__(IdentitySystem)
        system.get_identity = lambda: measured_identity

        self.assertEqual(system.analyze_identity_conflicts()[0]["type"], "low_coherence")
        self.assertTrue(any("coherent identity" in item for item in system.suggest_identity_development()))
        self.assertTrue(measured_identity_coherence_below(measured_identity, 0.6))

    def test_self_awareness_requires_reflection_records_and_is_labeled_proxy(self):
        analyzer = IdentityAnalyzer.__new__(IdentityAnalyzer)
        self.assertIsNone(analyzer._calc_self_awareness([]))
        self.assertIsNone(analyzer._calc_self_awareness([
            {"memory_type": "interaction", "text": "I think about this."}
        ]))
        proxy = analyzer._calc_self_awareness([
            {"memory_type": "reflection", "text": "I think about my own reasoning."}
        ])
        self.assertEqual(proxy, 1.0)

    def test_self_concept_persists_legacy_metric_migration_on_load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "self_concept.json")
            path.write_text(json.dumps({
                "beliefs": {},
                "state": {"coherence": 0.32, "stability": 0.41},
            }), encoding="utf-8")

            instance = SelfConceptSystem(str(path))
            saved = json.loads(path.read_text(encoding="utf-8"))["state"]
            SelfConceptSystem._live_instances.remove(instance)

        self.assertIsNone(saved["coherence"])
        self.assertIsNone(saved["stability"])
        self.assertEqual(saved["legacy_coherence_proxy"], 0.32)
        self.assertEqual(saved["legacy_stability_proxy"], 0.41)
        self.assertEqual(saved["coherence_status"], "unmeasured")
        self.assertEqual(saved["stability_status"], "unmeasured")

    def test_self_concept_cap_is_stable_and_does_not_report_transient_churn(self):
        synchronizer = SelfConceptSynchronizer.__new__(SelfConceptSynchronizer)
        synchronizer.dal = SimpleNamespace(get_beliefs=lambda: [
            {
                "name": f"belief_{index:02d}",
                "category": "expressed_belief",
                "confidence": 0.8,
            }
            for index in range(60)
        ] + [
            {
                "name": f"raw_concept_{index}",
                "category": "semantic_concept",
                "confidence": 0.99,
            }
            for index in range(3)
        ])
        beliefs = {}

        first_synced = synchronizer._sync_beliefs(beliefs)
        first_keys = set(beliefs["beliefs"])
        second_synced = synchronizer._sync_beliefs(beliefs)

        self.assertEqual(synchronizer._last_eligible_beliefs, 60)
        self.assertEqual(len(first_keys), synchronizer.BELIEF_MAX_COUNT)
        self.assertEqual(first_keys, set(beliefs["beliefs"]))
        self.assertEqual(first_synced, synchronizer.BELIEF_MAX_COUNT)
        self.assertEqual(second_synced, 0)
        self.assertEqual(synchronizer._last_cap_pruned, 0)
        self.assertFalse(any(key.startswith("raw_concept_") for key in first_keys))

    def test_semantic_hub_statistics_never_bootstrap_as_expressed_self_beliefs(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "self_concept.json").write_text(json.dumps({
                "beliefs": {
                    "expressed_semantic_hub_calme": {
                        "name": "expressed_semantic_hub_calme",
                        "statement": "Frequently referenced concept: calme (20 uses)",
                        "confidence": 0.85,
                    },
                    "insight_from_semantic_hub": {
                        "name": "insight_from_semantic_hub",
                        "statement": "It signifies a disconnect: Frequently referenced concept: calme "
                                    "but my actual behavior doesn't back that up",
                        "confidence": 0.45,
                    },
                    "expressed_practical": {
                        "name": "expressed_practical",
                        "statement": "I value practical approaches that work",
                        "confidence": 0.8,
                    },
                },
            }), encoding="utf-8")

            class _Dal:
                saved = []

                def get_belief_by_name(self, name):
                    return None

                def save_belief(self, belief):
                    self.saved.append(belief)

            bootstrapper = BeliefBootstrapper.__new__(BeliefBootstrapper)
            bootstrapper.persona_dir = Path(directory)
            bootstrapper.dal = _Dal()
            added, updated = bootstrapper._extract_from_self_concept()

        self.assertEqual((added, updated), (1, 0))
        self.assertEqual(len(bootstrapper.dal.saved), 1)
        self.assertEqual(bootstrapper.dal.saved[0]["name"], "expressed_practical")

    def test_synchronizer_quarantines_legacy_semantic_hub_self_beliefs(self):
        synchronizer = SelfConceptSynchronizer.__new__(SelfConceptSynchronizer)
        synchronizer.dal = SimpleNamespace(get_beliefs=lambda: [])
        state = {"beliefs": {
            "expressed_semantic_hub_calme": {
                "name": "expressed_semantic_hub_calme",
                "statement": "Frequently referenced concept: calme (20 uses)",
                "confidence": 0.85,
                "violations": 11,
                "affirmations": 0,
            },
            "insight_from_semantic_hub": {
                "name": "insight_from_semantic_hub",
                "statement": "Frequently referenced concept: calme but my actual behavior "
                            "doesn't back that up",
                "confidence": 0.45,
                "violations": 3,
                "affirmations": 0,
            },
            "expressed_practical": {
                "name": "expressed_practical",
                "statement": "I value practical approaches that work",
                "confidence": 0.8,
            },
        }}

        synchronizer._sync_beliefs(state)

        self.assertNotIn("expressed_semantic_hub_calme", state["beliefs"])
        self.assertNotIn("insight_from_semantic_hub", state["beliefs"])
        self.assertIn("expressed_practical", state["beliefs"])
        self.assertIn(
            "expressed_semantic_hub_calme", state["provenance_quarantine"]
        )
        self.assertIn("insight_from_semantic_hub", state["provenance_quarantine"])
        self.assertEqual(synchronizer._last_provenance_quarantined, 2)

    def test_synchronizer_quarantines_identity_store_hubs_and_derived_insights(self):
        with tempfile.TemporaryDirectory() as directory:
            identity_path = Path(directory, "identity.json")
            original_hub = {
                "name": "expressed_semantic_hub_calme",
                "statement": "Frequently referenced concept: calme (20 uses)",
                "confidence": 0.85,
            }
            original_insight = {
                "name": "insight_from_semantic_hub",
                "statement": "Frequently referenced concept: calme but my actual behavior "
                            "doesn't back that up",
                "confidence": 0.45,
            }
            identity_path.write_text(json.dumps({"beliefs": {
                "expressed_semantic_hub_calme": original_hub,
                "insight_from_semantic_hub": original_insight,
                "expressed_practical": {"name": "expressed_practical", "confidence": 0.8},
            }}), encoding="utf-8")

            synchronizer = SelfConceptSynchronizer(directory)
            moved = synchronizer._quarantine_identity_provenance()
            migrated = json.loads(identity_path.read_text(encoding="utf-8"))

        self.assertEqual(moved, 2)
        self.assertEqual(set(migrated["beliefs"]), {"expressed_practical"})
        self.assertEqual(
            migrated["provenance_quarantine"]["expressed_semantic_hub_calme"]["statement"],
            original_hub["statement"],
        )
        self.assertEqual(
            migrated["provenance_quarantine"]["insight_from_semantic_hub"]["statement"],
            original_insight["statement"],
        )

    def test_identity_provenance_quarantine_preserves_list_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            identity_path = Path(directory, "identity.json")
            identity_path.write_text(json.dumps({"beliefs": [
                {"name": "expressed_semantic_hub_calme", "statement":
                 "Frequently referenced concept: calme (20 uses)"},
                {"name": "expressed_practical", "statement": "Useful belief"},
            ]}), encoding="utf-8")

            synchronizer = SelfConceptSynchronizer(directory)
            moved = synchronizer._quarantine_identity_provenance()
            migrated = json.loads(identity_path.read_text(encoding="utf-8"))

        self.assertEqual(moved, 1)
        self.assertIsInstance(migrated["beliefs"], list)
        self.assertEqual([belief["name"] for belief in migrated["beliefs"]],
                         ["expressed_practical"])
        self.assertEqual(
            migrated["provenance_quarantine"]["expressed_semantic_hub_calme"]["statement"],
            "Frequently referenced concept: calme (20 uses)",
        )

    def test_identity_topic_generator_ignores_semantic_hub_violation_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "self_concept.json").write_text(json.dumps({
                "beliefs": {
                    "expressed_semantic_hub_calme": {
                        "name": "expressed_semantic_hub_calme",
                        "statement": "Frequently referenced concept: calme (20 uses)",
                        "confidence": 0.85,
                        "violations": 11,
                        "affirmations": 0,
                    },
                    "insight_from_semantic_hub": {
                        "name": "insight_from_semantic_hub",
                        "statement": "Frequently referenced concept: calme but my actual behavior "
                                    "doesn't back that up",
                        "confidence": 0.45,
                        "violations": 11,
                        "affirmations": 0,
                    },
                },
            }), encoding="utf-8")
            topic = generate_identity_topic(Path(directory))

        self.assertNotIn("Frequently referenced concept", topic)

    def test_goal_quality_filter_rebases_generated_identity_topic_with_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "self_concept.json").write_text(json.dumps({
                "beliefs": {
                    "expressed_semantic_hub_calme": {
                        "name": "expressed_semantic_hub_calme",
                        "statement": "Frequently referenced concept: calme (20 uses)",
                        "confidence": 0.85,
                        "violations": 11,
                        "affirmations": 0,
                    },
                },
            }), encoding="utf-8")
            goal = {
                "id": "generated-identity-goal",
                "name": "clarify_identity_and_values",
                "origin": "goal_quality_filter",
                "status": "active",
                "tension_source": "identity_stress",
                "topic": "I keep telling myself 'Frequently referenced concept: calme (20 uses)' "
                         "but my actual behavior doesn't back that up",
            }

            class _Dal:
                def __init__(self):
                    self.saved = []

                def save_goal(self, record):
                    self.saved.append(dict(record))

            dal = _Dal()
            quality_filter = GoalQualityFilter(directory)
            repaired = quality_filter._repair_legacy_semantic_hub_topics([goal], dal)

        self.assertEqual(repaired, 1)
        self.assertNotIn("Frequently referenced concept", goal["topic"])
        self.assertEqual(len(goal["topic_history"]), 1)
        self.assertIn("Frequently referenced concept", goal["topic_history"][0]["topic"])
        self.assertEqual(len(dal.saved), 1)

    def test_goal_quality_filter_does_not_report_failed_write_as_durable_change(self):
        with tempfile.TemporaryDirectory() as directory:
            goal = {
                "id": "goal-write-fail", "name": "noisy topic",
                "status": "active", "priority": 0.7,
                "quality_score": 0.72, "quality_reasons": ["previous durable score"],
                "quality_evaluated_at": "previous-evaluation",
            }

            class _Dal:
                def get_goals(self):
                    return [goal]

                def get_tensions(self):
                    return {}

                def save_goal(self, _record):
                    return False

            quality_filter = GoalQualityFilter(directory)
            engine = SimpleNamespace(reload_from_disk=lambda: None)
            with patch("core.data.access.DataAccess", return_value=_Dal()), \
                 patch.object(quality_filter, "_load_emotions", return_value={}), \
                 patch.object(quality_filter, "_score_goal", return_value=(
                     0.0, ["semantic topic-quality gate rejected topic"]
                 )), \
                 patch.object(quality_filter, "_repair_legacy_semantic_hub_topics", return_value=0), \
                 patch.object(quality_filter, "_generate_tension_goals", return_value=[]):
                report = quality_filter.run(goal_engine=engine)

        self.assertEqual(goal["status"], "active")
        self.assertEqual(goal["quality_score"], 0.72)
        self.assertEqual(goal["quality_reasons"], ["previous durable score"])
        self.assertEqual(goal["quality_evaluated_at"], "previous-evaluation")
        self.assertEqual(report["marked_noise"], [])
        self.assertEqual(report["goal_write_failed"], ["goal-write-fail"])
        self.assertEqual(report["summary"]["goal_write_failed"], 1)
        self.assertEqual(report["summary"]["goal_writes_succeeded"], 0)

    def test_goal_quality_filter_scores_and_persists_all_goals_as_one_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            from core.data.access import DataAccess

            dal = DataAccess(directory)
            for goal_id, name in (("g-a", "cognitive capability"), ("g-b", "knowledge integration")):
                self.assertTrue(dal.save_goal({
                    "id": goal_id, "name": name, "status": "active", "priority": 0.5,
                }))
            original_save = DataAccess._save
            writes = []

            def counted_save(instance, filename, data):
                writes.append(filename)
                return original_save(instance, filename, data)

            quality_filter = GoalQualityFilter(directory)
            engine = SimpleNamespace(reload_from_disk=lambda: None)
            with patch.object(DataAccess, "_save", counted_save), \
                 patch.object(quality_filter, "_load_emotions", return_value={}), \
                 patch.object(quality_filter, "_repair_legacy_semantic_hub_topics", return_value=0), \
                 patch.object(quality_filter, "_score_goal", return_value=(
                     0.5, ["test score"]
                 )), \
                 patch.object(quality_filter, "_generate_tension_goals", return_value=[]), \
                 patch("cognition.goal_semantics.batch_goal_quality_scores", return_value=(
                     {"cognitive capability": (0.2, "curiosity_drive"),
                      "knowledge integration": (0.2, "curiosity_drive")},
                     {"cognitive capability": (0.7, 0.2, True),
                      "knowledge integration": (0.7, 0.2, True)},
                 )):
                report = quality_filter.run(goal_engine=engine)

            self.assertEqual(writes, ["goals.json"])
            self.assertEqual(report["goal_writes_succeeded"], 2)
            self.assertEqual(report["semantic_scoring_batch_count"], 1)
            self.assertEqual(len(dal.get_goals()), 2)

    def test_legacy_identity_topic_repair_reverts_when_persistence_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            goal = {
                "id": "repair-fails", "name": "clarify_identity_and_values",
                "origin": "goal_quality_filter", "status": "active",
                "tension_source": "identity_stress",
                "topic": "I keep telling myself 'Frequently referenced concept: calme (20 uses)' "
                         "but my actual behavior doesn't back that up",
            }

            class _Dal:
                def save_goal(self, _record):
                    return False

            quality_filter = GoalQualityFilter(directory)
            repaired = quality_filter._repair_legacy_semantic_hub_topics([goal], _Dal())

        self.assertEqual(repaired, 0)
        self.assertIn("Frequently referenced concept", goal["topic"])
        self.assertNotIn("topic_history", goal)

    def test_epistemic_lead_in_is_not_saved_as_a_durable_user_characteristic(self):
        examples = (
            "Je suis curieux de savoir comment ton moteur fonctionne.",
            "Je suis curieux de comprendre comment ton moteur fonctionne.",
            "I'm curious about whether the controller is connected.",
            "I'm curious to learn how the cognitive loop works.",
        )
        for index, message in enumerate(examples):
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                manager = UserManager(Path(directory) / f"users-{index}.json")
                profile = manager.create("Fred")
                settings = SimpleNamespace(get_persona_name=lambda: "Lumina")
                boundary = SimpleNamespace(claims_persona_identity=lambda *_: False)
                with patch.dict(sys.modules, {
                    "managers.settings_manager": settings,
                    "identity_boundary": boundary,
                }):
                    changed = manager.learn_from_message(profile.id, message)
                self.assertFalse(changed)
                self.assertEqual(profile.characteristics, [])

    def test_profile_quarantine_migration_rolls_back_when_save_is_not_confirmed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "users.json"
            manager = UserManager(path)
            profile = manager.create("Fred")
            persisted = json.loads(path.read_text(encoding="utf-8"))
            persisted["users"][profile.id]["characteristics"] = [
                "curious to understand a question"
            ]
            path.write_text(json.dumps(persisted), encoding="utf-8")

            with patch.object(UserManager, "_save", lambda self: None):
                loaded = UserManager(path)

            loaded_profile = loaded.get(profile.id)
            self.assertEqual(
                loaded_profile.characteristics,
                ["curious to understand a question"],
            )
            self.assertEqual(loaded_profile.profile_provenance_quarantine, [])
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["users"][profile.id]["characteristics"],
                ["curious to understand a question"],
            )

    def test_profile_learning_stops_when_ephemeral_migration_persistence_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "users.json"
            manager = UserManager(path)
            profile = manager.create("Fred")
            profile.characteristics.append("curious to understand a question")

            with patch.object(UserManager, "_save", lambda self: None):
                receipt = manager.learn_from_message(
                    profile.id, "I prefer practical examples.", return_receipt=True,
                )

            self.assertEqual(receipt["status"], "persistence_failed")
            self.assertFalse(receipt["persisted"])
            self.assertEqual(profile.characteristics, ["curious to understand a question"])
            self.assertEqual(profile.preferences, [])
            self.assertEqual(profile.profile_provenance_quarantine, [])

    def test_attention_decay_returns_effect_and_persistence_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = CognitiveAttentionEngine.__new__(CognitiveAttentionEngine)
            engine._lock = threading.Lock()
            engine._path = Path(directory) / "attention.json"
            engine._learned_bias = {name: 0.0 for name in MODULES}
            engine._learned_bias[MODULES[0]] = 0.1

            global_receipt = engine.decay_bias()
            self.assertEqual(global_receipt["effect_status"], "state_decayed")
            self.assertEqual(global_receipt["outcome_status"], "completed")
            self.assertEqual(global_receipt["modules_changed"], 1)
            self.assertTrue(global_receipt["persisted"])
            self.assertTrue(engine._path.exists())

            memory = ContextualAttentionMemory.__new__(ContextualAttentionMemory)
            memory._lock = threading.Lock()
            memory._path = Path(directory) / "context.json"
            memory._contexts = {
                "trust=high": {
                    "module_signals": {
                        "self_model": {"mean": 0.4, "sum": 0.4, "count": 2},
                    },
                    "total_feedback_events": 2,
                },
                "noise": {
                    "module_signals": {
                        "semantic_memory": {"mean": 0.0005, "sum": 0.0005, "count": 1},
                    },
                    "total_feedback_events": 1,
                },
            }
            context_receipt = memory.decay()
            self.assertEqual(context_receipt["effect_status"], "context_bias_decayed")
            self.assertEqual(context_receipt["outcome_status"], "completed")
            self.assertEqual(context_receipt["signals_pruned"], 1)
            self.assertEqual(context_receipt["contexts_pruned"], 1)
            self.assertTrue(context_receipt["persisted"])
            persisted = json.loads(memory._path.read_text(encoding="utf-8"))
            self.assertEqual(list(persisted["contexts"]), ["trust=high"])


if __name__ == "__main__":
    unittest.main()

