"""Unit tests for .ecraft export, integrity verification, zip slip defense, and import."""

import json
import zipfile
from datetime import UTC, datetime

import pytest

from embedcraft.application.services.export_service import ExportService
from embedcraft.application.services.import_service import ImportService
from embedcraft.domain.entities import (
    Chunk,
    Collection,
    Document,
    DocumentStatus,
    Project,
)
from embedcraft.domain.exceptions import SecurityError


class FakeProjectRepo:
    def __init__(self, project: Project):
        self.project = project
        self.projects = {project.id: project, project.name: project}

    def get_by_name(self, name: str) -> Project | None:
        return self.projects.get(name)

    def get_by_id(self, project_id: str) -> Project | None:
        return self.projects.get(project_id)

    def save(self, project: Project) -> Project:
        self.projects[project.id] = project
        self.projects[project.name] = project
        return project


class FakeDocumentRepo:
    def __init__(self, documents: list[Document], chunks: list[Chunk]):
        self.documents = documents
        self.chunks = chunks

    def list_by_project(self, project_id: str) -> list[Document]:
        return [d for d in self.documents if d.project_id == project_id]

    def list_chunks_by_document(self, document_id: str) -> list[Chunk]:
        return [c for c in self.chunks if c.document_id == document_id]

    def list_chunks_by_project(self, project_id: str) -> list[Chunk]:
        doc_ids = {d.id for d in self.documents if d.project_id == project_id}
        return [c for c in self.chunks if c.document_id in doc_ids]

    def save_documents_batch(self, docs: list[Document]) -> None:
        self.documents.extend(docs)

    def save_chunks_batch(self, chunks: list[Chunk]) -> None:
        self.chunks.extend(chunks)


class FakeCollectionRepo:
    def __init__(self, collections: list[Collection]):
        self.collections = collections

    def list_by_project(self, project_id: str) -> list[Collection]:
        return [c for c in self.collections if c.project_id == project_id]

    def save(self, collection: Collection) -> Collection:
        self.collections.append(collection)
        return collection


@pytest.fixture
def sample_project_data():
    project = Project(
        name="finance-ai",
        description="Financial document RAG project",
    )
    doc = Document(
        project_id=project.id,
        source_id="src-1",
        relative_path="reports/q4.pdf",
        mime_type="application/pdf",
        size_bytes=1024,
        modified_at=datetime.now(UTC),
        file_hash="hash123",
        status=DocumentStatus.NEW,
    )
    chunk = Chunk(
        document_id=doc.id,
        document_version_id="ver-1",
        chunk_index=0,
        text="The quarterly revenue grew by 18% year over year.",
        token_count=10,
        chunk_hash="chunkhash123",
    )
    collection = Collection(
        project_id=project.id,
        name="default",
        description="Default finance collection",
    )
    return project, [doc], [chunk], [collection]


def test_export_project_creates_valid_ecraft_package(tmp_path, sample_project_data):
    project, docs, chunks, collections = sample_project_data
    proj_repo = FakeProjectRepo(project)
    doc_repo = FakeDocumentRepo(docs, chunks)
    coll_repo = FakeCollectionRepo(collections)

    export_service = ExportService(
        project_repo=proj_repo,
        document_repo=doc_repo,
        collection_repo=coll_repo,
    )

    out_file = tmp_path / "finance-export.ecraft"
    manifest = export_service.export_project(
        project_name_or_id="finance-ai",
        output_file=out_file,
        include_vectors=False,
    )

    assert out_file.exists()
    assert manifest.project_name == "finance-ai"
    assert manifest.document_count == 1
    assert manifest.chunk_count == 1
    assert not manifest.has_vectors

    # Inspect zip contents
    with zipfile.ZipFile(out_file, "r") as zf:
        file_list = zf.namelist()
        assert "manifest.json" in file_list
        assert "project.yaml" in file_list
        assert "data/documents.parquet" in file_list
        assert "data/chunks.parquet" in file_list
        assert "data/collections.parquet" in file_list
        assert "checksums.sha256" in file_list

        # Verify manifest json content
        manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest_data["format_version"] == "1.0.0"
        assert manifest_data["project_name"] == "finance-ai"

        # Verify checksums.sha256 content
        checksum_text = zf.read("checksums.sha256").decode("utf-8")
        assert "manifest.json" in checksum_text


def test_package_verification_success(tmp_path, sample_project_data):
    project, docs, chunks, collections = sample_project_data
    export_service = ExportService(
        project_repo=FakeProjectRepo(project),
        document_repo=FakeDocumentRepo(docs, chunks),
        collection_repo=FakeCollectionRepo(collections),
    )
    import_service = ImportService(
        project_repo=FakeProjectRepo(project),
        document_repo=FakeDocumentRepo(docs, chunks),
        collection_repo=FakeCollectionRepo(collections),
    )

    out_file = tmp_path / "valid.ecraft"
    export_service.export_project("finance-ai", out_file)

    verification = import_service.verify_package(out_file)
    assert verification["is_valid"] is True
    assert verification["errors"] == []
    assert verification["manifest"]["project_name"] == "finance-ai"
    assert verification["files_verified"] > 3


def test_package_verification_fails_on_tampered_content(tmp_path, sample_project_data):
    project, docs, chunks, collections = sample_project_data
    export_service = ExportService(
        project_repo=FakeProjectRepo(project),
        document_repo=FakeDocumentRepo(docs, chunks),
        collection_repo=FakeCollectionRepo(collections),
    )
    import_service = ImportService(
        project_repo=FakeProjectRepo(project),
        document_repo=FakeDocumentRepo(docs, chunks),
        collection_repo=FakeCollectionRepo(collections),
    )

    out_file = tmp_path / "tampered.ecraft"
    export_service.export_project("finance-ai", out_file)

    # Tamper with the zip by rewriting a file with modified bytes
    tampered_file = tmp_path / "tampered_corrupt.ecraft"
    with zipfile.ZipFile(out_file, "r") as zin:
        with zipfile.ZipFile(tampered_file, "w") as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "project.yaml":
                    data = b"tampered: true\nmalicious: payload"
                zout.writestr(item, data)

    verification = import_service.verify_package(tampered_file)
    assert verification["is_valid"] is False
    assert any("Checksum mismatch" in err for err in verification["errors"])


def test_zip_slip_path_traversal_defense(tmp_path, sample_project_data):
    """Ensure malicious zip files containing ../ entries are rejected with SecurityError."""
    import_service = ImportService(
        project_repo=FakeProjectRepo(sample_project_data[0]),
        document_repo=FakeDocumentRepo([], []),
        collection_repo=FakeCollectionRepo([]),
    )

    malicious_zip = tmp_path / "malicious.ecraft"
    with zipfile.ZipFile(malicious_zip, "w") as zf:
        zf.writestr("../evil.txt", "pwned")
        zf.writestr("manifest.json", "{}")
        zf.writestr("checksums.sha256", "")

    with pytest.raises(SecurityError) as exc_info:
        import_service.verify_package(malicious_zip)

    assert "Path traversal" in str(exc_info.value)


def test_import_project_restores_data(tmp_path, sample_project_data):
    project, docs, chunks, collections = sample_project_data
    proj_repo = FakeProjectRepo(project)
    doc_repo = FakeDocumentRepo(docs, chunks)
    coll_repo = FakeCollectionRepo(collections)

    export_service = ExportService(
        project_repo=proj_repo,
        document_repo=doc_repo,
        collection_repo=coll_repo,
    )
    import_service = ImportService(
        project_repo=proj_repo,
        document_repo=doc_repo,
        collection_repo=coll_repo,
    )

    out_file = tmp_path / "finance_backup.ecraft"
    export_service.export_project("finance-ai", out_file)

    # Import into a new project name
    imported_project = import_service.import_project(
        out_file, target_project_name="finance-ai-restored"
    )

    assert imported_project.name == "finance-ai-restored"
    assert proj_repo.get_by_name("finance-ai-restored") is not None

    # Verify documents and chunks were imported
    restored_docs = doc_repo.list_by_project(imported_project.id)
    assert len(restored_docs) == 1
    assert restored_docs[0].relative_path == "reports/q4.pdf"

    restored_chunks = doc_repo.list_chunks_by_project(imported_project.id)
    assert len(restored_chunks) == 1
    assert "quarterly revenue" in restored_chunks[0].text

