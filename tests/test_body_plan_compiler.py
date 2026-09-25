import unittest

from cognition.body_plan_compiler import compile_body_plan


class BodyPlanCompilerTests(unittest.TestCase):
    snapshot = {
        "snapshot_id": "snap-1",
        "objects": [
            {"id": "cup", "kind": "object", "position": [2.0, 1.0]},
            {"id": "chair", "kind": "chair", "position": [4.0, 1.0]},
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

    def test_preserves_exploration_before_manipulation(self):
        def llm(_prompt, _system, **_kwargs):
            return '{"objective":"tour the room then place the cup on the table","steps":[' \
                '{"step_id":"tour","verb":"explore","target":"scene"},' \
                '{"step_id":"grab","verb":"grab","target":"cup"},' \
                '{"step_id":"place","verb":"release","target":"table",' \
                '"postconditions":[{"type":"on_surface","target":"cup","surface":"table"}]}]}'

        result = compile_body_plan("Fais le tour de la pièce puis pose la tasse sur la table", self.snapshot, llm)
        self.assertTrue(result["accepted"], result)
        self.assertEqual([step["verb"] for step in result["steps"]], ["explore", "grab", "release"])
        self.assertEqual(result["steps"][0]["target"], "scene")
        self.assertEqual(result["steps"][0]["arguments"]["targets"], ["chair"])

    def test_semantic_audit_restores_missing_exploration_step(self):
        calls = []

        def llm(_prompt, _system, **_kwargs):
            calls.append(True)
            if len(calls) == 1:
                return '{"objective":"tour then place","steps":[' \
                    '{"step_id":"1","verb":"navigate","target":"goal"},' \
                    '{"step_id":"2","verb":"grab","target":"cup"},' \
                    '{"step_id":"3","verb":"release","target":"chair"}]}'
            return '{"needs_revision":true,"steps":[' \
                '{"step_id":"tour","verb":"explore","target":"scene"},' \
                '{"step_id":"grab","verb":"grab","target":"cup"},' \
                '{"step_id":"place","verb":"release","target":"chair"}]}'

        result = compile_body_plan("Tourne dans la pièce puis prends la tasse et pose-la sur la chaise", self.snapshot, llm)
        self.assertTrue(result["accepted"], result)
        self.assertEqual(result["steps"][0]["verb"], "explore")
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
