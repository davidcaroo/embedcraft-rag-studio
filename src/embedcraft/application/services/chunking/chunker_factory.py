"""Factory for creating chunking strategies based on processing profile."""

from __future__ import annotations

from embedcraft.application.services.chunking.fixed_chunker import FixedSizeChunker
from embedcraft.application.services.chunking.recursive_chunker import RecursiveChunker
from embedcraft.application.services.chunking.section_chunker import SectionChunker
from embedcraft.domain.entities import ProcessingProfile
from embedcraft.ports.documents import ChunkingStrategy


def get_chunker_for_profile(profile: ProcessingProfile) -> ChunkingStrategy:
    strategy = profile.chunking_strategy.lower()
    if strategy == "fixed":
        return FixedSizeChunker(
            chunk_size=profile.chunk_size,
            chunk_overlap=profile.chunk_overlap,
        )
    elif strategy == "section":
        return SectionChunker(max_chunk_size=profile.chunk_size)
    else:
        # Default is recursive
        return RecursiveChunker(
            chunk_size=profile.chunk_size,
            chunk_overlap=profile.chunk_overlap,
        )
