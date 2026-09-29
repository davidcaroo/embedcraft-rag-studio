"""Unit tests for domain entities and value objects."""

from datetime import datetime

from embedcraft.domain.entities import (
    Chunk,
    ExportManifest,
    Project,
)
from embedcraft.domain.exceptions import ConfigurationError
from embedcraft.domain.value_objects import (
    ChunkMetadata,
    DistanceMetric,
)


def test_project_entity_creation():
    project = Project(name="Test Project", description="Description")
    assert project.name == "Test Project"
    assert len(project.id) > 0
    assert project.active_revision_id is None
    assert isinstance(project.created_at, datetime)


def test_chunk_entity_with_metadata():
    metadata = ChunkMetadata(section="Capítulo 1", page=3, custom={"author": "Test"})
    chunk = Chunk(
        document_id="doc-1",
        document_version_id="ver-1",
        chunk_index=0,
        text="Este es un fragmento de texto para indexar.",
        chunk_hash="abc123hash",
        metadata=metadata,
        token_count=12,
    )
    assert chunk.document_id == "doc-1"
    assert chunk.metadata.section == "Capítulo 1"
    assert chunk.metadata.page == 3
    assert chunk.metadata.custom["author"] == "Test"


def test_export_manifest():
    manifest = ExportManifest(
        project_id="proj-123",
        project_name="Demo",
        embedding_model="all-MiniLM-L6-v2",
        dimension=384,
        distance_metric=DistanceMetric.COSINE,
        chunking_strategy="recursive",
        revision_id="rev-1",
        document_count=50,
        chunk_count=200,
        has_vectors=True,
    )
    assert manifest.format_version == "1.0.0"
    assert manifest.dimension == 384
    dump = manifest.model_dump()
    assert dump["document_count"] == 50


def test_domain_exceptions_to_dict():
    err = ConfigurationError(
        message="Configuración inválida",
        technical_detail="Parámetro chunk_size fuera de rango",
    )
    assert err.code == "ERR_CONFIG"
    data = err.to_dict()
    assert data["code"] == "ERR_CONFIG"
    assert "Configuración inválida" in data["message"]
    assert "chunk_size" in data["technical_detail"]
    assert err.retryable is False
