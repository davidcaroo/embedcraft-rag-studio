"""Test configuration and shared fixtures."""

import tempfile
from pathlib import Path

import pytest

from embedcraft.bootstrap.container import Container
from embedcraft.infrastructure.database.connection import DatabaseManager


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def test_db_manager(temp_dir):
    db_file = temp_dir / "test_embedcraft.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    mgr = DatabaseManager(db_url=db_url)
    mgr.init_schema()
    yield mgr
    mgr.close()


@pytest.fixture
def test_container(test_db_manager):
    return Container(db=test_db_manager)
