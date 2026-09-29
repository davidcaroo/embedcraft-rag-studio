"""Main CLI application entrypoint for EmbedCraft RAG Studio."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from embedcraft import __version__
from embedcraft.bootstrap.container import container
from embedcraft.cli.commands import ingest, project, source

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
    """Iniciar la interfaz gráfica de usuario PySide6 (Fase 4)."""
    console.print("[bold cyan]EmbedCraft RAG Studio GUI[/bold cyan]")
    console.print("[yellow]La interfaz gráfica completa está programada para la Fase 4.[/yellow]")
    console.print("El núcleo de datos, repositorios y CLI están completamente operativos.")


def main():
    app()


if __name__ == "__main__":
    main()
