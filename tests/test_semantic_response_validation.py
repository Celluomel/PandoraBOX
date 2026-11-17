import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "semantic_response_validation_under_test",
    ROOT / "cognition" / "semantic_response_validation.py",
)
semantic = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = semantic
SPEC.loader.exec_module(semantic)


class SemanticResponseValidationTests(unittest.TestCase):
    def test_reviewer_receipt_distinguishes_supported_answer_from_truth_proof(self):
        def reviewer(prompt, **kwargs):
            self.assertIn("REQUEST:", prompt)
            self.assertIn("CANDIDATE ANSWER:", prompt)
            self.assertEqual(kwargs["temperature"], 0.0)
            self.assertEqual(kwargs["json_schema"], semantic.REVIEW_RESPONSE_SCHEMA)
            return json.dumps({
                "relevant": True,
                "claim_basis": "factual",
                "evidence_support": "partially_supported",
                "contract_compliant": True,
                "material_issues": [],
                "repair": "",
            })

        result = semantic.review_response(
            reviewer,
            request="What did the current sensor report?",
            response="The latest reading is 0.8 m.",
            context="Latest sensor reading: 0.8 m.",
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["scope"], "probabilistic_semantic_consistency_not_truth_proof")

    def test_invalid_reviewer_output_is_not_misreported_as_validation(self):
        result = semantic.review_response(
            lambda *_args, **_kwargs: "not json",
            request="Question",
            response="Private answer text",
        )

        self.assertEqual(result["status"], "invalid_review_output")
        self.assertNotIn("Private answer text", str(result))

    def test_subjective_answer_can_pass_when_relevant_and_within_contract(self):
        def reviewer(*_args, **_kwargs):
            return json.dumps({
                "relevant": True,
                "claim_basis": "subjective_or_creative",
                "evidence_support": "insufficient_evidence",
                "contract_compliant": True,
                "material_issues": [],
                "repair": "",
            })

        result = semantic.review_response(
            reviewer,
            request="What is your view of the poem?",
            response="I find its imagery striking.",
        )

        self.assertEqual(result["status"], "passed")

    def test_strict_evidence_review_does_not_exempt_unsupported_subjective_claims(self):
        captured = {}

        def reviewer(prompt, **_kwargs):
            captured["prompt"] = prompt
            return json.dumps({
                "relevant": True,
                "claim_basis": "subjective_or_creative",
                "evidence_support": "insufficient_evidence",
                "contract_compliant": True,
                "material_issues": ["felt sensation is not in the signal snapshot"],
                "repair": "The modeled warmth channel is active; this is not evidence of a felt sensation.",
            })

        result = semantic.review_response(
            reviewer,
            request="What affect signals are active in you?",
            response="I feel a strong warmth.",
            context="AFFECT SELF-REPORT EVIDENCE: warmth=0.82 is a modeled channel.",
            constraints="Do not claim subjective experience.",
            require_evidence_support=True,
        )

        self.assertIn("evidence support is mandatory", captured["prompt"])
        self.assertEqual(result["status"], "needs_revision")
        self.assertEqual(result["evidence_support"], "insufficient_evidence")

    def test_review_call_exception_is_recorded_without_response_text(self):
        def fail(*_args, **_kwargs):
            raise TimeoutError

        result = semantic.review_response(
            fail, request="Question", response="Private answer text",
        )

        self.assertEqual(result, {
            "status": "unavailable",
            "scope": "probabilistic_semantic_consistency_not_truth_proof",
            "reason": "TimeoutError",
        })

    def test_large_prompt_context_is_reduced_to_request_relevant_passages(self):
        context = (
            "UNRELATED COGNITIVE STATE\n" + "calibration curiosity attention. " * 260
            + "\n\nCURRENT SENSOR EVIDENCE\nThe sensor value is 0.8 m."
            + "\n\nUNRELATED HISTORY\n" + "narrative identity and reflection. " * 260
        )
        captured = {}

        def reviewer(prompt, **_kwargs):
            captured["prompt"] = prompt
            return json.dumps({
                "relevant": True,
                "claim_basis": "factual",
                "evidence_support": "supported",
                "contract_compliant": True,
                "material_issues": [],
                "repair": "",
            })

        semantic.review_response(
            reviewer,
            request="What sensor value was reported?",
            response="The sensor value was 0.8 m.",
            context=context,
        )

        prompt = captured["prompt"]
        context_section = prompt.split("REFERENCE CONTEXT (may be incomplete):\n", 1)[1]
        context_section = context_section.split("\n\nCANDIDATE ANSWER:", 1)[0]
        self.assertLessEqual(len(context_section), semantic.MAX_CONTEXT_CHARS)
        self.assertIn("CURRENT SENSOR EVIDENCE", context_section)
        self.assertNotIn("UNRELATED HISTORY", context_section)


if __name__ == "__main__":
    unittest.main()
