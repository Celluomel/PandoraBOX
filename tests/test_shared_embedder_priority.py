import unittest
import urllib.error
from unittest.mock import patch

import numpy as np

from managers.llm_manager import LMStudioProvider
from utils.shared_embedder import (
    APIEmbedder,
    DEFAULT_BASE_URL,
    QUALITY_INTERACTIVE_REQUEST_TIMEOUT,
    QualityEndpointBackoff,
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

    def test_explicit_foreground_quality_embedding_can_run_during_interactive_turn(self):
        api = APIEmbedder("nomic-model", "http://127.0.0.1:1234/v1")
        payload = {
            "model": "nomic-model",
            "data": [
                {"index": 0, "embedding": [1.0, 0.0]},
                {"index": 1, "embedding": [0.0, 1.0]},
            ],
        }
        with patch("utils.shared_embedder._interactive_priority.is_set", return_value=True), patch.object(
            api, "_post", return_value=payload,
        ), patch("utils.shared_embedder._get_fast_embedder") as fast_fallback:
            vectors, space = api.encode_interactive_with_metadata(["intent", "query"])

        self.assertEqual(vectors.shape, (2, 2))
        self.assertEqual(space, api.embedding_space_id)
        self.assertEqual(api._transport_backoff_until, 0.0)
        fast_fallback.assert_not_called()

    def test_interactive_transport_timeout_is_bounded_and_backed_off(self):
        api = APIEmbedder("nomic-model", "http://127.0.0.1:1234/v1", timeout=8)
        with patch.object(
            api, "_post", side_effect=urllib.error.URLError(TimeoutError("timed out")),
        ) as post:
            with self.assertRaises(urllib.error.URLError):
                api.encode_interactive_with_metadata(["semantic route"])
            with self.assertRaises(QualityEndpointBackoff):
                api.encode_interactive_with_metadata(["next turn"])

        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs["timeout"], QUALITY_INTERACTIVE_REQUEST_TIMEOUT)
        self.assertGreater(api._transport_backoff_until, 0.0)

    def test_interactive_nontransport_error_does_not_enter_backoff(self):
        api = APIEmbedder("nomic-model", "http://127.0.0.1:1234/v1")
        with patch.object(api, "_post", side_effect=ValueError("malformed payload")):
            with self.assertRaisesRegex(ValueError, "malformed payload"):
                api.encode_interactive_with_metadata(["semantic route"])

        self.assertEqual(api._transport_backoff_until, 0.0)

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

    def test_transport_timeout_falls_back_once_then_short_circuits_retries(self):
        class Fast:
            model_name_or_path = "all-MiniLM-L6-v2"

            def encode(self, texts, **_kwargs):
                return np.ones((len(texts), 384), dtype="float32")

        api = APIEmbedder("nomic-model", "http://127.0.0.1:1234/v1")
        with patch.object(
            api, "_post", side_effect=urllib.error.URLError(TimeoutError("timed out"))
        ) as post, patch("utils.shared_embedder._get_fast_embedder", return_value=Fast()):
            first, first_space = api.encode_with_metadata(["first batch"])
            second, second_space = api.encode_with_metadata(["second batch"])

        self.assertEqual(first.shape, (1, 384))
        self.assertEqual(second.shape, (1, 384))
        self.assertEqual(first_space, "sentence-transformers:all-MiniLM-L6-v2")
        self.assertEqual(second_space, first_space)
        post.assert_called_once()

    def test_invalid_quality_response_does_not_enter_transport_backoff(self):
        api = APIEmbedder("nomic-model", "http://127.0.0.1:1234/v1")
        with patch.object(api, "_post", side_effect=ValueError("invalid response")):
            with self.assertRaisesRegex(ValueError, "invalid response"):
                api._encode_list(["probe"])

        self.assertEqual(api._transport_backoff_until, 0.0)

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
