from __future__ import annotations

import json
from pathlib import Path
from typing import List

import numpy as np

from ..config import INDEX_DIR

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    faiss = None


class VectorStore:
    def __init__(self) -> None:
        self.index_file = Path(INDEX_DIR / "faiss.index")
        self.metadata_file = Path(INDEX_DIR / "metadata.json")
        self.numpy_file = Path(INDEX_DIR / "embeddings.npy")

    def save(self, chunk_ids: List[str], embeddings: np.ndarray) -> None:
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        normalized = embeddings.astype("float32")
        if len(normalized):
            norms = np.linalg.norm(normalized, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            normalized = normalized / norms

        self.metadata_file.write_text(json.dumps(chunk_ids, ensure_ascii=False, indent=2), encoding="utf-8")
        if faiss is not None and len(normalized):
            index = faiss.IndexFlatIP(normalized.shape[1])
            index.add(normalized)
            faiss.write_index(index, str(self.index_file))
            if self.numpy_file.exists():
                self.numpy_file.unlink()
        else:
            np.save(self.numpy_file, normalized)
            if self.index_file.exists():
                self.index_file.unlink()

    def clear(self) -> None:
        for file_path in [self.index_file, self.metadata_file, self.numpy_file]:
            if file_path.exists():
                file_path.unlink()

    def search(self, query_embedding: np.ndarray, top_k: int) -> List[tuple[str, float]]:
        if not self.metadata_file.exists():
            return []
        chunk_ids = json.loads(self.metadata_file.read_text(encoding="utf-8"))
        if not chunk_ids:
            return []

        query = query_embedding.astype("float32")
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm

        if faiss is not None and self.index_file.exists():
            index = faiss.read_index(str(self.index_file))
            scores, indices = index.search(np.expand_dims(query, axis=0), top_k)
            results: List[tuple[str, float]] = []
            for idx, score in zip(indices[0], scores[0]):
                if idx < 0 or idx >= len(chunk_ids):
                    continue
                results.append((chunk_ids[idx], float(score)))
            return results

        if not self.numpy_file.exists():
            return []
        embeddings = np.load(self.numpy_file)
        scores = embeddings @ query
        order = np.argsort(scores)[::-1][:top_k]
        return [(chunk_ids[idx], float(scores[idx])) for idx in order if idx < len(chunk_ids)]
