import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from cognition.emotional_state import EmotionalStateManager
from cognition.self_model_moment import SelfModelMomentManager


class SelfModelAffectProfileTests(unittest.TestCase):
    def test_self_snapshot_keeps_channel_deviations_and_causal_events(self):
        with tempfile.TemporaryDirectory() as directory:
            affect = EmotionalStateManager(str(Path(directory) / "affect.json"))
            affect.update_from_cognitive_event(
                "contradiction_detected", intensity=0.9, source="belief_revision",
            )
            affect.update_from_cognitive_event(
                "tension_released", intensity=0.7, source="goal_resolution",
                context={"drive": "resolve_uncertainty"},
            )
            organism = SimpleNamespace(
                ai_system=SimpleNamespace(emotional_state=affect),
                _get_emotion_values=affect.get_current_values,
            )
            moments = SelfModelMomentManager(str(Path(directory) / "self.json"))
            moments.update(organism, SimpleNamespace(
                phi_proxy=0.6, qualia_tone="a present quality",
                coherence_trend="stable",
            ))

            profile = moments.current.emotional_profile
            fragment = moments.current.prompt_fragment()
            reloaded = SelfModelMomentManager(str(Path(directory) / "self.json"))

        self.assertGreaterEqual(len(profile["channels"]), 10)
        self.assertIn("anxiety", profile["channels"])
        self.assertIn("curiosity", profile["channels"])
        self.assertEqual(
            [event["event_type"] for event in profile["recent_causes"]],
            ["contradiction_detected", "tension_released"],
        )
        self.assertIn("affect profile=[", fragment)
        self.assertIn("moment valence=", fragment)
        self.assertIn("slow mood=", fragment)
        self.assertIn("recent affect causes=", fragment)
        self.assertEqual(reloaded.current.emotional_profile, profile)


if __name__ == "__main__":
    unittest.main()
