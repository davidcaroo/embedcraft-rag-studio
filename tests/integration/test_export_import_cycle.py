"""Integration test for .ecraft export -> verification -> import -> search cycle."""


from embedcraft.domain.value_objects import SearchMode


def test_full_export_import_search_cycle(test_container, tmp_path):
    with test_container.get_session() as db_session:

        # 1. Setup services from container
        project_service = test_container.get_project_service(db_session)
        ingestion_service = test_container.get_ingestion_service(db_session)
        indexing_service = test_container.get_indexing_service(db_session)
        export_service = test_container.get_export_service(db_session)
        import_service = test_container.get_import_service(db_session)
        doc_repo = test_container.get_document_repository(db_session)

        # 2. Create sample source and documents
        docs_dir = tmp_path / "source_docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        sample_file = docs_dir / "architecture.txt"
        sample_file.write_text(
            "EmbedCraft RAG Studio architecture features hexagonal domain design and offline-first LanceDB vector storage.",
            encoding="utf-8",
        )

        project = project_service.create_project("portal-system", "Testing system export")
        project_service.add_source(project.name, str(docs_dir), name="docs")

        # Ingest and index
        job = ingestion_service.run_ingestion(project.name)
        assert job.status.value == "completed"
        db_session.commit()

        rev = indexing_service.create_and_publish_revision(project.id, collection_name="default")
        assert rev.status.value == "active"
        db_session.commit()

        # Search in original project
        results = indexing_service.search(
            project.name, "hexagonal architecture", mode=SearchMode.HYBRID, top_k=5
        )
        assert len(results) > 0
        assert "hexagonal" in results[0].text

        # 3. Export to .ecraft
        export_pkg = tmp_path / "portal-system.ecraft"
        manifest = export_service.export_project(project.name, export_pkg, include_vectors=True)
        assert export_pkg.exists()
        assert manifest.document_count >= 1
        assert manifest.chunk_count >= 1

        # 4. Verify package integrity
        verify_result = import_service.verify_package(export_pkg)
        assert verify_result["is_valid"] is True
        assert verify_result["errors"] == []
        assert verify_result["files_verified"] >= 4

        # 5. Import package into a new project name
        imported_proj = import_service.import_project(
            export_pkg, target_project_name="portal-system-restored"
        )
        assert imported_proj.name == "portal-system-restored"
        assert imported_proj.id != project.id

        # 6. Verify restored data
        imported_docs = doc_repo.list_by_project(imported_proj.id)
        assert len(imported_docs) >= 1

        imported_chunks = doc_repo.list_chunks_by_project(imported_proj.id)
        assert len(imported_chunks) >= 1
        assert any("hexagonal" in c.text for c in imported_chunks)
