"""SQLite FTS5 full-text lexical search store with BM25 ranking."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from embedcraft.domain.entities import Chunk
from embedcraft.ports.vector_store import ScoredRecord


class SQLiteFTS5Store:
    def __init__(self, session: Session):
        self.session = session
        self._ensure_table()

    def _ensure_table(self) -> None:
        ddl = """
        CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(
            chunk_id UNINDEXED,
            project_id UNINDEXED,
            revision_id UNINDEXED,
            text,
            tokenize = 'unicode61'
        );
        """
        self.session.execute(text(ddl))
        self.session.flush()

    def index_chunks(
        self,
        project_id: str,
        revision_id: str,
        chunks: Sequence[Chunk],
    ) -> None:
        if not chunks:
            return

        insert_sql = """
        INSERT INTO fts_chunks (chunk_id, project_id, revision_id, text)
        VALUES (:chunk_id, :project_id, :revision_id, :text)
        """
        for chunk in chunks:
            self.session.execute(
                text(insert_sql),
                {
                    "chunk_id": chunk.id,
                    "project_id": project_id,
                    "revision_id": revision_id,
                    "text": chunk.text,
                },
            )
        self.session.flush()

    def search(
        self,
        project_id: str,
        revision_id: str,
        query: str,
        top_k: int = 10,
    ) -> list[ScoredRecord]:
        # Escape FTS5 special characters
        clean_query = query.replace('"', '""').replace("'", "''").strip()
        if not clean_query:
            return []

        search_sql = """
        SELECT chunk_id, text, bm25(fts_chunks) AS rank
        FROM fts_chunks
        WHERE fts_chunks MATCH :match_query AND revision_id = :rev
        ORDER BY rank
        LIMIT :top_k
        """
        import re
        tokens = re.findall(r"\w+", clean_query)
        if not tokens:
            return []

        # If user explicitly surrounded with quotes, do exact phrase match
        trimmed = query.strip()
        if trimmed.startswith('"') and trimmed.endswith('"') and len(trimmed) > 2:
            inner = trimmed[1:-1].replace('"', '""')
            match_expr = f'"{inner}"'
        else:
            match_expr = " OR ".join(f'"{t}"*' for t in tokens)

        try:
            rows = self.session.execute(
                text(search_sql),
                {"match_query": match_expr, "rev": revision_id, "top_k": top_k},
            ).fetchall()
        except SQLAlchemyError:
            self.session.rollback()
            try:
                # Fallback if complex token search fails
                fallback_expr = " OR ".join(f'"{t}"' for t in tokens)
                rows = self.session.execute(
                    text(search_sql),
                    {"match_query": fallback_expr, "rev": revision_id, "top_k": top_k},
                ).fetchall()
            except SQLAlchemyError:
                self.session.rollback()
                return []

        results: list[ScoredRecord] = []
        for row in rows:
            # Convert negative BM25 score to normalized positive scale (0.0 to 1.0)
            bm25_val = float(row[2])
            norm_score = 1.0 / (1.0 + abs(bm25_val))
            results.append(
                ScoredRecord(
                    chunk_id=row[0],
                    document_id="",
                    score=norm_score,
                    text=row[1],
                )
            )

        return results

    def delete_revision(self, project_id: str, revision_id: str) -> None:
        delete_sql = "DELETE FROM fts_chunks WHERE revision_id = :rev"
        self.session.execute(text(delete_sql), {"rev": revision_id})
        self.session.flush()
