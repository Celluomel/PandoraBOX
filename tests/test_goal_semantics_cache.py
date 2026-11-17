import unittest
from unittest.mock import patch

import numpy as np

from cognition import goal_semantics


class _FakeEmbedder:
    def __init__(self, model_name="fake-model", offset=0):
        self.calls = []
        self.model_name = model_name
        self.offset = offset

    def encode(self, texts):
        self.calls.append(list(texts))
        return np.asarray(
            [[len(text) + self.offset, sum(map(ord, text)) % 97] for text in texts],
            dtype="float32",
        )


class _FallbackEmbedder:
    model_name = "quality-model"
    embedding_space_id = "api:local:quality-model"

    def __init__(self):
        self.calls = 0

    def encode_with_metadata(self, texts):
        self.calls += 1
        return np.asarray([[1.0, 2.0] for _ in texts], dtype="float32"), "fast:minilm"


class _SwitchingSpaceEmbedder:
    model_name = "quality-model"
    embedding_space_id = "api:local:quality-model"

    def __init__(self):
        self.calls = []

    def encode_with_metadata(self, texts):
        self.calls.append(list(texts))
        if len(self.calls) == 1:
            return np.asarray([[10.0, 1.0] for _ in texts]), self.embedding_space_id
        return np.asarray([[20.0, 2.0] for _ in texts]), "fast:minilm"


class GoalSemanticsCacheTests(unittest.TestCase):
    def setUp(self):
        with goal_semantics._embedding_cache_lock:
            goal_semantics._embedding_cache.clear()
        self.embedder = _FakeEmbedder()
        self.patcher = patch("utils.shared_embedder.get_embedder", return_value=self.embedder)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        with goal_semantics._embedding_cache_lock:
            goal_semantics._embedding_cache.clear()

    def test_reuses_cached_vectors_and_only_embeds_new_text(self):
        first = goal_semantics.embed(["topic alpha", "fixed exemplar"])
        second = goal_semantics.embed(["fixed exemplar", "topic beta"])

        self.assertEqual(len(self.embedder.calls), 2)
        self.assertEqual(self.embedder.calls[0], ["topic alpha", "fixed exemplar"])
        self.assertEqual(self.embedder.calls[1], ["topic beta"])
        np.testing.assert_array_equal(first[1], second[0])
        self.assertEqual(second.shape, (2, 2))

    def test_duplicate_text_is_embedded_once(self):
        result = goal_semantics.embed(["same", "same"])
        self.assertEqual(self.embedder.calls, [["same"]])
        np.testing.assert_array_equal(result[0], result[1])

    def test_same_dimension_model_change_does_not_reuse_old_vectors(self):
        first_model = _FakeEmbedder(model_name="model-a", offset=0)
        second_model = _FakeEmbedder(model_name="model-b", offset=100)
        with patch("utils.shared_embedder.get_embedder", return_value=first_model):
            first = goal_semantics.embed(["shared topic"])
        with patch("utils.shared_embedder.get_embedder", return_value=second_model):
            second = goal_semantics.embed(["shared topic"])

        self.assertEqual(first_model.calls, [["shared topic"]])
        self.assertEqual(second_model.calls, [["shared topic"]])
        self.assertNotEqual(float(first[0, 0]), float(second[0, 0]))

    def test_quality_fallback_vectors_are_cached_under_actual_fast_space(self):
        fallback = _FallbackEmbedder()
        with patch("utils.shared_embedder.get_embedder", return_value=fallback):
            first = goal_semantics.embed(["fallback topic"])
            second = goal_semantics.embed(["fallback topic"])

        self.assertEqual(fallback.calls, 2)
        np.testing.assert_array_equal(first, second)
        self.assertIn(("fast:minilm", "fallback topic"), goal_semantics._embedding_cache)
        self.assertNotIn((fallback.embedding_space_id, "fallback topic"), goal_semantics._embedding_cache)

    def test_partial_cache_fallback_reembeds_batch_without_mixing_spaces(self):
        switching = _SwitchingSpaceEmbedder()
        with patch("utils.shared_embedder.get_embedder", return_value=switching):
            goal_semantics.embed(["cached nomic text"])
            result = goal_semantics.embed(["cached nomic text", "new text"])

        self.assertEqual(
            switching.calls,
            [["cached nomic text"], ["new text"], ["cached nomic text", "new text"]],
        )
        np.testing.assert_array_equal(result, np.asarray([[20.0, 2.0], [20.0, 2.0]]))

    def _score_topic(self, good_sim, noise_sim):
        rows = 1 + len(goal_semantics.GOOD_TOPIC_EXEMPLARS) + len(
            goal_semantics.NOISE_TOPIC_EXEMPLARS
        )
        with patch("cognition.goal_semantics.embed", return_value=np.zeros((rows, 2))), patch(
            "cognition.goal_semantics.max_cosine", side_effect=[good_sim, noise_sim]
        ):
            return goal_semantics.batch_topic_quality(["sample topic"])["sample topic"]

    def test_rejects_fragment_with_weak_positive_semantic_margin(self):
        # Live Nomic scoring for "après chaque" had a +0.0255 margin.
        good, noise, accepted = self._score_topic(0.4380, 0.4125)
        self.assertAlmostEqual(good - noise, 0.0255, places=4)
        self.assertFalse(accepted)

    def test_rejects_topic_that_is_closer_to_noise_than_good_examples(self):
        good, noise, accepted = self._score_topic(0.4686, 0.4706)
        self.assertLess(good - noise, 0.0)
        self.assertFalse(accepted)

    def test_accepts_topic_with_calibrated_positive_semantic_margin(self):
        good, noise, accepted = self._score_topic(0.5054, 0.4551)
        self.assertGreater(good - noise, goal_semantics.MIN_GOOD_TOPIC_MARGIN)
        self.assertTrue(accepted)


if __name__ == "__main__":
    unittest.main()
