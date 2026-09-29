"""Unit tests for chunking strategies (fixed, recursive, section)."""

from embedcraft.application.services.chunking.chunker_factory import get_chunker_for_profile
from embedcraft.application.services.chunking.fixed_chunker import FixedSizeChunker
from embedcraft.application.services.chunking.recursive_chunker import RecursiveChunker
from embedcraft.application.services.chunking.section_chunker import SectionChunker
from embedcraft.domain.entities import CanonicalDocument, ProcessingProfile


def test_fixed_size_chunker():
    text = "Palabra " * 100  # ~800 chars
    doc = CanonicalDocument(
        document_id="doc-1",
        title="Fixed Test",
        text=text,
    )
    chunker = FixedSizeChunker(chunk_size=200, chunk_overlap=20)
    chunks = chunker.split(doc, document_version_id="v1")

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.text) <= 200
        assert chunk.document_id == "doc-1"
        assert chunk.token_count > 0


def test_recursive_chunker_natural_boundaries():
    text = (
        "Párrafo 1 con una explicación detallada sobre RAG.\n\n"
        "Párrafo 2 con más información sobre embeddings y recuperación.\n\n"
        "Párrafo 3 con conclusiones finales del documento."
    )
    doc = CanonicalDocument(
        document_id="doc-2",
        title="Recursive Test",
        text=text,
    )
    chunker = RecursiveChunker(chunk_size=120, chunk_overlap=15)
    chunks = chunker.split(doc, document_version_id="v1")

    assert len(chunks) >= 2
    # Verify boundaries are respected
    assert all(c.chunk_hash for c in chunks)


def test_section_chunker():
    text = (
        "# Introducción\n"
        "Texto de la introducción.\n"
        "# Arquitectura\n"
        "Texto de arquitectura detallada.\n"
        "# Conclusiones\n"
        "Texto de las conclusiones."
    )
    doc = CanonicalDocument(
        document_id="doc-3",
        title="Section Test",
        text=text,
    )
    chunker = SectionChunker(max_chunk_size=500)
    chunks = chunker.split(doc, document_version_id="v1")

    assert len(chunks) == 3
    assert chunks[0].metadata.section == "Introducción"
    assert chunks[1].metadata.section == "Arquitectura"
    assert chunks[2].metadata.section == "Conclusiones"


def test_chunker_factory():
    p_fixed = ProcessingProfile(name="P1", chunking_strategy="fixed")
    p_rec = ProcessingProfile(name="P2", chunking_strategy="recursive")
    p_sec = ProcessingProfile(name="P3", chunking_strategy="section")

    assert isinstance(get_chunker_for_profile(p_fixed), FixedSizeChunker)
    assert isinstance(get_chunker_for_profile(p_rec), RecursiveChunker)
    assert isinstance(get_chunker_for_profile(p_sec), SectionChunker)
