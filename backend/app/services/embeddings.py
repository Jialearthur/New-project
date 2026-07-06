from __future__ import annotations

import hashlib
import re
from functools import lru_cache
from typing import List

from ..config import EMBEDDING_MODEL_NAME

try:
    from langchain_core.embeddings import Embeddings
except Exception:  # pragma: no cover - optional dependency
    Embeddings = object  # type: ignore

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except Exception:  # pragma: no cover - optional dependency
    HuggingFaceEmbeddings = None


TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+")


class HashingEmbeddings(Embeddings):
    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension
        self.model_name = "hashing-fallback"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._hashing_embedding(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._hashing_embedding(text)

    def _hashing_embedding(self, text: str) -> List[float]:
        vector = [0.0] * self.dimension
        tokens = TOKEN_PATTERN.findall(text.lower())
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            bucket = int(digest[:8], 16) % self.dimension
            vector[bucket] += 1.0
        norm = sum(value * value for value in vector) ** 0.5
        if norm > 0:
            vector = [value / norm for value in vector]
        return vector


@lru_cache(maxsize=1)
def get_embedding_service() -> Embeddings:
    if HuggingFaceEmbeddings is not None:
        try:
            return HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL_NAME,
                model_kwargs={"device": "cpu", "local_files_only": True},
                encode_kwargs={"normalize_embeddings": True},
            )
        except Exception:
            pass
    return HashingEmbeddings()
