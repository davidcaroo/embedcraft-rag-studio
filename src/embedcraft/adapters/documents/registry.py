"""Registry for discovering and dispatching document readers."""

from __future__ import annotations

from pathlib import Path

from embedcraft.adapters.documents.html_reader import HTMLReader
from embedcraft.adapters.documents.office_reader import DocxReader, PptxReader, XlsxReader
from embedcraft.adapters.documents.pdf_reader import PDFReader
from embedcraft.adapters.documents.structured_reader import CSVReader, JSONReader
from embedcraft.adapters.documents.text_reader import TextReader
from embedcraft.domain.exceptions import DocumentError
from embedcraft.ports.documents import DocumentReader


class DocumentReaderRegistry:
    def __init__(self):
        self._readers: list[DocumentReader] = [
            TextReader(),
            PDFReader(),
            DocxReader(),
            PptxReader(),
            XlsxReader(),
            CSVReader(),
            JSONReader(),
            HTMLReader(),
        ]

    def register_reader(self, reader: DocumentReader) -> None:
        """Register a custom reader (e.g. OCR reader or domain specific)."""
        self._readers.insert(0, reader)

    def get_reader_for_file(self, file_path: Path | str, mime_type: str = "") -> DocumentReader | None:
        p = Path(file_path)
        ext = p.suffix.lower()
        for reader in self._readers:
            if reader.supports(ext, mime_type):
                return reader
        return None

    def get_reader_or_raise(self, file_path: Path | str, mime_type: str = "") -> DocumentReader:
        reader = self.get_reader_for_file(file_path, mime_type)
        if not reader:
            p = Path(file_path)
            raise DocumentError(
                message=f"Formato no compatible: '{p.suffix}' en '{p.name}'.",
                technical_detail=f"No registered reader found for suffix={p.suffix}, mime_type={mime_type}",
            )
        return reader


default_reader_registry = DocumentReaderRegistry()
