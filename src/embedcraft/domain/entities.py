"""Domain Entities for EmbedCraft RAG Studio.

Independent of external frameworks, defining core business concepts and contracts.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from embedcraft.domain.value_objects import (
    ChunkMetadata,
    DistanceMetric,
    DocumentStatus,
    JobStatus,
    JobStepStatus,
    RevisionStatus,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class BaseEntity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Project(BaseEntity):
    name: str
    description: str = ""
    storage_path: str = ""
    active_revision_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Source(BaseEntity):
    project_id: str
    name: str
    uri_or_path: str
    source_type: str = "local_folder"  # local_folder, single_file, etc.
    enabled: bool = True
    recursive: bool = True
    include_patterns: list[str] = Field(default_factory=lambda: ["*.*"])
    exclude_patterns: list[str] = Field(default_factory=list)


class Document(BaseEntity):
    project_id: str
    source_id: str
    relative_path: str
    mime_type: str
    size_bytes: int
    modified_at: datetime
    file_hash: str
    status: DocumentStatus = DocumentStatus.NEW
    error_message: str | None = None
    custom_metadata: dict[str, Any] = Field(default_factory=dict)


class CanonicalDocument(BaseModel):
    document_id: str
    title: str
    text: str
    sections: list[dict[str, Any]] = Field(default_factory=list)
    tables: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_locator: str = ""


class DocumentVersion(BaseEntity):
    document_id: str
    version_number: int
    content_hash: str
    normalized_text_hash: str
    canonical_text: str = ""
    chunk_count: int = 0


class Chunk(BaseEntity):
    document_id: str
    document_version_id: str
    chunk_index: int
    text: str
    chunk_hash: str
    metadata: ChunkMetadata = Field(default_factory=ChunkMetadata)
    token_count: int = 0
    strategy_version: str = "v1"


class Collection(BaseEntity):
    project_id: str
    name: str
    description: str = ""
    embedding_model: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    distance_metric: DistanceMetric = DistanceMetric.COSINE
    vector_store_type: str = "lancedb"


class IndexRevision(BaseEntity):
    project_id: str
    revision_number: int
    status: RevisionStatus = RevisionStatus.DRAFT
    embedding_model: str
    dimension: int
    total_documents: int = 0
    total_chunks: int = 0
    staging_path: str = ""
    active_path: str = ""
    published_at: datetime | None = None


class ProcessingProfile(BaseEntity):
    name: str
    chunk_size: int = 512
    chunk_overlap: int = 64
    chunking_strategy: str = "recursive"  # fixed, section, recursive
    ocr_enabled: bool = False
    ocr_language: str = "eng+spa"
    batch_size: int = 64


class ProviderProfile(BaseEntity):
    name: str
    provider_type: str  # local_ollama, openai, azure, custom_http
    base_url: str | None = None
    model_name: str
    api_key_secret_ref: str | None = None  # Key identifier in Keyring
    options: dict[str, Any] = Field(default_factory=dict)


class JobStep(BaseEntity):
    job_id: str
    name: str
    step_order: int
    status: JobStepStatus = JobStepStatus.PENDING
    items_total: int = 0
    items_processed: int = 0
    items_failed: int = 0
    error_message: str | None = None


class Job(BaseEntity):
    project_id: str
    job_type: str  # scan, ingest, vectorize, export
    status: JobStatus = JobStatus.PENDING
    steps: list[JobStep] = Field(default_factory=list)
    checkpoint_data: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class Citation(BaseModel):
    document_id: str
    document_path: str
    document_title: str
    chunk_id: str
    section: str = ""
    page: int | None = None
    snippet: str


class RetrievalResult(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    score: float
    reranked_score: float | None = None
    collection_id: str
    citation: Citation
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExportManifest(BaseModel):
    format_version: str = "1.0.0"
    embedcraft_version: str = "0.1.0"
    project_id: str
    project_name: str
    exported_at: datetime = Field(default_factory=utc_now)
    embedding_model: str
    dimension: int
    distance_metric: DistanceMetric
    chunking_strategy: str
    revision_id: str
    document_count: int
    chunk_count: int
    has_vectors: bool = True
    files: list[str] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)
    compatibility_notes: str = ""
