import tempfile
import unittest
from pathlib import Path

from cognition.self_correction_engine import SelfCorrectionEngine


class SelfCorrectionPromptTests(unittest.TestCase):
    def test_unrelated_rule_is_not_injected_as_a_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = SelfCorrectionEngine(str(Path(directory) / "rules.json"))
            engine._rules = [{
                "rule": "Do not claim physical movement without actuator evidence.",
                "context": "robot motors movement actuators",
                "confidence": 0.91,
                "evidence": 4,
                "uses": 3,
            }]

            self.assertEqual(engine.prompt_fragment("continue the cognitive audit"), "")

    def test_related_rules_are_ranked_by_overlap_and_remain_compact(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = SelfCorrectionEngine(str(Path(directory) / "rules.json"))
            engine._rules = [
                {
                    "rule": "Check output and downstream effects before calling a module effective.",
                    "context": "cognitive audit output downstream modules",
                    "confidence": 0.72,
                    "evidence": 3,
                    "uses": 2,
                },
                {
                    "rule": "Never claim a movement without actuator evidence.",
                    "context": "robot movement actuator",
                    "confidence": 0.95,
                    "evidence": 5,
                    "uses": 4,
                },
            ]

            fragment = engine.prompt_fragment("audit module output and downstream effects")

            self.assertIn("Check output and downstream effects", fragment)
            self.assertNotIn("Never claim a movement", fragment)


if __name__ == "__main__":
    unittest.main()
