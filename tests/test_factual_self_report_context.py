import unittest
import importlib.util
import ast
from pathlib import Path

_HELPER_PATH = Path(__file__).resolve().parents[1] / "cognition" / "factual_self_report_context.py"
_SPEC = importlib.util.spec_from_file_location("factual_self_report_context_test", _HELPER_PATH)
_HELPER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPER)
history_without_assistant_claims = _HELPER.history_without_assistant_claims


class FactualSelfReportContextTests(unittest.TestCase):
    def test_factual_plan_route_is_initialized_before_closed_world_expression(self):
        source_path = _HELPER_PATH.parents[1] / "cognition" / "persona_bridge.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        bridge = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge"
        )
        lifecycle = next(
            node for node in bridge.body
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "_stream_with_full_lifecycle"
        )
        route_try = next(
            node for node in ast.walk(lifecycle)
            if isinstance(node, ast.Try)
            and any(
                isinstance(child, ast.Assign)
                and any(
                    isinstance(target, ast.Name)
                    and target.id == "_closed_world_cognitive_report_query"
                    for target in child.targets
                )
                for child in node.body
            )
        )
        factual_assignment = next(
            index for index, node in enumerate(route_try.body)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "_factual_plan_query"
                for target in node.targets
            )
        )
        closed_world_assignment = next(
            index for index, node in enumerate(route_try.body)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "_closed_world_cognitive_report_query"
                for target in node.targets
            )
        )
        self.assertLess(factual_assignment, closed_world_assignment)

    def test_turn_route_classification_is_recorded_against_input_evidence(self):
        source = (_HELPER_PATH.parents[1] / "cognition" / "persona_bridge.py").read_text(encoding="utf-8")
        self.assertIn('"turn_evidence_routing", "classified"', source)
        self.assertIn('"factual_plan_query": bool(_factual_plan_query)', source)
        self.assertIn('"closed_world_report": bool(_closed_world_cognitive_report_query)', source)
        self.assertIn('error_type=type(_architecture_query_error).__name__', source)

    def test_planner_self_report_suppresses_assistant_continuity_and_filters_history(self):
        source = (_HELPER_PATH.parents[1] / "cognition" / "persona_bridge.py").read_text(encoding="utf-8")
        self.assertIn(
            '"" if (_architecture_query or _factual_plan_query)', source,
        )
        self.assertIn('if _factual_self_report:', source)
        self.assertIn('"historical_assistant_context", "filtered"', source)

    def test_plan_answer_trace_consumes_the_snapshot_used_to_render_it(self):
        source = (_HELPER_PATH.parents[1] / "cognition" / "persona_bridge.py").read_text(encoding="utf-8")
        self.assertIn('"planner_factual_snapshot", "captured"', source)
        self.assertIn('snapshot=_planner_snapshot', source)
        self.assertIn('("turn_input", "planner_factual_snapshot")', source)

    def test_keeps_user_context_and_excludes_prior_assistant_claims(self):
        history = [
            {"role": "user", "content": "What is the active audit plan?"},
            {"role": "assistant", "content": "Confidence is 0.96."},
            {"role": "user", "content": "That confidence is not in the trace."},
            {"role": "assistant", "content": "I checked again."},
            {"role": "assistant", "content": "  "},
            {"role": "system", "content": "unexpected provider metadata"},
        ]

        filtered, counts = history_without_assistant_claims(history)

        self.assertEqual(
            filtered,
            [
                {"role": "user", "content": "What is the active audit plan?"},
                {"role": "user", "content": "That confidence is not in the trace."},
            ],
        )
        self.assertEqual(counts, {
            "retained_user_messages": 2,
            "excluded_assistant_messages": 2,
        })
        self.assertEqual(history[1]["content"], "Confidence is 0.96.")

    def test_invalid_history_fails_closed_to_empty_context(self):
        filtered, counts = history_without_assistant_claims(None)
        self.assertEqual(filtered, [])
        self.assertEqual(counts, {
            "retained_user_messages": 0,
            "excluded_assistant_messages": 0,
        })


if __name__ == "__main__":
    unittest.main()
