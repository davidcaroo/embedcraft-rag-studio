"""SQLite implementation for Document, DocumentVersion, and Chunk persistence."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from embedcraft.domain.entities import Chunk, Document, DocumentVersion
from embedcraft.domain.value_objects import ChunkMetadata, DocumentStatus
from embedcraft.infrastructure.database.models import (
    ChunkModel,
    DocumentModel,
    DocumentVersionModel,
)


class SQLiteDocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, document: Document) -> Document:
        model = self.session.query(DocumentModel).filter_by(id=document.id).first()
        if not model:
            # Check by path within project
            model = (
                self.session.query(DocumentModel)
                .filter_by(project_id=document.project_id, relative_path=document.relative_path)
                .first()
            )

        if not model:
            model = DocumentModel(
                id=document.id,
                project_id=document.project_id,
                source_id=document.source_id,
                relative_path=document.relative_path,
                mime_type=document.mime_type,
                size_bytes=document.size_bytes,
                modified_at=document.modified_at,
                file_hash=document.file_hash,
                status=document.status.value,
                error_message=document.error_message,
                custom_metadata_json=document.custom_metadata,
                created_at=document.created_at,
                updated_at=document.updated_at,
            )
            self.session.add(model)
        else:
            model.source_id = document.source_id
            model.mime_type = document.mime_type
            model.size_bytes = document.size_bytes
            model.modified_at = document.modified_at
            model.file_hash = document.file_hash
            model.status = document.status.value
            model.error_message = document.error_message
            model.custom_metadata_json = document.custom_metadata
            model.updated_at = datetime.now(UTC)
            document.id = model.id

        self.session.flush()
        return document

    def get_by_id(self, document_id: str) -> Document | None:
        model = self.session.query(DocumentModel).filter_by(id=document_id).first()
        if not model:
            return None
        return self._to_document_entity(model)

    def get_by_path(self, project_id: str, relative_path: str) -> Document | None:
        model = (
            self.session.query(DocumentModel)
            .filter_by(project_id=project_id, relative_path=relative_path)
            .first()
        )
        if not model:
            return None
        return self._to_document_entity(model)

    def list_by_project(self, project_id: str, limit: int = 100, offset: int = 0) -> list[Document]:
        models = (
            self.session.query(DocumentModel)
            .filter_by(project_id=project_id)
            .order_by(DocumentModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_document_entity(m) for m in models]

    def count_by_project(self, project_id: str) -> int:
        return self.session.query(DocumentModel).filter_by(project_id=project_id).count()

    def delete(self, document_id: str) -> bool:
        model = self.session.query(DocumentModel).filter_by(id=document_id).first()
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def save_version_with_chunks(
        self,
        version: DocumentVersion,
        chunks: Sequence[Chunk],
    ) -> DocumentVersion:
        v_model = DocumentVersionModel(
            id=version.id,
            document_id=version.document_id,
            version_number=version.version_number,
            content_hash=version.content_hash,
            normalized_text_hash=version.normalized_text_hash,
            canonical_text=version.canonical_text,
            chunk_count=len(chunks),
            created_at=version.created_at,
            updated_at=version.updated_at,
        )
        self.session.add(v_model)

        for chunk in chunks:
            c_model = ChunkModel(
                id=chunk.id,
                document_id=chunk.document_id,
                document_version_id=version.id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                chunk_hash=chunk.chunk_hash,
                metadata_json=chunk.metadata.model_dump(),
                token_count=chunk.token_count,
                strategy_version=chunk.strategy_version,
                created_at=chunk.created_at,
                updated_at=chunk.updated_at,
            )
            self.session.add(c_model)

        self.session.flush()
        version.chunk_count = len(chunks)
        return version

    def get_latest_version(self, document_id: str) -> DocumentVersion | None:
        model = (
            self.session.query(DocumentVersionModel)
            .filter_by(document_id=document_id)
            .order_by(DocumentVersionModel.version_number.desc())
            .first()
        )
        if not model:
            return None
        return DocumentVersion(
            id=model.id,
            document_id=model.document_id,
            version_number=model.version_number,
            content_hash=model.content_hash,
            normalized_text_hash=model.normalized_text_hash,
            canonical_text=model.canonical_text or "",
            chunk_count=model.chunk_count or 0,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_chunks_for_version(self, version_id: str) -> list[Chunk]:
        models = (
            self.session.query(ChunkModel)
            .filter_by(document_version_id=version_id)
            .order_by(ChunkModel.chunk_index.asc())
            .all()
        )
        return [
            Chunk(
                id=m.id,
                document_id=m.document_id,
                document_version_id=m.document_version_id,
                chunk_index=m.chunk_index,
                text=m.text,
                chunk_hash=m.chunk_hash,
                metadata=ChunkMetadata(**(m.metadata_json or {})),
                token_count=m.token_count or 0,
                strategy_version=m.strategy_version or "v1",
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    def get_chunk_by_id(self, chunk_id: str) -> Chunk | None:
        m = self.session.query(ChunkModel).filter_by(id=chunk_id).first()
        if not m:
            return None
        return Chunk(
            id=m.id,
            document_id=m.document_id,
            document_version_id=m.document_version_id,
            chunk_index=m.chunk_index,
            text=m.text,
            chunk_hash=m.chunk_hash,
            metadata=ChunkMetadata(**(m.metadata_json or {})),
            token_count=m.token_count or 0,
            strategy_version=m.strategy_version or "v1",
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def _to_document_entity(self, model: DocumentModel) -> Document:
        return Document(
            id=model.id,
            project_id=model.project_id,
            source_id=model.source_id,
            relative_path=model.relative_path,
            mime_type=model.mime_type,
            size_bytes=model.size_bytes or 0,
            modified_at=model.modified_at,
            file_hash=model.file_hash,
            status=DocumentStatus(model.status),
            error_message=model.error_message,
            custom_metadata=model.custom_metadata_json or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
