"""Vector storage port definition."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class VectorRecord(BaseModel):
    chunk_id: str
    document_id: str
    vector: list[float]
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScoredRecord(BaseModel):
    chunk_id: str
    document_id: str
    score: float
    text: str
    collection_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class VectorStore(Protocol):
    """Protocol for vector databases (LanceDB, in-memory, Qdrant)."""

    def create_collection_index(
        self,
        collection_id: str,
        revision_id: str,
        dimension: int,
        metric: str = "cosine",
    ) -> None:
        """Initialize an index for a collection revision."""
        ...

    def upsert(
        self,
        collection_id: str,
        revision_id: str,
        records: Sequence[VectorRecord],
    ) -> None:
        """Upsert vector records into the collection revision."""
        ...

    def search(
        self,
        collection_id: str,
        revision_id: str,
        query_vector: list[float],
        top_k: int = 10,
    ) -> list[ScoredRecord]:
        """Perform semantic similarity search on a specific revision."""
        ...

    def delete_revision(self, collection_id: str, revision_id: str) -> bool:
        """Remove revision index data."""
        ...
