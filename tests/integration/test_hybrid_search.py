"""Integration tests for semantic, lexical, and hybrid search with citations."""

from datetime import UTC, datetime

from embedcraft.adapters.embeddings.mock_provider import MockEmbeddingProvider
from embedcraft.adapters.vector_stores.memory_store import MemoryVectorStore
from embedcraft.bootstrap.container import Container
from embedcraft.domain.entities import Chunk, Document, DocumentVersion, Project, Source
from embedcraft.domain.value_objects import ChunkMetadata, DocumentStatus, SearchMode


def test_hybrid_search_retrieval_and_citations(test_db_manager):
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

        # 1. Project & Source
        proj = proj_repo.create(Project(name="Search Test Project"))
        src = source_repo.add(
            Source(
                project_id=proj.id,
                name="ManualSource",
                uri_or_path="C:/documents",
            )
        )

        # 2. Documents & Chunks
        doc = Document(
            project_id=proj.id,
            source_id=src.id,
            relative_path="manual.pdf",
            mime_type="application/pdf",
            size_bytes=2048,
            modified_at=datetime.now(UTC),
            file_hash="man_hash_1",
            status=DocumentStatus.NEW,
        )
        doc = doc_repo.upsert(doc)

        ver = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            content_hash="man_hash_1",
            normalized_text_hash="norm_man_1",
            canonical_text="Quantum computing leverages superposition. Relational databases rely on write-ahead logs.",
        )

        c1 = Chunk(
            document_id=doc.id,
            document_version_id=ver.id,
            chunk_index=0,
            chunk_hash="c_hash_1",
            text="Quantum computing leverages superposition and entanglement to solve hard problems.",
            metadata=ChunkMetadata(
                source_uri="C:/documents/manual.pdf",
                page=12,
                section="Quantum Theory",
            ),
        )
        c2 = Chunk(
            document_id=doc.id,
            document_version_id=ver.id,
            chunk_index=1,
            chunk_hash="c_hash_2",
            text="Standard relational databases rely on B-trees and write-ahead logs for ACID guarantees.",
            metadata=ChunkMetadata(
                source_uri="C:/documents/manual.pdf",
                page=45,
                section="Relational DBs",
            ),
        )

        doc_repo.save_version_with_chunks(ver, [c1, c2])
        session.commit()

        # 3. Publish Revision
        indexing_svc.create_and_publish_revision(proj.id)
        session.commit()

        # 4. Lexical Search
        lex_results = indexing_svc.search(
            project_identifier=proj.id,
            query="quantum superposition",
            mode=SearchMode.LEXICAL,
            top_k=2,
        )
        assert len(lex_results) >= 1
        assert "Quantum" in lex_results[0].text
        assert lex_results[0].citation.document_path == "manual.pdf"
        assert lex_results[0].citation.page == 12
        assert lex_results[0].citation.section == "Quantum Theory"

        # 5. Vector Search
        vec_results = indexing_svc.search(
            project_identifier=proj.id,
            query="quantum superposition",
            mode=SearchMode.VECTOR,
            top_k=2,
        )
        assert len(vec_results) == 2

        # 6. Hybrid Search (RRF)
        hybrid_results = indexing_svc.search(
            project_identifier=proj.id,
            query="relational databases write-ahead",
            mode=SearchMode.HYBRID,
            top_k=2,
        )
        assert len(hybrid_results) >= 1
        # The relational chunk should be retrieved
        assert any("relational databases" in r.text.lower() for r in hybrid_results)
