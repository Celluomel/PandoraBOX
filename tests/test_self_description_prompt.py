import unittest
import threading
import ast
import inspect
from pathlib import Path

from cognition.self_description import (
    ComponentDesc,
    SelfDescription,
    is_architecture_query,
    is_cognitive_trace_query,
    sanitize_displayed_cognitive_trace,
    trace_grounded_architecture_answer,
)


class SelfDescriptionPromptTests(unittest.TestCase):
    def test_architecture_query_detection_routes_english_and_french_requests(self):
        self.assertTrue(is_architecture_query("How does your cognitive harness work?"))
        self.assertTrue(is_architecture_query("Quels modules du harnais cognitif sont actifs ?"))
        self.assertTrue(is_architecture_query("Quels modules ont eu un tick observé ?"))
        self.assertFalse(is_architecture_query("Explique le fonctionnement de cette réponse."))
        self.assertTrue(is_architecture_query("Les modules indiquent-ils 0 tick ?"))
        self.assertFalse(is_architecture_query("What does the body camera see?"))

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
        self.assertIn("does not prove its result is correct", context)

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
                    "steps_completed": 0,
                    "steps_total": 15,
                    "completed_operations": [],
                    "next_operation": "memory_recall",
                    "last_outcome": {
                        "operation": "memory_recall",
                        "success": False,
                        "result": "No matching memory evidence",
                        "observed_at": 1794339900,
                    },
                },
            },
        )
        self.assertIn("progress 0/15", answer)
        self.assertIn("completed steps: none", answer)
        self.assertIn("failure", answer)
        self.assertIn("no per-module execution journal", answer)
        self.assertIn("no component execution can be confirmed", answer)
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
            "dominant_plan": {
                "objective": "plan",
                "steps_completed": "0",
                "steps_total": 15,
                "completed_operations": [],
                "last_outcome": {
                    "operation": "recall", "success": False,
                    "result": "failed", "unbounded": "discard",
                },
            },
        })
        self.assertNotIn("unexpected", snapshot)
        self.assertNotIn("private_blob", snapshot["active_goals"][0])
        self.assertNotIn("unbounded", snapshot["dominant_plan"]["last_outcome"])
        self.assertEqual(snapshot["dominant_plan"]["steps_completed"], 0)

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
            isinstance(node, ast.Name) and node.id == "_architecture_query"
            for node in ast.walk(search_policy)
        ), "architecture audit turns must use closed-world evidence")

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


if __name__ == "__main__":
    unittest.main()
