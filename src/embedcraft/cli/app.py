from __future__ import annotations

import json
import sys

import typer
from rich.console import Console
from rich.table import Table

# Ensure UTF-8 output on Windows consoles to prevent cp1252 charmap errors
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

from embedcraft import __version__
from embedcraft.bootstrap.container import container
from embedcraft.cli.commands import collection, index, ingest, project, search, source

app = typer.Typer(
    name="embedcraft",
    help="EmbedCraft RAG Studio: Plataforma profesional para creación, administración y prueba de sistemas RAG.",
    no_args_is_help=True,
)

console = Console()

# Register sub-commands
app.add_typer(project.app, name="project")
app.add_typer(source.app, name="source")
app.add_typer(ingest.app, name="ingest")
app.add_typer(ingest.preview_app, name="preview")
app.add_typer(collection.app, name="collection")
app.add_typer(index.app, name="index")
app.command("search")(search.search_cmd)


@app.command("version")
def version():
    """Mostrar la versión de EmbedCraft RAG Studio."""
    console.print(f"[bold cyan]EmbedCraft RAG Studio[/bold cyan] versión [bold green]{__version__}[/bold green]")


@app.command("doctor")
def doctor(
    as_json: bool = typer.Option(False, "--json", help="Imprimir diagnóstico en formato JSON."),
):
    """Comprobar el estado y salud del entorno, base de datos y dependencias."""
    checks = container.system_service.run_doctor()

    if as_json:
        console.print_json(json.dumps([c.model_dump() for c in checks]))
        return

    table = Table(title="EmbedCraft Doctor — Diagnóstico del Sistema")
    table.add_column("Categoría", style="bold")
    table.add_column("Verificación")
    table.add_column("Estado", justify="center")
    table.add_column("Mensaje / Detalle")

    has_errors = False
    for check in checks:
        if check.status == "ok":
            status_text = "[bold green]OK[/bold green]"
        elif check.status == "warning":
            status_text = "[bold yellow]ADVERTENCIA[/bold yellow]"
        else:
            status_text = "[bold red]ERROR[/bold red]"
            has_errors = True

        msg = check.message
        if check.detail:
            msg += f"\n[dim]{check.detail}[/dim]"
        table.add_row(check.category, check.name, status_text, msg)

    console.print(table)
    if has_errors:
        raise typer.Exit(code=1)


@app.command("gui")
def gui():
    """Iniciar la interfaz gráfica de usuario PySide6."""
    try:
        from embedcraft.gui.app import run_gui

        run_gui()
    except Exception as e:
        console.print(f"[bold red]Error iniciando GUI:[/bold red] {e}")
        raise typer.Exit(code=1) from e


def main():
    app()


if __name__ == "__main__":
    main()
