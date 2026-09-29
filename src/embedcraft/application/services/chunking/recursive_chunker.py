"""Recursive character chunking strategy respecting natural boundaries (paragraphs, sentences, words)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import ClassVar

from embedcraft.domain.entities import CanonicalDocument, Chunk
from embedcraft.domain.services.hashing import compute_text_hash
from embedcraft.domain.value_objects import ChunkMetadata


class RecursiveChunker:
    DEFAULT_SEPARATORS: ClassVar[list[str]] = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: list[str] | None = None,
    ):
        self.chunk_size = max(50, chunk_size)
        self.chunk_overlap = max(0, min(chunk_overlap, self.chunk_size - 10))
        self.separators = separators or self.DEFAULT_SEPARATORS

    @property
    def strategy_name(self) -> str:
        return "recursive"

    @property
    def version(self) -> str:
        return "1.0.0"

    def split(
        self,
        canonical_doc: CanonicalDocument,
        document_version_id: str,
    ) -> Sequence[Chunk]:
        raw_text = canonical_doc.text
        if not raw_text.strip():
            return []

        splits = self._split_text(raw_text, self.separators)
        chunks: list[Chunk] = []

        char_offset = 0
        for idx, segment in enumerate(splits):
            s_text = segment.strip()
            if not s_text:
                continue

            # Locate section / page if mentioned in text
            current_section = ""
            current_page = None
            if "--- Página " in s_text:
                try:
                    p_str = s_text.split("--- Página ")[1].split(" ---")[0]
                    current_page = int(p_str)
                except Exception:  # noqa: BLE001, S110
                    pass

            c_hash = compute_text_hash(s_text)
            metadata = ChunkMetadata(
                section=current_section,
                page=current_page,
                char_start=char_offset,
                char_end=char_offset + len(s_text),
                custom={"title": canonical_doc.title},
            )
            chunk = Chunk(
                id=str(uuid.uuid4()),
                document_id=canonical_doc.document_id,
                document_version_id=document_version_id,
                chunk_index=idx,
                text=s_text,
                chunk_hash=c_hash,
                metadata=metadata,
                token_count=len(s_text.split()),
                strategy_version=f"{self.strategy_name}:{self.version}",
            )
            chunks.append(chunk)
            char_offset += len(segment)

        return chunks

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        final_chunks: list[str] = []
        separator = separators[-1]
        new_separators = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1 :]
                break

        splits = text.split(separator) if separator else list(text)
        good_splits: list[str] = []

        for s in splits:
            if len(s) < self.chunk_size:
                good_splits.append(s)
            else:
                if good_splits:
                    merged = self._merge_splits(good_splits, separator)
                    final_chunks.extend(merged)
                    good_splits = []
                if not new_separators:
                    final_chunks.append(s)
                else:
                    other_info = self._split_text(s, new_separators)
                    final_chunks.extend(other_info)

        if good_splits:
            merged = self._merge_splits(good_splits, separator)
            final_chunks.extend(merged)

        return final_chunks

    def _merge_splits(self, splits: list[str], separator: str) -> list[str]:
        docs: list[str] = []
        current_doc: list[str] = []
        total = 0

        for d in splits:
            _len = len(d)
            if (total + _len + (len(separator) if current_doc else 0) > self.chunk_size) and current_doc:
                doc = separator.join(current_doc)
                if doc:
                    docs.append(doc)
                # Handle overlap by keeping tail elements
                while total > self.chunk_overlap or (
                    total + _len + (len(separator) if current_doc else 0) > self.chunk_size and total > 0
                ):
                    total -= len(current_doc[0]) + (len(separator) if len(current_doc) > 1 else 0)
                    current_doc.pop(0)
            current_doc.append(d)
            total += _len + (len(separator) if len(current_doc) > 1 else 0)

        if current_doc:
            doc = separator.join(current_doc)
            if doc:
                docs.append(doc)
        return docs
