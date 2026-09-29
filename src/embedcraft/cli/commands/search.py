"""CLI command for semantic, lexical, and hybrid search with citations."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel

from embedcraft.bootstrap.container import container
from embedcraft.domain.exceptions import EmbedCraftError
from embedcraft.domain.value_objects import SearchMode

console = Console()


def search_cmd(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto."),
    query: str = typer.Argument(..., help="Pregunta o consulta de búsqueda."),
    mode: str = typer.Option("hybrid", "--mode", "-m", help="Modo: hybrid, vector, lexical."),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Número de fragmentos a recuperar."),
    collection: str = typer.Option("default", "--collection", "-c", help="Colección a consultar."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir resultados en JSON."),
):
    """Ejecutar búsqueda RAG con trazabilidad de citas a fuentes originales."""
    search_mode = SearchMode(mode.lower())

    with container.get_session() as session:
        indexing_svc = container.get_indexing_service(session)
        try:
            results = indexing_svc.search(
                project_identifier=project,
                query=query,
                collection_name=collection,
                mode=search_mode,
                top_k=top_k,
            )
        except EmbedCraftError as e:
            console.print(f"[bold red]Error:[/bold red] {e.message}")
            raise typer.Exit(code=1)

        if as_json:
            console.print_json(json.dumps([r.model_dump(mode="json") for r in results]))
            return

        if not results:
            console.print(f"[yellow]No se encontraron fragmentos relevantes para: '{query}'[/yellow]")
            return

        console.print(f"\n[bold cyan]Resultados de búsqueda ({mode.upper()}) para:[/bold cyan] '[bold]{query}[/bold]'")
        console.print(f"Recuperados: {len(results)} fragmento(s)\n")

        for idx, res in enumerate(results, start=1):
            cite = res.citation
            sec_info = f" | Sección: {cite.section}" if cite.section else ""
            page_info = f" | Pág: {cite.page}" if cite.page else ""
            header = f"#{idx} [Score: {res.score:.4f}] Documento: {cite.document_path}{sec_info}{page_info}"

            content = f"{res.text.strip()}\n\n[dim]Chunk ID: {res.chunk_id}[/dim]"
            console.print(Panel(content, title=header, expand=False, border_style="cyan"))
