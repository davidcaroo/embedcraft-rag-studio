"""CLI commands for .ecraft export, import, and package verification."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from embedcraft.bootstrap.container import container
from embedcraft.domain.exceptions import EmbedCraftError

console = Console()
package_app = typer.Typer(name="package", help="Inspección y verificación de paquetes portables .ecraft.")


def export_cmd(
    project: str = typer.Argument(..., help="Nombre o ID del proyecto a exportar."),
    output: str = typer.Argument(..., help="Ruta de destino del archivo .ecraft a generar."),
    include_vectors: bool = typer.Option(
        True,
        "--include-vectors/--no-vectors",
        help="Incluir tabla de embeddings vectoriales en el paquete.",
    ),
    as_json: bool = typer.Option(
        False,
        "--json",
        help="Emitir la salida en formato JSON estructurado.",
    ),
) -> None:
    """Exportar un proyecto completo y sus artefactos a un archivo portable .ecraft."""
    try:
        with container.get_session() as session:
            export_svc = container.get_export_service(session)
            manifest = export_svc.export_project(
                project_name_or_id=project,
                output_file=Path(output),
                include_vectors=include_vectors,
            )

        if as_json:
            print(manifest.model_dump_json())
            return

        panel_text = (
            f"[bold green]Proyecto exportado exitosamente a formato .ecraft[/bold green]\n\n"
            f"[bold]Proyecto:[/bold] {manifest.project_name} ([dim]{manifest.project_id}[/dim])\n"
            f"[bold]Destino:[/bold] {output}\n"
            f"[bold]Versión de Formato:[/bold] {manifest.format_version}\n"
            f"[bold]Documentos:[/bold] {manifest.document_count} | [bold]Chunks:[/bold] {manifest.chunk_count}\n"
            f"[bold]Modelo de Embeddings:[/bold] {manifest.embedding_model} ({manifest.dimension}d)\n"
            f"[bold]Vectores Incluidos:[/bold] {'Sí' if manifest.has_vectors else 'No'}\n"
            f"[bold]Archivos Empaquetados:[/bold] {len(manifest.files)}"
        )
        console.print(Panel(panel_text, title="Exportación Completada", border_style="cyan"))

    except EmbedCraftError as exc:
        if as_json:
            console.print_json(json.dumps(exc.to_dict()))
        else:
            console.print(f"[bold red]Error en exportación:[/bold red] {exc.message}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        if as_json:
            console.print_json(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[bold red]Error inesperado:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


def import_cmd(
    package: str = typer.Argument(..., help="Ruta al archivo .ecraft a importar."),
    name: str | None = typer.Option(
        None,
        "--name",
        "-n",
        help="Nombre alternativo para el proyecto importado.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Sobrescribir si ya existe un proyecto con el mismo nombre.",
    ),
    as_json: bool = typer.Option(
        False,
        "--json",
        help="Emitir la salida en formato JSON estructurado.",
    ),
) -> None:
    """Importar un proyecto desde un archivo portable .ecraft con verificación de integridad."""
    try:
        with container.get_session() as session:
            import_svc = container.get_import_service(session)
            imported_project = import_svc.import_project(
                package_file=Path(package),
                target_project_name=name,
                overwrite=overwrite,
            )
            session.commit()

        if as_json:
            print(imported_project.model_dump_json())
            return

        panel_text = (
            f"[bold green]Proyecto importado exitosamente desde .ecraft[/bold green]\n\n"
            f"[bold]Nombre:[/bold] {imported_project.name}\n"
            f"[bold]ID Asignado:[/bold] {imported_project.id}\n"
            f"[bold]Descripción:[/bold] {imported_project.description}\n"
            f"[bold]Origen:[/bold] {package}"
        )
        console.print(Panel(panel_text, title="Importación Completada", border_style="green"))

    except EmbedCraftError as exc:
        if as_json:
            print(json.dumps(exc.to_dict()))
        else:
            console.print(f"[bold red]Error en importación:[/bold red] {exc.message}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        if as_json:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[bold red]Error inesperado:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@package_app.command("verify")
def verify_package_cmd(
    package: str = typer.Argument(..., help="Ruta al archivo .ecraft a verificar."),
    as_json: bool = typer.Option(
        False,
        "--json",
        help="Emitir el diagnóstico en formato JSON estructurado.",
    ),
) -> None:
    """Verificar la integridad criptográfica SHA-256 y seguridad de un paquete .ecraft sin importarlo."""
    try:
        with container.get_session() as session:
            import_svc = container.get_import_service(session)
            res = import_svc.verify_package(package_file=Path(package))

        if as_json:
            print(json.dumps(res))
            if not res["is_valid"]:
                raise typer.Exit(code=1)
            return

        if res["is_valid"]:
            manifest = res.get("manifest", {})
            table = Table(title="Detalle del Paquete .ecraft")
            table.add_column("Propiedad", style="cyan bold")
            table.add_column("Valor")

            table.add_row("Proyecto", manifest.get("project_name", "N/A"))
            table.add_row("Versión de Formato", manifest.get("format_version", "N/A"))
            table.add_row("Modelo de Embeddings", f"{manifest.get('embedding_model', 'N/A')} ({manifest.get('dimension', 'N/A')}d)")
            table.add_row("Documentos declarados", str(manifest.get("document_count", 0)))
            table.add_row("Chunks declarados", str(manifest.get("chunk_count", 0)))
            table.add_row("Archivos verificados SHA-256", f"[bold green]{res['files_verified']}[/bold green]")
            table.add_row("Estado de Integridad", "[bold green]INTEGRO (VALIDADO)[/bold green]")

            console.print(table)
        else:
            console.print(Panel(
                "[bold red]El paquete presenta fallos de integridad:[/bold red]\n" +
                "\n".join(f"• {err}" for err in res["errors"]),
                title="Verificación Fallida",
                border_style="red"
            ))
            raise typer.Exit(code=1)

    except EmbedCraftError as exc:
        if as_json:
            console.print_json(json.dumps(exc.to_dict()))
        else:
            console.print(f"[bold red]Error de verificación:[/bold red] {exc.message}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        if as_json:
            console.print_json(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[bold red]Error inesperado:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
