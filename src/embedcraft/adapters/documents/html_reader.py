"""HTML document reader using BeautifulSoup."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from bs4 import BeautifulSoup

from embedcraft.domain.entities import CanonicalDocument
from embedcraft.domain.exceptions import DocumentError


class HTMLReader:
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {".html", ".htm", ".xhtml"}

    def supports(self, extension: str, mime_type: str = "") -> bool:
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        return ext in self.SUPPORTED_EXTENSIONS or "text/html" in mime_type

    def extract(
        self,
        file_path: Path,
        document_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        try:
            raw_html = file_path.read_text(encoding="utf-8-sig", errors="replace")
            soup = BeautifulSoup(raw_html, "html.parser")
        except Exception as e:
            raise DocumentError(
                message=f"Error parseando documento HTML: {file_path.name}",
                technical_detail=str(e),
            ) from e

        # Remove script and style elements
        for element in soup(["script", "style", "noscript", "svg"]):
            element.decompose()

        title = file_path.stem
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        sections = []
        for header in soup.find_all(["h1", "h2", "h3", "h4"]):
            h_text = header.get_text().strip()
            if h_text:
                sections.append({"title": h_text, "tag": header.name})

        # Extract visible text
        text = soup.get_text(separator="\n", strip=True)

        return CanonicalDocument(
            document_id=document_id,
            title=title,
            text=text,
            sections=sections,
            tables=[],
            metadata={**(metadata or {}), "page_title": title},
            source_locator=str(file_path),
        )
