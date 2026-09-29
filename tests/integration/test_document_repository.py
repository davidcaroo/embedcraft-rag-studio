"""Integration tests for SQLiteDocumentRepository."""

from datetime import UTC, datetime

from embedcraft.adapters.persistence.sqlite_document_repository import SQLiteDocumentRepository
from embedcraft.adapters.persistence.sqlite_project_repository import (
    SQLiteProjectRepository,
    SQLiteSourceRepository,
)
from embedcraft.domain.entities import Chunk, Document, DocumentVersion, Project, Source
from embedcraft.domain.value_objects import ChunkMetadata, DocumentStatus


def test_document_repository_lifecycle(test_db_manager):
    with test_db_manager.get_session() as session:
        proj_repo = SQLiteProjectRepository(session)
        source_repo = SQLiteSourceRepository(session)
        doc_repo = SQLiteDocumentRepository(session)

        proj = proj_repo.create(Project(name="Doc Repo Proj"))
        src = source_repo.add(
            Source(
                project_id=proj.id,
                name="TestSrc",
                uri_or_path="C:/docs",
            )
        )

        doc = Document(
            project_id=proj.id,
            source_id=src.id,
            relative_path="docs/guide.txt",
            mime_type="text/plain",
            size_bytes=1024,
            modified_at=datetime.now(UTC),
            file_hash="hash-123",
            status=DocumentStatus.NEW,
        )
        saved = doc_repo.upsert(doc)
        assert saved.id == doc.id

        # Query by path
        by_path = doc_repo.get_by_path(proj.id, "docs/guide.txt")
        assert by_path is not None
        assert by_path.id == doc.id

        # Save version with chunks
        v1 = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            content_hash="hash-123",
            normalized_text_hash="norm-123",
            canonical_text="Hello world guide",
        )
        chunks = [
            Chunk(
                document_id=doc.id,
                document_version_id=v1.id,
                chunk_index=0,
                text="Hello world",
                chunk_hash="c1-hash",
                metadata=ChunkMetadata(section="Intro"),
            ),
            Chunk(
                document_id=doc.id,
                document_version_id=v1.id,
                chunk_index=1,
                text="guide",
                chunk_hash="c2-hash",
                metadata=ChunkMetadata(section="Body"),
            ),
        ]
        doc_repo.save_version_with_chunks(v1, chunks)

    # Verify in new session
    with test_db_manager.get_session() as session:
        doc_repo = SQLiteDocumentRepository(session)
        latest_ver = doc_repo.get_latest_version(doc.id)
        assert latest_ver is not None
        assert latest_ver.version_number == 1
        assert latest_ver.chunk_count == 2

        retrieved_chunks = doc_repo.get_chunks_for_version(latest_ver.id)
        assert len(retrieved_chunks) == 2
        assert retrieved_chunks[0].text == "Hello world"
        assert retrieved_chunks[1].text == "guide"
