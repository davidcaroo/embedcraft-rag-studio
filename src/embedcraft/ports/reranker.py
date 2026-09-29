"""Reranker provider port definition."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from embedcraft.domain.entities import RetrievalResult


@runtime_checkable
class RerankerProvider(Protocol):
    """Protocol for cross-encoder rerankers that refine retrieval ranking."""

    def rerank(
        self,
        query: str,
        results: Sequence[RetrievalResult],
        top_k: int = 5,
    ) -> list[RetrievalResult]: ...
