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
    def test_generic_skill_proposals_are_grounded_and_unverified(self):
        snapshot_value = BodySnapshot(
            source="sim_robot", frame="world",
            pose={"x": 0.0, "y": 0.0, "yaw": 0.0},
            objects=[
                {"id": "cup", "label": "cup", "kind": "target", "position": [1, 0, 0]},
                {"id": "table", "label": "table", "kind": "table", "position": [2, 0, 0]},
                {"id": "pillar", "label": "pillar", "kind": "obstacle", "position": [1, 1, 0]},
            ],
            capabilities=["navigate", "grab", "release"],
            reliability=1.0,
            semantic_scene={"entities": [{"id": "cup", "affordances": ["grab"]}]},
        )
        proposals = BodySkillLibrary.proposals(snapshot_value, BodyState(capabilities={"gripper": 1.0}))
        by_id = {(item["skill_id"], item.get("target")): item for item in proposals}
        self.assertIn(("body.approach", "cup"), by_id)
        self.assertIn(("body.grasp", "cup"), by_id)
        self.assertIn(("body.place", "table"), by_id)
        self.assertNotIn(("body.approach", "pillar"), by_id)
        self.assertTrue(all(item["verified"] is False for item in proposals))

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
