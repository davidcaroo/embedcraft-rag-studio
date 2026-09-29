"""CLI tests for document ingestion and preview commands."""

import uuid
from pathlib import Path

from typer.testing import CliRunner

from embedcraft.cli.app import app

runner = CliRunner()


def test_cli_ingest_and_preview_flow(tmp_path: Path):
    # Setup test corpus
    corpus_dir = tmp_path / "cli_corpus"
    corpus_dir.mkdir()
    doc_file = corpus_dir / "intro.txt"
    doc_file.write_text("Introducción a la plataforma EmbedCraft Studio.\nArquitectura y RAG.", encoding="utf-8")

    proj_name = f"cli_ingest_proj_{uuid.uuid4().hex[:6]}"
    # Create project and add source
    res1 = runner.invoke(app, ["project", "create", proj_name])
    assert res1.exit_code == 0, res1.stdout

    res2 = runner.invoke(app, ["source", "add", proj_name, str(corpus_dir)])
    assert res2.exit_code == 0

    # 1. Preview doc
    res_prev = runner.invoke(app, ["preview", "doc", str(doc_file)])
    assert res_prev.exit_code == 0
    assert "Documento Canónico: intro" in res_prev.stdout

    # 2. Preview chunks
    res_prev_c = runner.invoke(app, ["preview", "chunks", str(doc_file), "--chunk-size", "50"])
    assert res_prev_c.exit_code == 0
    assert "Fragmentos generados" in res_prev_c.stdout

    # 3. Ingest scan
    res_scan = runner.invoke(app, ["ingest", "scan", proj_name])
    assert res_scan.exit_code == 0
    assert "Nuevos" in res_scan.stdout

    # 4. Ingest run
    res_run = runner.invoke(app, ["ingest", "run", proj_name, "--chunk-size", "100"])
    assert res_run.exit_code == 0
    assert "Ingestión completada" in res_run.stdout

    # 5. Ingest status
    res_status = runner.invoke(app, ["ingest", "status", proj_name, "--json"])
    assert res_status.exit_code == 0
    assert "document_ingestion" in res_status.stdout
    assert "completed" in res_status.stdout

    # Cleanup
    runner.invoke(app, ["project", "delete", proj_name, "--yes"])
