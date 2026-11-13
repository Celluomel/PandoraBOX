"""Regression tests for human-paced persona age progression."""

from datetime import datetime, timedelta
import unittest
from types import SimpleNamespace

from cognition.ai_system import EnhancedAISystem, LifeEventDreamSystem, SystemConfig
from cognition.ai_identity import AIIdentity


class AgeProgressionTests(unittest.TestCase):
    def test_default_rate_is_one_age_year_per_calendar_year(self):
        self.assertAlmostEqual(SystemConfig().age_units_per_day, 1.0 / 365.2425)

    def test_persona_age_and_stage_follow_calendar_age(self):
        now = datetime.now()
        persona = object.__new__(EnhancedAISystem)
        persona.config = SystemConfig()
        persona._birth_date = now - timedelta(days=18 * 365.2425)

        self.assertAlmostEqual(persona.current_age, 18.0, delta=0.0001)
        self.assertEqual(persona.life_stage, "young_adult")

    def test_identity_dream_requires_measured_coherence_not_proxy(self):
        dream_system = object.__new__(LifeEventDreamSystem)
        current = AIIdentity(identity_coherence=0.38, identity_coherence_status="estimated_proxy")
        dream_system.ai_system = SimpleNamespace(
            identity_system=SimpleNamespace(get_identity=lambda: current)
        )
        self.assertFalse(dream_system._needs_identity_dev())

        current.identity_coherence_status = "measured"
        self.assertTrue(dream_system._needs_identity_dev())


if __name__ == "__main__":
    unittest.main()
