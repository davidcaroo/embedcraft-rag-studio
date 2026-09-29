"""PDF document reader using PyMuPDF (fitz)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import pymupdf

from embedcraft.domain.entities import CanonicalDocument
from embedcraft.domain.exceptions import DocumentError


class PDFReader:
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {".pdf"}

    def supports(self, extension: str, mime_type: str = "") -> bool:
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        return ext in self.SUPPORTED_EXTENSIONS or "application/pdf" in mime_type

    def extract(
        self,
        file_path: Path,
        document_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        try:
            doc = pymupdf.open(file_path)
        except Exception as e:
            raise DocumentError(
                message=f"No se pudo abrir el documento PDF: {file_path.name}",
                technical_detail=str(e),
            ) from e

        text_pages: list[str] = []
        sections: list[dict[str, Any]] = []

        try:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text("text").strip()
                if page_text:
                    text_pages.append(f"--- Página {page_num + 1} ---\n{page_text}")
                    sections.append({"title": f"Página {page_num + 1}", "page": page_num + 1})

            doc_metadata = doc.metadata or {}
            combined_metadata = {**(metadata or {}), **doc_metadata, "page_count": len(doc)}
        finally:
            doc.close()

        full_text = "\n\n".join(text_pages)
        return CanonicalDocument(
            document_id=document_id,
            title=file_path.stem,
            text=full_text,
            sections=sections,
            tables=[],
            metadata=combined_metadata,
            source_locator=str(file_path),
        )
