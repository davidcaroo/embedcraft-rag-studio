"""Integration tests for IndexingService revision lifecycle and rollbacks."""

from datetime import UTC, datetime
from pathlib import Path

from embedcraft.adapters.embeddings.mock_provider import MockEmbeddingProvider
from embedcraft.adapters.vector_stores.memory_store import MemoryVectorStore
from embedcraft.bootstrap.container import Container
from embedcraft.domain.entities import Chunk, Document, DocumentVersion, Project, Source
from embedcraft.domain.value_objects import ChunkMetadata, DocumentStatus, RevisionStatus


def test_indexing_service_publish_and_rollback(test_db_manager, temp_dir: Path):
    container = Container(
        db=test_db_manager,
        vector_store=MemoryVectorStore(),
        embedding_provider=MockEmbeddingProvider(dimension=8),
    )

    with container.get_session() as session:
        proj_repo = container.get_project_repository(session)
        source_repo = container.get_source_repository(session)
        doc_repo = container.get_document_repository(session)
        indexing_svc = container.get_indexing_service(session)

        # 1. Setup project & source
        project = proj_repo.create(Project(name="Test Indexing Project", description="Testing revisions"))
        source = source_repo.add(
            Source(
                project_id=project.id,
                name="TestSrc",
                uri_or_path="C:/docs",
            )
        )

        # 2. Add documents and chunks
        doc = Document(
            project_id=project.id,
            source_id=source.id,
            relative_path="docs/guide.txt",
            mime_type="text/plain",
            size_bytes=1024,
            modified_at=datetime.now(UTC),
            file_hash="hash-123",
            status=DocumentStatus.NEW,
        )
        doc = doc_repo.upsert(doc)

        v1 = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            content_hash="hash123",
            normalized_text_hash="norm123",
            canonical_text="EmbedCraft provides full local RAG pipeline with high performance.",
        )
        chunks = [
            Chunk(
                document_id=doc.id,
                document_version_id=v1.id,
                chunk_index=0,
                chunk_hash="chunkhash_1",
                text="EmbedCraft provides full local RAG pipeline with high performance.",
                metadata=ChunkMetadata(source_uri="C:/docs/guide.txt", section="Intro"),
            ),
            Chunk(
                document_id=doc.id,
                document_version_id=v1.id,
                chunk_index=1,
                chunk_hash="chunkhash_2",
                text="Hybrid search blends BM25 lexical ranking and cosine vector similarity.",
                metadata=ChunkMetadata(source_uri="C:/docs/guide.txt", section="Search"),
            ),
        ]
        doc_repo.save_version_with_chunks(v1, chunks)
        session.commit()

        # 3. Publish first revision
        rev1 = indexing_svc.create_and_publish_revision(
            project_identifier=project.id,
            collection_name="default",
        )
        session.commit()

        assert rev1.status == RevisionStatus.ACTIVE
        assert rev1.revision_number == 1
        assert rev1.total_chunks == 2

        # Verify project active revision
        refreshed_proj = proj_repo.get_by_id(project.id)
        assert refreshed_proj.active_revision_id == rev1.id

        # 4. Publish second revision
        rev2 = indexing_svc.create_and_publish_revision(
            project_identifier=project.id,
            collection_name="default",
        )
        session.commit()

        assert rev2.status == RevisionStatus.ACTIVE
        assert rev2.revision_number == 2

        refreshed_proj2 = proj_repo.get_by_id(project.id)
        assert refreshed_proj2.active_revision_id == rev2.id

        # 5. Rollback to rev1
        rolled_back = indexing_svc.rollback_revision(project.id, rev1.id)
        session.commit()

        assert rolled_back.id == rev1.id
        refreshed_proj3 = proj_repo.get_by_id(project.id)
        assert refreshed_proj3.active_revision_id == rev1.id
