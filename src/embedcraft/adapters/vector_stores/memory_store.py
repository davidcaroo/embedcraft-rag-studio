"""In-memory vector store for unit tests and lightweight verification."""

from __future__ import annotations

import math
from collections.abc import Sequence

from embedcraft.ports.vector_store import ScoredRecord, VectorRecord


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class MemoryVectorStore:
    def __init__(self):
        # Key: (collection_id, revision_id) -> list[VectorRecord]
        self._store: dict[tuple[str, str], list[VectorRecord]] = {}

    def create_collection_index(
        self,
        collection_id: str,
        revision_id: str,
        dimension: int,
        metric: str = "cosine",
    ) -> None:
        key = (collection_id, revision_id)
        if key not in self._store:
            self._store[key] = []

    def upsert(
        self,
        collection_id: str,
        revision_id: str,
        records: Sequence[VectorRecord],
    ) -> None:
        key = (collection_id, revision_id)
        if key not in self._store:
            self._store[key] = []
        self._store[key].extend(records)

    def search(
        self,
        collection_id: str,
        revision_id: str,
        query_vector: list[float],
        top_k: int = 10,
    ) -> list[ScoredRecord]:
        key = (collection_id, revision_id)
        records = self._store.get(key, [])
        if not records:
            return []

        scored: list[tuple[float, VectorRecord]] = []
        for r in records:
            sim = cosine_similarity(query_vector, r.vector)
            scored.append((sim, r))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: list[ScoredRecord] = []
        for sim, rec in scored[:top_k]:
            results.append(
                ScoredRecord(
                    chunk_id=rec.chunk_id,
                    document_id=rec.document_id,
                    score=float(sim),
                    text=rec.text,
                    collection_id=collection_id,
                    metadata=rec.metadata,
                )
            )
        return results

    def delete_revision(self, collection_id: str, revision_id: str) -> bool:
        key = (collection_id, revision_id)
        if key in self._store:
            del self._store[key]
            return True
        return False
