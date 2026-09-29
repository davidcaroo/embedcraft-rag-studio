"""Application service for Project and Source management."""

from __future__ import annotations

from pathlib import Path

from embedcraft.domain.entities import Project, Source
from embedcraft.domain.exceptions import ConfigurationError
from embedcraft.infrastructure.settings import settings
from embedcraft.ports.repositories import ProjectRepository, SourceRepository


class ProjectService:
    def __init__(self, project_repo: ProjectRepository, source_repo: SourceRepository):
        self.project_repo = project_repo
        self.source_repo = source_repo

    def create_project(self, name: str, description: str = "") -> Project:
        existing = self.project_repo.get_by_name(name)
        if existing:
            raise ConfigurationError(
                message=f"El proyecto con nombre '{name}' ya existe.",
                technical_detail=f"Duplicate project name conflict: {name}",
            )

        storage_path = str(settings.projects_dir / name)
        Path(storage_path).mkdir(parents=True, exist_ok=True)

        project = Project(
            name=name,
            description=description,
            storage_path=storage_path,
        )
        return self.project_repo.create(project)

    def get_project(self, identifier: str) -> Project | None:
        # Try by id first, then name
        proj = self.project_repo.get_by_id(identifier)
        if not proj:
            proj = self.project_repo.get_by_name(identifier)
        return proj

    def list_projects(self) -> list[Project]:
        return self.project_repo.list_all()

    def delete_project(self, identifier: str) -> bool:
        proj = self.get_project(identifier)
        if not proj:
            return False
        return self.project_repo.delete(proj.id)

    def add_source(
        self,
        project_identifier: str,
        path_or_uri: str,
        name: str | None = None,
        recursive: bool = True,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> Source:
        proj = self.get_project(project_identifier)
        if not proj:
            raise ConfigurationError(
                message=f"No se encontró el proyecto '{project_identifier}'.",
                technical_detail=f"Project not found: {project_identifier}",
            )

        p = Path(path_or_uri)
        source_name = name or p.name or "source"
        source = Source(
            project_id=proj.id,
            name=source_name,
            uri_or_path=str(p.resolve() if p.exists() else path_or_uri),
            recursive=recursive,
            include_patterns=include_patterns or ["*.*"],
            exclude_patterns=exclude_patterns or [],
        )
        return self.source_repo.add(source)

    def list_sources(self, project_identifier: str) -> list[Source]:
        proj = self.get_project(project_identifier)
        if not proj:
            raise ConfigurationError(
                message=f"No se encontró el proyecto '{project_identifier}'.",
            )
        return self.source_repo.list_by_project(proj.id)
