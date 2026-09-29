"""Dependency injection container / bootstrap composition root."""

from __future__ import annotations

from sqlalchemy.orm import Session

from embedcraft.adapters.persistence.sqlite_job_repository import SQLiteJobRepository
from embedcraft.adapters.persistence.sqlite_project_repository import (
    SQLiteProjectRepository,
    SQLiteSourceRepository,
)
from embedcraft.adapters.secrets.keyring_secret_store import KeyringSecretStore
from embedcraft.application.services.project_service import ProjectService
from embedcraft.application.services.system_service import SystemService
from embedcraft.infrastructure.database.connection import DatabaseManager, db_manager


class Container:
    def __init__(self, db: DatabaseManager | None = None):
        self.db = db or db_manager
        self.db.init_schema()
        self.secret_store = KeyringSecretStore()
        self.system_service = SystemService()

    def get_session(self):
        return self.db.get_session()

    def get_project_service(self, session: Session) -> ProjectService:
        project_repo = SQLiteProjectRepository(session)
        source_repo = SQLiteSourceRepository(session)
        return ProjectService(project_repo=project_repo, source_repo=source_repo)

    def get_job_repository(self, session: Session) -> SQLiteJobRepository:
        return SQLiteJobRepository(session)


# Global container instance
container = Container()
