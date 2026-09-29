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
        import re

        clean_name = name.strip()
        if not clean_name or "/" in clean_name or "\\" in clean_name or ".." in clean_name:
            raise ConfigurationError(
                message=f"Nombre de proyecto inválido: '{name}'.",
                technical_detail="Project name cannot contain path separators or traversal sequences.",
            )

        if not re.match(r"^[\w\-. ]+$", clean_name):
            raise ConfigurationError(
                message=f"Nombre de proyecto inválido: '{name}'. Solo se permiten caracteres alfanuméricos, guiones y espacios.",
                technical_detail="Project name contains disallowed characters.",
            )

        target_dir = (settings.projects_dir / clean_name).resolve()
        base_dir = settings.projects_dir.resolve()
        if not target_dir.is_relative_to(base_dir):
            raise ConfigurationError(
                message=f"La ruta del proyecto '{name}' intenta escapar del directorio de almacenamiento.",
                technical_detail="Path traversal attempt detected in project name.",
            )

        existing = self.project_repo.get_by_name(clean_name)
        if existing:
            raise ConfigurationError(
                message=f"El proyecto con nombre '{clean_name}' ya existe.",
                technical_detail=f"Duplicate project name conflict: {clean_name}",
            )

        storage_path = str(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        project = Project(
            name=clean_name,
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
