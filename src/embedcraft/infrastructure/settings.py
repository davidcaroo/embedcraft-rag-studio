"""Application settings and path resolution for EmbedCraft RAG Studio.

Adheres to Windows standards: %LOCALAPPDATA%/EmbedCraft and %APPDATA%/EmbedCraft.
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings


def get_default_base_dir() -> Path:
    # Use LOCALAPPDATA on Windows, fallback to ~/.embedcraft
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        base = Path(local_app_data) / "EmbedCraft"
    else:
        base = Path.home() / ".embedcraft"
    base.mkdir(parents=True, exist_ok=True)
    return base


class Settings(BaseSettings):
    app_name: str = "EmbedCraft RAG Studio"
    version: str = "0.1.0"
    base_dir: Path = get_default_base_dir()
    db_filename: str = "embedcraft.db"
    log_filename: str = "embedcraft.log"
    offline_mode: bool = False
    telemetry_enabled: bool = False

    @property
    def database_path(self) -> Path:
        return self.base_dir / self.db_filename

    @property
    def database_url(self) -> str:
        # SQLite URL with forward slashes
        return f"sqlite:///{self.database_path.as_posix()}"

    @property
    def logs_dir(self) -> Path:
        path = self.base_dir / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def log_path(self) -> Path:
        return self.logs_dir / self.log_filename

    @property
    def models_cache_dir(self) -> Path:
        path = self.base_dir / "models"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def projects_dir(self) -> Path:
        path = self.base_dir / "projects"
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
