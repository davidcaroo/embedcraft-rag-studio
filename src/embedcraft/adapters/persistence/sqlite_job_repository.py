"""SQLite implementation of Job and JobStep persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from embedcraft.domain.entities import Job, JobStep
from embedcraft.domain.value_objects import JobStatus, JobStepStatus
from embedcraft.infrastructure.database.models import JobModel, JobStepModel


class SQLiteJobRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, job: Job) -> Job:
        job_model = JobModel(
            id=job.id,
            project_id=job.project_id,
            job_type=job.job_type,
            status=job.status.value,
            checkpoint_data_json=job.checkpoint_data,
            error_message=job.error_message,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
        self.session.add(job_model)
        for step in job.steps:
            step_model = JobStepModel(
                id=step.id,
                job_id=job.id,
                name=step.name,
                step_order=step.step_order,
                status=step.status.value,
                items_total=step.items_total,
                items_processed=step.items_processed,
                items_failed=step.items_failed,
                error_message=step.error_message,
                created_at=step.created_at,
                updated_at=step.updated_at,
            )
            self.session.add(step_model)
        self.session.flush()
        return job

    def get_by_id(self, job_id: str) -> Job | None:
        model = self.session.query(JobModel).filter_by(id=job_id).first()
        if not model:
            return None
        return self._to_entity(model)

    def list_by_project(self, project_id: str) -> list[Job]:
        models = self.session.query(JobModel).filter_by(project_id=project_id).order_by(JobModel.created_at.desc()).all()
        return [self._to_entity(m) for m in models]

    def update(self, job: Job) -> Job:
        model = self.session.query(JobModel).filter_by(id=job.id).first()
        if model:
            model.status = job.status.value
            model.checkpoint_data_json = job.checkpoint_data
            model.error_message = job.error_message
            model.started_at = job.started_at
            model.completed_at = job.completed_at
            model.updated_at = datetime.now(UTC)

            # Update steps
            for step in job.steps:
                s_model = self.session.query(JobStepModel).filter_by(id=step.id).first()
                if s_model:
                    s_model.status = step.status.value
                    s_model.items_total = step.items_total
                    s_model.items_processed = step.items_processed
                    s_model.items_failed = step.items_failed
                    s_model.error_message = step.error_message
                    s_model.updated_at = datetime.now(UTC)
                else:
                    self.session.add(
                        JobStepModel(
                            id=step.id,
                            job_id=job.id,
                            name=step.name,
                            step_order=step.step_order,
                            status=step.status.value,
                            items_total=step.items_total,
                            items_processed=step.items_processed,
                            items_failed=step.items_failed,
                            error_message=step.error_message,
                            created_at=step.created_at,
                            updated_at=step.updated_at,
                        )
                    )
            self.session.flush()
        return job

    def _to_entity(self, model: JobModel) -> Job:
        steps = [
            JobStep(
                id=s.id,
                job_id=s.job_id,
                name=s.name,
                step_order=s.step_order,
                status=JobStepStatus(s.status),
                items_total=s.items_total or 0,
                items_processed=s.items_processed or 0,
                items_failed=s.items_failed or 0,
                error_message=s.error_message,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in sorted(model.steps, key=lambda x: x.step_order)
        ]
        return Job(
            id=model.id,
            project_id=model.project_id,
            job_type=model.job_type,
            status=JobStatus(model.status),
            steps=steps,
            checkpoint_data=model.checkpoint_data_json or {},
            error_message=model.error_message,
            started_at=model.started_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
