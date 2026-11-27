import tempfile
import unittest
from pathlib import Path

from cognition.arbitration import ArbitrationDecision
from cognition.phenomenal_binder import ExperientialMoment
from cognition.prompt_context_budget import (
    PromptContextBudget,
    TOTAL_TOKEN_CAP,
    fit_system_prompt_to_context,
)
from cognition.self_model_moment import SelfModelMoment


class PromptContextInfluenceTests(unittest.TestCase):
    def test_final_prompt_budget_preserves_core_and_route_tail(self):
        core = "CORE_IDENTITY\n" + ("middle-context " * 5000)
        route = "ARCHITECTURE_CONTRACT: preserve workspace source distinctions."
        fitted, receipt = fit_system_prompt_to_context(
            core,
            "What does the Global Workspace do?",
            context_tokens=4096,
            output_tokens=2048,
            protected_tail=route,
        )

        self.assertTrue(receipt["protected_tail_preserved"])
        self.assertTrue(fitted.startswith("CORE_IDENTITY"))
        self.assertTrue(fitted.endswith(route))
        self.assertLessEqual(
            len(fitted) + len("What does the Global Workspace do?"),
            receipt["total_input_char_budget"],
        )
        self.assertEqual(receipt["status"], "compacted")

    def test_prompt_budget_leaves_short_prompt_unchanged(self):
        prompt = "A compact prompt with all its evidence."
        fitted, receipt = fit_system_prompt_to_context(
            prompt, "Say hello.", context_tokens=8192, output_tokens=1024,
        )
        self.assertEqual(fitted, prompt)
        self.assertEqual(receipt["status"], "within_budget")

    def test_admission_record_keeps_the_cognitive_turn_id(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contributions.json"
            budget = PromptContextBudget(str(path), turn_id="turn-audit-123")
            budget.add("self_state", "self_model_moment", "[self model]")
            budget.assemble()
            budget.save()

            import json
            record = json.loads(path.read_text(encoding="utf-8"))[0]

        self.assertEqual(record["turn_id"], "turn-audit-123")

    def test_selection_receipt_reports_the_actual_budget_decision_without_text(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = PromptContextBudget(str(Path(directory) / "contributions.json"))
            budget.add("user_model", "behavioral_user_model", "u" * 200)
            budget.add("preferences", "communication", "c" * 400)
            budget.assemble()

            selected = budget.selection_receipt("user_model", "behavioral_user_model")
            omitted = budget.selection_receipt("preferences", "communication")

        self.assertEqual(selected, {
            "registered": True, "selected": True, "reason": "budget_ok", "tokens": 50,
        })
        self.assertEqual(omitted, {
            "registered": True, "selected": False, "reason": "category_full", "tokens": 0,
        })
        self.assertNotIn("text", selected)

    def test_state_fragments_are_compact_and_keep_distinct_signal_types(self):
        self_state = SelfModelMoment(
            phi=0.75,
            coherence_trend="stable",
            qualia_tone="a warm, open quality — reaching toward the other",
            emotional_ground="holding curiosity (100%)",
            capability_stance=(
                "[Self-awareness] Currently rested (load 8%), feeling confident. "
                "Strongest: emotional_support"
            ),
            narrative_thread="A long autobiographical narrative that belongs to identity context.",
            top_values="honesty, non maleficence",
        ).prompt_fragment()
        experiential = ExperientialMoment(
            timestamp=1.0,
            phi_proxy=0.72,
            valence=0.64,
            arousal=0.67,
            foreground="continuing to hold the user's audit question",
            penumbra="an unresolved question about output evidence",
            coherence_trend="integrating",
        ).phenomenal_prompt()

        self.assertIn("φ=0.75", self_state)
        self.assertIn("capability=", self_state)
        self.assertNotIn("Narrative thread:", self_state)
        self.assertIn("valence=+0.64", experiential)
        self.assertIn("arousal=0.67", experiential)
        self.assertNotIn("feels unusually unified", experiential)
        self.assertLess(len(self_state), 320)
        self.assertLess(len(experiential), 420)

    def test_core_decision_and_state_sections_survive_prompt_budget(self):
        decision = ArbitrationDecision(
            dominant_drive="help_user",
            secondary_drives=["connect"],
            reasoning_style="empathetic",
            temperature=0.72,
            depth_directive=(
                "Respond with genuine warmth and attentiveness to the person. "
                "Focus on connection and being truly helpful."
            ),
        )
        arbitration = decision.prompt_injection(
            ecology_fragment="Right now you are most motivated by helping and connecting.",
            tension_fragment="You feel driven to accomplish something meaningful.",
        )

        with tempfile.TemporaryDirectory() as directory:
            budget = PromptContextBudget(str(Path(directory) / "contributions.json"))
            budget.add("self_state", "self_model_moment", "[Self model compact state]")
            budget.add("self_state", "self_interruption", "[Self notice compact signal]")
            budget.add("self_state", "phenomenal_moment", "[Derived affect, focus, arousal, coherence]")
            budget.add("self_state", "temporal_frame", "[Current temporal context]")
            budget.add("cognitive_pressure", "energy", "[Energy: 78/100]")
            budget.add("cognitive_pressure", "arbitration", arbitration)
            budget.add("cognitive_pressure", "global_workspace", "[Workspace focus and alternatives]")
            budget.add("attention", "attention", "[Attention focus]")
            budget.add("attention", "curiosity", "[Current interests]")
            budget.add("attention", "attention_focus", "[Primary and secondary cognitive focus]")

            assembled = budget.assemble()
            selected = {e.source for e in budget._entries if e.selected}

        self.assertIn("arbitration", selected)
        self.assertIn("global_workspace", selected)
        self.assertIn("phenomenal_moment", selected)
        self.assertIn("self_interruption", selected)
        self.assertIn("attention_focus", selected)
        self.assertIn("Arbitration decision", assembled)
        self.assertLessEqual(budget._total_used, TOTAL_TOKEN_CAP)

    def test_relevant_self_correction_has_reserved_budget_before_identity_history(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = PromptContextBudget(str(Path(directory) / "contributions.json"))
            # The full current planner self-report is ~347 tokens; it must be
            # retained before lower-priority context consumes the global cap.
            budget.add("factual_telemetry", "long_horizon_plan", "p" * 1388)
            budget.add("self_evidence", "grounded_identity", "e" * 480)
            budget.add("self_state", "self_model_moment", "s" * 720)
            budget.add("self_correction", "self_correction", "c" * 480)
            budget.add("identity", "narrative_identity", "n" * 800)

            budget.assemble()
            selected = {entry.source for entry in budget._entries if entry.selected}

        self.assertIn("long_horizon_plan", selected)
        self.assertIn("self_correction", selected)
        self.assertNotIn("narrative_identity", selected)

    def test_measured_live_planner_report_above_previous_cap_is_admitted(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = PromptContextBudget(str(Path(directory) / "contributions.json"))
            budget.add("factual_telemetry", "long_horizon_plan", "p" * 1700)  # 425 estimated tokens
            budget.add("identity", "narrative_identity", "n" * 1800)

            assembled = budget.assemble()
            entries = {entry.source: entry for entry in budget._entries}

        self.assertTrue(entries["long_horizon_plan"].selected)
        self.assertEqual(entries["long_horizon_plan"].tokens, 425)
        self.assertIn("p" * 100, assembled)
        self.assertLessEqual(budget._total_used, TOTAL_TOKEN_CAP)

    def test_compact_behavioral_user_model_survives_full_core_prompt_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = PromptContextBudget(str(Path(directory) / "contributions.json"))
            budget.add("factual_telemetry", "long_horizon_plan", "p" * 1680)  # 420 tokens
            budget.add("self_evidence", "grounded_identity", "e" * 480)       # 120 tokens
            budget.add("self_correction", "self_correction", "c" * 480)     # 120 tokens
            budget.add("self_state", "self_model_state", "s" * 720)           # 180 tokens
            budget.add("user_model", "behavioral_user_model", "u" * 200)      # 50 tokens
            budget.add("attention", "attention", "a" * 320)                    # lower priority

            budget.assemble()
            entries = {entry.source: entry for entry in budget._entries}

        self.assertTrue(entries["behavioral_user_model"].selected)
        self.assertEqual(entries["behavioral_user_model"].reason, "budget_ok")
        self.assertFalse(entries["attention"].selected)
        self.assertLessEqual(budget._total_used, TOTAL_TOKEN_CAP)


if __name__ == "__main__":
    unittest.main()
