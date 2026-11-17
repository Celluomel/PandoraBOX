import unittest
from unittest.mock import patch

import numpy as np

from cognition import goal_semantics


class _FakeEmbedder:
    def __init__(self):
        self.calls = []

    def encode(self, texts):
        self.calls.append(list(texts))
        return np.asarray([[len(text), sum(map(ord, text)) % 97] for text in texts], dtype="float32")


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
