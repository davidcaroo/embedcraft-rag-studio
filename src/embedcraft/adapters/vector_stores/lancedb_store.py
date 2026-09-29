"""LanceDB vector store adapter for high-performance persistent local indexing."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import lancedb

from embedcraft.infrastructure.settings import settings
from embedcraft.ports.vector_store import ScoredRecord, VectorRecord


class LanceDBVectorStore:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or (settings.base_dir / "indices" / "lancedb")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(str(self.base_dir))

    def _table_name(self, collection_id: str, revision_id: str) -> str:
        # LanceDB table names must be valid identifiers
        clean_col = collection_id.replace("-", "_")
        clean_rev = revision_id.replace("-", "_")
        return f"idx_{clean_col}_{clean_rev}"

    def _has_table(self, table_name: str) -> bool:
        if hasattr(self.db, "list_tables"):
            res = self.db.list_tables()
            if hasattr(res, "tables"):
                return table_name in res.tables
            if isinstance(res, (list, tuple)):
                return table_name in res
        return table_name in self.db.table_names()

    def create_collection_index(
        self,
        collection_id: str,
        revision_id: str,
        dimension: int,
        metric: str = "cosine",
    ) -> None:
        # In LanceDB, tables are created on the first write with schema inference
        pass

    def upsert(
        self,
        collection_id: str,
        revision_id: str,
        records: Sequence[VectorRecord],
    ) -> None:
        if not records:
            return

        table_name = self._table_name(collection_id, revision_id)
        data = [
            {
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "vector": r.vector,
                "text": r.text,
                "metadata_json": json.dumps(r.metadata),
            }
            for r in records
        ]

        if self._has_table(table_name):
            tbl = self.db.open_table(table_name)
            tbl.add(data)
        else:
            self.db.create_table(table_name, data=data)

    def search(
        self,
        collection_id: str,
        revision_id: str,
        query_vector: list[float],
        top_k: int = 10,
    ) -> list[ScoredRecord]:
        table_name = self._table_name(collection_id, revision_id)
        if not self._has_table(table_name):
            return []

        tbl = self.db.open_table(table_name)
        # Search returns records sorted by distance
        results = tbl.search(query_vector).limit(top_k).to_list()

        scored_records: list[ScoredRecord] = []
        for row in results:
            # LanceDB cosine distance ranges from 0 (identical) to 2 (opposite)
            # Similarity score = 1.0 - distance
            distance = row.get("_distance", 1.0)
            score = max(0.0, 1.0 - distance)
            meta = {}
            if row.get("metadata_json"):
                try:
                    meta = json.loads(row["metadata_json"])
                except (json.JSONDecodeError, TypeError):
                    meta = {}

            scored_records.append(
                ScoredRecord(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    score=float(score),
                    text=row["text"],
                    collection_id=collection_id,
                    metadata=meta,
                )
            )

        return scored_records

    def delete_revision(self, collection_id: str, revision_id: str) -> bool:
        table_name = self._table_name(collection_id, revision_id)
        if self._has_table(table_name):
            self.db.drop_table(table_name)
            return True
        return False
