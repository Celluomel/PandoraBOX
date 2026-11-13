"""Regression tests for concrete cognitive defects found in the Nov 9 log."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
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

from cognition.goal_engine import GoalEngine
from cognition.goal_quality_filter import GoalQualityFilter
from cognition.profile_flow import update_behavioral_user_profile
from cognition.belief_bootstrapper import BeliefBootstrapper
from cognition.tension_topics import generate_identity_topic
from cognition.grounded_introspection import GroundedIntrospectionGenerator
from cognition.semantic_extractor import SemanticExtractor
from cognition.semantic_memory import SemanticMemory
from cognition.self_concept_synchronizer import SelfConceptSynchronizer
from cognition.self_concept import SelfConceptSystem
from cognition.cognitive_attention_engine import CognitiveAttentionEngine
from cognition.decision_commitment import Commitment, DecisionCommitmentLayer
from cognition.ai_identity import AIIdentity, CoreValues, IdentityAnalyzer, IdentityComponent
from cognition.self_description import SelfDescription
from cognition.simple_thought_evaluator import SimpleThoughtEvaluator
from cognition.turn_context_evidence import (
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
        self.assertNotIn("Private decision content", str(summary))

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
        extractor = SemanticExtractor(memory)
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
            memory.record_observation("visual odometry", "conversation", "user_topic", 0.8)
            self.assertNotIn("visual odometry", memory.recent_user_topics())
            memory.record_observation("visual odometry", "conversation", "user_topic", 0.8)
            self.assertIn("visual odometry", memory.recent_user_topics())

    def test_goal_admission_rejects_log_fragments_but_keeps_real_phrases(self):
        for noise in (
            "toujours", "quelles", "arxchiv", "assez", "sois",
            "module", "modules", "cognitifs",
        ):
            self.assertTrue(GoalEngine._is_lexical_noise_topic(noise), noise)
        self.assertFalse(GoalEngine._is_lexical_noise_topic("cognitive architecture"))

    def test_goal_quality_filter_cannot_preserve_goal_engine_lexical_noise(self):
        quality = GoalQualityFilter.__new__(GoalQualityFilter)
        score, reasons = quality._score_goal(
            {"name": "soory", "origin": "thought_goal_linker", "priority": 0.95,
             "origin_thoughts": ["supporting thought", "another thought"]},
            tensions={"curiosity_drive": 1.0}, emotions={"curiosity": 1.0},
        )
        self.assertEqual(score, 0.0)
        self.assertTrue(reasons[0].startswith("lexical-noise topic"))

        real_score, _ = quality._score_goal(
            {"name": "improve cognitive architecture", "origin": "manual", "priority": 0.5},
            tensions={}, emotions={},
        )
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
                    "cognition.identity_boundary": boundary,
                }):
                    changed = manager.learn_from_message(profile.id, message)
                self.assertFalse(changed)
                self.assertEqual(profile.characteristics, [])


if __name__ == "__main__":
    unittest.main()
