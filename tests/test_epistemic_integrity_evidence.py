from __future__ import annotations

import threading
import unittest
from types import SimpleNamespace

from cognition.epistemic_integrity_engine import (
    EpistemicIntegrityEngine,
    EpistemicState,
)


class EpistemicIntegrityEvidenceTests(unittest.TestCase):
    def _engine(self):
        engine = object.__new__(EpistemicIntegrityEngine)
        engine._lock = threading.RLock()
        engine._state = EpistemicState()
        return engine

    def test_compatible_language_is_unverified_not_grounded(self):
        engine = self._engine()
        result = engine._check_grounding(
            "The system continues its development.",
            "evolution",
            {"phi": 0.5, "coherence_trend": "stable", "emotional_ground": "neutral"},
        )

        self.assertIsNone(result[0])
        self.assertEqual(result[2], [])
        self.assertIn("not positive evidence", result[1])

    def test_keyword_overlap_in_tension_is_not_positive_evidence(self):
        engine = self._engine()
        result = engine._check_grounding(
            "There is a tension between memory and goals.",
            "contradiction",
            {"known_tensions": "memory goals", "goal_urgencies": "", "beliefs": ""},
        )

        self.assertIsNone(result[0])
        self.assertEqual(result[2], [])

    def test_unverified_reflection_does_not_change_belief_confidence(self):
        engine = self._engine()
        belief = SimpleNamespace(confidence=0.55, affirmations=0, violations=0)
        self_concept = SimpleNamespace(_beliefs={"self-understanding": belief}, _save=lambda: None)
        engine._get_self_concept = lambda: self_concept

        delta = engine._apply_grounding_effect(["self-understanding"], None)

        self.assertEqual(delta, 0.0)
        self.assertEqual(belief.confidence, 0.55)
        self.assertEqual(belief.affirmations, 0)
        self.assertEqual(belief.violations, 0)

    def test_reflection_screen_never_counts_as_grounding_or_changes_confidence(self):
        engine = self._engine()
        belief = SimpleNamespace(confidence=0.55, affirmations=0, violations=0)
        self_concept = SimpleNamespace(_beliefs={"self-understanding": belief}, _save=lambda: None)
        engine._get_self_concept = lambda: self_concept
        engine._save = lambda: None
        engine._check_disagreement = lambda *_args: None
        engine._check_grounding = lambda *_args: (
            True, "no lexical contradiction found", ["self-understanding"]
        )
        engine._update_grounding_index = lambda *_args: self.fail(
            "heuristic screening must not update measurement indices"
        )

        record = engine.validate_reflection(
            "My self-understanding is stable.",
            "evolution",
            3,
            {"phi": 0.5},
        )

        self.assertEqual(record.screen_status, "compatible")
        self.assertIsNone(record.grounded)
        self.assertEqual(record.confidence_delta, 0.0)
        self.assertEqual(belief.confidence, 0.55)
        self.assertEqual(belief.affirmations, 0)
        self.assertEqual(engine._recent_grounding_rate(), None)

    def test_unverified_records_are_excluded_from_grounding_rate(self):
        engine = self._engine()
        engine._state.grounding_log = [
            {"grounded": None},
            {"grounded": False, "measurement_status": "measured", "measurement_source": "external_eval"},
            {"grounded": True, "measurement_status": "measured", "measurement_source": "external_eval"},
        ]

        self.assertEqual(engine._recent_grounding_rate(), 0.5)

        engine._state.grounding_log = [{"grounded": None}]
        self.assertIsNone(engine._recent_grounding_rate())

    def test_legacy_heuristic_booleans_are_not_counted_as_measurements(self):
        engine = self._engine()
        engine._state.grounding_log = [
            {"grounded": True, "reason": "old lexical match"},
            {"grounded": False, "reason": "old lexical mismatch"},
        ]

        self.assertIsNone(engine._recent_grounding_rate())

    def test_disagreement_compares_prior_reflection_text_not_validator_reason(self):
        engine = self._engine()
        engine._state.grounding_log = [{
            "reflection_mode": "evolution",
            "reflection_cycle": 5,
            "reflection_output": "Integration is increasing and coherence is growing.",
            "reason": "no contradiction detected",
            "grounded": None,
        }]

        result = engine._check_disagreement(
            "The trajectory is fragmenting and development is dispersing.",
            "evolution",
            6,
        )

        self.assertIsNotNone(result)
        self.assertIn("Integration is increasing", result.position_a)
        self.assertEqual(result.cycle_a, 5)


if __name__ == "__main__":
    unittest.main()
