import unittest

from cognition.decision_pressure import DecisionPressureCalculator
from cognition.emotional_state import (
    EMOTION_DEFAULT_BASELINES,
    EmotionalStateManager,
)


class DecisionPressureAffectContractTests(unittest.TestCase):
    def test_resting_baselines_are_neutral_and_affect_deviations_change_valence(self):
        baseline_valence, _ = EmotionalStateManager.calculate_valence_arousal(
            EMOTION_DEFAULT_BASELINES
        )
        self.assertEqual(baseline_valence, 0.0)

        positive_shift = dict(EMOTION_DEFAULT_BASELINES)
        positive_shift["warmth"] += 0.2
        positive_valence, _ = EmotionalStateManager.calculate_valence_arousal(
            positive_shift
        )
        self.assertGreater(positive_valence, 0.0)

        negative_shift = dict(EMOTION_DEFAULT_BASELINES)
        negative_shift["anxiety"] += 0.2
        negative_valence, _ = EmotionalStateManager.calculate_valence_arousal(
            negative_shift
        )
        self.assertLess(negative_valence, 0.0)

    def test_pressure_uses_canonical_valence_and_arousal_but_keeps_pressure_separate(self):
        values = {
            "satisfaction": 0.72,
            "warmth": 0.68,
            "enthusiasm": 0.55,
            "relief": 0.20,
            "frustration": 0.24,
            "anxiety": 0.18,
            "sadness": 0.08,
            "disappointment": 0.10,
            "curiosity": 0.81,
            "surprise": 0.22,
            "anticipation": 0.31,
        }
        expected_valence, expected_arousal = (
            EmotionalStateManager.calculate_valence_arousal(values)
        )
        calculator = DecisionPressureCalculator(".")
        signals = calculator._compute_emotional_signals({
            "emotions": {
                name: {"value": value}
                for name, value in values.items()
            }
        })

        self.assertEqual(signals["emotional_valence"], expected_valence)
        self.assertEqual(signals["emotional_arousal"], expected_arousal)
        self.assertGreaterEqual(signals["emotional_pressure"], 0.0)
        self.assertLessEqual(signals["emotional_pressure"], 1.0)
        self.assertNotEqual(signals["emotional_pressure"], signals["emotional_valence"])
        self.assertIn("emotional_pressure", calculator.weights)
        self.assertNotIn("emotional_valence", calculator.weights)

    def test_missing_emotional_snapshot_is_explicitly_neutral(self):
        signals = DecisionPressureCalculator(".")._compute_emotional_signals({})
        self.assertEqual(signals, {
            "emotional_valence": 0.0,
            "emotional_arousal": 0.0,
            "emotional_pressure": 0.0,
        })


if __name__ == "__main__":
    unittest.main()
