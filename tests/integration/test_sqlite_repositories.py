"""Integration tests for SQLite repositories, WAL mode and transactions."""

from sqlalchemy import text

from embedcraft.adapters.persistence.sqlite_job_repository import SQLiteJobRepository
from embedcraft.adapters.persistence.sqlite_project_repository import (
    SQLiteProjectRepository,
    SQLiteSourceRepository,
)
from embedcraft.domain.entities import Job, JobStep, Project, Source
from embedcraft.domain.value_objects import JobStatus, JobStepStatus


def test_sqlite_pragmas(test_db_manager):
    with test_db_manager.get_session() as session:
        journal_mode = session.execute(text("PRAGMA journal_mode;")).scalar()
        busy_timeout = session.execute(text("PRAGMA busy_timeout;")).scalar()
        foreign_keys = session.execute(text("PRAGMA foreign_keys;")).scalar()

        assert journal_mode.upper() == "WAL"
        assert busy_timeout == 30000
        assert foreign_keys == 1


def test_project_repository_crud(test_db_manager):
    with test_db_manager.get_session() as session:
        repo = SQLiteProjectRepository(session)
        project = Project(name="Test Repo Project", description="Testing SQLite CRUD")
        created = repo.create(project)

        assert created.id == project.id
        fetched = repo.get_by_id(project.id)
        assert fetched is not None
        assert fetched.name == "Test Repo Project"

        fetched_by_name = repo.get_by_name("Test Repo Project")
        assert fetched_by_name is not None
        assert fetched_by_name.id == project.id

        # Update
        fetched.description = "Updated description"
        repo.update(fetched)

    # Verify in new session
    with test_db_manager.get_session() as session:
        repo = SQLiteProjectRepository(session)
        updated = repo.get_by_id(project.id)
        assert updated.description == "Updated description"

        # Delete
        assert repo.delete(project.id) is True
        assert repo.get_by_id(project.id) is None


def test_source_repository_crud(test_db_manager):
    with test_db_manager.get_session() as session:
        proj_repo = SQLiteProjectRepository(session)
        source_repo = SQLiteSourceRepository(session)

        project = proj_repo.create(Project(name="Source Test Proj"))
        source = Source(
            project_id=project.id,
            name="Manuals",
            uri_or_path="C:/docs/manuals",
            recursive=True,
        )
        created_source = source_repo.add(source)
        assert created_source.id == source.id

        sources = source_repo.list_by_project(project.id)
        assert len(sources) == 1
        assert sources[0].name == "Manuals"


def test_job_repository_steps_and_recovery(test_db_manager):
    with test_db_manager.get_session() as session:
        proj_repo = SQLiteProjectRepository(session)
        job_repo = SQLiteJobRepository(session)

        project = proj_repo.create(Project(name="Job Test Proj"))
        step1 = JobStep(job_id="dummy", name="Scan", step_order=1, items_total=10)
        step2 = JobStep(job_id="dummy", name="Ingest", step_order=2, items_total=10)

        job = Job(
            project_id=project.id,
            job_type="scan_and_ingest",
            status=JobStatus.RUNNING,
            steps=[step1, step2],
            checkpoint_data={"last_scanned_index": 5},
        )
        created_job = job_repo.create(job)
        assert len(created_job.steps) == 2

    # Update job status and checkpoint simulation (restarting/recovery)
    with test_db_manager.get_session() as session:
        job_repo = SQLiteJobRepository(session)
        retrieved = job_repo.get_by_id(created_job.id)
        assert retrieved is not None
        assert retrieved.status == JobStatus.RUNNING
        assert retrieved.checkpoint_data["last_scanned_index"] == 5

        # Update step
        retrieved.steps[0].status = JobStepStatus.COMPLETED
        retrieved.steps[0].items_processed = 10
        retrieved.checkpoint_data["last_scanned_index"] = 10
        job_repo.update(retrieved)

    with test_db_manager.get_session() as session:
        job_repo = SQLiteJobRepository(session)
        updated = job_repo.get_by_id(created_job.id)
        assert updated.steps[0].status == JobStepStatus.COMPLETED
        assert updated.steps[0].items_processed == 10
        assert updated.checkpoint_data["last_scanned_index"] == 10
