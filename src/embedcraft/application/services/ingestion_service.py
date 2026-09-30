"""Application service for document discovery, diffing, extraction, chunking, and job orchestration."""

from __future__ import annotations

import mimetypes
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from embedcraft.adapters.documents.registry import (
    DocumentReaderRegistry,
    default_reader_registry,
)
from embedcraft.application.services.chunking.chunker_factory import get_chunker_for_profile
from embedcraft.domain.entities import (
    CanonicalDocument,
    Chunk,
    Document,
    DocumentVersion,
    Job,
    JobStep,
    ProcessingProfile,
)
from embedcraft.domain.exceptions import ConfigurationError, DocumentError
from embedcraft.domain.services.hashing import (
    compute_file_hash,
    compute_normalized_text_hash,
    generate_stable_document_id,
)
from embedcraft.domain.value_objects import (
    DocumentStatus,
    JobStatus,
    JobStepStatus,
)
from embedcraft.infrastructure.logging import logger
from embedcraft.ports.repositories import (
    DocumentRepository,
    JobRepository,
    ProjectRepository,
    SourceRepository,
)

MAX_DOCUMENT_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB maximum document size limit


class ScanItem(BaseModel):
    document_id: str
    source_id: str
    relative_path: str
    absolute_path: str
    file_hash: str
    size_bytes: int
    modified_at: datetime
    mime_type: str
    status: DocumentStatus
    reason: str = ""


class ScanResult(BaseModel):
    project_id: str
    total_found: int = 0
    new_count: int = 0
    modified_count: int = 0
    unchanged_count: int = 0
    deleted_count: int = 0
    unsupported_count: int = 0
    items: list[ScanItem] = Field(default_factory=list)

    @property
    def new_paths(self) -> list[str]:
        return [i.relative_path for i in self.items if i.status == DocumentStatus.NEW]

    @property
    def modified_paths(self) -> list[str]:
        return [i.relative_path for i in self.items if i.status == DocumentStatus.MODIFIED]

    @property
    def deleted_paths(self) -> list[str]:
        return [i.relative_path for i in self.items if i.status == DocumentStatus.DELETED]


class IngestionService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        source_repo: SourceRepository,
        document_repo: DocumentRepository,
        job_repo: JobRepository,
        reader_registry: DocumentReaderRegistry | None = None,
    ):
        self.project_repo = project_repo
        self.source_repo = source_repo
        self.document_repo = document_repo
        self.job_repo = job_repo
        self.reader_registry = reader_registry or default_reader_registry

    def scan_sources(self, project_identifier: str) -> ScanResult:
        """Scan all configured sources for a project and calculate incremental diffs."""
        project = self.project_repo.get_by_id(project_identifier) or self.project_repo.get_by_name(project_identifier)
        if not project:
            raise ConfigurationError(f"Proyecto no encontrado: {project_identifier}")

        sources = self.source_repo.list_by_project(project.id)
        existing_docs = {d.relative_path: d for d in self.document_repo.list_by_project(project.id, limit=100000)}

        result = ScanResult(project_id=project.id)
        scanned_paths: set[str] = set()

        for source in sources:
            if not source.enabled:
                continue

            src_root = Path(source.uri_or_path)
            if not src_root.exists():
                logger.warning("source_path_does_not_exist", path=source.uri_or_path)
                continue

            files_to_check: list[Path] = []
            if src_root.is_file():
                files_to_check.append(src_root)
            else:
                glob_pattern = "**/*" if source.recursive else "*"
                files_to_check.extend([p for p in src_root.glob(glob_pattern) if p.is_file()])

            for file_path in files_to_check:
                rel_path = (
                    file_path.relative_to(src_root).as_posix()
                    if src_root.is_dir()
                    else file_path.name
                )
                scanned_paths.add(rel_path)

                stat = file_path.stat()
                if stat.st_size > MAX_DOCUMENT_SIZE_BYTES:
                    result.unsupported_count += 1
                    result.items.append(
                        ScanItem(
                            document_id=generate_stable_document_id(project.id, rel_path),
                            source_id=source.id,
                            relative_path=rel_path,
                            absolute_path=str(file_path.resolve()),
                            file_hash="",
                            size_bytes=stat.st_size,
                            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                            mime_type="application/octet-stream",
                            status=DocumentStatus.FAILED,
                            reason=f"El archivo supera el tamaño máximo permitido (100 MB): {stat.st_size / (1024 * 1024):.1f} MB.",
                        )
                    )
                    continue

                mime, _ = mimetypes.guess_type(file_path)
                mime_type = mime or "application/octet-stream"

                # Check support
                reader = self.reader_registry.get_reader_for_file(file_path, mime_type)
                if not reader:
                    result.unsupported_count += 1
                    result.items.append(
                        ScanItem(
                            document_id=generate_stable_document_id(project.id, rel_path),
                            source_id=source.id,
                            relative_path=rel_path,
                            absolute_path=str(file_path.resolve()),
                            file_hash="",
                            size_bytes=stat.st_size,
                            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                            mime_type=mime_type,
                            status=DocumentStatus.UNSUPPORTED,
                            reason="No hay lector registrado para esta extensión.",
                        )
                    )
                    continue

                f_hash = compute_file_hash(file_path)
                stable_id = generate_stable_document_id(project.id, rel_path)
                existing = existing_docs.get(rel_path)

                if not existing:
                    status = DocumentStatus.NEW
                    result.new_count += 1
                elif existing.file_hash != f_hash:
                    status = DocumentStatus.MODIFIED
                    result.modified_count += 1
                else:
                    status = DocumentStatus.UNCHANGED
                    result.unchanged_count += 1

                result.items.append(
                    ScanItem(
                        document_id=stable_id,
                        source_id=source.id,
                        relative_path=rel_path,
                        absolute_path=str(file_path.resolve()),
                        file_hash=f_hash,
                        size_bytes=stat.st_size,
                        modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                        mime_type=mime_type,
                        status=status,
                    )
                )

        # Detect deleted documents
        for rel_path, doc in existing_docs.items():
            if rel_path not in scanned_paths and doc.status != DocumentStatus.DELETED:
                result.deleted_count += 1
                result.items.append(
                    ScanItem(
                        document_id=doc.id,
                        source_id=doc.source_id,
                        relative_path=doc.relative_path,
                        absolute_path="",
                        file_hash=doc.file_hash,
                        size_bytes=doc.size_bytes,
                        modified_at=doc.modified_at,
                        mime_type=doc.mime_type,
                        status=DocumentStatus.DELETED,
                        reason="El archivo fue eliminado del origen de datos.",
                    )
                )

        result.total_found = len(result.items)
        return result

    def preview_document(self, file_path: Path | str) -> CanonicalDocument:
        """Extract canonical document representation for live UI/CLI inspection."""
        p = Path(file_path)
        if not p.is_file():
            raise DocumentError(f"Archivo no encontrado: {file_path}")

        if p.stat().st_size > MAX_DOCUMENT_SIZE_BYTES:
            raise DocumentError(
                f"El archivo '{p.name}' supera el tamaño máximo permitido de previsualización (100 MB)."
            )

        mime, _ = mimetypes.guess_type(p)
        reader = self.reader_registry.get_reader_or_raise(p, mime or "")
        return reader.extract(p, document_id="preview-id")

    def preview_chunks(
        self,
        file_path: Path | str,
        profile: ProcessingProfile | None = None,
    ) -> list[Chunk]:
        """Preview chunks of a document with the given profile."""
        doc = self.preview_document(file_path)
        active_profile = profile or ProcessingProfile(name="Default")
        chunker = get_chunker_for_profile(active_profile)
        return list(chunker.split(doc, document_version_id="preview-version"))

    def run_ingestion(
        self,
        project_identifier: str,
        profile: ProcessingProfile | None = None,
        job_id: str | None = None,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> Job:
        """Execute incremental document ingestion, extraction and chunking."""
        project = self.project_repo.get_by_id(project_identifier) or self.project_repo.get_by_name(project_identifier)
        if not project:
            raise ConfigurationError(f"Proyecto no encontrado: {project_identifier}")

        active_profile = profile or ProcessingProfile(name="Default")
        chunker = get_chunker_for_profile(active_profile)

        scan_result = self.scan_sources(project.id)
        items_to_process = [
            item
            for item in scan_result.items
            if item.status in (DocumentStatus.NEW, DocumentStatus.MODIFIED)
        ]

        # Setup or retrieve Job
        if job_id:
            job = self.job_repo.get_by_id(job_id)
            if not job:
                raise ConfigurationError(f"Trabajo con ID '{job_id}' no encontrado.")
        else:
            step1 = JobStep(
                job_id="dummy",
                name="Ingestión y Fragmentación",
                step_order=1,
                status=JobStepStatus.RUNNING,
                items_total=len(items_to_process),
            )
            job = Job(
                project_id=project.id,
                job_type="document_ingestion",
                status=JobStatus.RUNNING,
                steps=[step1],
                checkpoint_data={"processed_doc_ids": []},
                started_at=datetime.now(UTC),
            )
            job = self.job_repo.create(job)

        step = job.steps[0]
        step.status = JobStepStatus.RUNNING
        job.status = JobStatus.RUNNING
        self.job_repo.update(job)

        processed_ids: list[str] = job.checkpoint_data.get("processed_doc_ids", [])

        for idx, item in enumerate(items_to_process):
            # Check cooperative cancellation or pause
            current_job_state = self.job_repo.get_by_id(job.id)
            if current_job_state and current_job_state.status in (JobStatus.PAUSED, JobStatus.CANCELLED):
                logger.info("job_execution_stopped_by_user", status=current_job_state.status)
                return current_job_state

            if item.document_id in processed_ids:
                continue

            file_path = Path(item.absolute_path)
            try:
                # 1. Upsert Document entity
                doc_entity = Document(
                    id=item.document_id,
                    project_id=project.id,
                    source_id=item.source_id,
                    relative_path=item.relative_path,
                    mime_type=item.mime_type,
                    size_bytes=item.size_bytes,
                    modified_at=item.modified_at,
                    file_hash=item.file_hash,
                    status=DocumentStatus.NEW,
                )
                doc_entity = self.document_repo.upsert(doc_entity)

                # 2. Extract Canonical Document
                reader = self.reader_registry.get_reader_or_raise(file_path, item.mime_type)
                canonical_doc = reader.extract(file_path, document_id=doc_entity.id)

                # 3. Compute normalized hash & version
                norm_hash = compute_normalized_text_hash(canonical_doc.text)
                latest_version = self.document_repo.get_latest_version(doc_entity.id)
                next_ver_num = (latest_version.version_number + 1) if latest_version else 1

                version_entity = DocumentVersion(
                    document_id=doc_entity.id,
                    version_number=next_ver_num,
                    content_hash=item.file_hash,
                    normalized_text_hash=norm_hash,
                    canonical_text=canonical_doc.text,
                )

                # 4. Chunk document
                chunks = chunker.split(canonical_doc, document_version_id=version_entity.id)

                # 5. Persist version and chunks
                self.document_repo.save_version_with_chunks(version_entity, chunks)

                # 6. Update document status to unchanged
                doc_entity.status = DocumentStatus.UNCHANGED
                doc_entity.error_message = None
                self.document_repo.upsert(doc_entity)

                step.items_processed += 1
                processed_ids.append(item.document_id)

            except Exception as e:  # noqa: BLE001
                logger.exception("document_processing_failed", file=item.relative_path, error=str(e))
                step.items_failed += 1
                try:
                    failed_doc = Document(
                        id=item.document_id,
                        project_id=project.id,
                        source_id=item.source_id,
                        relative_path=item.relative_path,
                        mime_type=item.mime_type,
                        size_bytes=item.size_bytes,
                        modified_at=item.modified_at,
                        file_hash=item.file_hash,
                        status=DocumentStatus.FAILED,
                        error_message=str(e),
                    )
                    self.document_repo.upsert(failed_doc)
                except Exception:  # noqa: BLE001, S110
                    pass

            # Update checkpoint every document
            job.checkpoint_data["processed_doc_ids"] = processed_ids
            self.job_repo.update(job)

            if progress_callback:
                progress_callback(idx + 1, len(items_to_process), item.relative_path)

        # Mark job finished
        step.status = JobStepStatus.COMPLETED
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(UTC)
        self.job_repo.update(job)
        return job

    def pause_job(self, job_id: str) -> bool:
        job = self.job_repo.get_by_id(job_id)
        if job and job.status == JobStatus.RUNNING:
            job.status = JobStatus.PAUSED
            self.job_repo.update(job)
            return True
        return False

    def cancel_job(self, job_id: str) -> bool:
        job = self.job_repo.get_by_id(job_id)
        if job and job.status in (JobStatus.RUNNING, JobStatus.PAUSED):
            job.status = JobStatus.CANCELLED
            self.job_repo.update(job)
            return True
        return False
