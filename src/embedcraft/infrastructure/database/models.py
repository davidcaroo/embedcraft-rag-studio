"""SQLAlchemy ORM models for EmbedCraft RAG Studio SQLite database."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(UTC)


class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, default="")
    storage_path = Column(Text, default="")
    active_revision_id = Column(String(36), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    sources = relationship("SourceModel", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("DocumentModel", back_populates="project", cascade="all, delete-orphan")
    collections = relationship("CollectionModel", back_populates="project", cascade="all, delete-orphan")
    revisions = relationship("IndexRevisionModel", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("JobModel", back_populates="project", cascade="all, delete-orphan")


class SourceModel(Base):
    __tablename__ = "sources"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    uri_or_path = Column(Text, nullable=False)
    source_type = Column(String(50), default="local_folder")
    enabled = Column(Boolean, default=True)
    recursive = Column(Boolean, default=True)
    include_patterns_json = Column(JSON, default=list)
    exclude_patterns_json = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("ProjectModel", back_populates="sources")
    documents = relationship("DocumentModel", back_populates="source", cascade="all, delete-orphan")


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    relative_path = Column(Text, nullable=False, index=True)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, default=0)
    modified_at = Column(DateTime, nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    status = Column(String(30), default="new", index=True)
    error_message = Column(Text, nullable=True)
    custom_metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("ProjectModel", back_populates="documents")
    source = relationship("SourceModel", back_populates="documents")
    versions = relationship("DocumentVersionModel", back_populates="document", cascade="all, delete-orphan")


class DocumentVersionModel(Base):
    __tablename__ = "document_versions"

    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    content_hash = Column(String(64), nullable=False)
    normalized_text_hash = Column(String(64), nullable=False)
    canonical_text = Column(Text, default="")
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    document = relationship("DocumentModel", back_populates="versions")
    chunks = relationship("ChunkModel", back_populates="document_version", cascade="all, delete-orphan")


class ChunkModel(Base):
    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    document_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    chunk_hash = Column(String(64), nullable=False, index=True)
    metadata_json = Column(JSON, default=dict)
    token_count = Column(Integer, default=0)
    strategy_version = Column(String(50), default="v1")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    document_version = relationship("DocumentVersionModel", back_populates="chunks")


class CollectionModel(Base):
    __tablename__ = "collections"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    embedding_model = Column(String(100), default="all-MiniLM-L6-v2")
    dimension = Column(Integer, default=384)
    distance_metric = Column(String(20), default="cosine")
    vector_store_type = Column(String(50), default="lancedb")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("ProjectModel", back_populates="collections")


class IndexRevisionModel(Base):
    __tablename__ = "index_revisions"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False)
    status = Column(String(30), default="draft", index=True)
    embedding_model = Column(String(100), nullable=False)
    dimension = Column(Integer, nullable=False)
    total_documents = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    staging_path = Column(Text, default="")
    active_path = Column(Text, default="")
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("ProjectModel", back_populates="revisions")


class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type = Column(String(50), nullable=False)
    status = Column(String(30), default="pending", index=True)
    checkpoint_data_json = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("ProjectModel", back_populates="jobs")
    steps = relationship("JobStepModel", back_populates="job", cascade="all, delete-orphan")


class JobStepModel(Base):
    __tablename__ = "job_steps"

    id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    step_order = Column(Integer, nullable=False)
    status = Column(String(30), default="pending")
    items_total = Column(Integer, default=0)
    items_processed = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    job = relationship("JobModel", back_populates="steps")
