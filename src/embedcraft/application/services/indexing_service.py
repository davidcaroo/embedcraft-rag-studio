"""Application service for atomic revision publication, vector indexing, and hybrid search."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from embedcraft.adapters.embeddings.cache import SQLiteEmbeddingCache
from embedcraft.domain.entities import (
    Citation,
    IndexRevision,
    RetrievalResult,
)
from embedcraft.domain.exceptions import ConfigurationError, VectorStoreError
from embedcraft.domain.value_objects import RevisionStatus, SearchMode
from embedcraft.infrastructure.logging import logger
from embedcraft.ports.embeddings import EmbeddingProvider
from embedcraft.ports.lexical_store import LexicalSearchStore
from embedcraft.ports.repositories import (
    CollectionRepository,
    DocumentRepository,
    ProjectRepository,
    RevisionRepository,
)
from embedcraft.ports.vector_store import ScoredRecord, VectorRecord, VectorStore


class IndexingProgress(BaseModel):
    revision_id: str
    total_chunks: int
    processed_chunks: int
    cached_chunks: int
    status: RevisionStatus


class IndexingService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        document_repo: DocumentRepository,
        collection_repo: CollectionRepository,
        revision_repo: RevisionRepository,
        vector_store: VectorStore,
        fts_store: LexicalSearchStore,
        embedding_provider: EmbeddingProvider,
        embedding_cache: SQLiteEmbeddingCache,
    ):
        self.project_repo = project_repo
        self.document_repo = document_repo
        self.collection_repo = collection_repo
        self.revision_repo = revision_repo
        self.vector_store = vector_store
        self.fts_store = fts_store
        self.embedding_provider = embedding_provider
        self.cache = embedding_cache

    def create_and_publish_revision(
        self,
        project_identifier: str,
        collection_name: str = "default",
        batch_size: int = 64,
    ) -> IndexRevision:
        """Create, index in staging, validate, and atomically activate a new index revision."""
        project = self.project_repo.get_by_id(project_identifier) or self.project_repo.get_by_name(project_identifier)
        if not project:
            raise ConfigurationError(f"Proyecto no encontrado: {project_identifier}")

        # Get or create collection
        collection = self.collection_repo.get_by_name(project.id, collection_name)
        if not collection:
            from embedcraft.domain.entities import Collection
            collection = self.collection_repo.create(
                Collection(
                    project_id=project.id,
                    name=collection_name,
                    embedding_model=self.embedding_provider.model_name,
                    dimension=self.embedding_provider.dimension,
                )
            )

        # 1. Gather all chunks from latest document versions
        documents = self.document_repo.list_by_project(project.id, limit=100000)
        all_chunks = []
        for doc in documents:
            latest_v = self.document_repo.get_latest_version(doc.id)
            if latest_v:
                chunks = self.document_repo.get_chunks_for_version(latest_v.id)
                all_chunks.extend(chunks)

        if not all_chunks:
            raise ConfigurationError("El proyecto no tiene documentos o fragmentos para indexar.")

        # Determine next revision number
        existing_revs = self.revision_repo.list_by_project(project.id)
        next_rev_num = (max(r.revision_number for r in existing_revs) + 1) if existing_revs else 1

        # 2. Create Revision in DRAFT state
        revision = IndexRevision(
            project_id=project.id,
            revision_number=next_rev_num,
            status=RevisionStatus.DRAFT,
            embedding_model=self.embedding_provider.model_name,
            dimension=self.embedding_provider.dimension,
            total_documents=len(documents),
            total_chunks=len(all_chunks),
            staging_path=f"staging_{project.id}_{next_rev_num}",
        )
        revision = self.revision_repo.create(revision)

        try:
            # 3. Transition to PROCESSING
            revision.status = RevisionStatus.PROCESSING
            self.revision_repo.update(revision)

            # Check cache for existing vector hashes
            chunk_hashes = [c.chunk_hash for c in all_chunks]
            cached_vectors = self.cache.get_many(
                chunk_hashes,
                model_name=self.embedding_provider.model_name,
                dimension=self.embedding_provider.dimension,
            )

            # Identify missing chunks to embed
            missing_chunks = [c for c in all_chunks if c.chunk_hash not in cached_vectors]
            if missing_chunks:
                logger.info("computing_embeddings", count=len(missing_chunks), model=self.embedding_provider.model_name)
                for i in range(0, len(missing_chunks), batch_size):
                    batch = missing_chunks[i : i + batch_size]
                    batch_texts = [c.text for c in batch]
                    batch_vectors = self.embedding_provider.embed_texts(batch_texts)

                    # Update cache
                    cache_items = [(c.chunk_hash, v) for c, v in zip(batch, batch_vectors)]
                    self.cache.set_many(
                        cache_items,
                        model_name=self.embedding_provider.model_name,
                        dimension=self.embedding_provider.dimension,
                    )
                    for c, v in zip(batch, batch_vectors):
                        cached_vectors[c.chunk_hash] = v

            # 4. Transition to STAGING & Write to Vector Store & FTS5
            revision.status = RevisionStatus.STAGING
            self.revision_repo.update(revision)

            records: list[VectorRecord] = []
            for c in all_chunks:
                vec = cached_vectors.get(c.chunk_hash)
                if vec:
                    records.append(
                        VectorRecord(
                            chunk_id=c.id,
                            document_id=c.document_id,
                            vector=vec,
                            text=c.text,
                            metadata=c.metadata.model_dump(),
                        )
                    )

            self.vector_store.create_collection_index(
                collection_id=collection.id,
                revision_id=revision.id,
                dimension=self.embedding_provider.dimension,
            )
            self.vector_store.upsert(
                collection_id=collection.id,
                revision_id=revision.id,
                records=records,
            )

            # Write to Lexical FTS5
            self.fts_store.index_chunks(
                project_id=project.id,
                revision_id=revision.id,
                chunks=all_chunks,
            )

            # 5. Transition to VALIDATING
            revision.status = RevisionStatus.VALIDATING
            self.revision_repo.update(revision)

            # Verification query
            test_results = self.vector_store.search(
                collection_id=collection.id,
                revision_id=revision.id,
                query_vector=records[0].vector,
                top_k=1,
            )
            if not test_results:
                raise VectorStoreError("Validación del índice falló: la consulta de prueba no arrojó resultados.")

            # 6. ATOMIC ACTIVATION
            revision.status = RevisionStatus.ACTIVE
            revision.published_at = datetime.now(UTC)
            revision.active_path = revision.staging_path
            self.revision_repo.update(revision)

            # Point project to new active revision
            project.active_revision_id = revision.id
            self.project_repo.update(project)
            logger.info("revision_published_successfully", revision_number=revision.revision_number)
            return revision

        except Exception as e:
            logger.exception("revision_indexing_failed", error=str(e))
            revision.status = RevisionStatus.FAILED
            self.revision_repo.update(revision)
            # Clean up staging index data
            self.vector_store.delete_revision(collection.id, revision.id)
            self.fts_store.delete_revision(project.id, revision.id)
            raise

    def rollback_revision(self, project_identifier: str, target_revision_id: str) -> IndexRevision:
        """Rollback project active revision to a previously verified active revision."""
        project = self.project_repo.get_by_id(project_identifier) or self.project_repo.get_by_name(project_identifier)
        if not project:
            raise ConfigurationError(f"Proyecto no encontrado: {project_identifier}")

        target_rev = self.revision_repo.get_by_id(target_revision_id)
        if not target_rev or target_rev.project_id != project.id:
            raise ConfigurationError(f"Revisión '{target_revision_id}' no pertenece al proyecto.")

        if target_rev.status != RevisionStatus.ACTIVE:
            raise ConfigurationError("Solo se puede hacer rollback a revisiones con estado ACTIVE.")

        project.active_revision_id = target_rev.id
        self.project_repo.update(project)
        return target_rev

    def search(
        self,
        project_identifier: str,
        query: str,
        collection_name: str = "default",
        mode: SearchMode = SearchMode.HYBRID,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Query RAG system across vector, lexical or hybrid search with full citation traceability."""
        project = self.project_repo.get_by_id(project_identifier) or self.project_repo.get_by_name(project_identifier)
        if not project:
            raise ConfigurationError(f"Proyecto no encontrado: {project_identifier}")

        if not project.active_revision_id:
            raise ConfigurationError("El proyecto no tiene una revisión de índice activa. Ejecute la publicación de índice primero.")

        collection = self.collection_repo.get_by_name(project.id, collection_name)
        if not collection:
            raise ConfigurationError(f"Colección '{collection_name}' no encontrada en el proyecto.")

        rev_id = project.active_revision_id

        # 1. Vector Search
        vector_results: list[ScoredRecord] = []
        if mode in (SearchMode.VECTOR, SearchMode.HYBRID):
            query_vector = self.embedding_provider.embed_query(query)
            vector_results = self.vector_store.search(
                collection_id=collection.id,
                revision_id=rev_id,
                query_vector=query_vector,
                top_k=top_k * 2,
            )

        # 2. Lexical Search (FTS5)
        lexical_results: list[ScoredRecord] = []
        if mode in (SearchMode.LEXICAL, SearchMode.HYBRID):
            lexical_results = self.fts_store.search(
                project_id=project.id,
                revision_id=rev_id,
                query=query,
                top_k=top_k * 2,
            )

        # 3. Score Fusion (Reciprocal Rank Fusion - RRF)
        scored_map: dict[str, float] = {}
        content_map: dict[str, ScoredRecord] = {}

        # RRF constant k=60
        K = 60.0
        if mode == SearchMode.HYBRID:
            for rank, r in enumerate(vector_results, start=1):
                scored_map[r.chunk_id] = scored_map.get(r.chunk_id, 0.0) + (1.0 / (K + rank))
                content_map[r.chunk_id] = r
            for rank, r in enumerate(lexical_results, start=1):
                scored_map[r.chunk_id] = scored_map.get(r.chunk_id, 0.0) + (1.0 / (K + rank))
                if r.chunk_id not in content_map:
                    content_map[r.chunk_id] = r
        elif mode == SearchMode.VECTOR:
            for r in vector_results:
                scored_map[r.chunk_id] = r.score
                content_map[r.chunk_id] = r
        else:  # LEXICAL
            for r in lexical_results:
                scored_map[r.chunk_id] = r.score
                content_map[r.chunk_id] = r

        # Sort descending by fused score
        sorted_chunks = sorted(scored_map.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # 4. Build traceable RetrievalResult with Citations
        retrieval_results: list[RetrievalResult] = []
        for chunk_id, score in sorted_chunks:
            rec = content_map[chunk_id]
            doc_id = rec.document_id
            meta = dict(rec.metadata)

            if not doc_id or not meta:
                chunk = self.document_repo.get_chunk_by_id(chunk_id)
                if chunk:
                    doc_id = chunk.document_id
                    if not meta:
                        meta = chunk.metadata.model_dump()

            doc = self.document_repo.get_by_id(doc_id) if doc_id else None

            doc_path = doc.relative_path if doc else "desconocido"
            doc_title = (doc.custom_metadata.get("title") if doc else None) or Path(doc_path).stem

            citation = Citation(
                document_id=doc_id or "",
                document_path=doc_path,
                document_title=doc_title,
                chunk_id=chunk_id,
                section=meta.get("section", ""),
                page=meta.get("page"),
                snippet=rec.text[:200],
            )

            retrieval_results.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    text=rec.text,
                    score=float(score),
                    collection_id=collection.id,
                    citation=citation,
                    metadata=meta,
                )
            )

        return retrieval_results
