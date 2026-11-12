import tempfile
import unittest
from pathlib import Path

from cognition.arbitration import ArbitrationDecision
from cognition.phenomenal_binder import ExperientialMoment
from cognition.prompt_context_budget import PromptContextBudget, TOTAL_TOKEN_CAP
from cognition.self_model_moment import SelfModelMoment


class PromptContextInfluenceTests(unittest.TestCase):
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
            budget.add("factual_telemetry", "long_horizon_plan", "p" * 1280)
            budget.add("self_evidence", "grounded_identity", "e" * 480)
            budget.add("self_state", "self_model_moment", "s" * 720)
            budget.add("self_correction", "self_correction", "c" * 480)
            budget.add("identity", "narrative_identity", "n" * 800)

            budget.assemble()
            selected = {entry.source for entry in budget._entries if entry.selected}

        self.assertIn("long_horizon_plan", selected)
        self.assertIn("self_correction", selected)
        self.assertNotIn("narrative_identity", selected)


if __name__ == "__main__":
    unittest.main()
