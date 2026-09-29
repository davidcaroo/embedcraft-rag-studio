"""Tests for embedcraft Typer CLI commands."""

import json

from typer.testing import CliRunner

from embedcraft.cli.app import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "EmbedCraft RAG Studio versión" in result.stdout


def test_cli_doctor():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Diagnóstico del Sistema" in result.stdout
    assert "Versión de Python" in result.stdout


def test_cli_doctor_json():
    result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert any(c["name"] == "Versión de Python" for c in data)


def test_cli_project_flow():
    # 1. Create project
    proj_name = "cli_test_proj"
    res_create = runner.invoke(app, ["project", "create", proj_name, "--desc", "CLI Test Project"])
    assert res_create.exit_code == 0
    assert f"Proyecto '{proj_name}' creado exitosamente" in res_create.stdout

    # 2. List projects
    res_list = runner.invoke(app, ["project", "list"])
    assert res_list.exit_code == 0
    assert proj_name in res_list.stdout

    # 3. List as JSON
    res_list_json = runner.invoke(app, ["project", "list", "--json"])
    assert res_list_json.exit_code == 0
    items = json.loads(res_list_json.stdout)
    assert any(p["name"] == proj_name for p in items)

    # 4. Show project
    res_show = runner.invoke(app, ["project", "show", proj_name])
    assert res_show.exit_code == 0
    assert f"Proyecto: {proj_name}" in res_show.stdout

    # 5. Add source
    res_source = runner.invoke(app, ["source", "add", proj_name, "C:/temp/testdocs", "--name", "Docs"])
    assert res_source.exit_code == 0
    assert "Fuente 'Docs' añadida con éxito" in res_source.stdout

    # 6. List sources
    res_src_list = runner.invoke(app, ["source", "list", proj_name])
    assert res_src_list.exit_code == 0
    assert "Docs" in res_src_list.stdout

    # 7. Delete project
    res_del = runner.invoke(app, ["project", "delete", proj_name, "--yes"])
    assert res_del.exit_code == 0
    assert f"Proyecto '{proj_name}' eliminado" in res_del.stdout
