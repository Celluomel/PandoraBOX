"""Tests for the evidence-backed self model built by IdentityGrounding."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys
from types import ModuleType

# Load the lightweight module without executing cognition/__init__.py, which
# imports optional numerical runtime dependencies not needed by these tests.
ROOT = Path(__file__).resolve().parents[1]
package = ModuleType("cognition")
package.__path__ = [str(ROOT / "cognition")]
sys.modules.setdefault("cognition", package)
from cognition.identity_grounding import IdentityGrounding
from cognition.prompt_context_budget import PromptContextBudget


def _evidence(**overrides):
    data = {
        "efficacy": {},
        "focus": {},
        "capabilities": {},
        "aspirations": [],
        "closure": {},
        "planning": {},
        "corrections": {},
        "restructuring": {},
        "calibration": {},
        "narrative_chapters": [],
        "total_interactions": 0,
    }
    data.update(overrides)
    return data


class EvidentialSelfModelTests(unittest.TestCase):
    def test_only_repeated_outcomes_create_verified_capability_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            grounding = IdentityGrounding(persona_dir=folder)
            snapshot = grounding.ground(_evidence(
                efficacy={
                    "goal-a|memory_recall": {"eff": 0.82, "n": 4},
                    "goal-b|web_search": {"eff": 0.90, "n": 1},
                },
            ))

            claims = {item["id"]: item for item in snapshot["claim_ledger"]}
            self.assertEqual(claims["capability:goal-a|memory_recall"]["status"], "verified")
            self.assertEqual(claims["capability:goal-b|web_search"]["status"], "unverified")
            self.assertEqual(snapshot["version"], 2)

    def test_focus_without_observations_is_not_claimed_as_reliable(self):
        with tempfile.TemporaryDirectory() as folder:
            grounding = IdentityGrounding(persona_dir=folder)
            snapshot = grounding.ground(_evidence(
                focus={
                    "checks_total": 0,
                    "focus_stability": 1.0,
                    "override_rate": 0.0,
                },
            ))

            self.assertFalse(snapshot["focus"]["holds_focus"])
            self.assertEqual(snapshot["focus"]["status"], "unmeasured")
            self.assertFalse(any(
                item["id"] == "ability:maintain_focus"
                for item in snapshot["claim_ledger"]
            ))
            self.assertIn("not yet have enough observations", snapshot["statement"])

    def test_agency_keeps_active_plan_separate_from_aspiration(self):
        with tempfile.TemporaryDirectory() as folder:
            grounding = IdentityGrounding(persona_dir=folder)
            snapshot = grounding.ground(_evidence(
                planning={
                    "active_goals": [{"id": "g1", "topic": "test memory"}],
                    "dominant_plan": {
                        "objective": "test memory",
                        "steps_completed": 2,
                        "steps_total": 4,
                        "reasoning_confidence": 0.72,
                    },
                },
                aspirations=[{
                    "id": "a1",
                    "domain": "reasoning",
                    "statement": "become more causally precise",
                }],
            ))

            self.assertEqual(snapshot["agency"]["status"], "active")
            self.assertEqual(snapshot["agency"]["dominant_plan"]["objective"], "test memory")
            self.assertEqual(snapshot["agency"]["aspirations"][0]["state"], "desired_not_achieved")
            self.assertFalse(any(
                item["statement"] == "become more causally precise"
                for item in snapshot["claim_ledger"]
            ))

    def test_correction_event_survives_refresh_and_stays_developing(self):
        with tempfile.TemporaryDirectory() as folder:
            grounding = IdentityGrounding(persona_dir=folder)
            grounding.record_interaction_evidence(
                user_input="that answer ignored the main constraint",
                response="corrected response",
                validator_score=0.72,
                correction={
                    "id": "corr_1",
                    "rule": "Resolve the main constraint first.",
                    "confidence": 0.58,
                },
            )
            snapshot = grounding.ground(_evidence(
                corrections={
                    "rules": 1,
                    "top_rules": [{
                        "id": "corr_1",
                        "rule": "Resolve the main constraint first.",
                        "confidence": 0.58,
                        "evidence": 1,
                        "successful_turns": 0,
                    }],
                },
            ))

            self.assertEqual(snapshot["self_correction"]["status"], "developing")
            self.assertTrue(any(
                event["kind"] == "self_correction"
                for event in snapshot["autobiographical_timeline"]
            ))
            claim = next(
                item for item in snapshot["claim_ledger"]
                if item["id"] == "correction:corr_1"
            )
            self.assertEqual(claim["status"], "developing")

    def test_calibration_is_explicitly_unmeasured_until_resolved(self):
        with tempfile.TemporaryDirectory() as folder:
            grounding = IdentityGrounding(persona_dir=folder)
            empty = grounding.ground(_evidence(
                calibration={"modules": {}, "pending_count": 2},
            ))
            self.assertEqual(empty["metacognition"]["status"], "unmeasured")

            calibrated = grounding.ground(_evidence(
                calibration={
                    "modules": {"pcm": {"ece": 0.08, "total_resolved": 12}},
                    "pending_count": 1,
                },
            ))
            self.assertEqual(calibrated["metacognition"]["status"], "calibrated")
            self.assertEqual(calibrated["metacognition"]["resolved_predictions"], 12)

    def test_prompt_always_enforces_epistemic_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            grounding = IdentityGrounding(persona_dir=folder)
            fragment = grounding.identity_block()
            self.assertIn("Evidence-backed self", fragment)
            self.assertIn("Never present an unverified inner narrative as fact", fragment)
            self.assertIn("No capability currently has sufficient", fragment)

    def test_evidence_has_a_prompt_budget_independent_from_experiential_state(self):
        with tempfile.TemporaryDirectory() as folder:
            budget = PromptContextBudget(path=str(Path(folder) / "contributions.json"))
            self_state = "S" * 400
            evidence = "E" * 400
            budget.add("self_state", "phenomenal_moment", self_state)
            budget.add("self_evidence", "grounded_identity", evidence)

            assembled = budget.assemble()

            self.assertIn(self_state, assembled)
            self.assertIn(evidence, assembled)


if __name__ == "__main__":
    unittest.main()
