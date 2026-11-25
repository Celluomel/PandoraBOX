"""Regression tests for goal preservation in practical decisions."""
import ast
from pathlib import Path
import sys
import time
from types import ModuleType
import unittest
from unittest.mock import patch

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
package = ModuleType("cognition")
package.__path__ = [str(ROOT / "cognition")]
sys.modules["cognition"] = package

from cognition.goal_means_reasoning import (
    analysis_prompt, goal_means_contract, guarded_response, is_analysis_followup,
    parse_analysis, classify_goal_means_intent, _GOAL_MEANS_ROUTER_CACHE,
    _GOAL_MEANS_POSITIVE_EXAMPLES, _GOAL_MEANS_NEGATIVE_EXAMPLES,
)
from cognition.abstract_reasoning_engine import AbstractReasoningEngine, ReasoningResult


class GoalMeansReasoningTests(unittest.TestCase):
    def test_semantic_router_uses_vector_margin_and_routes_uncertainty_to_analysis(self):
        class FakeEmbedder:
            embedding_space_id = "test-semantic-space"

            def encode_interactive_with_metadata(self, texts):
                if isinstance(texts, str):
                    texts = [texts]
                    single = True
                else:
                    single = False
                rows = []
                for text in texts:
                    if text in _GOAL_MEANS_POSITIVE_EXAMPLES:
                        rows.append([1.0, 0.0])
                    elif text in _GOAL_MEANS_NEGATIVE_EXAMPLES:
                        rows.append([0.0, 1.0])
                    elif text == "action-like":
                        rows.append([0.8, 0.2])
                    elif text == "boundary":
                        rows.append([0.710, 0.704])
                    else:
                        rows.append([0.2, 0.98])
                values = np.asarray(rows, dtype="float64")
                return (values[0] if single else values), self.embedding_space_id

        _GOAL_MEANS_ROUTER_CACHE.clear()
        positive = classify_goal_means_intent("action-like", embedder=FakeEmbedder())
        boundary = classify_goal_means_intent("boundary", embedder=FakeEmbedder())
        factual = classify_goal_means_intent("factual", embedder=FakeEmbedder())

        self.assertEqual(positive["status"], "semantic_action_candidate")
        self.assertEqual(positive["route"], "analyze")
        self.assertEqual(boundary["status"], "semantic_boundary_uncertain")
        self.assertEqual(boundary["route"], "analyze")
        self.assertEqual(factual["status"], "semantic_non_action_or_low_evidence")
        self.assertEqual(factual["route"], "skip")
        self.assertIn("not a probability", positive["score_semantics"])

    def test_semantic_protocol_is_injected_independent_of_wording(self):
        question = (
            "je dois aller laver ma voiture et le lavage auto se trouve a 150 "
            "metres dois'je prendre ma voiture"
        )
        contract = goal_means_contract(question)
        self.assertIn("advice, choose an action, or plan", contract)
        self.assertIn("factual questions, research requests", contract)
        self.assertIn("advice, choose an action, or plan", goal_means_contract("Parlons de musique."))

    def test_deferred_selector_uses_semantic_applicability_field(self):
        self.assertIn("do not use keyword lists, phrase matching", analysis_prompt("J'ai faim."))
        not_applicable = parse_analysis('{"applicable": false, "primary_goal": "", "options": []}')
        self.assertIsNotNone(not_applicable)
        self.assertFalse(not_applicable.applicable)

    def test_contract_orders_goal_and_prerequisites_before_preferences(self):
        contract = goal_means_contract("Should I take route A or route B?")
        self.assertIn("preserve the user's actual outcome", contract)
        self.assertIn("must be present", contract)
        self.assertIn("Reject an option", contract)
        self.assertIn("Treat unknown conditions as unknown", contract)
        self.assertIn(
            'decision-maker is named "Fred"',
            analysis_prompt("Dois-je y aller ?", agent_name="Fred"),
        )

    def test_structured_analysis_exposes_feasibility_to_final_generation(self):
        raw = '''```json
        {
          "primary_goal": "deliver the package",
          "required_conditions": ["the package must reach the destination"],
          "options": [
            {"name": "leave it at home", "agent_at_execution_location": true, "patient_at_execution_location": false, "required_resources_available": true, "feasible": true, "reason": "the package does not move"},
            {"name": "carry it", "agent_at_execution_location": true, "patient_at_execution_location": true, "required_resources_available": true, "feasible": false, "reason": "the package reaches the destination"}
          ],
          "recommended_option": "carry it",
          "decisive_reason": "the package must move"
        }
        ```'''
        analysis = parse_analysis(raw)
        fragment = analysis.prompt_fragment()
        self.assertIn("Primary intended outcome: deliver the package", fragment)
        self.assertIn("Option leave it at home: INFEASIBLE", fragment)
        self.assertIn("Recommendation: carry it", fragment)
        self.assertIn("Decisive reason: the package reaches the destination", fragment)
        self.assertIn("logical AND of all four fields", analysis_prompt("Should I go?"))
        self.assertIn("neutral action phrases from the user's perspective", analysis_prompt("Should I go?"))
        self.assertIn('never as Lumina\'s or the user\'s first-', analysis_prompt("Should I go?"))

    def test_guard_replaces_a_recommendation_that_reverses_feasibility(self):
        raw = '''{
          "primary_goal": "réparer le vélo",
          "options": [
            {"name": "à pied", "agent_at_execution_location": true, "patient_at_execution_location": false, "required_resources_available": true, "reason": "Le vélo resterait sur place."},
            {"name": "avec le vélo", "agent_at_execution_location": true, "patient_at_execution_location": true, "required_resources_available": true, "reason": "Le vélo arrive à l'atelier."}
          ],
          "recommended_option": "à pied"
        }'''
        analysis = parse_analysis(raw)
        response, replaced = guarded_response(
            "Je vous recommande d'y aller à pied car il fait beau.",
            analysis,
            "Je dois réparer mon vélo chez le réparateur, est-ce que j'y vais à pied ou avec le vélo ?",
        )
        self.assertTrue(replaced)
        self.assertIn("avec le vélo", response)
        self.assertNotIn("il fait beau", response)

    def test_agent_physical_limit_can_make_an_option_infeasible(self):
        analysis = parse_analysis('''{
          "primary_goal": "intercepter un objet",
          "options": [{
            "name": "courir jusqu'au point d'impact",
            "agent_at_execution_location": true,
            "patient_at_execution_location": true,
            "required_resources_available": true,
            "agent_capability_sufficient": false,
            "feasible": true,
            "reason": "la performance requise dépasse les limites humaines"
          }]
        }''')
        self.assertFalse(analysis.options[0].feasible)

    def test_material_continuity_repairs_ambiguous_travel_analysis(self):
        analysis = parse_analysis('''{
          "primary_goal": "réparer le microscope",
          "semantic_roles": {
            "agent": "Fred",
            "action": "réparer",
            "patient_or_theme": "le microscope",
            "execution_location": "l'atelier"
          },
          "options": [
            {"name": "à pied", "agent_at_execution_location": true, "patient_at_execution_location": true, "required_resources_available": true, "feasible": true, "reason": "trajet agréable"},
            {"name": "avec le microscope", "agent_at_execution_location": true, "patient_at_execution_location": true, "required_resources_available": true, "feasible": true, "reason": "trajet possible"}
          ],
          "recommended_option": "ask for clarification"
        }''')
        self.assertEqual("avec le microscope", analysis.unique_feasible_option().name)
        self.assertFalse(analysis.options[0].moves_patient_or_theme)
        self.assertFalse(analysis.options[0].patient_at_execution_location)
        self.assertTrue(analysis.options[1].moves_patient_or_theme)
        self.assertIn("présence de le microscope", analysis.options[1].reason)

    def test_explicit_patient_motion_controls_feasibility(self):
        analysis = parse_analysis('''{
          "primary_goal": "inspect the machine at the lab",
          "semantic_roles": {"action": "inspect", "patient_or_theme": "machine", "execution_location": "lab"},
          "patient_must_move_to_execution_location": true,
          "options": [
            {"name": "go alone", "moves_patient_or_theme": false, "agent_at_execution_location": true, "patient_at_execution_location": true, "required_resources_available": true, "agent_capability_sufficient": true},
            {"name": "transport the machine", "moves_patient_or_theme": true, "agent_at_execution_location": true, "patient_at_execution_location": false, "required_resources_available": true, "agent_capability_sufficient": true}
          ]
        }''')
        self.assertFalse(analysis.options[0].feasible)
        self.assertTrue(analysis.options[1].feasible)
        self.assertEqual("transport the machine", analysis.recommended_option)

    def test_guard_replaces_even_a_valid_recommendation_with_unsupported_reason(self):
        raw = '''{
          "primary_goal": "deliver the parcel",
          "options": [
            {"name": "leave it", "agent_at_execution_location": true, "patient_at_execution_location": false, "required_resources_available": true, "reason": "parcel stays behind"},
            {"name": "carry it", "agent_at_execution_location": true, "patient_at_execution_location": true, "required_resources_available": true, "reason": "parcel arrives"}
          ],
          "recommended_option": "carry it"
        }'''
        analysis = parse_analysis(raw)
        candidate = "I recommend carry it because the parcel must arrive."
        response, replaced = guarded_response(candidate, analysis, "Should I leave it or carry it?")
        self.assertTrue(replaced)
        self.assertIn("I recommend **carry it**", response)
        self.assertIn("parcel arrives", response)
        self.assertNotIn("because the parcel must arrive", response)

    def test_guard_replaces_correct_option_with_wrong_causal_explanation(self):
        raw = '''{
          "primary_goal": "laver la voiture au lavage",
          "options": [
            {"name": "à pied", "agent_at_execution_location": true, "patient_at_execution_location": false, "required_resources_available": true, "reason": "la voiture resterait à la maison"},
            {"name": "en voiture", "agent_at_execution_location": true, "patient_at_execution_location": true, "required_resources_available": true, "reason": "la voiture doit être présente au lavage"}
          ]
        }'''
        analysis = parse_analysis(raw)
        response, replaced = guarded_response(
            "Je recommande d'y aller en voiture car 150 mètres, c'est trop loin à pied.",
            analysis,
            "Je dois laver ma voiture à 150 mètres, dois-je prendre ma voiture ?",
        )
        self.assertTrue(replaced)
        self.assertIn("en voiture", response)
        self.assertIn("présente au lavage", response)
        self.assertNotIn("150 mètres", response)

    def test_guard_uses_structured_reason_when_model_adds_contrasting_reasoning(self):
        raw = '''{
          "primary_goal": "deliver the parcel",
          "options": [
            {"name": "leave it", "agent_at_execution_location": true, "patient_at_execution_location": false, "required_resources_available": true, "reason": "parcel stays behind"},
            {"name": "carry it", "agent_at_execution_location": true, "patient_at_execution_location": true, "required_resources_available": true, "reason": "parcel arrives"}
          ]
        }'''
        analysis = parse_analysis(raw)
        candidate = "I recommend carry it. Leaving it would be easier, but the parcel would stay behind."
        response, replaced = guarded_response(candidate, analysis, "Should I leave it or carry it?")
        self.assertTrue(replaced)
        self.assertIn("I recommend **carry it**", response)
        self.assertIn("parcel arrives", response)

    def test_followup_recognizes_option_confirmation_and_causal_correction(self):
        raw = '''{
          "primary_goal": "laver la voiture",
          "options": [
            {"name": "à pied", "agent_at_execution_location": true, "patient_at_execution_location": false, "required_resources_available": true, "reason": "la voiture reste ailleurs"},
            {"name": "en voiture", "agent_at_execution_location": true, "patient_at_execution_location": true, "required_resources_available": true, "reason": "la voiture arrive au lavage"}
          ]
        }'''
        analysis = parse_analysis(raw)
        self.assertTrue(is_analysis_followup("la voiture", analysis))
        self.assertTrue(is_analysis_followup(
            "si je n'amène pas la voiture je ne peux pas la laver", analysis
        ))
        self.assertFalse(is_analysis_followup("parlons maintenant de musique", analysis))

        response, replaced = guarded_response(
            "Et si nous explorions tout de même la marche ?",
            analysis,
            "si je n'amène pas la voiture je ne peux pas la laver",
            continuation=True,
        )
        self.assertTrue(replaced)
        self.assertTrue(response.startswith("Exactement."))

    def test_french_option_is_normalized_to_an_infinitive_phrase(self):
        analysis = parse_analysis('''{
          "primary_goal": "laver la voiture",
          "options": [
            {"name": "y vais en voiture", "agent_at_execution_location": true, "patient_at_execution_location": true, "required_resources_available": true, "reason": "la voiture arrive"}
          ]
        }''')
        self.assertEqual(analysis.recommended_option, "y aller en voiture")

    def test_contract_is_injected_immediately_before_generation(self):
        tree = ast.parse((ROOT / "cognition/persona_bridge.py").read_text(encoding="utf-8"))
        method = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "_stream_with_full_lifecycle"
        )
        source = ast.get_source_segment(
            (ROOT / "cognition/persona_bridge.py").read_text(encoding="utf-8"), method
        )
        self.assertIn("goal_means_contract(effective_input)", source)
        self.assertIn("classify_goal_means_intent", source)
        self.assertIn("goal_means_pre_response_analysis", source)
        self.assertIn('getattr(_analysis_manager, "generate_bare_result", None)', source)
        self.assertIn("_allow_interactive_turn=True", source)
        self.assertIn('_audit_origin="cognition.goal_means_reasoning.pre_response"', source)
        self.assertNotIn("is_practical_decision", source)
        self.assertNotIn("Lead with the feasible recommendation", source)
        self.assertIn("guarded_response", source)
        self.assertIn("_validate_before_display", source)
        self.assertLess(source.index("goal_means_contract(effective_input)"), source.index("def _stream():"))
        self.assertLess(source.index("classify_goal_means_intent"), source.index("def _stream():"))
        self.assertLess(
            source.index('_deterministic_response = ""'),
            source.index("classify_goal_means_intent"),
        )
        self.assertIn("_goal_means_gate_response", source)

        bridge_source = (ROOT / "cognition/persona_bridge.py").read_text(encoding="utf-8")
        tree = ast.parse(bridge_source)
        deferred = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "run_deferred_goal_means_analysis"
        )
        deferred_source = ast.get_source_segment(bridge_source, deferred)
        self.assertIn("analysis_prompt(user_text", deferred_source)
        self.assertIn("generate_bare_result", deferred_source)
        self.assertIn("parse_analysis", deferred_source)

    def test_goal_means_does_not_schedule_a_second_provider_call_after_delivery(self):
        source = (ROOT / "cognition/persona_bridge.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        stream = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "_stream_with_full_lifecycle"
        )
        stream_source = ast.get_source_segment(source, stream)
        stage = stream_source[stream_source.index('"goal_means_post_response"'):]
        self.assertIn("covered_by_foreground_protocol", stage)
        self.assertNotIn("run_deferred_goal_means_analysis", stage)

    def test_blocking_fallback_keeps_quantitative_guard(self):
        source = (ROOT / "cognition/persona_bridge.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        method = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "_get_response_stream_impl"
        )
        method_source = ast.get_source_segment(source, method)
        fallback_call = method_source.index("self._system.get_response")
        guard_call = method_source.index("guard_quantitative_response", fallback_call)
        fake_stream = method_source.index("# Fake-stream word by word")
        self.assertLess(fallback_call, guard_call)
        self.assertLess(guard_call, fake_stream)

    def test_physically_impossible_turn_bypasses_llm_but_keeps_history(self):
        source = (ROOT / "cognition/persona_bridge.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        method = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "_stream_with_full_lifecycle"
        )
        method_source = ast.get_source_segment(source, method)
        deterministic_branch = method_source.index("if _deterministic_response:")
        provider_call = method_source.index("for token in self._llm_stream_fn")
        self.assertLess(deterministic_branch, provider_call)
        self.assertIn("_record_exchange(effective_input, _deterministic_response)", method_source)
        self.assertIn("physically infeasible turn resolved without LLM", method_source)

    def test_llm_reload_rewires_goal_means_analysis_manager(self):
        source = (ROOT / "core/state.py").read_text(encoding="utf-8")
        self.assertIn("self.persona._external_llm_fn = new_bare", source)

    def test_previous_reasoning_is_preserved_but_marked_as_continuity(self):
        engine = AbstractReasoningEngine(None, None)
        previous = ReasoningResult(
            user_id="fred",
            core_concept="identity",
            prompt_fragment="prior insight",
        )
        engine._cache["fred"] = previous
        engine._last_input["fred"] = "what is identity"
        engine._last_run["fred"] = time.time()

        with patch.object(engine, "_score_abstractness", return_value=0.1):
            self.assertIsNone(engine.reason("fred", "a concrete follow-up"))

        fragment = engine.get_reasoning_fragment("fred")
        self.assertIn("prior insight", fragment)
        self.assertIn("continuity only", fragment)
        self.assertIn("must not replace or override", fragment)


if __name__ == "__main__":
    unittest.main()
