"""Ports for document extraction and chunking strategies."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from embedcraft.domain.entities import CanonicalDocument, Chunk


@runtime_checkable
class DocumentReader(Protocol):
    """Protocol for extracting content from documents into CanonicalDocument."""

    def supports(self, extension: str, mime_type: str = "") -> bool:
        """Check if this reader supports the given file extension or MIME type."""
        ...

    def extract(
        self,
        file_path: Path,
        document_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        """Extract canonical document from file path."""
        ...


@runtime_checkable
class ChunkingStrategy(Protocol):
    """Protocol for partitioning a canonical document into chunks."""

    @property
    def strategy_name(self) -> str:
        """Name of the chunking strategy."""
        ...

    @property
    def version(self) -> str:
        """Version string of the chunking algorithm."""
        ...

    def split(
        self,
        canonical_doc: CanonicalDocument,
        document_version_id: str,
    ) -> Sequence[Chunk]:
        """Split a canonical document into structured chunks."""
        ...
