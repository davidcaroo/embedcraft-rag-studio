"""Deterministic hashing utilities for files, normalized text, and chunk tracking."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import BinaryIO

try:
    import blake3

    HAS_BLAKE3 = True
except ImportError:
    HAS_BLAKE3 = False


def compute_file_hash(path: Path | str, chunk_size: int = 65536) -> str:
    """Compute blake3 (or sha256 fallback) hash of a file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    if HAS_BLAKE3:
        hasher = blake3.blake3()
    else:
        hasher = hashlib.sha256()

    with p.open("rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()


def compute_stream_hash(stream: BinaryIO, chunk_size: int = 65536) -> str:
    """Compute hash of an open binary stream from current position."""
    if HAS_BLAKE3:
        hasher = blake3.blake3()
    else:
        hasher = hashlib.sha256()

    while chunk := stream.read(chunk_size):
        hasher.update(chunk)

    return hasher.hexdigest()


def normalize_text(text: str) -> str:
    """Normalize text for consistent diffing and hashing.

    - Strips UTF-8 BOM if present
    - Replaces CRLF and CR with LF
    - Collapses multiple whitespace spaces/tabs into single space per line
    - Strips leading and trailing line whitespace
    """
    text = text.lstrip("\ufeff")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Clean whitespace per line
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def compute_text_hash(text: str) -> str:
    """Compute deterministic hash of arbitrary text."""
    encoded = text.encode("utf-8")
    if HAS_BLAKE3:
        return blake3.blake3(encoded).hexdigest()
    return hashlib.sha256(encoded).hexdigest()


def compute_normalized_text_hash(raw_text: str) -> str:
    """Compute deterministic hash of normalized text."""
    normalized = normalize_text(raw_text)
    return compute_text_hash(normalized)


def generate_stable_document_id(project_id: str, relative_path: str) -> str:
    """Generate a stable, deterministic UUID-like string based on project and relative path."""
    clean_path = relative_path.replace("\\", "/").strip().lower()
    combined = f"{project_id}::{clean_path}".encode()
    hex_digest = hashlib.sha256(combined).hexdigest()
    # Format as standard UUID 8-4-4-4-12
    return f"{hex_digest[:8]}-{hex_digest[8:12]}-{hex_digest[12:16]}-{hex_digest[16:20]}-{hex_digest[20:32]}"
