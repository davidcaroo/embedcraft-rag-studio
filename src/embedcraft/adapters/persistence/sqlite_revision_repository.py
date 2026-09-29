"""SQLite implementation for Collection and IndexRevision persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from embedcraft.domain.entities import Collection, IndexRevision
from embedcraft.domain.value_objects import DistanceMetric, RevisionStatus
from embedcraft.infrastructure.database.models import CollectionModel, IndexRevisionModel


class SQLiteCollectionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, collection: Collection) -> Collection:
        model = CollectionModel(
            id=collection.id,
            project_id=collection.project_id,
            name=collection.name,
            description=collection.description,
            embedding_model=collection.embedding_model,
            dimension=collection.dimension,
            distance_metric=collection.distance_metric.value,
            vector_store_type=collection.vector_store_type,
            created_at=collection.created_at,
            updated_at=collection.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return collection

    def get_by_id(self, collection_id: str) -> Collection | None:
        model = self.session.query(CollectionModel).filter_by(id=collection_id).first()
        if not model:
            return None
        return self._to_entity(model)

    def get_by_name(self, project_id: str, name: str) -> Collection | None:
        model = (
            self.session.query(CollectionModel)
            .filter_by(project_id=project_id, name=name)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def list_by_project(self, project_id: str) -> list[Collection]:
        models = (
            self.session.query(CollectionModel)
            .filter_by(project_id=project_id)
            .order_by(CollectionModel.created_at.asc())
            .all()
        )
        return [self._to_entity(m) for m in models]

    def delete(self, collection_id: str) -> bool:
        model = self.session.query(CollectionModel).filter_by(id=collection_id).first()
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def _to_entity(self, m: CollectionModel) -> Collection:
        return Collection(
            id=m.id,
            project_id=m.project_id,
            name=m.name,
            description=m.description or "",
            embedding_model=m.embedding_model,
            dimension=m.dimension,
            distance_metric=DistanceMetric(m.distance_metric),
            vector_store_type=m.vector_store_type,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )


class SQLiteRevisionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, revision: IndexRevision) -> IndexRevision:
        model = IndexRevisionModel(
            id=revision.id,
            project_id=revision.project_id,
            revision_number=revision.revision_number,
            status=revision.status.value,
            embedding_model=revision.embedding_model,
            dimension=revision.dimension,
            total_documents=revision.total_documents,
            total_chunks=revision.total_chunks,
            staging_path=revision.staging_path,
            active_path=revision.active_path,
            published_at=revision.published_at,
            created_at=revision.created_at,
            updated_at=revision.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return revision

    def get_by_id(self, revision_id: str) -> IndexRevision | None:
        model = self.session.query(IndexRevisionModel).filter_by(id=revision_id).first()
        if not model:
            return None
        return self._to_entity(model)

    def list_by_project(self, project_id: str) -> list[IndexRevision]:
        models = (
            self.session.query(IndexRevisionModel)
            .filter_by(project_id=project_id)
            .order_by(IndexRevisionModel.revision_number.desc())
            .all()
        )
        return [self._to_entity(m) for m in models]

    def get_latest_active(self, project_id: str) -> IndexRevision | None:
        model = (
            self.session.query(IndexRevisionModel)
            .filter_by(project_id=project_id, status=RevisionStatus.ACTIVE.value)
            .order_by(IndexRevisionModel.revision_number.desc())
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def update(self, revision: IndexRevision) -> IndexRevision:
        model = self.session.query(IndexRevisionModel).filter_by(id=revision.id).first()
        if model:
            model.status = revision.status.value
            model.total_documents = revision.total_documents
            model.total_chunks = revision.total_chunks
            model.staging_path = revision.staging_path
            model.active_path = revision.active_path
            model.published_at = revision.published_at
            model.updated_at = datetime.now(UTC)
            self.session.flush()
        return revision

    def _to_entity(self, m: IndexRevisionModel) -> IndexRevision:
        return IndexRevision(
            id=m.id,
            project_id=m.project_id,
            revision_number=m.revision_number,
            status=RevisionStatus(m.status),
            embedding_model=m.embedding_model,
            dimension=m.dimension,
            total_documents=m.total_documents or 0,
            total_chunks=m.total_chunks or 0,
            staging_path=m.staging_path or "",
            active_path=m.active_path or "",
            published_at=m.published_at,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
