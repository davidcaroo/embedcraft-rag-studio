"""CLI commands for managing projects."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from embedcraft.bootstrap.container import container
from embedcraft.domain.exceptions import EmbedCraftError

app = typer.Typer(name="project", help="Administración de proyectos RAG.")
console = Console()


@app.command("create")
def create_project(
    name: str = typer.Argument(..., help="Nombre único del proyecto."),
    description: str = typer.Option("", "--desc", "-d", help="Descripción opcional."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir salida en formato JSON."),
):
    """Crear un nuevo proyecto RAG."""
    with container.get_session() as session:
        service = container.get_project_service(session)
        try:
            proj = service.create_project(name=name, description=description)
            if as_json:
                console.print_json(json.dumps(proj.model_dump(mode="json")))
            else:
                console.print(f"[bold green][OK][/bold green] Proyecto '[bold cyan]{proj.name}[/bold cyan]' creado exitosamente.")
                console.print(f"  [dim]ID:[/dim] {proj.id}")
                console.print(f"  [dim]Almacenamiento:[/dim] {proj.storage_path}")
        except EmbedCraftError as e:
            if as_json:
                console.print_json(json.dumps(e.to_dict()))
            else:
                console.print(f"[bold red]Error:[/bold red] {e.message}")
            raise typer.Exit(code=1)


@app.command("list")
def list_projects(
    as_json: bool = typer.Option(False, "--json", help="Imprimir salida en formato JSON."),
):
    """Listar todos los proyectos registrados."""
    with container.get_session() as session:
        service = container.get_project_service(session)
        projects = service.list_projects()

        if as_json:
            data = [p.model_dump(mode="json") for p in projects]
            console.print_json(json.dumps(data))
            return

        if not projects:
            console.print("[yellow]No hay proyectos creados aún. Use 'embedcraft project create <nombre>'[/yellow]")
            return

        table = Table(title="Proyectos RAG")
        table.add_column("Nombre", style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Descripción")
        table.add_column("Creado")

        for p in projects:
            table.add_row(
                p.name,
                p.id[:8] + "...",
                p.description or "-",
                p.created_at.strftime("%Y-%m-%d %H:%M"),
            )
        console.print(table)


@app.command("show")
def show_project(
    identifier: str = typer.Argument(..., help="Nombre o ID del proyecto."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir salida en formato JSON."),
):
    """Mostrar detalles de un proyecto específico."""
    with container.get_session() as session:
        service = container.get_project_service(session)
        proj = service.get_project(identifier)
        if not proj:
            console.print(f"[bold red]Error:[/bold red] Proyecto '{identifier}' no encontrado.")
            raise typer.Exit(code=1)

        if as_json:
            console.print_json(json.dumps(proj.model_dump(mode="json")))
            return

        console.print(f"\n[bold cyan]Proyecto: {proj.name}[/bold cyan]")
        console.print(f"  ID: {proj.id}")
        console.print(f"  Descripción: {proj.description or '-'}")
        console.print(f"  Ruta: {proj.storage_path}")
        console.print(f"  Revisión activa: {proj.active_revision_id or 'Ninguna'}")
        console.print(f"  Creado: {proj.created_at.isoformat()}\n")


@app.command("delete")
def delete_project(
    identifier: str = typer.Argument(..., help="Nombre o ID del proyecto."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirmar eliminación sin preguntar."),
):
    """Eliminar un proyecto y sus metadatos asociados."""
    if not yes:
        confirm = typer.confirm(f"¿Está seguro de que desea eliminar el proyecto '{identifier}'?")
        if not confirm:
            console.print("[dim]Operación cancelada.[/dim]")
            raise typer.Exit(code=0)

    with container.get_session() as session:
        service = container.get_project_service(session)
        deleted = service.delete_project(identifier)
        if deleted:
            console.print(f"[bold green][OK][/bold green] Proyecto '{identifier}' eliminado.")
        else:
            console.print(f"[bold red]Error:[/bold red] No se encontró el proyecto '{identifier}'.")
            raise typer.Exit(code=1)
