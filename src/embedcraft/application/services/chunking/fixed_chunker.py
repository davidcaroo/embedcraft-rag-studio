"""Fixed-size chunking strategy with overlap."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from embedcraft.domain.entities import CanonicalDocument, Chunk
from embedcraft.domain.services.hashing import compute_text_hash
from embedcraft.domain.value_objects import ChunkMetadata


class FixedSizeChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = max(50, chunk_size)
        self.chunk_overlap = max(0, min(chunk_overlap, self.chunk_size - 10))

    @property
    def strategy_name(self) -> str:
        return "fixed_size"

    @property
    def version(self) -> str:
        return "1.0.0"

    def split(
        self,
        canonical_doc: CanonicalDocument,
        document_version_id: str,
    ) -> Sequence[Chunk]:
        text = canonical_doc.text
        if not text.strip():
            return []

        chunks: list[Chunk] = []
        step = self.chunk_size - self.chunk_overlap
        start = 0
        chunk_idx = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:
                c_hash = compute_text_hash(chunk_text)
                metadata = ChunkMetadata(
                    char_start=start,
                    char_end=end,
                    custom={"title": canonical_doc.title},
                )
                chunk = Chunk(
                    id=str(uuid.uuid4()),
                    document_id=canonical_doc.document_id,
                    document_version_id=document_version_id,
                    chunk_index=chunk_idx,
                    text=chunk_text,
                    chunk_hash=c_hash,
                    metadata=metadata,
                    token_count=len(chunk_text.split()),
                    strategy_version=f"{self.strategy_name}:{self.version}",
                )
                chunks.append(chunk)
                chunk_idx += 1

            if end >= len(text):
                break
            start += step

        return chunks
