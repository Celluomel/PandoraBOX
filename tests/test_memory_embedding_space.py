from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from cognition.ai_system import EnhancedMemorySystem


class _QualityEmbedder:
    embedding_space_id = "api:http://127.0.0.1:1234/v1:text-embedding-nomic-embed-text-v1.5"

    def get_sentence_embedding_dimension(self):
        return 768


def test_configured_quality_model_selects_quality_embedder():
    from managers.settings_manager import config as robot_config

    memory = EnhancedMemorySystem.__new__(EnhancedMemorySystem)
    memory.config = SimpleNamespace(
        embedding_model_name="text-embedding-nomic-embed-text-v1.5",
        faiss=SimpleNamespace(embedding_dim=384),
    )
    embedder = _QualityEmbedder()

    with patch.object(
        robot_config,
        "QUALITY_EMBED_MODEL",
        "text-embedding-nomic-embed-text-v1.5",
    ), patch("utils.shared_embedder.get_embedder", return_value=embedder) as get_embedder:
        memory._init_embedding_model()

    get_embedder.assert_called_once_with(
        "text-embedding-nomic-embed-text-v1.5", quality=True,
    )
    assert memory.embedding_model is embedder
    assert memory.embedding_dim == 768


def test_memory_index_encoding_uses_and_checks_exact_embedding_space():
    class StrictEmbedder(_QualityEmbedder):
        def encode_strict_with_metadata(self, texts, *, batch_size):
            assert batch_size == 16
            return np.ones((len(texts), 768), dtype=np.float32), self.embedding_space_id

    memory = EnhancedMemorySystem.__new__(EnhancedMemorySystem)
    memory.config = SimpleNamespace(embedding_model_name="nomic-config-label")
    memory.embedding_model = StrictEmbedder()
    memory.embedding_dim = 768

    vectors = memory._encode_memory_vectors(["a", "b"], batch_size=16)

    assert vectors.shape == (2, 768)
    assert memory._embedding_model_id() == memory.embedding_model.embedding_space_id


def test_memory_index_rejects_a_vector_from_another_model_space():
    class WrongSpaceEmbedder(_QualityEmbedder):
        def encode_strict_with_metadata(self, texts, *, batch_size):
            return np.ones((len(texts), 768), dtype=np.float32), "api:other:model"

    memory = EnhancedMemorySystem.__new__(EnhancedMemorySystem)
    memory.config = SimpleNamespace(embedding_model_name="nomic-config-label")
    memory.embedding_model = WrongSpaceEmbedder()
    memory.embedding_dim = 768

    with pytest.raises(ValueError, match="Embedding space mismatch"):
        memory._encode_memory_vectors("query")
