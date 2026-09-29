"""Embedding cache backed by SQLite to minimize redundant model inferences."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from sqlalchemy.orm import Session

from embedcraft.infrastructure.database.models import EmbeddingCacheModel


def make_cache_key(text_hash: str, model_name: str, dimension: int) -> str:
    seed = f"{text_hash}::{model_name}::{dimension}".encode()
    return hashlib.sha256(seed).hexdigest()


class SQLiteEmbeddingCache:
    def __init__(self, session: Session):
        self.session = session

    def get_many(
        self,
        text_hashes: Sequence[str],
        model_name: str,
        dimension: int,
    ) -> dict[str, list[float]]:
        """Retrieve cached vectors for a set of text hashes."""
        if not text_hashes:
            return {}

        keys = [make_cache_key(th, model_name, dimension) for th in text_hashes]
        models = (
            self.session.query(EmbeddingCacheModel)
            .filter(EmbeddingCacheModel.id.in_(keys))
            .all()
        )
        return {m.text_hash: m.vector_json for m in models}

    def set_many(
        self,
        items: Sequence[tuple[str, list[float]]],  # (text_hash, vector)
        model_name: str,
        dimension: int,
    ) -> None:
        """Store multiple embeddings in the cache."""
        for text_hash, vector in items:
            key = make_cache_key(text_hash, model_name, dimension)
            existing = self.session.query(EmbeddingCacheModel).filter_by(id=key).first()
            if not existing:
                cache_entry = EmbeddingCacheModel(
                    id=key,
                    text_hash=text_hash,
                    model_name=model_name,
                    dimension=dimension,
                    vector_json=vector,
                )
                self.session.add(cache_entry)
        self.session.flush()
