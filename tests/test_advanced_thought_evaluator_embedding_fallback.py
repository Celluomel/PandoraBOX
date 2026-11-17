from unittest.mock import patch

import numpy as np

from cognition.advanced_thought_evaluator import AdvancedThoughtEvaluator


class _SpaceEmbedder:
    def __init__(self, space_id):
        self.space_id = space_id

    def encode_with_metadata(self, texts):
        return np.asarray([[1.0, 0.0] for _ in texts]), self.space_id


def test_advanced_evaluator_uses_word_overlap_for_uncalibrated_fallback():
    evaluator = AdvancedThoughtEvaluator()
    embedder = _SpaceEmbedder("sentence-transformers:all-MiniLM-L6-v2")
    with patch("utils.shared_embedder.get_embedder", return_value=embedder):
        result = evaluator._compute_goal_similarity(
            ["robot odometry"], [{"name": "mechanical walking"}],
        )

    assert result == 0.0


def test_advanced_evaluator_uses_cosine_for_calibrated_nomic():
    evaluator = AdvancedThoughtEvaluator()
    embedder = _SpaceEmbedder(
        "api:http://localhost:1234/v1:text-embedding-nomic-embed-text-v1.5"
    )
    with patch("utils.shared_embedder.get_embedder", return_value=embedder):
        result = evaluator._compute_goal_similarity(
            ["robot odometry"], [{"name": "mechanical walking"}],
        )

    assert result == 1.0
