"""CLI commands for managing collections."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from embedcraft.bootstrap.container import container
from embedcraft.domain.entities import Collection

app = typer.Typer(name="collection", help="Administración de colecciones de índices.")
console = Console()


@app.command("list")
def list_collections(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir en JSON."),
):
    """Listar colecciones de un proyecto."""
    with container.get_session() as session:
        proj_svc = container.get_project_service(session)
        col_repo = container.get_collection_repository(session)

        proj = proj_svc.get_project(project)
        if not proj:
            console.print(f"[bold red]Error:[/bold red] Proyecto '{project}' no encontrado.")
            raise typer.Exit(code=1)

        cols = col_repo.list_by_project(proj.id)
        if as_json:
            console.print_json(json.dumps([c.model_dump(mode="json") for c in cols]))
            return

        if not cols:
            console.print(f"[yellow]El proyecto '{project}' no tiene colecciones creadas aún.[/yellow]")
            return

        table = Table(title=f"Colecciones de '{project}'")
        table.add_column("Nombre", style="bold cyan")
        table.add_column("Modelo de Embeddings")
        table.add_column("Dimensión", justify="right")
        table.add_column("Métrica")
        table.add_column("Backend")

        for c in cols:
            table.add_row(c.name, c.embedding_model, str(c.dimension), c.distance_metric.value, c.vector_store_type)
        console.print(table)


@app.command("create")
def create_collection(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto."),
    name: str = typer.Argument(..., help="Nombre de la colección."),
    model: str = typer.Option("all-MiniLM-L6-v2", "--model", "-m", help="Nombre del modelo de embeddings."),
    dimension: int = typer.Option(384, "--dimension", "-d", help="Dimensión del vector."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir en JSON."),
):
    """Crear una nueva colección con modelo de embeddings y métricas específicas."""
    with container.get_session() as session:
        proj_svc = container.get_project_service(session)
        col_repo = container.get_collection_repository(session)

        proj = proj_svc.get_project(project)
        if not proj:
            console.print(f"[bold red]Error:[/bold red] Proyecto '{project}' no encontrado.")
            raise typer.Exit(code=1)

        existing = col_repo.get_by_name(proj.id, name)
        if existing:
            console.print(f"[bold red]Error:[/bold red] La colección '{name}' ya existe en el proyecto.")
            raise typer.Exit(code=1)

        col = Collection(
            project_id=proj.id,
            name=name,
            embedding_model=model,
            dimension=dimension,
        )
        created = col_repo.create(col)

        if as_json:
            console.print_json(json.dumps(created.model_dump(mode="json")))
            return

        console.print(f"[bold green][OK][/bold green] Colección '[bold cyan]{created.name}[/bold cyan]' creada.")
        console.print(f"  Modelo: {created.embedding_model} (dim={created.dimension})")


@app.command("inspect")
def inspect_collection(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto."),
    collection: str = typer.Argument(..., help="Nombre de la colección."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir en JSON."),
):
    """Inspeccionar detalles de configuración y métricas de una colección."""
    with container.get_session() as session:
        proj_svc = container.get_project_service(session)
        col_repo = container.get_collection_repository(session)

        proj = proj_svc.get_project(project)
        if not proj:
            console.print(f"[bold red]Error:[/bold red] Proyecto '{project}' no encontrado.")
            raise typer.Exit(code=1)

        col = col_repo.get_by_name(proj.id, collection)
        if not col:
            console.print(f"[bold red]Error:[/bold red] Colección '{collection}' no encontrada.")
            raise typer.Exit(code=1)

        if as_json:
            console.print_json(json.dumps(col.model_dump(mode="json")))
            return

        console.print(f"\n[bold cyan]Colección: {col.name}[/bold cyan]")
        console.print(f"  ID: {col.id}")
        console.print(f"  Proyecto: {proj.name}")
        console.print(f"  Modelo Embeddings: {col.embedding_model}")
        console.print(f"  Dimensión: {col.dimension}")
        console.print(f"  Métrica de distancia: {col.distance_metric.value}")
        console.print(f"  Backend vectorial: {col.vector_store_type}\n")
