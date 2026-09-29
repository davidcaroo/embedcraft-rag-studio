"""Structured data readers: CSV, JSON, and JSONL."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, ClassVar

from embedcraft.domain.entities import CanonicalDocument
from embedcraft.domain.exceptions import DocumentError


class CSVReader:
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {".csv", ".tsv"}

    def supports(self, extension: str, mime_type: str = "") -> bool:
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        return ext in self.SUPPORTED_EXTENSIONS or "text/csv" in mime_type

    def extract(
        self,
        file_path: Path,
        document_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        try:
            with file_path.open("r", encoding="utf-8-sig", errors="replace") as f:
                # Detect delimiter
                sample = f.read(2048)
                f.seek(0)
                delimiter = "\t" if file_path.suffix.lower() == ".tsv" else ","
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    delimiter = dialect.delimiter
                except Exception:  # noqa: BLE001, S110
                    pass

                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)
        except Exception as e:
            raise DocumentError(
                message=f"Error leyendo archivo CSV: {file_path.name}",
                technical_detail=str(e),
            ) from e

        text_lines = []
        if rows:
            header = rows[0]
            text_lines.append("Columnas: " + " | ".join(header))
            for idx, r in enumerate(rows[1:], start=1):
                # Associate each cell with header name if available
                pairs = [f"{header[i]}: {r[i]}" if i < len(header) else str(r[i]) for i in range(len(r))]
                text_lines.append(f"Fila {idx}: " + "; ".join(pairs))

        return CanonicalDocument(
            document_id=document_id,
            title=file_path.stem,
            text="\n".join(text_lines),
            sections=[{"title": "Datos Tabulares", "row_count": len(rows)}],
            tables=[{"row_count": len(rows), "columns": rows[0] if rows else []}],
            metadata={**(metadata or {}), "row_count": len(rows)},
            source_locator=str(file_path),
        )


class JSONReader:
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {".json", ".jsonl"}

    def supports(self, extension: str, mime_type: str = "") -> bool:
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        return ext in self.SUPPORTED_EXTENSIONS or "application/json" in mime_type

    def extract(
        self,
        file_path: Path,
        document_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        ext = file_path.suffix.lower()
        text_parts: list[str] = []

        try:
            if ext == ".jsonl":
                with file_path.open("r", encoding="utf-8-sig", errors="replace") as f:
                    for line_idx, line in enumerate(f, start=1):
                        line_str = line.strip()
                        if line_str:
                            item = json.loads(line_str)
                            text_parts.append(f"Registro {line_idx}:\n" + json.dumps(item, ensure_ascii=False, indent=2))
            else:
                raw_json = file_path.read_text(encoding="utf-8-sig", errors="replace")
                data = json.loads(raw_json)
                if isinstance(data, list):
                    for idx, item in enumerate(data, start=1):
                        text_parts.append(f"Elemento {idx}:\n" + json.dumps(item, ensure_ascii=False, indent=2))
                else:
                    text_parts.append(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception as e:
            raise DocumentError(
                message=f"Error parseando archivo JSON/JSONL: {file_path.name}",
                technical_detail=str(e),
            ) from e

        return CanonicalDocument(
            document_id=document_id,
            title=file_path.stem,
            text="\n\n".join(text_parts),
            sections=[{"title": "Estructura JSON", "format": ext}],
            tables=[],
            metadata=metadata or {},
            source_locator=str(file_path),
        )
