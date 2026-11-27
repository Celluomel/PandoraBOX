import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from cognition.emotional_state import EmotionalStateManager
from cognition.self_model_moment import SelfModelMoment, SelfModelMomentManager
from cognition.self_revision_engine import SelfRevisionEngine


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

    def test_self_model_revises_affect_configuration_when_mix_changes_at_same_phi(self):
        with tempfile.TemporaryDirectory() as directory:
            affect = EmotionalStateManager(str(Path(directory) / "affect.json"))
            snapshot = affect.get_self_model_snapshot(event_limit=0)
            snapshot["channels"]["curiosity"].update(
                value=0.72, baseline=0.30, deviation=0.42,
            )
            affect.get_self_model_snapshot = lambda **_kw: snapshot
            organism = SimpleNamespace(
                ai_system=SimpleNamespace(emotional_state=affect),
                _get_emotion_values=affect.get_current_values,
            )
            moments = SelfModelMomentManager(str(Path(directory) / "self.json"))
            moments.current = SelfModelMoment(
                phi=0.6, qualia_tone="prior affect configuration",
                emotional_profile={"channels": {
                    "curiosity": {"value": 0.30, "baseline": 0.30, "deviation": 0.0},
                }},
            )

            updated = moments.update(organism, SimpleNamespace(
                phi_proxy=0.6, qualia_tone="new affect configuration",
                coherence_trend="stable",
            ))

        self.assertEqual(updated.phi, 0.6)
        self.assertEqual(updated.qualia_tone, "new affect configuration")
        self.assertIn("curiosity", updated.emotional_profile["channels"])

    def test_self_revision_accumulates_measured_mixtures_not_words(self):
        with tempfile.TemporaryDirectory() as directory:
            affect = EmotionalStateManager(str(Path(directory) / "affect.json"))
            affect.update_from_cognitive_event(
                "contradiction_detected", intensity=1.0, source="belief_revision",
            )
            affect.get_self_model_snapshot = lambda **_kw: {
                "channels": {
                    "anxiety": {"value": 0.60, "baseline": 0.30, "deviation": 0.30},
                    "curiosity": {"value": 0.55, "baseline": 0.30, "deviation": 0.25},
                },
                "valence": -0.1, "arousal": 0.6,
                "mood_valence": 0.0, "mood_arousal": 0.3,
            }
            current = SimpleNamespace(qualia_tone="old", phi=0.6)
            organism = SimpleNamespace(
                ai_system=SimpleNamespace(emotional_state=affect),
                self_moment=SimpleNamespace(current=current),
            )
            revision = SelfRevisionEngine()

            first = revision._revise_qualia(organism, "curiosity", 0.2)
            second = revision._revise_qualia(organism, "peace", 0.2)
            third = revision._revise_qualia(organism, "unrelated phrase", 0.2)

        self.assertIsNone(first)
        self.assertIsNone(second)
        self.assertIsNotNone(third)
        self.assertIn("affect configuration:", current.qualia_tone)
        self.assertIn("repeated across 3 turns", third.trigger)


if __name__ == "__main__":
    unittest.main()
