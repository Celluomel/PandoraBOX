import unittest
import sys
from pathlib import Path
from types import ModuleType

# Keep this pure-function test isolated from cognition/__init__ and its optional
# FAISS/LLM runtime imports.
ROOT = Path(__file__).resolve().parents[1]
package = ModuleType("cognition")
package.__path__ = [str(ROOT / "cognition")]
sys.modules.setdefault("cognition", package)

from cognition.emotional_text_appraisal import appraise_emotional_text


class EmotionalTextAppraisalTests(unittest.TestCase):
    def test_english_negation_flips_polarity_without_classifying_negator_as_emotion(self):
        self.assertEqual(appraise_emotional_text("not bad"), {"valence": "Positive", "arousal": "Medium"})
        self.assertEqual(appraise_emotional_text("not good"), {"valence": "Negative", "arousal": "Medium"})
        self.assertEqual(appraise_emotional_text("I am not upset"), {"valence": "Positive", "arousal": "Medium"})

    def test_french_affect_and_negation_are_recognized(self):
        self.assertEqual(appraise_emotional_text("Je suis très heureux"), {"valence": "Positive", "arousal": "Medium"})
        self.assertEqual(appraise_emotional_text("Je ne suis pas inquiet"), {"valence": "Positive", "arousal": "Medium"})
        self.assertEqual(appraise_emotional_text("Je suis déçu"), {"valence": "Negative", "arousal": "Medium"})

    def test_ordinary_requests_and_questions_are_not_negative_or_high_arousal(self):
        self.assertEqual(appraise_emotional_text("Please help me"), {"valence": "Neutral", "arousal": "Low"})
        self.assertEqual(appraise_emotional_text("Which module is used?"), {"valence": "Neutral", "arousal": "Medium"})
        self.assertEqual(appraise_emotional_text("Don't stop until fixed"), {"valence": "Neutral", "arousal": "Low"})

    def test_word_boundaries_prevent_substring_false_matches(self):
        self.assertEqual(appraise_emotional_text("The issue is in the module."), {"valence": "Negative", "arousal": "Medium"})
        self.assertEqual(appraise_emotional_text("A good solution."), {"valence": "Positive", "arousal": "Medium"})

    def test_high_arousal_requires_explicit_strong_word_or_repeated_exclamation(self):
        self.assertEqual(appraise_emotional_text("This is urgent!"), {"valence": "Neutral", "arousal": "High"})
        self.assertEqual(appraise_emotional_text("Thanks!"), {"valence": "Positive", "arousal": "Medium"})


if __name__ == "__main__":
    unittest.main()
