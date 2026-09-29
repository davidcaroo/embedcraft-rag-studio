"""Dependency injection container / bootstrap composition root."""

from __future__ import annotations

from sqlalchemy.orm import Session

from embedcraft.adapters.embeddings.cache import SQLiteEmbeddingCache
from embedcraft.adapters.embeddings.mock_provider import MockEmbeddingProvider
from embedcraft.adapters.llm.mock_provider import MockLLMProvider
from embedcraft.adapters.persistence.sqlite_document_repository import SQLiteDocumentRepository
from embedcraft.adapters.persistence.sqlite_job_repository import SQLiteJobRepository
from embedcraft.adapters.persistence.sqlite_project_repository import (
    SQLiteProjectRepository,
    SQLiteSourceRepository,
)
from embedcraft.adapters.persistence.sqlite_revision_repository import (
    SQLiteCollectionRepository,
    SQLiteRevisionRepository,
)
from embedcraft.adapters.rerankers.scoring_reranker import LexicalScoringReranker
from embedcraft.adapters.secrets.keyring_secret_store import KeyringSecretStore
from embedcraft.adapters.vector_stores.lancedb_store import LanceDBVectorStore
from embedcraft.application.services.chat_service import ChatService
from embedcraft.application.services.export_service import ExportService
from embedcraft.application.services.import_service import ImportService
from embedcraft.application.services.indexing_service import IndexingService
from embedcraft.application.services.ingestion_service import IngestionService
from embedcraft.application.services.project_service import ProjectService
from embedcraft.application.services.system_service import SystemService
from embedcraft.infrastructure.database.connection import DatabaseManager, db_manager
from embedcraft.infrastructure.database.fts5_store import SQLiteFTS5Store
from embedcraft.ports.embeddings import EmbeddingProvider
from embedcraft.ports.llm import LLMProvider
from embedcraft.ports.reranker import RerankerProvider
from embedcraft.ports.vector_store import VectorStore


class Container:
    def __init__(
        self,
        db: DatabaseManager | None = None,
        vector_store: VectorStore | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        llm_provider: LLMProvider | None = None,
        reranker: RerankerProvider | None = None,
    ):
        self.db = db or db_manager
        self.db.init_schema()
        self.secret_store = KeyringSecretStore()
        self.system_service = SystemService()
        self.vector_store = vector_store or LanceDBVectorStore()
        self.embedding_provider = embedding_provider or MockEmbeddingProvider()
        self.llm_provider = llm_provider or MockLLMProvider()
        self.reranker = reranker or LexicalScoringReranker()

    def get_session(self):
        return self.db.get_session()

    def get_project_repository(self, session: Session) -> SQLiteProjectRepository:
        return SQLiteProjectRepository(session)

    def get_source_repository(self, session: Session) -> SQLiteSourceRepository:
        return SQLiteSourceRepository(session)

    def get_project_service(self, session: Session) -> ProjectService:
        project_repo = SQLiteProjectRepository(session)
        source_repo = SQLiteSourceRepository(session)
        return ProjectService(project_repo=project_repo, source_repo=source_repo)

    def get_document_repository(self, session: Session) -> SQLiteDocumentRepository:
        return SQLiteDocumentRepository(session)

    def get_job_repository(self, session: Session) -> SQLiteJobRepository:
        return SQLiteJobRepository(session)

    def get_collection_repository(self, session: Session) -> SQLiteCollectionRepository:
        return SQLiteCollectionRepository(session)

    def get_revision_repository(self, session: Session) -> SQLiteRevisionRepository:
        return SQLiteRevisionRepository(session)

    def get_ingestion_service(self, session: Session) -> IngestionService:
        project_repo = SQLiteProjectRepository(session)
        source_repo = SQLiteSourceRepository(session)
        doc_repo = SQLiteDocumentRepository(session)
        job_repo = SQLiteJobRepository(session)
        return IngestionService(
            project_repo=project_repo,
            source_repo=source_repo,
            document_repo=doc_repo,
            job_repo=job_repo,
        )

    def get_indexing_service(self, session: Session) -> IndexingService:
        project_repo = SQLiteProjectRepository(session)
        doc_repo = SQLiteDocumentRepository(session)
        col_repo = SQLiteCollectionRepository(session)
        rev_repo = SQLiteRevisionRepository(session)
        fts_store = SQLiteFTS5Store(session)
        cache = SQLiteEmbeddingCache(session)

        return IndexingService(
            project_repo=project_repo,
            document_repo=doc_repo,
            collection_repo=col_repo,
            revision_repo=rev_repo,
            vector_store=self.vector_store,
            fts_store=fts_store,
            embedding_provider=self.embedding_provider,
            embedding_cache=cache,
        )

    def get_chat_service(self, session: Session) -> ChatService:
        indexing_svc = self.get_indexing_service(session)
        return ChatService(
            indexing_service=indexing_svc,
            llm_provider=self.llm_provider,
            reranker=self.reranker,
        )

    def get_export_service(self, session: Session) -> ExportService:
        proj_repo = SQLiteProjectRepository(session)
        doc_repo = SQLiteDocumentRepository(session)
        coll_repo = SQLiteCollectionRepository(session)
        return ExportService(
            project_repo=proj_repo,
            document_repo=doc_repo,
            collection_repo=coll_repo,
            vector_store=self.vector_store,
        )

    def get_import_service(self, session: Session) -> ImportService:
        proj_repo = SQLiteProjectRepository(session)
        doc_repo = SQLiteDocumentRepository(session)
        coll_repo = SQLiteCollectionRepository(session)
        fts5_store = SQLiteFTS5Store(session)
        return ImportService(
            project_repo=proj_repo,
            document_repo=doc_repo,
            collection_repo=coll_repo,
            vector_store=self.vector_store,
            fts5_store=fts5_store,
        )


# Global container instance
container = Container()
