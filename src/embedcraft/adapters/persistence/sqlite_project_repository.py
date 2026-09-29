"""SQLite implementation of Project, Source, and Document repositories."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from embedcraft.domain.entities import Project, Source
from embedcraft.infrastructure.database.models import ProjectModel, SourceModel


class SQLiteProjectRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, project: Project) -> Project:
        model = ProjectModel(
            id=project.id,
            name=project.name,
            description=project.description,
            storage_path=project.storage_path,
            active_revision_id=project.active_revision_id,
            metadata_json=project.metadata,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return project

    def get_by_id(self, project_id: str) -> Project | None:
        model = self.session.query(ProjectModel).filter_by(id=project_id).first()
        if not model:
            return None
        return self._to_entity(model)

    def get_by_name(self, name: str) -> Project | None:
        model = self.session.query(ProjectModel).filter_by(name=name).first()
        if not model:
            return None
        return self._to_entity(model)

    def list_all(self) -> list[Project]:
        models = self.session.query(ProjectModel).order_by(ProjectModel.created_at.desc()).all()
        return [self._to_entity(m) for m in models]

    def update(self, project: Project) -> Project:
        model = self.session.query(ProjectModel).filter_by(id=project.id).first()
        if model:
            model.name = project.name
            model.description = project.description
            model.storage_path = project.storage_path
            model.active_revision_id = project.active_revision_id
            model.metadata_json = project.metadata
            model.updated_at = datetime.now(UTC)
            self.session.flush()
        return project

    def delete(self, project_id: str) -> bool:
        model = self.session.query(ProjectModel).filter_by(id=project_id).first()
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def _to_entity(self, model: ProjectModel) -> Project:
        return Project(
            id=model.id,
            name=model.name,
            description=model.description or "",
            storage_path=model.storage_path or "",
            active_revision_id=model.active_revision_id,
            metadata=model.metadata_json or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SQLiteSourceRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, source: Source) -> Source:
        model = SourceModel(
            id=source.id,
            project_id=source.project_id,
            name=source.name,
            uri_or_path=source.uri_or_path,
            source_type=source.source_type,
            enabled=source.enabled,
            recursive=source.recursive,
            include_patterns_json=source.include_patterns,
            exclude_patterns_json=source.exclude_patterns,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return source

    def get_by_id(self, source_id: str) -> Source | None:
        model = self.session.query(SourceModel).filter_by(id=source_id).first()
        if not model:
            return None
        return Source(
            id=model.id,
            project_id=model.project_id,
            name=model.name,
            uri_or_path=model.uri_or_path,
            source_type=model.source_type,
            enabled=model.enabled,
            recursive=model.recursive,
            include_patterns=model.include_patterns_json or ["*.*"],
            exclude_patterns=model.exclude_patterns_json or [],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def list_by_project(self, project_id: str) -> list[Source]:
        models = self.session.query(SourceModel).filter_by(project_id=project_id).all()
        return [
            Source(
                id=m.id,
                project_id=m.project_id,
                name=m.name,
                uri_or_path=m.uri_or_path,
                source_type=m.source_type,
                enabled=m.enabled,
                recursive=m.recursive,
                include_patterns=m.include_patterns_json or ["*.*"],
                exclude_patterns=m.exclude_patterns_json or [],
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    def delete(self, source_id: str) -> bool:
        model = self.session.query(SourceModel).filter_by(id=source_id).first()
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False
