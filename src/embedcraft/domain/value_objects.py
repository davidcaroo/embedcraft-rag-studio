"""Domain Value Objects and Enums for EmbedCraft RAG Studio."""

from enum import Enum

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    NEW = "new"
    UNCHANGED = "unchanged"
    MODIFIED = "modified"
    DELETED = "deleted"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class RevisionStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    STAGING = "staging"
    VALIDATING = "validating"
    ACTIVE = "active"
    FAILED = "failed"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DistanceMetric(str, Enum):
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"


class SearchMode(str, Enum):
    VECTOR = "vector"
    LEXICAL = "lexical"
    HYBRID = "hybrid"


class ChunkMetadata(BaseModel):
    section: str = ""
    page: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    custom: dict[str, str] = Field(default_factory=dict)
