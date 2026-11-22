import tempfile
import unittest
import importlib.util
from types import SimpleNamespace
from pathlib import Path


class BodyCapabilityLearningTest(unittest.TestCase):
    def test_simulated_scene_capabilities_are_not_learned(self):
        module_path = Path(__file__).resolve().parent.parent / "cognition" / "body_capability_learning.py"
        spec = importlib.util.spec_from_file_location("body_capability_learning_under_test", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        BodyCapabilityLearner = module.BodyCapabilityLearner

        with tempfile.TemporaryDirectory() as temp_dir:
            learner = BodyCapabilityLearner(Path(temp_dir) / "capabilities.json")
            result = learner.observe(SimpleNamespace(
                source="sim_robot", kind="scene", subject="body",
                provenance={},
                value={"capabilities": {"locomotion": True}, "affordances": {"goal": True}},
            ))
            self.assertIsNone(result)
            self.assertEqual(learner.snapshot()["capabilities"], {})

    def test_only_explicit_inventory_and_verified_physical_actions_build_skill_evidence(self):
        module_path = Path(__file__).resolve().parent.parent / "cognition" / "body_capability_learning.py"
        spec = importlib.util.spec_from_file_location("body_capability_learning_under_test", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temp_dir:
            learner = module.BodyCapabilityLearner(Path(temp_dir) / "capabilities.json")
            declared = learner.observe(SimpleNamespace(
                source="remote:body:hardware_inventory", kind="robot_capability_inventory",
                subject="robot.capability_inventory", provenance={"simulated": False},
                value={"capabilities": {"locomotion": {"installed": False, "available": False}}},
            ))
            self.assertEqual(declared["items"][0]["state"], "observed")
            self.assertEqual(
                learner.snapshot()["capabilities"]["locomotion"]["evidence_scope"],
                "robot_capability_inventory_declaration",
            )

            unverified = learner.observe(SimpleNamespace(
                source="body_action", kind="actuation_feedback", subject="robot.walk",
                provenance={"command_status": "acknowledged", "verification_status": "unknown",
                            "outcome": {"kind": "success"}},
                value="acknowledged",
            ))
            self.assertIsNone(unverified)

            for index in range(3):
                result = learner.observe(SimpleNamespace(
                    source="body_action", kind="actuation_feedback", subject="robot.walk",
                    provenance={"command_status": "executed", "verification_status": "verified_observation",
                                "outcome": {"kind": "success", "trial": index, "simulated": False}},
                    value="executed",
                ))
            self.assertEqual(result["items"][0]["state"], "verified")
            skills = learner.snapshot()["skills"]
            self.assertEqual(skills["body.robot.walk"]["state"], "verified")
            self.assertGreaterEqual(skills["body.robot.walk"]["generalization"], 0.75)
            self.assertTrue((Path(temp_dir) / "capabilities.json").exists())
