"""Lexical search store port definition."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from embedcraft.domain.entities import Chunk
from embedcraft.ports.vector_store import ScoredRecord


@runtime_checkable
class LexicalSearchStore(Protocol):
    """Protocol for BM25 / Full-Text Search (SQLite FTS5)."""

    def index_chunks(
        self,
        project_id: str,
        revision_id: str,
        chunks: Sequence[Chunk],
    ) -> None:
        """Index chunks for full-text search."""
        ...

    def search(
        self,
        project_id: str,
        revision_id: str,
        query: str,
        top_k: int = 10,
    ) -> list[ScoredRecord]:
        """Search chunks using lexical full-text matching."""
        ...

    def delete_revision(self, project_id: str, revision_id: str) -> None:
        """Delete FTS index entries for a specific revision."""
        ...
