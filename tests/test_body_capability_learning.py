import tempfile
import unittest
import importlib.util
from types import SimpleNamespace
from pathlib import Path


class BodyCapabilityLearningTest(unittest.TestCase):
    def test_capability_progresses_from_observed_to_verified_evidence(self):
        module_path = Path(__file__).resolve().parent.parent / "cognition" / "body_capability_learning.py"
        spec = importlib.util.spec_from_file_location("body_capability_learning_under_test", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        BodyCapabilityLearner = module.BodyCapabilityLearner

        with tempfile.TemporaryDirectory() as temp_dir:
            learner = BodyCapabilityLearner(Path(temp_dir) / "capabilities.json")
            first = learner.observe(SimpleNamespace(
                source="sim_robot", kind="scene", subject="body",
                provenance={},
                value={"capabilities": {"navigate": True}},
            ))
            self.assertEqual(first["items"][0]["state"], "observed")
            for index in range(3):
                result = learner.observe(SimpleNamespace(
                    source="sim_robot", kind="actuation_feedback", subject="navigate",
                    provenance={},
                    value={"action": "navigate", "outcome": {"kind": "success", "trial": index}},
                ))
            self.assertEqual(result["items"][0]["state"], "verified")
            self.assertTrue((Path(temp_dir) / "capabilities.json").exists())
