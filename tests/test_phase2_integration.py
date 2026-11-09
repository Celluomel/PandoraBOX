import unittest
from types import SimpleNamespace

from core.phase2_integration import Phase2Orchestrator
from cognition.narrative_synthesizer import NarrativeSynthesizer


class Phase2NarrativeInputTests(unittest.TestCase):
    def test_narrative_synthesis_normalizes_emotional_state_manager(self):
        received = {}

        class Narrative:
            def create_narrative_from_cycle(self, cycle_data):
                received.update(cycle_data)
                return "narrative"

        phase2 = Phase2Orchestrator.__new__(Phase2Orchestrator)
        phase2.components = {"narrative_synthesizer": Narrative()}
        phase2.components.update({
            "advanced_evaluator": None,
            "thought_goal_linker": None,
            "thread_identity_linker": None,
        })
        emotional_manager = SimpleNamespace(emotions={
            "curiosity": SimpleNamespace(value=0.82),
            "calm": 0.41,
            "invalid": float("nan"),
        })

        result = phase2.synthesize_narrative({"emotions": emotional_manager})

        self.assertEqual(result, "narrative")
        self.assertEqual(received["emotions"], {"curiosity": 0.82, "calm": 0.41})

    def test_narrative_synthesis_keeps_plain_numeric_emotion_maps(self):
        received = {}

        class Narrative:
            def create_narrative_from_cycle(self, cycle_data):
                received.update(cycle_data)
                return None

        phase2 = Phase2Orchestrator.__new__(Phase2Orchestrator)
        phase2.components = {"narrative_synthesizer": Narrative()}

        phase2.synthesize_narrative({"emotions": {"joy": 0.7}})

        self.assertEqual(received["emotions"], {"joy": 0.7})

    def test_live_narrative_synthesizer_accepts_emotional_manager_shape(self):
        phase2 = Phase2Orchestrator.__new__(Phase2Orchestrator)
        phase2.components = {
            "narrative_synthesizer": NarrativeSynthesizer("unused-test-path"),
        }
        phase2.components.update({
            "advanced_evaluator": None,
            "thought_goal_linker": None,
            "thread_identity_linker": None,
        })

        result = phase2.synthesize_narrative({
            "pressure": {"total": 0.5},
            "energy_level": 1.0,
            "emotions": SimpleNamespace(emotions={
                "curiosity": SimpleNamespace(value=0.82),
            }),
        })

        self.assertIsInstance(result, str)
        self.assertIn("curiosity", result)


if __name__ == "__main__":
    unittest.main()
