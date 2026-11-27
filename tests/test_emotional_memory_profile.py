import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from cognition.emotional_memory import EmotionalMemorySystem
from cognition.emotional_state import EmotionalStateManager


class EmotionalMemoryProfileTests(unittest.TestCase):
    def test_interaction_trace_preserves_mixed_affect_and_turn_cause(self):
        with tempfile.TemporaryDirectory() as directory:
            affect = EmotionalStateManager(str(Path(directory) / "affect.json"))
            affect.update_from_cognitive_event(
                "contradiction_detected", intensity=1.0,
                source="belief_review", turn_id="affect-turn-7",
            )
            # Construct a strong mixed state: the signed projection can be
            # small while both channels remain meaningfully above baseline.
            affect.emotions["curiosity"].value = 1.0
            affect.emotions["anxiety"].value = 1.0
            organism = SimpleNamespace(
                ai_system=SimpleNamespace(emotional_state=affect),
            )
            memory = EmotionalMemorySystem(
                organism, str(Path(directory) / "emotional_memory.json"),
            )

            memory.record_from_interaction(
                "Describe the current self", "A long answer does not define arousal.",
                "fred", turn_id="affect-turn-7",
            )
            trace = memory._state.traces[-1]
            residue = memory.compute_residue()

        self.assertEqual(trace["turn_id"], "affect-turn-7")
        self.assertEqual(trace["evidence_source"], "emotional_state_snapshot")
        self.assertEqual(len(trace["affect_profile"]["channels"]), 11)
        self.assertEqual(trace["affect_profile"]["recent_causes"][-1]["turn_id"], "affect-turn-7")
        self.assertIn("curiosity", residue.channel_deviations)
        self.assertIn("anxiety", residue.channel_deviations)
        self.assertGreater(residue.channel_deviations["curiosity"], 0.0)
        self.assertGreater(residue.channel_deviations["anxiety"], 0.0)

    def test_residue_reapplies_channel_mix_instead_of_nonexistent_label(self):
        with tempfile.TemporaryDirectory() as directory:
            affect = EmotionalStateManager(str(Path(directory) / "affect.json"))
            organism = SimpleNamespace(ai_system=SimpleNamespace(emotional_state=affect))
            memory = EmotionalMemorySystem(
                organism, str(Path(directory) / "emotional_memory.json"),
            )
            profile = {
                "channels": {
                    "curiosity": {"value": 0.8, "baseline": 0.3, "deviation": 0.5},
                    "anxiety": {"value": 0.7, "baseline": 0.3, "deviation": 0.4},
                },
                "valence": -0.1,
                "arousal": 0.8,
                "recent_causes": [],
            }
            memory.record_if_significant(
                valence=-0.1, arousal=0.8, affect_profile=profile,
                evidence_source="emotional_state_snapshot",
            )
            before = affect.get_current_values()
            residue = memory.compute_residue()
            memory.apply_residue_to_emotional_state(residue)
            after = affect.get_current_values()

        self.assertGreater(after["curiosity"], before["curiosity"])
        self.assertGreater(after["anxiety"], before["anxiety"])
        self.assertNotIn("melancholy", after)


if __name__ == "__main__":
    unittest.main()
