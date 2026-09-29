"""Embedding provider port definition."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for embedding providers (SentenceTransformers, APIs, Mock)."""

    @property
    def model_name(self) -> str:
        """Name or identifier of the embedding model."""
        ...

    @property
    def dimension(self) -> int:
        """Dimension size of generated vectors."""
        ...

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts in a batch."""
        ...

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding vector for a single search query."""
        ...
