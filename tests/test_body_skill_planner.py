import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from body_runtime_host.worldmodel.contracts import BodySnapshot, PlanStep
from body_runtime_host.worldmodel.skills import BodySkillLibrary
from body_runtime_host.worldmodel.types import BodyState, Outcome


def snapshot(capabilities=None):
    return BodySnapshot(
        source="sim_robot", frame="world",
        pose={"x": 0.0, "y": 0.0, "yaw": 0.0},
        objects=[], capabilities=["navigate"] if capabilities is None else capabilities, reliability=1.0,
    )


class BodySkillPlannerTests(unittest.TestCase):
    def test_skill_requires_repeated_evidence_before_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = BodySkillLibrary(Path(tmp) / "skills.json")
            step = PlanStep("move", "navigate")
            body = BodyState()
            selected, reason = library.resolve(step, snapshot(), body)
            self.assertIsNone(selected)
            self.assertIn("no verified", reason)
            for _ in range(3):
                library.record_trial(step, Outcome(kind="success"), snapshot(), body)
            selected, reason = library.resolve(step, snapshot(), body)
            self.assertEqual(selected["skill_id"], "body.navigate")
            self.assertIn("verified skill selected", reason)

    def test_skill_is_refused_when_precondition_disappears(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = BodySkillLibrary(Path(tmp) / "skills.json")
            step = PlanStep("move", "navigate")
            body = BodyState()
            for _ in range(3):
                library.record_trial(step, Outcome(kind="success"), snapshot(), body)
            selected, reason = library.resolve(step, snapshot([]), BodyState(capabilities={"speed": 0}))
            self.assertIsNone(selected)
            self.assertIn("precondition", reason)

    def test_skill_is_suspended_after_failure_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = BodySkillLibrary(Path(tmp) / "skills.json")
            step = PlanStep("move", "navigate")
            body = BodyState()
            for _ in range(3):
                library.record_trial(step, Outcome(kind="success"), snapshot(), body)
            for _ in range(3):
                library.record_trial(step, Outcome(kind="failure"), snapshot(), body)
            selected, reason = library.resolve(step, snapshot(), body)
            self.assertIsNone(selected)
            self.assertIn("no verified", reason)
            self.assertEqual(library.snapshot()["skills"]["body.navigate"]["state"], "suspended")


if __name__ == "__main__":
    unittest.main()
