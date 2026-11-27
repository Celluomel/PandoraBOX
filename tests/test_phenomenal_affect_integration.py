import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from cognition.emotional_state import EmotionalStateManager
from cognition.phenomenal_binder import ExperientialMoment, PhenomenalBinder
from cognition.affect_composition import affect_profile_change


class PhenomenalAffectIntegrationTests(unittest.TestCase):
    @staticmethod
    def _signals(channel, deviation):
        channels = {
            name: {"value": 0.30, "baseline": 0.30, "deviation": 0.0}
            for name in (
                "curiosity", "warmth", "anxiety", "satisfaction", "frustration",
                "enthusiasm", "surprise", "sadness", "relief", "disappointment",
                "anticipation",
            )
        }
        channels[channel] = {
            "value": 0.30 + deviation,
            "baseline": 0.30,
            "deviation": deviation,
        }
        return {
            "emotions": {name: item["value"] for name, item in channels.items()},
            "affect_profile": {"channels": channels},
            "energy": 1.0,
            "pressure_total": 0.0,
            "contradiction_count": 0,
        }

    def test_all_channels_are_interpreted_as_baseline_relative_affect(self):
        binder = PhenomenalBinder.__new__(PhenomenalBinder)
        surprise = binder._compute_valence_arousal(
            self._signals("surprise", 0.35)
        )
        sadness = binder._compute_valence_arousal(
            self._signals("sadness", 0.35)
        )
        relief = binder._compute_valence_arousal(
            self._signals("relief", 0.35)
        )

        self.assertGreater(surprise[1], sadness[1])
        self.assertLess(sadness[0], 0.0)
        self.assertGreater(relief[0], 0.0)

    def test_resting_baselines_do_not_create_a_permanent_emotional_tone(self):
        binder = PhenomenalBinder.__new__(PhenomenalBinder)
        valence, arousal = binder._compute_valence_arousal(
            self._signals("curiosity", 0.0)
        )
        self.assertAlmostEqual(valence, 0.0)
        self.assertAlmostEqual(arousal, 0.4)

    def test_same_valence_but_different_channel_mixtures_produce_distinct_self_texture(self):
        binder = PhenomenalBinder.__new__(PhenomenalBinder)
        curiosity_profile = {"channels": {
            "curiosity": {"value": 0.70, "baseline": 0.30, "deviation": 0.40},
            "anxiety": {"value": 0.30, "baseline": 0.30, "deviation": 0.0},
        }}
        mixed_profile = {"channels": {
            "curiosity": {"value": 0.30, "baseline": 0.30, "deviation": 0.0},
            "anxiety": {"value": 0.70, "baseline": 0.30, "deviation": 0.40},
        }}

        curiosity_texture = binder._derive_qualia_tone(0.0, 0.5, {
            "affect_profile": curiosity_profile,
        })
        mixed_texture = binder._derive_qualia_tone(0.0, 0.5, {
            "affect_profile": mixed_profile,
        })

        self.assertNotEqual(curiosity_texture, mixed_texture)
        self.assertIn("curiosity +0.40", curiosity_texture)
        self.assertIn("anxiety +0.40", mixed_texture)
        self.assertGreater(affect_profile_change(curiosity_profile, mixed_profile), 0.39)

    def test_event_provenance_and_affect_mix_reach_experiential_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            affect = EmotionalStateManager(str(Path(directory) / "affect.json"))
            affect.update_from_cognitive_event(
                "identity_threatened", intensity=0.9, source="self_model",
                turn_id="turn-affect-42",
            )
            organism = SimpleNamespace(
                ai_system=SimpleNamespace(emotional_state=affect),
                _get_emotion_values=affect.get_current_values,
            )
            binder = PhenomenalBinder.__new__(PhenomenalBinder)
            signals = binder._harvest_signals(organism)
            profile = signals["affect_profile"]
            moment = ExperientialMoment(
                timestamp=1.0, affect_profile=profile,
                valence=-0.2, arousal=0.6,
            )
            prompt = moment.phenomenal_prompt()

        self.assertEqual(len(profile["channels"]), 11)
        self.assertEqual(profile["recent_causes"][-1]["turn_id"], "turn-affect-42")
        self.assertIn("affect_mix=", prompt)
        self.assertIn("affect_causes=identity_threatened", prompt)
        self.assertIn("anxiety=", prompt)


if __name__ == "__main__":
    unittest.main()
