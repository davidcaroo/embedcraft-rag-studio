"""CLI tests for embedcraft evaluate command."""

import json
import uuid

from typer.testing import CliRunner

from embedcraft.cli.app import app

runner = CliRunner()


def test_cli_evaluate_flow(tmp_path):
    proj_name = f"eval-proj-{uuid.uuid4().hex[:6]}"
    doc_dir = tmp_path / "docs"
    doc_dir.mkdir(parents=True, exist_ok=True)
    doc_file = doc_dir / "policy.txt"
    doc_file.write_text(
        "EmbedCraft zero-hallucination policy requires explicit citation of source grounding.",
        encoding="utf-8",
    )

    # 1. Setup project, source, ingest, index
    runner.invoke(app, ["project", "create", proj_name])
    runner.invoke(app, ["source", "add", proj_name, str(doc_dir)])
    runner.invoke(app, ["ingest", "run", proj_name])
    runner.invoke(app, ["index", "publish", proj_name, "--collection", "default"])

    # 2. Create evaluation dataset
    dataset_file = tmp_path / "benchmark.json"
    dataset_content = [
        {
            "query": "zero-hallucination policy grounding",
            "expected_documents": ["policy.txt"],
        },
        {
            "query": "unrelated quantum mechanics string theory",
            "expected_documents": ["quantum.pdf"],
        },
    ]
    dataset_file.write_text(json.dumps(dataset_content), encoding="utf-8")

    # 3. Run evaluation with --json
    res = runner.invoke(app, ["evaluate", proj_name, str(dataset_file), "--k", "5", "--json"])
    assert res.exit_code == 0
    clean_out = res.stdout[res.stdout.find("{") :]
    report = json.loads(clean_out)

    assert report["project_name"] == proj_name
    assert report["total_queries"] == 2
    assert report["k"] == 5
    assert report["hit_rate"] == 0.5
    assert len(report["results"]) == 2

    # 4. Run evaluation with standard terminal output
    res_text = runner.invoke(app, ["evaluate", proj_name, str(dataset_file), "--k", "5"])
    assert res_text.exit_code == 0
    assert "Resultados de Evaluación RAG" in res_text.stdout
    assert "Hit Rate" in res_text.stdout
