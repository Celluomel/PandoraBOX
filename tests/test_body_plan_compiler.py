import unittest

from cognition.body_plan_compiler import compile_body_plan


class BodyPlanCompilerTests(unittest.TestCase):
    snapshot = {
        "snapshot_id": "snap-1",
        "objects": [
            {"id": "cup", "kind": "object"},
            {"id": "chair", "kind": "chair"},
        ],
        "capabilities": ["navigate", "grab", "release"],
    }

    def test_compiles_arbitrary_destination_without_phrase_dictionary(self):
        def llm(_prompt, _system, **_kwargs):
            return '{"objective":"place cup on chair","steps":[' \
                '{"step_id":"approach-cup","verb":"navigate","target":"cup"},' \
                '{"step_id":"grab-cup","verb":"grab","target":"cup"},' \
                '{"step_id":"approach-chair","verb":"navigate","target":"chair"},' \
                '{"step_id":"place-cup","verb":"release","target":"chair",' \
                '"postconditions":[{"type":"on_surface","target":"cup","surface":"chair"}]}]}'

        result = compile_body_plan("Pose la tasse sur la chaise", self.snapshot, llm)
        self.assertTrue(result["accepted"])
        self.assertTrue(result["requires_confirmation"])
        self.assertEqual(result["steps"][-1]["target"], "chair")
        self.assertEqual(result["steps"][-1]["postconditions"][0]["surface"], "chair")

    def test_rejects_unknown_protocol_verb(self):
        def llm(_prompt, _system, **_kwargs):
            return '{"objective":"do it","steps":[{"verb":"fly","target":"cup"}]}'

        result = compile_body_plan("Fais quelque chose", self.snapshot, llm)
        self.assertFalse(result["accepted"])
        self.assertIn("unsupported Body verb", result["error"])


if __name__ == "__main__":
    unittest.main()
