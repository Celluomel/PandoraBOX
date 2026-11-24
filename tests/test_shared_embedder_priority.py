import unittest
from unittest.mock import patch

import numpy as np

from managers.llm_manager import LMStudioProvider
from utils.shared_embedder import (
    APIEmbedder,
    DEFAULT_BASE_URL,
    interactive_priority_active,
    set_interactive_priority,
)


class InteractiveEmbeddingPriorityTests(unittest.TestCase):
    def test_local_lm_studio_defaults_to_reachable_ipv4_loopback(self):
        self.assertEqual(DEFAULT_BASE_URL, "http://127.0.0.1:1234/v1")
        self.assertEqual(
            LMStudioProvider().base_url,
            "http://127.0.0.1:1234/v1",
        )

    def test_interactive_turn_does_not_fall_back_to_local_embedding(self):
        with patch("utils.shared_embedder._interactive_priority.is_set", return_value=True), patch(
            "utils.shared_embedder._get_fast_embedder"
        ) as fast_fallback:
            with self.assertRaisesRegex(RuntimeError, "deferred during interactive turn"):
                APIEmbedder("nomic", "http://localhost:1234/v1").encode(["background work"])
        fast_fallback.assert_not_called()

    def test_quality_response_model_mismatch_uses_explicit_fast_space(self):
        class Fast:
            model_name_or_path = "all-MiniLM-L6-v2"

            def encode(self, texts, **_kwargs):
                return np.ones((len(texts), 384), dtype="float32")

        api = APIEmbedder("nomic-model", "http://localhost:1234/v1")
        with patch.object(api, "_post", return_value={
            "model": "different-model",
            "data": [{"index": 0, "embedding": [1.0, 0.0]}],
        }), patch("utils.shared_embedder._get_fast_embedder", return_value=Fast()):
            vectors, space_id = api.encode_with_metadata(["probe"])

        self.assertEqual(vectors.shape, (1, 384))
        self.assertEqual(space_id, "sentence-transformers:all-MiniLM-L6-v2")

    def test_quality_response_rejects_nonfinite_vectors(self):
        class Fast:
            model_name_or_path = "all-MiniLM-L6-v2"

            def encode(self, texts, **_kwargs):
                return np.ones((len(texts), 384), dtype="float32")

        api = APIEmbedder("nomic-model", "http://localhost:1234/v1")
        with patch.object(api, "_post", return_value={
            "model": "nomic-model",
            "data": [{"index": 0, "embedding": [float("nan"), 0.0]}],
        }), patch("utils.shared_embedder._get_fast_embedder", return_value=Fast()):
            vectors, space_id = api.encode_with_metadata(["probe"])

        self.assertTrue(np.isfinite(vectors).all())
        self.assertEqual(space_id, "sentence-transformers:all-MiniLM-L6-v2")

    def test_quality_response_rejects_missing_vector_indices(self):
        class Fast:
            model_name_or_path = "all-MiniLM-L6-v2"

            def encode(self, texts, **_kwargs):
                return np.ones((len(texts), 384), dtype="float32")

        api = APIEmbedder("nomic-model", "http://localhost:1234/v1")
        with patch.object(api, "_post", return_value={
            "model": "nomic-model",
            "data": [],
        }), patch("utils.shared_embedder._get_fast_embedder", return_value=Fast()):
            vectors, space_id = api.encode_with_metadata(["probe"])

        self.assertEqual(vectors.shape, (1, 384))
        self.assertEqual(space_id, "sentence-transformers:all-MiniLM-L6-v2")

    def test_priority_state_can_be_set_and_cleared(self):
        set_interactive_priority(True)
        self.assertTrue(interactive_priority_active())
        set_interactive_priority(False)
        self.assertFalse(interactive_priority_active())


if __name__ == "__main__":
    unittest.main()
