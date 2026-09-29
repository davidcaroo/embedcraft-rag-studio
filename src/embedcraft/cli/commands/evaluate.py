"""CLI command for benchmarking RAG projects against evaluation datasets."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from embedcraft.bootstrap.container import container
from embedcraft.domain.exceptions import EmbedCraftError
from embedcraft.domain.value_objects import SearchMode

console = Console()


def evaluate_cmd(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto a evaluar."),
    dataset: str = typer.Argument(..., help="Ruta al archivo JSON con el conjunto de evaluación."),
    top_k: int = typer.Option(10, "--k", "-k", help="Profundidad Top-K de recuperación para la evaluación."),
    mode: str = typer.Option(
        "hybrid",
        "--mode",
        "-m",
        help="Modo de búsqueda a evaluar: 'hybrid', 'vector' o 'lexical'.",
    ),
    as_json: bool = typer.Option(
        False,
        "--json",
        help="Emitir los resultados y métricas en formato JSON estructurado.",
    ),
) -> None:
    """Evaluar la precisión técnica (Recall@K, Hit Rate, MRR, Cobertura de Citas) contra un dataset."""
    try:
        search_mode = SearchMode(mode.lower())
    except ValueError:
        console.print(f"[bold red]Modo no válido:[/bold red] '{mode}'. Opciones: hybrid, vector, lexical.")
        raise typer.Exit(code=1)

    try:
        with container.get_session() as session:
            eval_svc = container.get_evaluation_service(session)
            report = eval_svc.evaluate_from_file(
                project_name=project,
                file_path=Path(dataset),
                top_k=top_k,
                mode=search_mode,
            )

        if as_json:
            print(report.model_dump_json())
            return

        # Render rich results
        table = Table(title=f"Resultados de Evaluación RAG — Proyecto: {report.project_name}")
        table.add_column("Métrica", style="bold cyan")
        table.add_column("Valor", justify="right")
        table.add_column("Objetivo Recomendado", style="dim")

        table.add_row("Total Consultas Evaluadas", str(report.total_queries), "—")
        table.add_row("Top-K Evaluado", str(report.k), "—")
        table.add_row(
            "Hit Rate",
            f"[{'bold green' if report.hit_rate >= 0.8 else 'bold yellow'}]{report.hit_rate:.1%}[/]",
            "≥ 80.0%",
        )
        table.add_row(
            "MRR (Mean Reciprocal Rank)",
            f"[{'bold green' if report.mrr >= 0.7 else 'bold yellow'}]{report.mrr:.3f}[/]",
            "≥ 0.700",
        )
        table.add_row(
            f"Recall@{report.k}",
            f"[{'bold green' if report.recall_at_k >= 0.8 else 'bold yellow'}]{report.recall_at_k:.1%}[/]",
            "≥ 80.0%",
        )
        table.add_row(
            f"Precision@{report.k}",
            f"{report.precision_at_k:.1%}",
            "—",
        )
        table.add_row(
            "Cobertura de Citas",
            f"[{'bold green' if report.citation_coverage >= 0.9 else 'bold yellow'}]{report.citation_coverage:.1%}[/]",
            "≥ 95.0%",
        )
        table.add_row(
            "Latencia Promedio",
            f"{report.avg_latency_ms:.1f} ms",
            "< 150 ms",
        )

        console.print(table)

    except EmbedCraftError as exc:
        if as_json:
            print(json.dumps(exc.to_dict()))
        else:
            console.print(f"[bold red]Error en evaluación:[/bold red] {exc.message}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        if as_json:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[bold red]Error inesperado:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
