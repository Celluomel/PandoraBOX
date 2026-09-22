import unittest
from unittest.mock import patch

from utils.shared_embedder import APIEmbedder, interactive_priority_active, set_interactive_priority


class InteractiveEmbeddingPriorityTests(unittest.TestCase):
    def test_interactive_turn_does_not_fall_back_to_local_embedding(self):
        with patch("utils.shared_embedder._interactive_priority.is_set", return_value=True), patch(
            "utils.shared_embedder._get_fast_embedder"
        ) as fast_fallback:
            with self.assertRaisesRegex(RuntimeError, "deferred during interactive turn"):
                APIEmbedder("nomic", "http://localhost:1234/v1").encode(["background work"])
        fast_fallback.assert_not_called()

    def test_priority_state_can_be_set_and_cleared(self):
        set_interactive_priority(True)
        self.assertTrue(interactive_priority_active())
        set_interactive_priority(False)
        self.assertFalse(interactive_priority_active())


if __name__ == "__main__":
    unittest.main()
