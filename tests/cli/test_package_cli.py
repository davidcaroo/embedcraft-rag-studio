"""CLI tests for embedcraft export, import, and package verify commands."""

import json
import uuid

from typer.testing import CliRunner

from embedcraft.cli.app import app

runner = CliRunner()


def test_cli_export_verify_import_flow(tmp_path):
    proj_name = f"cli-pack-{uuid.uuid4().hex[:6]}"
    doc_dir = tmp_path / "docs"
    doc_dir.mkdir(parents=True, exist_ok=True)
    (doc_dir / "sample.txt").write_text(
        "EmbedCraft portable format packaging enables safe cross-environment sharing.",
        encoding="utf-8",
    )

    # 1. Create project and add source
    res_create = runner.invoke(app, ["project", "create", proj_name])
    assert res_create.exit_code == 0

    res_source = runner.invoke(app, ["source", "add", proj_name, str(doc_dir)])
    assert res_source.exit_code == 0

    # 2. Ingest
    res_ingest = runner.invoke(app, ["ingest", "run", proj_name])
    assert res_ingest.exit_code == 0

    # 3. Export to .ecraft
    export_file = tmp_path / f"{proj_name}.ecraft"
    res_export = runner.invoke(app, ["export", proj_name, str(export_file), "--json"])
    assert res_export.exit_code == 0
    assert export_file.exists()

    # Parse JSON output
    clean_out = res_export.stdout[res_export.stdout.find("{") :]
    manifest_data = json.loads(clean_out)
    assert manifest_data["project_name"] == proj_name
    assert manifest_data["document_count"] >= 1

    # 4. Verify package
    res_verify = runner.invoke(app, ["package", "verify", str(export_file), "--json"])
    assert res_verify.exit_code == 0
    clean_verify = res_verify.stdout[res_verify.stdout.find("{") :]
    verify_data = json.loads(clean_verify)
    assert verify_data["is_valid"] is True
    assert verify_data["files_verified"] >= 4

    # 5. Import package into new project name
    imported_name = f"{proj_name}-restored"
    res_import = runner.invoke(app, ["import", str(export_file), "--name", imported_name, "--json"])
    assert res_import.exit_code == 0
    clean_import = res_import.stdout[res_import.stdout.find("{") :]
    import_data = json.loads(clean_import)
    assert import_data["name"] == imported_name

    # 6. Verify imported project is listed in project list
    res_list = runner.invoke(app, ["project", "list", "--json"])
    assert res_list.exit_code == 0
    clean_list = res_list.stdout[res_list.stdout.find("[") :]
    projects = json.loads(clean_list)
    assert any(p["name"] == imported_name for p in projects)
