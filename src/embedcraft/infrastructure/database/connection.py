"""SQLite database connection and session management with WAL mode and foreign keys enabled."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from embedcraft.infrastructure.database.models import Base
from embedcraft.infrastructure.settings import settings


def _enable_sqlite_features(dbapi_con, _):
    """Enable WAL mode, 30s busy timeout, and foreign keys on SQLite connection."""
    cursor = dbapi_con.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA busy_timeout=30000;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


class DatabaseManager:
    def __init__(self, db_url: str | None = None):
        self.url = db_url or settings.database_url
        self.engine = create_engine(
            self.url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
        if self.url.startswith("sqlite"):
            event.listen(self.engine, "connect", _enable_sqlite_features)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    def init_schema(self) -> None:
        """Create all tables in the database."""
        Base.metadata.create_all(self.engine)

    def close(self) -> None:
        """Dispose the engine and release SQLite file locks."""
        self.engine.dispose()

    @contextmanager
    def get_session(self) -> Generator[Session]:
        """Provide a transactional scope around a series of operations."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


db_manager = DatabaseManager()
