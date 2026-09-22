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


if __name__ == "__main__":
    unittest.main()
