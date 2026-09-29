"""CLI tests for collection, index, and search commands."""

import json
import uuid
from pathlib import Path

from typer.testing import CliRunner

from embedcraft.cli.app import app

runner = CliRunner()


def test_cli_collection_and_index_and_search(tmp_path: Path):
    proj_name = f"search_proj_{uuid.uuid4().hex[:8]}"
    res_proj = runner.invoke(app, ["project", "create", proj_name])
    assert res_proj.exit_code == 0

    # 1. Collection list initially
    res_col_list = runner.invoke(app, ["collection", "list", proj_name])
    assert res_col_list.exit_code == 0

    # 2. Add source and file
    test_file = tmp_path / "rag_guide.txt"
    test_file.write_text("EmbedCraft RAG Studio architecture uses hexagonal ports and adapters.")

    runner.invoke(app, ["source", "add", proj_name, str(test_file)])
    runner.invoke(app, ["ingest", "run", proj_name])

    # 3. Publish index
    res_idx = runner.invoke(app, ["index", "publish", proj_name])
    assert res_idx.exit_code == 0
    assert "publicada y activa" in res_idx.stdout

    # 4. List revisions
    res_rev_list = runner.invoke(app, ["index", "list", proj_name])
    assert res_rev_list.exit_code == 0
    assert "active" in res_rev_list.stdout.lower()

    # 5. Search
    res_search = runner.invoke(app, ["search", proj_name, "hexagonal architecture", "--mode", "hybrid"])
    assert res_search.exit_code == 0
    assert "Recuperados:" in res_search.stdout
    assert "hexagonal ports" in res_search.stdout

    # 6. Search JSON output
    res_search_json = runner.invoke(app, ["search", proj_name, "hexagonal", "--json"])
    assert res_search_json.exit_code == 0
    data = json.loads(res_search_json.stdout)
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "citation" in data[0]
