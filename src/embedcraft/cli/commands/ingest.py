"""CLI commands for document scanning, incremental ingestion, and previewing."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from embedcraft.bootstrap.container import container
from embedcraft.domain.entities import ProcessingProfile
from embedcraft.domain.exceptions import EmbedCraftError

app = typer.Typer(name="ingest", help="Ingestión, escaneo incremental y procesamiento de documentos.")
preview_app = typer.Typer(name="preview", help="Previsualización de documentos y fragmentos.")
console = Console()


@app.command("scan")
def scan_documents(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto a escanear."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir resultado en formato JSON."),
):
    """Escanear fuentes del proyecto y calcular diferencias incrementales (nuevos, modificados, sin cambios, eliminados)."""
    with container.get_session() as session:
        ingest_svc = container.get_ingestion_service(session)
        try:
            result = ingest_svc.scan_sources(project)
        except EmbedCraftError as e:
            console.print(f"[bold red]Error:[/bold red] {e.message}")
            raise typer.Exit(code=1)

        if as_json:
            console.print_json(json.dumps(result.model_dump(mode="json")))
            return

        table = Table(title=f"Escaneo Incremental — Proyecto: {project}")
        table.add_column("Métrica / Categoría", style="bold")
        table.add_column("Cantidad", justify="right")

        table.add_row("Total analizados", str(result.total_found))
        table.add_row("[bold green]Nuevos[/bold green]", f"[green]{result.new_count}[/green]")
        table.add_row("[bold yellow]Modificados[/bold yellow]", f"[yellow]{result.modified_count}[/yellow]")
        table.add_row("Sin cambios", str(result.unchanged_count))
        table.add_row("[bold red]Eliminados[/bold red]", f"[red]{result.deleted_count}[/red]")
        table.add_row("[dim]No compatibles[/dim]", f"[dim]{result.unsupported_count}[/dim]")

        console.print(table)


@app.command("run")
def run_ingestion(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto a procesar."),
    chunk_size: int = typer.Option(500, "--chunk-size", "-c", help="Tamaño máximo de fragmento en caracteres."),
    chunk_overlap: int = typer.Option(50, "--overlap", "-o", help="Solapamiento de fragmentos."),
    strategy: str = typer.Option("recursive", "--strategy", "-s", help="Estrategia: recursive, fixed, section."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir resultado final en formato JSON."),
):
    """Ejecutar ingestión incremental, extracción y fragmentación."""
    profile = ProcessingProfile(
        name="CLI-Profile",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunking_strategy=strategy,
    )

    with container.get_session() as session:
        ingest_svc = container.get_ingestion_service(session)
        try:
            if as_json:
                job = ingest_svc.run_ingestion(project, profile=profile)
                console.print_json(json.dumps(job.model_dump(mode="json")))
                return

            console.print(f"\n[bold cyan]Iniciando ingestión para el proyecto '{project}'...[/bold cyan]")
            console.print(f"Estrategia: [green]{strategy}[/green] | Chunk size: {chunk_size} | Overlap: {chunk_overlap}\n")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task_id = progress.add_task("Procesando documentos...", total=100)

                def update_progress(current: int, total: int, current_file: str):
                    progress.update(
                        task_id,
                        total=total,
                        completed=current,
                        description=f"[cyan]{current_file[:30]}[/cyan] ({current}/{total})",
                    )

                job = ingest_svc.run_ingestion(
                    project,
                    profile=profile,
                    progress_callback=update_progress,
                )

            step = job.steps[0] if job.steps else None
            console.print(f"\n[bold green][OK] Ingestión completada.[/bold green] Trabajo ID: [dim]{job.id}[/dim]")
            if step:
                console.print(f"  Procesados: [bold green]{step.items_processed}[/bold green] | Fallidos: [bold red]{step.items_failed}[/bold red]")

        except EmbedCraftError as e:
            console.print(f"[bold red]Error:[/bold red] {e.message}")
            raise typer.Exit(code=1)


@app.command("status")
def job_status(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir en JSON."),
):
    """Consultar historial y estado de trabajos de ingestión."""
    with container.get_session() as session:
        proj_svc = container.get_project_service(session)
        job_repo = container.get_job_repository(session)
        proj = proj_svc.get_project(project)
        if not proj:
            console.print(f"[bold red]Error:[/bold red] Proyecto '{project}' no encontrado.")
            raise typer.Exit(code=1)

        jobs = job_repo.list_by_project(proj.id)
        if as_json:
            console.print_json(json.dumps([j.model_dump(mode="json") for j in jobs]))
            return

        if not jobs:
            console.print(f"[yellow]No hay trabajos registrados para el proyecto '{project}'.[/yellow]")
            return

        table = Table(title=f"Historial de Trabajos — {project}")
        table.add_column("Job ID", style="dim")
        table.add_column("Tipo")
        table.add_column("Estado")
        table.add_column("Procesados / Total")
        table.add_column("Fecha")

        for j in jobs:
            s = j.steps[0] if j.steps else None
            counts = f"{s.items_processed}/{s.items_total}" if s else "-"
            table.add_row(
                j.id[:8] + "...",
                j.job_type,
                f"[bold green]{j.status.value}[/bold green]" if j.status.value == "completed" else j.status.value,
                counts,
                j.created_at.strftime("%Y-%m-%d %H:%M"),
            )
        console.print(table)


# Preview subcommands
@preview_app.command("doc")
def preview_doc(
    path: str = typer.Argument(..., help="Ruta local al documento para extraer texto canónico."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir salida en JSON."),
):
    """Previsualizar el texto canónico y metadatos extraídos de un archivo."""
    with container.get_session() as session:
        ingest_svc = container.get_ingestion_service(session)
        try:
            canonical_doc = ingest_svc.preview_document(path)
        except EmbedCraftError as e:
            console.print(f"[bold red]Error:[/bold red] {e.message}")
            raise typer.Exit(code=1)

        if as_json:
            console.print_json(json.dumps(canonical_doc.model_dump()))
            return

        console.print(f"\n[bold cyan]Documento Canónico: {canonical_doc.title}[/bold cyan]")
        console.print(f"Ruta: [dim]{canonical_doc.source_locator}[/dim]")
        console.print(f"Secciones identificadas: {len(canonical_doc.sections)}")
        console.print(f"Tablas extraídas: {len(canonical_doc.tables)}")
        console.print("\n[bold]Muestra de contenido extraído:[/bold]\n")
        sample_text = canonical_doc.text[:1200]
        console.print(sample_text)
        if len(canonical_doc.text) > 1200:
            console.print(f"\n[dim]... (+ {len(canonical_doc.text) - 1200} caracteres adicionales)[/dim]")


@preview_app.command("chunks")
def preview_chunks_cmd(
    path: str = typer.Argument(..., help="Ruta local al documento a fragmentar."),
    chunk_size: int = typer.Option(500, "--chunk-size", "-c", help="Tamaño de fragmento."),
    chunk_overlap: int = typer.Option(50, "--overlap", "-o", help="Solapamiento."),
    strategy: str = typer.Option("recursive", "--strategy", "-s", help="Estrategia: recursive, fixed, section."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir fragmentos en JSON."),
):
    """Previsualizar cómo se dividirá un documento en fragmentos."""
    profile = ProcessingProfile(
        name="Preview-Profile",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunking_strategy=strategy,
    )
    with container.get_session() as session:
        ingest_svc = container.get_ingestion_service(session)
        try:
            chunks = ingest_svc.preview_chunks(path, profile=profile)
        except EmbedCraftError as e:
            console.print(f"[bold red]Error:[/bold red] {e.message}")
            raise typer.Exit(code=1)

        if as_json:
            console.print_json(json.dumps([c.model_dump(mode="json") for c in chunks]))
            return

        console.print(f"\n[bold cyan]Fragmentos generados:[/bold cyan] {len(chunks)} fragmento(s)")
        for idx, chunk in enumerate(chunks[:5]):
            console.print(f"\n[bold magenta]--- Fragmento #{idx + 1} (Tokens aprox: {chunk.token_count}, Caracteres: {len(chunk.text)}) ---[/bold magenta]")
            if chunk.metadata.section:
                console.print(f"[dim]Sección: {chunk.metadata.section}[/dim]")
            if chunk.metadata.page:
                console.print(f"[dim]Página: {chunk.metadata.page}[/dim]")
            console.print(chunk.text[:300] + ("..." if len(chunk.text) > 300 else ""))

        if len(chunks) > 5:
            console.print(f"\n[dim]... y {len(chunks) - 5} fragmento(s) más no mostrados.[/dim]")
