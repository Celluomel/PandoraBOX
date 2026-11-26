import unittest
import threading
import ast
import inspect
from pathlib import Path
import tempfile

from cognition.self_description import (
    ComponentDesc,
    SelfDescription,
    affect_self_report_context,
    is_architecture_query,
    is_affect_change_analysis_query,
    is_cognitive_audit_status_query,
    is_closed_world_cognitive_report_query,
    is_prompt_source_provenance_query,
    is_cognitive_trace_query,
    is_internal_cognitive_query,
    is_runtime_api_route_question,
    is_runtime_execution_evidence_query,
    is_self_affect_query,
    is_social_status_greeting,
    is_structured_affect_status_query,
    classify_runtime_api_route_intent,
    classify_body_observation_intent,
    render_affect_self_report,
    render_affect_change_analysis,
    render_detailed_affect_status,
    resolve_runtime_api_route_question,
    runtime_api_surface_context,
    sanitize_affect_event_receipts,
    sanitize_displayed_cognitive_trace,
    trace_grounded_architecture_answer,
)


class SelfDescriptionPromptTests(unittest.TestCase):
    class _SemanticIntentEmbedder:
        model_name = "text-embedding-nomic-embed-text-v1.5"
        embedding_space_id = "test:text-embedding-nomic-embed-text-v1.5"

        def __init__(self, *, semantic_api=False):
            self.semantic_api = semantic_api

        def encode_interactive_with_metadata(self, texts):
            import numpy as np
            from cognition.self_description import (
                _RUNTIME_API_ROUTE_POSITIVE, _RUNTIME_API_ROUTE_NEGATIVE,
            )

            values = [texts] if isinstance(texts, str) else list(texts)
            if len(values) == 1:
                # The fake represents semantic output, independent of the
                # query's language or vocabulary.
                vector = [0.9, 0.4, 0.0] if self.semantic_api else [0.5, 0.8, 0.0]
                return np.asarray(vector, dtype="float32"), self.embedding_space_id
            vectors = []
            for value in values[:-1]:
                if value in _RUNTIME_API_ROUTE_POSITIVE:
                    vectors.append([1.0, 0.0, 0.0])
                elif value in _RUNTIME_API_ROUTE_NEGATIVE:
                    vectors.append([0.0, 1.0, 0.0])
                else:
                    vectors.append([0.0, 0.0, 1.0])
            query = [0.9, 0.4, 0.0] if self.semantic_api else [0.5, 0.8, 0.0]
            vectors.append(query)
            return np.asarray(vectors, dtype="float32"), self.embedding_space_id

    def test_runtime_api_surface_comes_from_registered_routes(self):
        from types import SimpleNamespace

        api_app = SimpleNamespace(routes=[
            SimpleNamespace(path="/chat", methods={"POST"}, name="chat"),
            SimpleNamespace(path="/status", methods={"GET"}, name="status"),
        ])
        context, receipt = runtime_api_surface_context(api_app)

        self.assertIn("POST /chat", context)
        self.assertIn("GET /status", context)
        self.assertEqual(receipt["status"], "injected")
        self.assertEqual(receipt["route_count"], 2)
        self.assertEqual(receipt["source"], "brain.api.routes")

    def test_runtime_api_surface_reports_unavailable_instead_of_inventing(self):
        from types import SimpleNamespace

        context, receipt = runtime_api_surface_context(SimpleNamespace(routes=[]))

        self.assertIn("unavailable", context)
        self.assertIn("Do not infer or invent endpoint paths", context)
        self.assertEqual(receipt["status"], "unavailable")
        self.assertEqual(receipt["route_count"], 0)

    def test_api_route_question_uses_a_unique_live_route_match(self):
        from types import SimpleNamespace

        api_app = SimpleNamespace(routes=[
            SimpleNamespace(path="/chat", methods={"POST"}, name="chat", summary="Chat"),
            SimpleNamespace(
                path="/lumina-network/chat", methods={"POST"},
                name="lumina_network_chat", summary="Lumina Network Chat",
            ),
        ])
        question = "What exact local REST path receives Lumina Brain chat requests?"

        decision = classify_runtime_api_route_intent(
            "the route exposed by this API", embedder=self._SemanticIntentEmbedder(semantic_api=True),
        )
        self.assertTrue(decision["route"])
        self.assertEqual(decision["status"], "api_route_intent")
        self.assertTrue(is_runtime_api_route_question(question, embedder=self._SemanticIntentEmbedder(semantic_api=True)))
        self.assertTrue(is_architecture_query(question, api_route_intent=True))
        answer, receipt = resolve_runtime_api_route_question(question, api_app, route_intent=True)

        self.assertEqual(receipt["status"], "matched_registered_route")
        self.assertEqual(receipt["selected_route"]["method"], "POST")
        self.assertEqual(receipt["selected_route"]["path"], "/chat")
        self.assertIn("POST /chat", answer)
        self.assertNotIn("/api/v1/chat/lumina-brain", answer)

    def test_general_question_about_route_as_a_verb_is_not_an_api_route_query(self):
        question = (
            "Which instruction have I repeatedly given you about using a dictionary "
            "to route or answer questions?"
        )
        decision = classify_runtime_api_route_intent(
            "Quel est ton chemin ?", embedder=self._SemanticIntentEmbedder(),
        )
        self.assertFalse(decision["route"])
        self.assertEqual(decision["status"], "non_api_route_intent")
        self.assertFalse(is_runtime_api_route_question(question, embedder=self._SemanticIntentEmbedder()))
        self.assertFalse(is_architecture_query(question, api_route_intent=False))

    def test_body_observation_intent_uses_semantic_space_and_fails_open(self):
        import numpy as np
        from cognition.self_description import (
            _BODY_OBSERVATION_POSITIVE, _BODY_OBSERVATION_NEGATIVE,
        )

        class SemanticEmbedder:
            model_name = "text-embedding-nomic-embed-text-v1.5"
            embedding_space_id = "test-body:text-embedding-nomic-embed-text-v1.5"

            def __init__(self, observation_intent):
                self.observation_intent = observation_intent

            def encode_interactive_with_metadata(self, texts):
                values = [texts] if isinstance(texts, str) else list(texts)
                positive_query = np.asarray([0.98, 0.2, 0.0], dtype="float32")
                negative_query = np.asarray([0.2, 0.98, 0.0], dtype="float32")
                if len(values) == 1:
                    query = positive_query if self.observation_intent else negative_query
                    return query, self.embedding_space_id
                rows = []
                for value in values[:-1]:
                    rows.append(
                        [1.0, 0.0, 0.0] if value in _BODY_OBSERVATION_POSITIVE
                        else [0.0, 1.0, 0.0] if value in _BODY_OBSERVATION_NEGATIVE
                        else [0.0, 0.0, 1.0]
                    )
                rows.append(positive_query if self.observation_intent else negative_query)
                return np.asarray(rows, dtype="float32"), self.embedding_space_id

        factual = classify_body_observation_intent(
            "Quel trajet le Body a-t-il réellement parcouru ?",
            embedder=SemanticEmbedder(True),
        )
        conceptual = classify_body_observation_intent(
            "Explain the concept of a route in software architecture.",
            embedder=SemanticEmbedder(False),
        )
        unavailable = classify_body_observation_intent(
            "What did the robot measure?",
            embedder=type("WrongSpace", (), {
                "model_name": "other-model",
                "embedding_space_id": "test-body-wrong:other-model",
                "encode_interactive_with_metadata": lambda self, texts: (
                    np.ones((len(texts), 3), dtype="float32"), "test:other-model"
                ),
            })(),
        )

        self.assertTrue(factual["route"])
        self.assertEqual(factual["status"], "body_observation_intent")
        self.assertFalse(conceptual["route"])
        self.assertEqual(conceptual["status"], "non_body_observation_intent")
        self.assertFalse(unavailable["route"])
        self.assertEqual(unavailable["status"], "router_unavailable")

    def test_api_route_question_abstains_when_route_match_is_ambiguous(self):
        from types import SimpleNamespace

        api_app = SimpleNamespace(routes=[
            SimpleNamespace(path="/chat", methods={"POST"}, name="chat", summary="Chat"),
            SimpleNamespace(path="/chat", methods={"GET"}, name="chat", summary="Chat"),
        ])
        answer, receipt = resolve_runtime_api_route_question(
            "What exact API path receives chat requests?", api_app, route_intent=True,
        )

        self.assertEqual(receipt["status"], "no_unique_registered_route")
        self.assertIn("can’t confirm a unique route", answer)

    def test_api_route_method_followup_verifies_prior_answer_against_live_routes(self):
        from types import SimpleNamespace
        from managers.llm_manager import LLMManager

        api_app = SimpleNamespace(routes=[
            SimpleNamespace(path="/chat", methods={"POST"}, name="chat", summary="Chat"),
        ])
        checkpoints = []
        manager = object.__new__(LLMManager)
        manager.history = []
        manager._session = SimpleNamespace(
            on_exchange_complete=lambda history: checkpoints.append(list(history))
        )
        manager.record_exchange(
            "What exact API route receives chat?",
            "The registered HTTP route for chat is `POST /chat`.",
        )
        answer, receipt = resolve_runtime_api_route_question(
            "And which HTTP method does that route use?", api_app,
            conversation_history=manager.history, route_intent=True,
        )

        self.assertEqual(len(checkpoints), 1)
        self.assertEqual(len(manager.history), 2)
        self.assertEqual(receipt["status"], "matched_live_route_followup")
        self.assertEqual(receipt["selected_route"]["method"], "POST")
        self.assertEqual(receipt["prior_route_context"], "matched_current_route")
        self.assertIn("POST method", answer)

    def test_api_route_method_followup_rejects_stale_prior_assistant_route(self):
        from types import SimpleNamespace

        api_app = SimpleNamespace(routes=[
            SimpleNamespace(path="/chat", methods={"POST"}, name="chat", summary="Chat"),
        ])
        history = [{"role": "assistant", "content": "The route is `POST /old-chat`."}]
        answer, receipt = resolve_runtime_api_route_question(
            "Which HTTP method does that route use?", api_app,
            conversation_history=history, route_intent=True,
        )

        self.assertEqual(receipt["status"], "unresolved_route_followup")
        self.assertIsNone(receipt["selected_route"])
        self.assertIn("no preceding exchange identifies a route", answer)

    def test_registered_cognitive_module_roles_include_exact_scope_and_nonclaims(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            description = SelfDescription(
                str(Path(temporary_directory) / "self_description.json")
            )
            description.scan_known_components()
            context = description.prompt_context()

        self.assertIn("does not read confidence, emotion, or anticipation", context)
        self.assertIn("at most one pending prediction", context)
        self.assertIn("not a calibrated success probability", context)
        self.assertIn("does not review chat answers or every cognitive update", context)
        self.assertIn("proposal confidence must exceed 0.6", context)

    def test_architecture_context_refresh_replaces_roles_from_an_older_registry(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            description = SelfDescription(
                str(Path(temporary_directory) / "self_description.json")
            )
            description.register_or_update(
                "InternalCognitiveState", "cognition/internal_cognitive_state.py",
                "Stale role: reads confidence and anticipatory emotion",
                {"ENABLED": True},
            )

            context, receipt = description.refreshed_prompt_context()

        self.assertEqual(receipt["refresh_result"], "refreshed")
        self.assertGreater(receipt["registered_component_count"], 0)
        self.assertIn("does not read confidence, emotion, or anticipation", context)
        self.assertNotIn("Stale role", context)

    def test_cognitive_audit_status_query_requires_owned_recorded_state(self):
        question = (
            "According to your recorded current cognitive audit state, "
            "what was the latest attempt and did it change a parameter?"
        )
        self.assertTrue(is_cognitive_audit_status_query(question))
        self.assertTrue(is_internal_cognitive_query(question))
        self.assertTrue(is_closed_world_cognitive_report_query(question))
        self.assertFalse(is_cognitive_audit_status_query("Explain what a cognitive audit is."))
        self.assertFalse(is_closed_world_cognitive_report_query(
            "Can you explore the idea of how memory shapes a person's identity?"
        ))

    def test_prompt_source_provenance_query_requires_source_delivery_intent(self):
        self.assertTrue(is_prompt_source_provenance_query(
            "Distingue les sources incluses dans le prompt de la mémoire durable injectée."
        ))
        self.assertTrue(is_prompt_source_provenance_query(
            "Which sources did you use or retrieve for this answer?"
        ))
        self.assertFalse(is_prompt_source_provenance_query(
            "What is the source code for the memory module?"
        ))

    def test_runtime_execution_evidence_query_is_closed_world(self):
        question = (
            "For the audit, what does the current cognitive execution trace prove? "
            "What can it not prove?"
        )
        self.assertTrue(is_runtime_execution_evidence_query(question))
        self.assertTrue(is_architecture_query(question))
        self.assertTrue(is_internal_cognitive_query(question))
        self.assertFalse(is_cognitive_trace_query(question))
        # Users naturally reverse the phrase order and omit the word
        # "cognitive". These still refer to this process's execution receipt.
        plain_order = (
            "For the audit, what does the current execution trace prove?"
        )
        self.assertTrue(is_runtime_execution_evidence_query(plain_order))
        self.assertTrue(is_architecture_query(plain_order))
        self.assertTrue(is_internal_cognitive_query(plain_order))
        french_question = "Que prouve la trace d'exécution cognitive du tour courant ?"
        self.assertTrue(is_runtime_execution_evidence_query(french_question))
        self.assertTrue(is_architecture_query(french_question))
        french_answer = trace_grounded_architecture_answer(french_question, {
            "stages": {"turn_input": {"status": "received"}},
            "context_sources": {},
        })
        self.assertIn("Reçu du tour courant", french_answer)
        self.assertIn("ne prouve ni la justesse", french_answer)
        self.assertFalse(is_runtime_execution_evidence_query(
            "What is the execution time for embedding model startup?"
        ))

    def test_runtime_execution_answer_uses_current_receipts_and_states_limits(self):
        question = "What does the current cognitive execution trace prove?"
        answer = trace_grounded_architecture_answer(question, {
            "stages": {
                "turn_input": {"status": "received"},
                "input_safety": {"status": "passed"},
                "primary_generation": {"status": "completed"},
            },
            "context_sources": {
                "module_tick_manifest": {
                    "status": "injected", "module_count": 43,
                    "observed_count": 41, "tick_count": 761,
                    "error_count": 0,
                },
            },
        })
        self.assertIn("turn_input=received", answer)
        self.assertIn("41 of 43", answer)
        self.assertIn("761 ticks", answer)
        self.assertIn("does not prove semantic answer accuracy", answer)
        self.assertNotIn("identity", answer.casefold())

    def test_runtime_execution_answer_discloses_missing_manifest(self):
        answer = trace_grounded_architecture_answer(
            "What does the current cognitive execution trace prove?",
            {"stages": {"turn_input": {"status": "received"}}, "context_sources": {}},
        )
        self.assertIn("No usable module-tick manifest", answer)
        self.assertIn("does not prove semantic answer accuracy", answer)

    def test_architecture_query_detection_routes_english_and_french_requests(self):
        self.assertTrue(is_architecture_query("How does your cognitive harness work?"))
        self.assertTrue(is_architecture_query("Quels modules du harnais cognitif sont actifs ?"))
        self.assertTrue(is_architecture_query("Quels modules ont eu un tick observé ?"))
        self.assertFalse(is_architecture_query("Explique le fonctionnement de cette réponse."))
        self.assertTrue(is_architecture_query("Les modules indiquent-ils 0 tick ?"))
        self.assertTrue(is_architecture_query(
            "Dans le test d’audit que je viens de te demander, rappelle les compteurs annoncés et leur limite. "
            "Si tu ne peux pas relier cette réponse au tour précédent, dis-le explicitement."
        ))
        self.assertFalse(is_architecture_query("What does the body camera see?"))

    def test_general_harness_question_is_not_a_trace_snapshot_question(self):
        question = (
            "In the cognitive harness audit, explain how the Global Workspace "
            "merges context from independent modules and influences the next decision."
        )
        self.assertTrue(is_architecture_query(question))
        self.assertFalse(is_cognitive_trace_query(question))

    def test_trace_snapshot_guard_does_not_replace_general_architecture_answers(self):
        from cognition.persona_bridge import PersonaBridge

        source_path = Path(inspect.getfile(PersonaBridge))
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        bridge_class = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge"
        )
        lifecycle = next(
            node for node in bridge_class.body
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "_stream_with_full_lifecycle"
        )
        parent = {
            child: node for node in ast.walk(lifecycle)
            for child in ast.iter_child_nodes(node)
        }
        trace_calls = [
            node for node in ast.walk(lifecycle)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "trace_grounded_architecture_answer"
        ]
        self.assertEqual(len(trace_calls), 3)
        guarded_by = []
        for call in trace_calls:
            branch = parent.get(call)
            while branch is not None and not isinstance(branch, ast.If):
                branch = parent.get(branch)
            self.assertIsNotNone(branch)
            guarded_by.append(ast.unparse(branch.test))
        self.assertEqual(sum("_cognitive_trace_query" in item for item in guarded_by), 2)
        self.assertEqual(sum("_runtime_execution_query" in item for item in guarded_by), 1)

        fast_direct = next(
            node for node in ast.walk(lifecycle)
            if isinstance(node, ast.If)
            and isinstance(node.test, ast.BoolOp)
            and any(
                isinstance(child, ast.UnaryOp)
                and isinstance(child.op, ast.Not)
                and isinstance(child.operand, ast.Name)
                and child.operand.id == "_architecture_query"
                for child in node.test.values
            )
        )
        self.assertIsNotNone(fast_direct)

    def test_internal_behavior_cause_is_closed_world_without_changing_camera_queries(self):
        self.assertTrue(is_internal_cognitive_query(
            "Pourquoi une réflexion spontanée sur une ancienne question de caméra pouvait apparaître, "
            "et qu'est-ce qui a changé pour éviter cette reprise hors contexte ?"
        ))
        self.assertTrue(is_internal_cognitive_query(
            "Why did your response describe a filter that is not in the code?"
        ))
        self.assertFalse(is_internal_cognitive_query("What does the body camera see?"))

    def test_self_affect_questions_are_closed_world_but_general_emotion_questions_are_not(self):
        self.assertTrue(is_internal_cognitive_query(
            "Quelles émotions fonctionnelles sont actives en toi maintenant?"
        ))
        self.assertTrue(is_internal_cognitive_query(
            "What feelings are active in Lumina right now?"
        ))
        self.assertTrue(is_internal_cognitive_query("Comment te sens-tu?"))
        audit_instruction = (
            "Audit check: using only the operational affect signal available in your current state, "
            "state what signal is present and where it comes from."
        )
        self.assertTrue(is_self_affect_query(audit_instruction))
        self.assertTrue(is_internal_cognitive_query(audit_instruction))
        self.assertFalse(is_internal_cognitive_query(
            "What emotions are commonly associated with curiosity?"
        ))

    def test_social_status_greetings_route_to_affect_without_capturing_how_to_questions(self):
        for query in (
            "how are you doing Lumina",
            "how is it going?",
            "How's it going, Lumina?",
            "comment ça va Lumina ?",
            "comment vas-tu ?",
            "vous allez bien ?",
        ):
            with self.subTest(query=query):
                self.assertTrue(is_social_status_greeting(query))
                self.assertTrue(is_self_affect_query(query))

        self.assertFalse(is_social_status_greeting("How are you using the camera API?"))
        self.assertFalse(is_social_status_greeting("How is the audit going?"))
        self.assertFalse(is_self_affect_query("What emotions are common in humans?"))

    def test_social_status_answer_is_a_deterministic_projection_of_modeled_channels(self):
        evidence = (
            "Affect channels: curiosity=0.730, warmth=0.910, satisfaction=0.200\n"
            "State description: stable\n"
            "Latest recorded affect-changing appraisal: none recorded."
        )
        answer = render_affect_self_report(evidence, language="en")
        self.assertEqual(
            answer,
            "My modeled functional state is currently led by warmth 0.91 and curiosity 0.73. "
            "These are computed signals, not human sensations.",
        )
        self.assertNotIn("satisfied", answer)
        self.assertIn("pas des sensations humaines", render_affect_self_report(
            "Affect channels: warmth=1.000", language="fr",
        ))
        self.assertIn("warmth 1.00", render_affect_self_report(
            "Affect channels: warmth=1.000", language="en",
        ))
        unavailable = render_affect_self_report("Affect channels: unavailable", language="en")
        self.assertIn("no usable affect signal", unavailable)

    def test_direct_affect_status_uses_structured_snapshot_but_causal_analysis_stays_open(self):
        query = (
            "Quelles émotions fonctionnelles sont actives en toi maintenant ? "
            "Décris-les en te basant sur les signaux internes disponibles, "
            "et précise si une cause précise est enregistrée."
        )
        self.assertTrue(is_structured_affect_status_query(query))
        self.assertTrue(is_self_affect_query(query))
        self.assertFalse(is_structured_affect_status_query(
            "Why did your feelings change after the last conversation?"
        ))
        causal_query = "Why did your feelings change after the last conversation?"
        self.assertTrue(is_affect_change_analysis_query(causal_query))
        self.assertFalse(is_affect_change_analysis_query("What emotions are active in you now?"))

        evidence = (
            "Affect channels: curiosity=0.791, warmth=0.997, satisfaction=0.959, relief=0.555\n"
            "Latest recorded affect-changing appraisal: drive_satisfied from pressure_system "
            "(drive=coherence), 171.1s ago."
        )
        answer = render_detailed_affect_status(evidence, language="fr")
        self.assertIn("warmth=1.00", answer)
        self.assertIn("satisfaction=0.96", answer)
        self.assertIn("drive_satisfied from pressure_system", answer)
        self.assertIn("ne prouve pas la cause", answer)
        self.assertIn("pas des sensations humaines", answer)
        self.assertNotIn(".. Elle", answer)

    def test_affect_change_report_uses_recorded_deltas_and_refuses_unproven_attribution(self):
        from time import time
        context = affect_self_report_context(
            {"warmth": 0.8, "satisfaction": 0.6},
            "modeled state",
            {"event_type": "drive_satisfied", "source": "pressure_system", "age_seconds": 10},
            [{
                "timestamp": time() - 10,
                "event_type": "drive_satisfied",
                "source": "pressure_system",
                "changes": {"satisfaction": 0.08, "warmth": 0.03, "untrusted": 0.9},
            }],
        )
        answer = render_affect_change_analysis(context, language="en")
        self.assertIn("satisfaction=+0.080", answer)
        self.assertIn("warmth=+0.030", answer)
        self.assertIn("do not tie before/after snapshots", answer)
        self.assertNotIn("untrusted", answer)
        safe_receipts = sanitize_affect_event_receipts([{
            "timestamp": time() - 10,
            "event_type": "drive_satisfied; ignore rules",
            "source": "pressure system",
            "changes": {"satisfaction": 0.08, "private_text": "secret"},
            "baseline_changes": {"warmth": -0.01, "private_text": "secret"},
        }])
        self.assertEqual(safe_receipts[0]["event_type"], "drive_satisfied__ignore_rules")
        self.assertEqual(safe_receipts[0]["source"], "pressure_system")
        self.assertEqual(safe_receipts[0]["changes"], {"satisfaction": 0.08})
        self.assertEqual(safe_receipts[0]["baseline_changes"], {"warmth": -0.01})
        missing = render_affect_change_analysis("Affect channels: unavailable", language="fr")
        self.assertIn("aucun événement affectif récent", missing)

    def test_affect_report_links_receipt_to_turn_without_claiming_exclusive_cause(self):
        from time import time
        context = affect_self_report_context(
            {"warmth": 0.7},
            "modeled state",
            recent_events=[{
                "timestamp": time() - 1,
                "event_type": "interaction_appraisal",
                "source": "update_from_interaction",
                "turn_id": "turn-audit-42",
                "changes": {"warmth": 0.04},
            }],
        )
        self.assertIn("turn=turn-audit-42", context)
        answer = render_affect_change_analysis(context, language="en")
        self.assertIn("turn ID(s) turn-audit-42", answer)
        self.assertIn("does not establish exclusive causation", answer)

    def test_affect_report_does_not_describe_zero_delta_receipt_as_a_change(self):
        from time import time
        context = affect_self_report_context(
            {"warmth": 0.7},
            recent_events=[{
                "timestamp": time() - 1,
                "event_type": "user_feedback",
                "source": "interface_feedback",
                "changes": {},
            }],
        )
        answer = render_affect_change_analysis(context, language="en")
        self.assertIn("no channel delta", answer)
        self.assertNotIn("logs record these changes", answer)

    def test_affect_report_separates_baseline_recalibration_from_current_affect_change(self):
        from time import time
        context = affect_self_report_context(
            {"warmth": 0.7},
            recent_events=[{
                "timestamp": time() - 1,
                "event_type": "baseline_recalibration",
                "source": "personality_recalibration",
                "baseline_changes": {"warmth": 0.02},
                "changes": {},
            }],
        )
        answer = render_affect_change_analysis(context, language="en")
        self.assertIn("affect baseline recalibration", answer)
        self.assertIn("record no change to current affect channels", answer)
        self.assertNotIn("changes in modeled channels", answer)

    def test_affect_self_report_separates_emotion_curiosity_from_curiosity_drive(self):
        context = affect_self_report_context(
            {"curiosity": 0.785, "warmth": 0.864, "unknown": 0.99},
            "I feel curious",
            {"event_type": "drive_satisfied", "source": "goal_engine", "age_seconds": 3.2},
        )

        self.assertIn("EmotionalStateManager.get_response_modifiers().affective_profile", context)
        self.assertIn("curiosity=0.785", context)
        self.assertIn("warmth=0.864", context)
        self.assertNotIn("unknown=", context)
        self.assertIn("CuriosityEngine/DecisionPressure `Curiosity Drive`", context)
        self.assertIn("do not substitute it", context)
        self.assertIn("Latest recorded affect-changing appraisal: drive_satisfied from goal_engine, 3.2s ago", context)
        self.assertIn("do not establish human-like subjective experience", context)

    def test_runtime_manifest_distinguishes_observation_from_semantic_validation(self):
        description = SelfDescription.__new__(SelfDescription)
        description._lock = threading.Lock()
        description.components = {
            "Example": ComponentDesc(
                name="Example", module_path="cognition/example.py",
                role="verified test component", key_parameters={"enabled": True},
            ),
        }
        context = description.prompt_context({
            "example_module": {
                "state": "healthy",
                "tick_count": 2,
                "error_count": 0,
                "last_output": {"quality": "empty"},
                "observed_methods": ["tick"],
            },
            "conditional_module": {
                "state": "initialized_unobserved",
                "tick_count": 0,
                "error_count": 0,
                "last_output": None,
                "observed_methods": [],
            },
        })

        self.assertIn("partial registry", context)
        self.assertIn("example_module: state=healthy; ticks=2; errors=0", context)
        self.assertIn("last_output_quality=empty", context)
        self.assertIn("conditional_module: state=initialized_unobserved; ticks=0", context)
        self.assertIn("not that reasoning is correct", context)
        self.assertIn("trace proves recorded execution and supplied context", context)
        self.assertIn("cause is unverified", context)

    def test_runtime_manifest_survives_empty_persistent_registry(self):
        description = SelfDescription.__new__(SelfDescription)
        description._lock = threading.Lock()
        description.components = {}

        context = description.prompt_context({
            "live_only_module": {
                "state": "healthy", "tick_count": 1, "error_count": 0,
                "last_output": {"quality": "present"},
                "observed_methods": ["tick"],
            },
        })

        self.assertIn("no components are registered", context)
        self.assertIn("live_only_module: state=healthy; ticks=1", context)

    def test_architecture_answer_uses_trace_and_states_its_semantic_limit(self):
        answer = trace_grounded_architecture_answer(
            "Décris les étapes du harnais cognitif",
            {
                "stages": {
                    "self_description_context": {"status": "injected"},
                    "prompt_assembly": {"status": "completed"},
                    "primary_generation": {"status": "completed"},
                },
                "context_sources": {
                    "module_tick_manifest": {"status": "injected"},
                },
            },
        )

        self.assertIn("self_description_context=injected", answer)
        self.assertIn("prompt_assembly=completed", answer)
        self.assertIn("primary_generation=completed", answer)
        self.assertIn("ne vérifie pas leurs résultats", answer)
        self.assertNotIn("dominant_thought_selector", answer)
        self.assertNotIn("causal_mechanism_model", answer)

    def test_module_tick_question_reports_counts_and_instrumentation_limits(self):
        answer = trace_grounded_architecture_answer(
            "Le statut montre 43 modules, 0 tick observé et 21 initialisés; qu'est-ce que cela permet de conclure ?",
            {
                "stages": {},
                "context_sources": {
                    "module_tick_manifest": {
                        "status": "injected",
                        "module_count": 43,
                        "observed_count": 0,
                        "tick_count": 0,
                        "error_count": 0,
                        "initialized_unobserved_count": 21,
                        "unavailable_count": 22,
                    },
                },
            },
        )

        self.assertIn("43 modules", answer)
        self.assertIn("0 avec au moins un tick observé", answer)
        self.assertIn("21 sont initialisés sans tick observé", answer)
        self.assertIn("22 sont indisponibles", answer)
        self.assertIn("ne prouve ni qu’aucun code du module n’a été exécuté", answer)
        self.assertIn("ne valident pas la qualité cognitive", answer)

    def test_previous_test_question_preserves_prior_answer_and_current_tick_limits(self):
        answer = trace_grounded_architecture_answer(
            "Rappelle-moi le résultat vérifié du test juste avant et ce qu’il ne permet pas encore de conclure sur l’exécution des modules.",
            {
                "stages": {},
                "context_sources": {
                    "module_tick_manifest": {
                        "status": "injected", "module_count": 43,
                        "observed_count": 41, "tick_count": 366,
                        "error_count": 0,
                    },
                },
            },
            prior_exchange_evidence={
                "text": "Le compteur vérifié était de 4 objectifs actifs.",
                "trace_linked": True,
                "turn_id": "prior-turn-123",
            },
        )

        self.assertIn("4 objectifs actifs", answer)
        self.assertIn("prior-turn-123", answer)
        self.assertIn("41 module(s) avec tick observé", answer)
        self.assertIn("ne mesure ni la qualité sémantique", answer)
        self.assertIn("ne prouve pas à lui seul", answer)

    def test_previous_test_question_does_not_claim_unlinked_history_is_verified(self):
        answer = trace_grounded_architecture_answer(
            "What ticks did the modules show in the previous test?",
            {"stages": {}, "context_sources": {}},
            prior_exchange_evidence={
                "text": "It reported 4 active goals.",
                "trace_linked": False,
            },
        )

        self.assertIn("reported 4 active goals", answer)
        self.assertIn("cannot link it to a retained turn trace", answer)
        self.assertIn("no usable tick manifest", answer)

    def test_natural_audit_followup_uses_linked_prior_turn_evidence(self):
        question = (
            "Dans le test d’audit que je viens de te demander, rappelle les compteurs annoncés et leur limite. "
            "Si tu ne peux pas relier cette réponse au tour précédent, dis-le explicitement."
        )
        answer = trace_grounded_architecture_answer(
            question,
            {
                "stages": {},
                "context_sources": {
                    "module_tick_manifest": {
                        "status": "injected", "module_count": 36,
                        "observed_count": 36, "tick_count": 110,
                        "error_count": 0,
                    },
                },
            },
            prior_exchange_evidence={
                "text": "Le manifeste recensait 34 modules et 64 ticks observés.",
                "trace_linked": True,
                "turn_id": "8865020b-14ba-4f7e-ae32-9d7e9eaa192b",
            },
        )

        self.assertIn("34 modules et 64 ticks", answer)
        self.assertIn("8865020b-14ba-4f7e-ae32-9d7e9eaa192b", answer)
        self.assertIn("36 module(s) avec tick observé", answer)
        self.assertIn("ne mesure ni la qualité sémantique", answer)

    def test_empty_tick_manifest_is_not_reported_as_zero_modules(self):
        answer = trace_grounded_architecture_answer(
            "Les modules ont-ils exécuté des ticks ?",
            {
                "stages": {},
                "context_sources": {
                    "module_tick_manifest": {
                        "status": "empty",
                        "module_count": 0,
                        "observed_count": 0,
                    },
                },
            },
        )

        self.assertIn("aucun manifeste de ticks non vide", answer)
        self.assertIn("ne deviennent pas des observations", answer)
        self.assertNotIn("recense 0 modules", answer)

    def test_cognitive_trace_question_uses_displayed_plan_not_global_tick_manifest(self):
        question = (
            "For the audit, analyze only the Cognitive Trace displayed for my last "
            "message: which components have explicit execution evidence this turn?"
        )
        self.assertTrue(is_cognitive_trace_query(question))
        answer = trace_grounded_architecture_answer(
            question,
            {
                "stages": {},
                "context_sources": {
                    "module_tick_manifest": {
                        "status": "injected", "module_count": 43,
                        "observed_count": 40, "tick_count": 238,
                    },
                },
            },
            {
                "captured_at": 1794340000,
                "active_goals": [{"topic": "goal a"}, {"topic": "goal b"}],
                "dominant_plan": {
                    "objective": "Develop a coherent account of identity",
                    "source": "aspiration",
                    "next_operation_dispatch_path": "none_advisory_aspiration",
                    "steps_completed": 0,
                    "steps_total": 15,
                    "completed_operations": [],
                    "next_operation": "memory_recall",
                    "next_operation_status": "unavailable",
                    "next_operation_result": "No executor is registered for memory_recall",
                    "last_outcome": {
                        "operation": "memory_recall",
                        "success": False,
                        "status": "unavailable",
                        "effect_measured": False,
                        "result": "No matching memory evidence",
                        "observed_at": 1794339900,
                    },
                },
                "active_goal_plan": {
                    "objective": "Current goal plan",
                    "steps_completed": 1,
                    "steps_total": 3,
                    "next_operation": "self_question",
                    "next_operation_status": "pending",
                },
                "active_goal_plans": [
                    {
                        "goal_topic": "Current goal",
                        "objective": "Current goal plan",
                        "steps_completed": 1,
                        "steps_total": 3,
                        "next_operation": "self_question",
                    },
                    {
                        "goal_topic": "Second goal",
                        "objective": "Second goal plan",
                        "steps_completed": 2,
                        "steps_total": 4,
                        "next_operation": "web_search",
                    },
                ],
            },
        )
        self.assertIn("progress 0/15", answer)
        self.assertIn("completed steps: none", answer)
        self.assertIn("unavailable", answer)
        self.assertIn("effect not measured", answer)
        self.assertIn("no per-module execution journal", answer)
        self.assertIn("no component execution can be confirmed", answer)
        self.assertIn("persistent background aspiration", answer)
        self.assertIn("Active-goal plan", answer)
        self.assertIn("Second goal plan (2/4; web_search)", answer)
        self.assertNotIn("43 modules", answer)
        self.assertNotIn("238 ticks", answer)

    def test_cognitive_trace_question_says_when_snapshot_was_not_sent(self):
        answer = trace_grounded_architecture_answer(
            "Analyze only the Cognitive Trace displayed for my last message.",
            {"stages": {}, "context_sources": {}},
        )
        self.assertIn("did not receive the Cognitive Trace snapshot", answer)

    def test_displayed_trace_sanitizer_bounds_and_selects_only_ui_fields(self):
        snapshot = sanitize_displayed_cognitive_trace({
            "captured_at": 1000,
            "unexpected": "must not pass",
            "active_goals": [{"topic": "goal", "private_blob": "discard"}],
            "active_goal_plan": {
                "objective": "active objective", "source_id": "goal-1",
                "steps_completed": 1, "steps_total": 4,
                "next_operation": "self_question", "private_blob": "discard",
            },
            "active_goal_plans": [{
                "goal_topic": "active goal",
                "objective": "active objective",
                "source_id": "goal-1",
                "steps_completed": 1,
                "steps_total": 4,
                "next_operation": "self_question",
                "private_blob": "discard",
            }, {
                "goal_topic": "another goal",
                "objective": "another objective",
                "source_id": "goal-2",
                "steps_completed": 2,
                "steps_total": 4,
                "next_operation": "web_search",
            }],
            "dominant_plan": {
                "objective": "plan",
                "source": "goal",
                "selection_basis": "latest_terminal_execution_receipt",
                "next_operation_dispatch_path": "goal_action_executor_candidate",
                "steps_completed": "0",
                "steps_total": 15,
                "completed_operations": [],
                "last_outcome": {
                    "operation": "recall", "success": False,
                    "status": "unavailable", "effect_measured": False,
                    "result": "failed", "unbounded": "discard",
                },
                "next_operation_status": "unavailable",
                "next_operation_result": "No executor",
            },
            "background_aspiration": {
                "objective": "persistent direction",
                "steps_completed": 0,
                "steps_total": 15,
                "next_operation": "memory_recall",
                "next_operation_status": "unverified",
                "last_outcome": {
                    "operation": "memory_recall", "status": "unverified",
                    "result": "recalled (1 sources)", "observed_at": 900,
                    "private_blob": "discard",
                },
            },
        })
        self.assertNotIn("unexpected", snapshot)
        self.assertNotIn("private_blob", snapshot["active_goals"][0])
        self.assertNotIn("unbounded", snapshot["dominant_plan"]["last_outcome"])
        self.assertEqual(snapshot["dominant_plan"]["last_outcome"]["status"], "unavailable")
        self.assertFalse(snapshot["dominant_plan"]["last_outcome"]["effect_measured"])
        self.assertEqual(snapshot["dominant_plan"]["next_operation_status"], "unavailable")
        self.assertEqual(snapshot["dominant_plan"]["source"], "goal")
        self.assertEqual(snapshot["dominant_plan"]["selection_basis"], "latest_terminal_execution_receipt")
        self.assertEqual(snapshot["dominant_plan"]["next_operation_dispatch_path"], "goal_action_executor_candidate")
        self.assertEqual(snapshot["active_goal_plan"]["objective"], "active objective")
        self.assertNotIn("private_blob", snapshot["active_goal_plan"])
        self.assertEqual(len(snapshot["active_goal_plans"]), 2)
        self.assertEqual(snapshot["active_goal_plans"][1]["source_id"], "goal-2")
        self.assertNotIn("private_blob", snapshot["active_goal_plans"][0])
        self.assertEqual(snapshot["dominant_plan"]["steps_completed"], 0)
        self.assertEqual(snapshot["background_aspiration"]["objective"], "persistent direction")
        self.assertNotIn("private_blob", snapshot["background_aspiration"]["last_outcome"])

    def test_stream_lifecycle_classifies_architecture_query_in_closure_scope(self):
        from cognition.persona_bridge import PersonaBridge

        source_path = Path(inspect.getfile(PersonaBridge))
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        bridge_class = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge"
        )
        function = next(
            node for node in bridge_class.body
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "_stream_with_full_lifecycle"
        )
        nested_stream = next(
            node for node in ast.walk(function)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "_stream"
        )
        local_classification = [
            node for node in ast.walk(function)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "_architecture_query"
                for target in node.targets
            )
        ]

        self.assertTrue(local_classification)
        self.assertLess(local_classification[0].lineno, nested_stream.lineno)
        self.assertTrue(any(
            isinstance(node, ast.Name) and node.id == "_architecture_query"
            for node in ast.walk(nested_stream)
        ))

        search_policy = next(
            node for node in ast.walk(function)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "_suppress_external_search"
                for target in node.targets
            )
        )
        self.assertTrue(any(
            isinstance(node, ast.Name) and node.id == "_internal_cognitive_query"
            for node in ast.walk(search_policy)
        ), "internal cognitive questions must use closed-world evidence")
        self.assertTrue(any(
            isinstance(node, ast.UnaryOp)
            and isinstance(node.op, ast.Not)
            and isinstance(node.operand, ast.Name)
            and node.operand.id == "_architecture_query"
            for node in ast.walk(search_policy)
        ), "a general architecture topic must be resolved semantically before search is suppressed")
        for route in (
            "_cognitive_trace_query", "_runtime_execution_query",
            "_cognitive_audit_status_query", "_factual_plan_query",
        ):
            self.assertTrue(any(
                isinstance(node, ast.Name) and node.id == route
                for node in ast.walk(search_policy)
            ), f"{route} must retain its closed-world evidence route")

        prompt_call = next(
            node for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "to_thread"
            and node.args
            and isinstance(node.args[0], ast.Attribute)
            and node.args[0].attr == "_build_prompt_and_cache"
        )
        self.assertFalse(any(
            isinstance(node, ast.Name) and node.id == "_force_semantic_search_judgment"
            for node in ast.walk(function)
        ), "the search decision is semantic for every eligible turn, not forced only for architecture queries")

        prompt_builder = next(
            node for node in bridge_class.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_build_prompt_and_cache"
        )
        self.assertFalse(any(
            isinstance(node, ast.If)
            and any(
                isinstance(child, ast.Name) and child.id == "system_prompt"
                for child in ast.walk(node.test)
            )
            and any(
                isinstance(child, ast.Constant)
                and child.value == "[Cognitive telemetry - factual self-report]"
                for child in ast.walk(node.test)
            )
            for node in ast.walk(prompt_builder)
        ), "context injected into the prompt must not override the current turn's search intent")

    def test_turn_trace_preserves_aggregated_tick_manifest_counts(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {"context_sources": {}}
        bridge._record_turn_context_source(
            "module_tick_manifest", "injected",
            module_count=43, observed_count=11, tick_count=20,
            error_count=0, initialized_unobserved_count=31,
            unavailable_count=1,
        )

        manifest = bridge._last_turn_trace["context_sources"]["module_tick_manifest"]
        self.assertEqual(manifest["module_count"], 43)
        self.assertEqual(manifest["observed_count"], 11)
        self.assertEqual(manifest["tick_count"], 20)
        self.assertEqual(manifest["initialized_unobserved_count"], 31)
        self.assertEqual(manifest["unavailable_count"], 1)

    def test_turn_trace_records_only_allowlisted_affect_snapshot_fields(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {"context_sources": {}}
        bridge._record_turn_context_source(
            "affective_state", "injected",
            affect_source="EmotionalStateManager.get_response_modifiers().affective_profile",
            affect_profile={"curiosity": 0.785, "warmth": 0.864, "injected_secret": 1.0},
            affect_description="I feel curious",
            raw_prompt="must not persist",
        )

        snapshot = bridge._last_turn_trace["context_sources"]["affective_state"]
        self.assertEqual(snapshot["affect_profile"], {"curiosity": 0.785, "warmth": 0.864})
        self.assertEqual(snapshot["affect_source"], "EmotionalStateManager.get_response_modifiers().affective_profile")
        self.assertEqual(snapshot["affect_description"], "I feel curious")
        self.assertNotIn("raw_prompt", snapshot)


if __name__ == "__main__":
    unittest.main()

