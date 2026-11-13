import json
import tempfile
import unittest
from pathlib import Path

from cognition.profile_flow import update_behavioral_user_profile
from cognition.world_model import WorldModel


class WorldModelProfilePersistenceTests(unittest.TestCase):
    def test_behavioral_topic_context_does_not_claim_user_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            model = WorldModel(None, path=str(Path(directory) / "world.json"))
            profile = model.update_from_interaction(
                user_id="fred",
                user_text="Can you explain photosynthesis?",
                response="Photosynthesis converts light into chemical energy.",
                emotion="neutral",
            )

            fragment = profile.prompt_fragment()

        self.assertIn("Topics discussed (conversation co-occurrence only", fragment)
        self.assertIn("not evidence of the user's preferences, intentions, or expertise", fragment)
        self.assertIn("photosynthesis", fragment)

    def test_world_model_estimates_are_never_labeled_as_explicit_profile_facts(self):
        with tempfile.TemporaryDirectory() as directory:
            model = WorldModel(None, path=str(Path(directory) / "world.json"))
            profile = model.update_from_interaction(
                user_id="fred",
                user_text="Can you explain photosynthesis?",
                response="Photosynthesis converts light into chemical energy.",
                emotion="neutral",
            )
            profile.preferred_depth = "deep"
            profile.formality = "casual"
            fragment = profile.prompt_fragment()

        self.assertIn("INFERRED BEHAVIORAL INTERACTION MODEL", fragment)
        self.assertIn("not explicit user statements or named-profile facts", fragment)
        self.assertIn("Possible response-style estimates (inferred", fragment)
        self.assertNotIn("Style: deep, casual", fragment)

    def test_human_profile_receipt_follows_verified_atomic_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "world.json"
            model = WorldModel(None, path=str(path))

            receipt = update_behavioral_user_profile(
                model,
                user_id="fred",
                user_text="I prefer concise technical answers.",
                response="Understood.",
                emotion="neutral",
                human_interaction=True,
            )

            self.assertEqual(receipt["status"], "updated")
            self.assertTrue(receipt["persisted"])
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["user_profiles"]["fred"]["interaction_count"], 1)

    def test_failed_profile_write_is_not_reported_as_updated(self):
        with tempfile.TemporaryDirectory() as directory:
            blocked_path = Path(directory) / "world.json"
            blocked_path.mkdir()
            model = WorldModel(None, path=str(Path(directory) / "working.json"))
            model._path = blocked_path

            receipt = update_behavioral_user_profile(
                model,
                user_id="fred",
                user_text="I prefer concise technical answers.",
                response="Understood.",
                emotion="neutral",
                human_interaction=True,
            )

            self.assertEqual(receipt["status"], "persistence_failed")
            self.assertFalse(receipt["persisted"])
            self.assertTrue(receipt["changed"])
            self.assertFalse((Path(directory) / "world.json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
