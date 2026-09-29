"""Unit tests for hashing utilities and stable document IDs."""

from pathlib import Path

from embedcraft.domain.services.hashing import (
    compute_file_hash,
    compute_normalized_text_hash,
    generate_stable_document_id,
    normalize_text,
)


def test_compute_file_hash(tmp_path: Path):
    file1 = tmp_path / "sample.txt"
    file1.write_text("Hello EmbedCraft!", encoding="utf-8")

    h1 = compute_file_hash(file1)
    assert len(h1) in (32, 64)

    # Identical content must yield identical hash
    file2 = tmp_path / "sample_copy.txt"
    file2.write_text("Hello EmbedCraft!", encoding="utf-8")
    assert compute_file_hash(file2) == h1

    # Different content
    file3 = tmp_path / "sample_diff.txt"
    file3.write_text("Different content", encoding="utf-8")
    assert compute_file_hash(file3) != h1


def test_normalize_text_and_hash():
    t1 = "Línea 1   con espacios   múltiples.\r\nLínea 2.\r\n"
    t2 = "Línea 1 con espacios múltiples.\nLínea 2."

    norm1 = normalize_text(t1)
    norm2 = normalize_text(t2)
    assert norm1 == norm2
    assert compute_normalized_text_hash(t1) == compute_normalized_text_hash(t2)


def test_generate_stable_document_id():
    id1 = generate_stable_document_id("proj-1", "docs/manual.pdf")
    id2 = generate_stable_document_id("proj-1", "docs\\manual.pdf")  # Cross-platform Windows/Linux slash normalization
    assert id1 == id2
    assert len(id1) == 36  # Standard UUID format 8-4-4-4-12
