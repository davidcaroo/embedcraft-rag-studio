"""CLI commands for managing project sources."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from embedcraft.bootstrap.container import container
from embedcraft.domain.exceptions import EmbedCraftError

app = typer.Typer(name="source", help="Administración de fuentes documentales para proyectos.")
console = Console()


@app.command("add")
def add_source(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto destino."),
    path: str = typer.Argument(..., help="Ruta local al archivo o directorio a indexar."),
    name: str | None = typer.Option(None, "--name", "-n", help="Nombre descriptivo para la fuente."),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", help="Escanear subdirectorios recursivamente."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir salida en formato JSON."),
):
    """Añadir una fuente de documentos a un proyecto."""
    with container.get_session() as session:
        service = container.get_project_service(session)
        try:
            source = service.add_source(
                project_identifier=project,
                path_or_uri=path,
                name=name,
                recursive=recursive,
            )
            if as_json:
                console.print_json(json.dumps(source.model_dump(mode="json")))
            else:
                console.print(f"[bold green][OK][/bold green] Fuente '[bold cyan]{source.name}[/bold cyan]' añadida con éxito.")
                console.print(f"  [dim]Ruta:[/dim] {source.uri_or_path}")
                console.print(f"  [dim]Recursivo:[/dim] {'Sí' if source.recursive else 'No'}")
        except EmbedCraftError as e:
            if as_json:
                console.print_json(json.dumps(e.to_dict()))
            else:
                console.print(f"[bold red]Error:[/bold red] {e.message}")
            raise typer.Exit(code=1)


@app.command("list")
def list_sources(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir salida en formato JSON."),
):
    """Listar fuentes documentales configuradas en un proyecto."""
    with container.get_session() as session:
        service = container.get_project_service(session)
        try:
            sources = service.list_sources(project)
        except EmbedCraftError as e:
            console.print(f"[bold red]Error:[/bold red] {e.message}")
            raise typer.Exit(code=1)

        if as_json:
            data = [s.model_dump(mode="json") for s in sources]
            console.print_json(json.dumps(data))
            return

        if not sources:
            console.print(f"[yellow]El proyecto no tiene fuentes configuradas aún. Use 'embedcraft source add {project} <ruta>'[/yellow]")
            return

        table = Table(title=f"Fuentes del proyecto '{project}'")
        table.add_column("Nombre", style="bold cyan")
        table.add_column("Ruta / URI")
        table.add_column("Recursivo")
        table.add_column("Activo")

        for s in sources:
            table.add_row(
                s.name,
                s.uri_or_path,
                "Sí" if s.recursive else "No",
                "Sí" if s.enabled else "No",
            )
        console.print(table)
