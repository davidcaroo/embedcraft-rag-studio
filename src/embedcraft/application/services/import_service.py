"""Import and verification service for portable .ecraft packages with path traversal protection."""

from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import yaml

from embedcraft.domain.entities import (
    Chunk,
    Collection,
    Document,
    Project,
    utc_now,
)
from embedcraft.domain.exceptions import EmbedCraftError, SecurityError
from embedcraft.domain.value_objects import ChunkMetadata, DocumentStatus


def _is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """Verifies that target_path resolves strictly inside base_dir (Zip Slip defense)."""
    try:
        resolved_base = base_dir.resolve()
        resolved_target = target_path.resolve()
        return resolved_target.is_relative_to(resolved_base)
    except (ValueError, RuntimeError):
        return False


class ImportService:
    """Verifies and imports projects from portable .ecraft packages."""

    def __init__(
        self,
        project_repo: Any,
        document_repo: Any,
        collection_repo: Any,
        vector_store: Any | None = None,
        fts5_store: Any | None = None,
    ) -> None:
        self.project_repo = project_repo
        self.document_repo = document_repo
        self.collection_repo = collection_repo
        self.vector_store = vector_store
        self.fts5_store = fts5_store

    def verify_package(self, package_file: Path | str) -> dict[str, Any]:
        """Inspects and validates an .ecraft package against corruption and security vulnerabilities."""
        pkg_path = Path(package_file)
        if not pkg_path.exists():
            raise EmbedCraftError(f"Package file not found: {pkg_path}")

        if not zipfile.is_zipfile(pkg_path):
            raise EmbedCraftError(f"File is not a valid zip or .ecraft archive: {pkg_path}")

        errors: list[str] = []
        files_verified = 0
        manifest_data: dict[str, Any] = {}

        dummy_base = Path("/safe_base").resolve()

        with zipfile.ZipFile(pkg_path, "r") as zf:
            # 1. Zip Slip / Path Traversal Defense
            for info in zf.infolist():
                name = info.filename
                if name.startswith("/") or name.startswith("\\") or ":" in name or ".." in name:
                    raise SecurityError(
                        f"Path traversal vulnerability detected in archive entry: {name}"
                    )
                target = (dummy_base / name).resolve()
                if not _is_safe_path(dummy_base, target):
                    raise SecurityError(
                        f"Path traversal attempt detected escaping root: {name}"
                    )

            namelist = zf.namelist()
            if "manifest.json" not in namelist:
                errors.append("Package missing required manifest.json")
            if "checksums.sha256" not in namelist:
                errors.append("Package missing required checksums.sha256")

            # Parse manifest
            if "manifest.json" in namelist:
                try:
                    manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
                except Exception as exc:
                    errors.append(f"Corrupt manifest.json: {exc}")

            # Parse checksums.sha256 and verify file hashes
            if "checksums.sha256" in namelist:
                checksums_content = zf.read("checksums.sha256").decode("utf-8")
                expected_checksums: dict[str, str] = {}
                for line in checksums_content.strip().splitlines():
                    parts = line.strip().split(maxsplit=1)
                    if len(parts) == 2:
                        expected_checksums[parts[1].strip()] = parts[0].strip()

                for entry_name, expected_hash in expected_checksums.items():
                    if entry_name not in namelist:
                        errors.append(f"Missing file declared in checksums: {entry_name}")
                        continue

                    # Compute hash directly from archive bytes
                    data = zf.read(entry_name)
                    actual_hash = hashlib.sha256(data).hexdigest()
                    if actual_hash != expected_hash:
                        errors.append(
                            f"Checksum mismatch for '{entry_name}': expected {expected_hash}, got {actual_hash}"
                        )
                    else:
                        files_verified += 1

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "manifest": manifest_data,
            "files_verified": files_verified,
            "package_path": str(pkg_path),
        }

    def import_project(
        self,
        package_file: Path | str,
        target_project_name: str | None = None,
        overwrite: bool = False,
    ) -> Project:
        """Imports an .ecraft package into local SQLite, vector, and lexical stores."""
        verification = self.verify_package(package_file)
        if not verification["is_valid"]:
            error_details = "; ".join(verification["errors"])
            raise EmbedCraftError(f"Cannot import corrupted package: {error_details}")

        pkg_path = Path(package_file)

        with tempfile.TemporaryDirectory() as tmp_dir_str:
            extract_dir = Path(tmp_dir_str)

            with zipfile.ZipFile(pkg_path, "r") as zf:
                # Safe extraction (Zip Slip defense applied per file)
                for member in zf.infolist():
                    dest_file = extract_dir / member.filename
                    if not _is_safe_path(extract_dir, dest_file):
                        raise SecurityError(
                            f"Illegal path traversal extracting {member.filename}"
                        )
                    zf.extract(member, extract_dir)

            # Read project configuration
            project_yaml_path = extract_dir / "project.yaml"
            proj_data: dict[str, Any] = {}
            if project_yaml_path.exists():
                with open(project_yaml_path, encoding="utf-8") as f:
                    proj_data = yaml.safe_load(f) or {}

            # Determine project name
            proj_name = target_project_name or proj_data.get("name") or "imported-project"

            existing = self.project_repo.get_by_name(proj_name)
            if existing and not overwrite:
                raise EmbedCraftError(
                    f"A project named '{proj_name}' already exists. Specify a different target name."
                )

            project = Project(
                name=proj_name,
                description=proj_data.get("description", "Imported from .ecraft package"),
                storage_path=proj_data.get("storage_path", ""),
            )
            if hasattr(self.project_repo, "create"):
                self.project_repo.create(project)
            else:
                self.project_repo.save(project)

            # Import collections
            colls_pq = extract_dir / "data" / "collections.parquet"
            if colls_pq.exists():
                table = pq.read_table(colls_pq)
                for row in table.to_pylist():
                    if row.get("name"):
                        coll = Collection(
                            project_id=project.id,
                            name=row["name"],
                            description=row.get("description", ""),
                            embedding_model=row.get("embedding_model", "all-MiniLM-L6-v2"),
                            dimension=row.get("dimension", 384),
                        )
                        if hasattr(self.collection_repo, "create"):
                            self.collection_repo.create(coll)
                        else:
                            self.collection_repo.save(coll)

            # Import documents
            docs_pq = extract_dir / "data" / "documents.parquet"
            doc_id_map: dict[str, str] = {}
            if docs_pq.exists():
                table = pq.read_table(docs_pq)
                imported_docs: list[Document] = []
                for row in table.to_pylist():
                    if row.get("id"):
                        old_id = row["id"]
                        raw_meta = row.get("custom_metadata") or "{}"
                        meta_dict = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
                        doc = Document(
                            project_id=project.id,
                            source_id=row.get("source_id", "imported-source"),
                            relative_path=row.get("relative_path", "unknown"),
                            mime_type=row.get("mime_type", "application/octet-stream"),
                            size_bytes=row.get("size_bytes", 0),
                            modified_at=utc_now(),
                            file_hash=row.get("file_hash", ""),
                            status=DocumentStatus.NEW,
                            custom_metadata=meta_dict,
                        )
                        doc_id_map[old_id] = doc.id
                        imported_docs.append(doc)
                if imported_docs:
                    self.document_repo.save_documents_batch(imported_docs)

            # Import chunks
            chunks_pq = extract_dir / "data" / "chunks.parquet"
            imported_chunks: list[Chunk] = []
            if chunks_pq.exists():
                table = pq.read_table(chunks_pq)
                for row in table.to_pylist():
                    if row.get("text"):
                        old_doc_id = row.get("document_id", "")
                        new_doc_id = doc_id_map.get(old_doc_id, old_doc_id)
                        raw_meta = row.get("metadata") or "{}"
                        meta_dict = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
                        chunk = Chunk(
                            document_id=new_doc_id,
                            document_version_id=row.get("document_version_id", "ver-imported"),
                            chunk_index=row.get("chunk_index", 0),
                            text=row.get("text", ""),
                            token_count=row.get("token_count", 0),
                            chunk_hash=row.get("chunk_hash", ""),
                            metadata=ChunkMetadata(**meta_dict) if isinstance(meta_dict, dict) else ChunkMetadata(),
                        )
                        imported_chunks.append(chunk)

                if imported_chunks:
                    self.document_repo.save_chunks_batch(imported_chunks)

            # Import vectors if vector_store is provided and embeddings exist
            embs_pq = extract_dir / "vectors" / "embeddings.parquet"
            if embs_pq.exists() and self.vector_store:
                table = pq.read_table(embs_pq)
                for row in table.to_pylist():
                    c_id = row.get("chunk_id")
                    emb = row.get("embedding")
                    if c_id and emb:
                        try:
                            self.vector_store.upsert_chunk(c_id, emb, project.id)
                        except Exception:
                            pass

            # Index into FTS5 lexical store if available
            if self.fts5_store and imported_chunks:
                for c in imported_chunks:
                    try:
                        self.fts5_store.index_chunk(
                            chunk_id=c.id,
                            document_id=c.document_id,
                            project_id=c.project_id,
                            text=c.text,
                        )
                    except Exception:
                        pass

            return project
