"""CLI commands for index publishing, revisions, and rollbacks."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from embedcraft.bootstrap.container import container
from embedcraft.domain.exceptions import EmbedCraftError

app = typer.Typer(name="index", help="Administración de índices y revisiones.")
console = Console()


@app.command("publish")
def publish_index(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto."),
    collection: str = typer.Option("default", "--collection", "-c", help="Colección a indexar."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir en JSON."),
):
    """Crear y publicar atómicamente una nueva revisión de índice vectorial y léxico."""
    with container.get_session() as session:
        indexing_svc = container.get_indexing_service(session)
        try:
            if not as_json:
                console.print(f"[bold cyan]Indexando y publicando revisión para '{project}'...[/bold cyan]")
            revision = indexing_svc.create_and_publish_revision(
                project_identifier=project,
                collection_name=collection,
            )
            if as_json:
                console.print_json(json.dumps(revision.model_dump(mode="json")))
                return

            console.print(f"[bold green][OK][/bold green] Revisión #[bold cyan]{revision.revision_number}[/bold cyan] publicada y activa.")
            console.print(f"  ID: {revision.id}")
            console.print(f"  Documentos: {revision.total_documents} | Fragmentos: {revision.total_chunks}")
            console.print(f"  Modelo: {revision.embedding_model} (dim={revision.dimension})")
        except EmbedCraftError as e:
            console.print(f"[bold red]Error:[/bold red] {e.message}")
            raise typer.Exit(code=1)


@app.command("list")
def list_revisions(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir en JSON."),
):
    """Listar historial de revisiones del proyecto."""
    with container.get_session() as session:
        proj_svc = container.get_project_service(session)
        rev_repo = container.get_revision_repository(session)

        proj = proj_svc.get_project(project)
        if not proj:
            console.print(f"[bold red]Error:[/bold red] Proyecto '{project}' no encontrado.")
            raise typer.Exit(code=1)

        revs = rev_repo.list_by_project(proj.id)
        if as_json:
            console.print_json(json.dumps([r.model_dump(mode="json") for r in revs]))
            return

        if not revs:
            console.print(f"[yellow]No hay revisiones para '{project}'. Use 'embedcraft index publish {project}'[/yellow]")
            return

        table = Table(title=f"Revisiones de Índice — {project}")
        table.add_column("Rev #", justify="right")
        table.add_column("Estado")
        table.add_column("Activa", justify="center")
        table.add_column("Documentos", justify="right")
        table.add_column("Fragmentos", justify="right")
        table.add_column("Publicada")

        for r in revs:
            is_active = "✔" if r.id == proj.active_revision_id else "-"
            table.add_row(
                str(r.revision_number),
                f"[bold green]{r.status.value}[/bold green]" if r.status.value == "active" else r.status.value,
                f"[bold green]{is_active}[/bold green]" if is_active == "✔" else "-",
                str(r.total_documents),
                str(r.total_chunks),
                r.published_at.strftime("%Y-%m-%d %H:%M") if r.published_at else "-",
            )
        console.print(table)


@app.command("rollback")
def rollback_index(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto."),
    revision_id: str = typer.Argument(..., help="ID de la revisión previa a restaurar."),
):
    """Hacer rollback a una revisión activa previa."""
    with container.get_session() as session:
        indexing_svc = container.get_indexing_service(session)
        try:
            rev = indexing_svc.rollback_revision(project, revision_id)
            console.print(f"[bold green][OK][/bold green] Rollback exitoso a revisión #{rev.revision_number} ({rev.id}).")
        except EmbedCraftError as e:
            console.print(f"[bold red]Error:[/bold red] {e.message}")
            raise typer.Exit(code=1)
