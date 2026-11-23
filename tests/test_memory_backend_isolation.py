import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest


faiss = pytest.importorskip("faiss")


class _Embedder:
    def get_sentence_embedding_dimension(self):
        return 3

    def encode(self, texts, **_kwargs):
        if isinstance(texts, str):
            texts = [texts]
        rows = []
        for index, text in enumerate(texts):
            seed = sum(str(text).encode("utf-8")) + index
            rows.append([float(seed % 7 + 1), float(seed % 5 + 1), 1.0])
        return np.asarray(rows, dtype=np.float32)


def test_auxiliary_memory_migrates_documents_without_touching_cognitive_index(tmp_path):
    from managers.memory_manager import FAISSMemoryBackend
    from managers.settings_manager import config

    cognitive_path = tmp_path / "faiss_index.bin"
    original_index = faiss.IndexIDMap(faiss.IndexFlatL2(3))
    original_index.add_with_ids(
        np.asarray([[1.0, 0.0, 0.0]], dtype=np.float32),
        np.asarray([42], dtype=np.int64),
    )
    faiss.write_index(original_index, str(cognitive_path))
    original_bytes = cognitive_path.read_bytes()

    legacy_docs = [
        {"content": "User: I prefer concise answers.", "metadata": {"role": "user"}},
        {"content": "Lumina: I will keep replies concise.", "metadata": {"role": "assistant"}},
    ]
    legacy_meta = cognitive_path.with_suffix(".meta.json")
    legacy_meta.write_text(json.dumps(legacy_docs), encoding="utf-8")

    with patch.object(config, "MEMORY_FAISS_PATH", str(cognitive_path)), patch(
        "utils.shared_embedder.get_embedder", return_value=_Embedder()
    ):
        backend = FAISSMemoryBackend()

    interaction_path = tmp_path / "faiss_index_interaction.bin"
    interaction_meta = tmp_path / "faiss_index_interaction.meta.json"
    assert backend.INDEX_PATH == interaction_path
    assert backend.META_PATH == interaction_meta
    assert backend._index.ntotal == len(legacy_docs)
    assert len(backend._docs) == len(legacy_docs)
    assert interaction_path.is_file()
    assert interaction_meta.is_file()
    assert cognitive_path.read_bytes() == original_bytes
    assert json.loads(legacy_meta.read_text(encoding="utf-8")) == legacy_docs

    backend.add_memory("new auxiliary observation", {"role": "vision"})
    assert backend._index.ntotal == len(legacy_docs) + 1
    assert len(backend._docs) == len(legacy_docs) + 1
    assert cognitive_path.read_bytes() == original_bytes
    assert json.loads(legacy_meta.read_text(encoding="utf-8")) == legacy_docs
