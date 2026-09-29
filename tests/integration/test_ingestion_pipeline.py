"""Integration tests for incremental ingestion pipeline, scanning, and change detection."""

from pathlib import Path

from embedcraft.domain.entities import ProcessingProfile
from embedcraft.domain.value_objects import JobStatus


def test_incremental_ingestion_lifecycle(test_container, tmp_path: Path):
    # Setup test documents directory
    docs_dir = tmp_path / "corpus"
    docs_dir.mkdir()

    f1 = docs_dir / "doc1.txt"
    f1.write_text("Primer documento sobre inteligencia artificial y RAG.", encoding="utf-8")

    f2 = docs_dir / "doc2.md"
    f2.write_text("# Arquitectura RAG\nDetalles técnicos del pipeline de indexación.", encoding="utf-8")

    with test_container.get_session() as session:
        proj_svc = test_container.get_project_service(session)
        ingest_svc = test_container.get_ingestion_service(session)

        # 1. Create project & add source
        proj = proj_svc.create_project(name="Pipeline Proj")
        proj_svc.add_source(proj.name, str(docs_dir), name="Corpus")

        # 2. Initial scan: must detect 2 NEW documents
        scan1 = ingest_svc.scan_sources(proj.name)
        assert scan1.new_count == 2
        assert scan1.unchanged_count == 0
        assert scan1.modified_count == 0

        # 3. Run initial ingestion
        profile = ProcessingProfile(name="TestProfile", chunk_size=100, chunk_overlap=10)
        job1 = ingest_svc.run_ingestion(proj.name, profile=profile)
        assert job1.status == JobStatus.COMPLETED
        assert job1.steps[0].items_processed == 2

        # 4. Immediate second scan without file modifications: must be 2 UNCHANGED
        scan2 = ingest_svc.scan_sources(proj.name)
        assert scan2.new_count == 0
        assert scan2.modified_count == 0
        assert scan2.unchanged_count == 2

        # 5. Modify 1 file and scan again: must detect 1 MODIFIED, 1 UNCHANGED
        f1.write_text("Primer documento MODIFICADO con nueva información.", encoding="utf-8")
        scan3 = ingest_svc.scan_sources(proj.name)
        assert scan3.modified_count == 1
        assert scan3.unchanged_count == 1

        # 6. Re-run ingestion: ONLY the modified file is processed
        job2 = ingest_svc.run_ingestion(proj.name, profile=profile)
        assert job2.status == JobStatus.COMPLETED
        assert job2.steps[0].items_processed == 1

        # 7. Check version increment for modified doc
        doc_repo = test_container.get_document_repository(session)
        doc1_entity = doc_repo.get_by_path(proj.id, "doc1.txt")
        assert doc1_entity is not None
        v_latest = doc_repo.get_latest_version(doc1_entity.id)
        assert v_latest.version_number == 2

        # 8. Delete 1 file and scan: must detect 1 DELETED
        f2.unlink()
        scan4 = ingest_svc.scan_sources(proj.name)
        assert scan4.deleted_count == 1


def test_preview_services(test_container, tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("Línea de prueba para verificar preview de texto canónico.", encoding="utf-8")

    with test_container.get_session() as session:
        ingest_svc = test_container.get_ingestion_service(session)
        doc = ingest_svc.preview_document(sample)
        assert doc.title == "sample"
        assert "Línea de prueba" in doc.text

        chunks = ingest_svc.preview_chunks(sample)
        assert len(chunks) >= 1
        assert chunks[0].document_id == "preview-id"
