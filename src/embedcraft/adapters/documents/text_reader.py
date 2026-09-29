"""Text and Markdown document reader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from embedcraft.domain.entities import CanonicalDocument
from embedcraft.domain.exceptions import DocumentError


class TextReader:
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {".txt", ".md", ".markdown", ".rst"}

    def supports(self, extension: str, mime_type: str = "") -> bool:
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        return ext in self.SUPPORTED_EXTENSIONS or "text/plain" in mime_type or "text/markdown" in mime_type

    def extract(
        self,
        file_path: Path,
        document_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            raise DocumentError(
                message=f"No se pudo leer el archivo de texto: {file_path.name}",
                technical_detail=str(e),
            ) from e

        # Extract basic sections if markdown headers are present
        sections = []
        current_section = "Introducción"
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            if line.startswith("#"):
                current_section = line.lstrip("#").strip()
                sections.append({"title": current_section, "line": idx + 1})

        return CanonicalDocument(
            document_id=document_id,
            title=file_path.stem,
            text=content,
            sections=sections,
            tables=[],
            metadata=metadata or {},
            source_locator=str(file_path),
        )
