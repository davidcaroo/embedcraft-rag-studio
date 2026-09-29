"""Deterministic mock embedding provider for tests and offline development."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence


class MockEmbeddingProvider:
    """Generates deterministic pseudo-random unit vectors based on text hashes."""

    def __init__(self, model_name: str = "mock-mini-384", dimension: int = 384):
        self._model_name = model_name
        self._dimension = dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_query(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        # Generate deterministic vector from SHA-256 seed
        seed_bytes = hashlib.sha256(query.encode("utf-8")).digest()
        vector: list[float] = []
        for i in range(self._dimension):
            byte_val = seed_bytes[i % len(seed_bytes)]
            val = ((byte_val + i * 17) % 256) / 128.0 - 1.0
            vector.append(val)

        # Normalize to unit length (L2 norm) for cosine similarity
        norm = math.sqrt(sum(x * x for x in vector)) or 1.0
        return [x / norm for x in vector]
