"""CLI command for interactive and direct RAG chat with technical diagnostics."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from embedcraft.bootstrap.container import container
from embedcraft.domain.exceptions import EmbedCraftError
from embedcraft.domain.value_objects import SearchMode

app = typer.Typer(name="chat", help="Chat interactivo RAG y diagnóstico de recuperación.")
console = Console()


def _render_session(session_data, as_json: bool = False):
    if as_json:
        console.print_json(json.dumps(session_data.model_dump(mode="json"), indent=2))
        return

    # 1. Answer Panel
    title = f"[bold cyan]Respuesta RAG[/bold cyan] ({session_data.mode.upper()})"
    if session_data.retrieval_only:
        title += " [yellow][SOLO RECUPERACIÓN][/yellow]"
    console.print(Panel(session_data.answer, title=title, border_style="cyan"))

    # 2. Citations Table
    if session_data.citations:
        table = Table(title="Citas y Fuentes Fundamentadas")
        table.add_column("#", justify="center", style="bold")
        table.add_column("Documento", style="cyan")
        table.add_column("Página / Sección")
        table.add_column("Fragmento")

        for idx, cite in enumerate(session_data.citations, start=1):
            pos = []
            if cite.page:
                pos.append(f"Pág. {cite.page}")
            if cite.section:
                pos.append(f"Sec. {cite.section}")
            pos_str = " | ".join(pos) if pos else "—"

            table.add_row(str(idx), cite.document_path, pos_str, cite.snippet.replace("\n", " ")[:80] + "...")
        console.print(table)

    # 3. Technical Diagnostics Summary
    lat = session_data.latencies
    tok = session_data.tokens
    diag_text = (
        f"[dim]Latencias: Recuperación: {lat.retrieval_ms:.1f}ms | Rerank: {lat.rerank_ms:.1f}ms | "
        f"Generación: {lat.generation_ms:.1f}ms | Total: {lat.total_ms:.1f}ms | "
        f"Tokens: Prompt: {tok.prompt_tokens} | Comp: {tok.completion_tokens} | Total: {tok.total_tokens}[/dim]"
    )
    console.print(diag_text)
    console.print()


def chat_cmd(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto."),
    query: str = typer.Option(None, "--query", "-q", help="Consulta directa (omita para modo interactivo)."),
    mode: str = typer.Option("hybrid", "--mode", "-m", help="Modo: hybrid, vector, lexical."),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Número de fragmentos a recuperar."),
    collection: str = typer.Option("default", "--collection", "-c", help="Colección a consultar."),
    rerank: bool = typer.Option(False, "--rerank", help="Aplicar reranker léxico."),
    retrieval_only: bool = typer.Option(False, "--retrieval-only", help="Solo recuperar fragmentos sin invocar LLM."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir sesión de diagnóstico en JSON."),
):
    """Ejecutar sesión de chat RAG con fundamentación estricta y citas."""
    search_mode = SearchMode(mode.lower())

    with container.get_session() as session:
        chat_svc = container.get_chat_service(session)

        # Single direct query mode
        if query:
            try:
                diag = chat_svc.ask(
                    project_identifier=project,
                    query=query,
                    collection_name=collection,
                    mode=search_mode,
                    top_k=top_k,
                    use_reranker=rerank,
                    retrieval_only=retrieval_only,
                )
                _render_session(diag, as_json=as_json)
            except EmbedCraftError as e:
                console.print(f"[bold red]Error:[/bold red] {e.message}")
                raise typer.Exit(code=1)
            return

        # Interactive REPL mode
        console.print("[bold cyan]EmbedCraft RAG Studio — Sesión de Chat Interactivo[/bold cyan]")
        console.print(f"Proyecto activo: [bold]{project}[/bold] | Modo: [bold]{mode}[/bold] | Top-K: {top_k}")
        console.print("[dim]Escriba 'salir' o 'exit' para terminar la sesión.[/dim]\n")

        while True:
            try:
                user_query = console.input("[bold green]Pregunta > [/bold green]").strip()
                if not user_query:
                    continue
                if user_query.lower() in ("exit", "quit", "salir"):
                    console.print("[yellow]Sesión finalizada.[/yellow]")
                    break

                diag = chat_svc.ask(
                    project_identifier=project,
                    query=user_query,
                    collection_name=collection,
                    mode=search_mode,
                    top_k=top_k,
                    use_reranker=rerank,
                    retrieval_only=retrieval_only,
                )
                _render_session(diag, as_json=as_json)

            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Sesión interrumpida.[/yellow]")
                break
            except EmbedCraftError as e:
                console.print(f"[bold red]Error:[/bold red] {e.message}\n")
