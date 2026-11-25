import json
import tempfile
import unittest
from pathlib import Path

from cognition.profile_flow import update_behavioral_user_profile
from cognition.world_model import WorldModel


class WorldModelProfilePersistenceTests(unittest.TestCase):
    def test_assistant_only_topics_do_not_become_user_profile_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            model = WorldModel(None, path=str(Path(directory) / "world.json"))
            profile = model.update_from_interaction(
                user_id="fred",
                user_text="Can you help with my robot?",
                response="Quasars and nebulae are fascinating astronomy topics.",
                emotion="neutral",
            )

        self.assertIn("robot", profile.topic_entries)
        self.assertNotIn("quasars", profile.topic_entries)
        self.assertNotIn("nebulae", profile.topic_entries)
        self.assertNotIn("quasars", model._global_topic_df)
        self.assertNotIn("nebulae", model._global_topic_df)

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

        self.assertIn("Topics only (not preferences)", fragment)
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

        self.assertIn("Inferred interaction model", fragment)
        self.assertIn("not explicit user-stated facts", fragment)
        self.assertIn("Possible reply style (inferred", fragment)
        self.assertNotIn("Style: deep, casual", fragment)
        self.assertLessEqual(len(fragment), 200)

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

    def test_profile_receipt_reports_actual_topic_and_interaction_updates(self):
        with tempfile.TemporaryDirectory() as directory:
            model = WorldModel(None, path=str(Path(directory) / "world.json"))

            receipt = update_behavioral_user_profile(
                model,
                user_id="fred",
                user_text="Can you help with my robot?",
                response="I can help.",
                emotion="neutral",
                human_interaction=True,
            )

        self.assertEqual(receipt["status"], "updated")
        self.assertTrue(receipt["persisted"])
        self.assertGreater(receipt["extracted_count"], 0)
        self.assertIn("topic_profile", receipt["categories_updated"])
        self.assertIn("interaction_dynamics", receipt["categories_updated"])
        self.assertNotIn("robot", str(receipt))

    def test_non_topic_turn_updates_interaction_dynamics_only(self):
        with tempfile.TemporaryDirectory() as directory:
            model = WorldModel(None, path=str(Path(directory) / "world.json"))

            receipt = update_behavioral_user_profile(
                model,
                user_id="fred",
                user_text="A long closed-world audit question about current plan telemetry.",
                response="The current snapshot is 2/4 and does not verify goal attainment.",
                emotion="neutral",
                human_interaction=True,
                learn_semantic_profile=False,
            )
            profile = model.user_profiles["fred"]

        self.assertEqual(receipt["learning_scope"], "interaction_dynamics_only")
        self.assertEqual(receipt["extracted_count"], 0)
        self.assertEqual(receipt["categories_updated"], ["interaction_dynamics"])
        self.assertEqual(profile.interaction_count, 1)
        self.assertEqual(profile.topic_entries, {})
        self.assertEqual(profile.expertise, {})
        self.assertEqual(profile.preferred_depth, "medium")
        self.assertGreater(profile.relational.avg_message_length, 0)

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
            self.assertEqual(receipt["categories_updated"], [])
            self.assertFalse((Path(directory) / "world.json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
