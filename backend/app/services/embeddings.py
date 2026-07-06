from __future__ import annotations

import hashlib
import re
from functools import lru_cache
from typing import Iterable, List

import numpy as np

from ..config import EMBEDDING_MODEL_NAME

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None


TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+")


class EmbeddingService:
    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension
        self.model_name = EMBEDDING_MODEL_NAME
        self.model = None
        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception:
                self.model = None

    def embed_texts(self, texts: Iterable[str]) -> np.ndarray:
        text_list = list(texts)
        if not text_list:
            return np.empty((0, self.dimension), dtype=np.float32)
        if self.model is not None:
            embeddings = self.model.encode(text_list, normalize_embeddings=True)
            return np.asarray(embeddings, dtype=np.float32)
        return self._hashing_embeddings(text_list)

    def embed_query(self, text: str) -> np.ndarray:
        embeddings = self.embed_texts([text])
        return embeddings[0] if len(embeddings) else np.zeros(self.dimension, dtype=np.float32)

    def _hashing_embeddings(self, texts: List[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for row_index, text in enumerate(texts):
            tokens = TOKEN_PATTERN.findall(text.lower())
            if not tokens:
                continue
            for token in tokens:
                digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
                bucket = int(digest[:8], 16) % self.dimension
                vectors[row_index, bucket] += 1.0
            norm = np.linalg.norm(vectors[row_index])
            if norm > 0:
                vectors[row_index] /= norm
        return vectors


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
