"""Section-based chunking strategy splitting by document headers and structural boundaries."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from embedcraft.domain.entities import CanonicalDocument, Chunk
from embedcraft.domain.services.hashing import compute_text_hash
from embedcraft.domain.value_objects import ChunkMetadata


class SectionChunker:
    def __init__(self, max_chunk_size: int = 1000):
        self.max_chunk_size = max_chunk_size

    @property
    def strategy_name(self) -> str:
        return "section"

    @property
    def version(self) -> str:
        return "1.0.0"

    def split(
        self,
        canonical_doc: CanonicalDocument,
        document_version_id: str,
    ) -> Sequence[Chunk]:
        # If document has explicit sections, split by sections
        if not canonical_doc.text.strip():
            return []

        chunks: list[Chunk] = []

        # Check if text contains explicit section markers or markdown headers
        lines = canonical_doc.text.split("\n")
        current_section = "General"
        current_lines: list[str] = []
        chunk_idx = 0

        def flush_chunk(lines_to_flush: list[str], sec_name: str) -> None:
            nonlocal chunk_idx
            sec_text = "\n".join(lines_to_flush).strip()
            if not sec_text:
                return

            # Check if exceeds max size, in which case sub-chunk
            start = 0
            while start < len(sec_text):
                sub_text = sec_text[start : start + self.max_chunk_size].strip()
                if sub_text:
                    chunk = Chunk(
                        id=str(uuid.uuid4()),
                        document_id=canonical_doc.document_id,
                        document_version_id=document_version_id,
                        chunk_index=chunk_idx,
                        text=sub_text,
                        chunk_hash=compute_text_hash(sub_text),
                        metadata=ChunkMetadata(
                            section=sec_name,
                            custom={"title": canonical_doc.title},
                        ),
                        token_count=len(sub_text.split()),
                        strategy_version=f"{self.strategy_name}:{self.version}",
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                start += self.max_chunk_size

        for line in lines:
            if line.startswith(("#", "--- Página ", "--- Hoja: ")):
                if current_lines:
                    flush_chunk(current_lines, current_section)
                    current_lines = []
                current_section = line.lstrip("#- ").strip()
            current_lines.append(line)

        if current_lines:
            flush_chunk(current_lines, current_section)

        return chunks
