"""CLI tests for embedcraft chat command."""

import json
import uuid
from pathlib import Path

from typer.testing import CliRunner

from embedcraft.cli.app import app

runner = CliRunner()


def test_cli_chat_direct_query_and_json(tmp_path: Path):
    proj_name = f"chat_proj_{uuid.uuid4().hex[:8]}"
    runner.invoke(app, ["project", "create", proj_name])

    # Add source file with knowledge
    doc_path = tmp_path / "system_spec.txt"
    doc_path.write_text("EmbedCraft RAG Studio implements zero-hallucination citation grounding.")

    runner.invoke(app, ["source", "add", proj_name, str(doc_path)])
    runner.invoke(app, ["ingest", "run", proj_name])
    runner.invoke(app, ["index", "publish", proj_name])

    # 1. Direct query mode
    res_chat = runner.invoke(app, ["chat", proj_name, "--query", "citation grounding", "--mode", "hybrid"])
    assert res_chat.exit_code == 0
    assert "Respuesta RAG" in res_chat.stdout
    assert "citation grounding" in res_chat.stdout

    # 2. JSON output mode
    res_json = runner.invoke(app, ["chat", proj_name, "--query", "grounding", "--json"])
    assert res_json.exit_code == 0
    json_start = res_json.stdout.find("{")
    assert json_start != -1
    data = json.loads(res_json.stdout[json_start:])
    assert "answer" in data
    assert "latencies" in data
    assert "citations" in data
    assert len(data["citations"]) >= 1

    # 3. Retrieval-only mode
    res_ro = runner.invoke(app, ["chat", proj_name, "--query", "grounding", "--retrieval-only"])
    assert res_ro.exit_code == 0
    assert "SOLO RECUPERACIÓN" in res_ro.stdout
