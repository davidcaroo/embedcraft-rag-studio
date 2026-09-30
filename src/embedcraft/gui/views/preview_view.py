"""Preview view with 3-pane inspection: documents, canonical text, and chunks."""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from embedcraft.bootstrap.container import container
from embedcraft.gui.components.card import Card


class PreviewView(QWidget):
    """3-pane interactive inspector for documents, canonical text, and chunks."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("workspace")
        self._current_project_id: str | None = None
        self._selected_doc_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        header = QHBoxLayout()
        title = QLabel("Previsualización e Inspección Documental", self)
        title.setObjectName("viewTitle")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # 3-pane Splitter
        splitter = QSplitter(self)

        # Pane 1: Documents Table
        doc_card = Card("1. Documentos", "Catálogo de documentos registrados", self)
        self.doc_table = QTableWidget(self)
        self.doc_table.setColumnCount(2)
        self.doc_table.setHorizontalHeaderLabels(["Ruta / Archivo", "Estado"])
        self.doc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.doc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.doc_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.doc_table.setSelectionMode(QTableWidget.SingleSelection)
        self.doc_table.itemSelectionChanged.connect(self._on_doc_selected)
        doc_card.add_widget(self.doc_table)
        splitter.addWidget(doc_card)

        # Pane 2: Canonical Normal Text
        text_card = Card("2. Texto Normalizado", "Contenido canónico extraído", self)
        self.text_viewer = QPlainTextEdit(self)
        self.text_viewer.setReadOnly(True)
        text_card.add_widget(self.text_viewer)
        splitter.addWidget(text_card)

        # Pane 3: Chunks & Metadata
        chunks_card = Card("3. Fragmentos (Chunks)", "Estrategia aplicada y metadatos", self)
        self.chunk_table = QTableWidget(self)
        self.chunk_table.setColumnCount(3)
        self.chunk_table.setHorizontalHeaderLabels(["#", "Tokens", "Texto"])
        self.chunk_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.chunk_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.chunk_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.chunk_table.setSelectionBehavior(QTableWidget.SelectRows)
        chunks_card.add_widget(self.chunk_table)

        self.chunk_detail = QPlainTextEdit(self)
        self.chunk_detail.setMaximumHeight(150)
        self.chunk_detail.setReadOnly(True)
        chunks_card.add_widget(self.chunk_detail)
        self.chunk_table.itemSelectionChanged.connect(self._on_chunk_selected)

        splitter.addWidget(chunks_card)

        splitter.setSizes([280, 500, 380])
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(2, 3)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setCollapsible(2, False)
        layout.addWidget(splitter)

    def set_project(self, project_id: str):
        self._current_project_id = project_id
        self.reload_documents()

    def reload_documents(self):
        self.doc_table.setRowCount(0)
        self.text_viewer.clear()
        self.chunk_table.setRowCount(0)
        self.chunk_detail.clear()

        if not self._current_project_id:
            return

        try:
            with container.get_session() as session:
                doc_repo = container.get_document_repository(session)
                docs = doc_repo.list_by_project(self._current_project_id)

                self.doc_table.setRowCount(len(docs))
                for idx, d in enumerate(docs):
                    item = QTableWidgetItem(d.relative_path)
                    item.setData(32, d.id)
                    self.doc_table.setItem(idx, 0, item)
                    self.doc_table.setItem(idx, 1, QTableWidgetItem(d.status.value.upper()))

                if docs:
                    self.doc_table.selectRow(0)

        except Exception:
            pass

    def _on_doc_selected(self):
        items = self.doc_table.selectedItems()
        if not items:
            return
        doc_id = items[0].data(32)
        self._selected_doc_id = doc_id
        self._load_doc_details(doc_id)

    def _load_doc_details(self, document_id: str):
        self.text_viewer.clear()
        self.chunk_table.setRowCount(0)
        self.chunk_detail.clear()

        try:
            with container.get_session() as session:
                doc_repo = container.get_document_repository(session)
                ver = doc_repo.get_latest_version(document_id)
                if not ver:
                    self.text_viewer.setPlainText("El documento aún no tiene una versión procesada.")
                    return

                self.text_viewer.setPlainText(ver.canonical_text)

                chunks = doc_repo.get_chunks_for_version(ver.id)
                self.chunk_table.setRowCount(len(chunks))
                for idx, c in enumerate(chunks):
                    item_idx = QTableWidgetItem(str(c.chunk_index))
                    item_idx.setData(32, c.text)
                    self.chunk_table.setItem(idx, 0, item_idx)
                    self.chunk_table.setItem(idx, 1, QTableWidgetItem(str(c.token_count)))
                    preview_txt = c.text.replace("\n", " ")[:60]
                    self.chunk_table.setItem(idx, 2, QTableWidgetItem(preview_txt))

                if chunks:
                    self.chunk_table.selectRow(0)

        except Exception:
            pass

    def _on_chunk_selected(self):
        items = self.chunk_table.selectedItems()
        if not items:
            return
        full_text = items[0].data(32)
        self.chunk_detail.setPlainText(full_text or "")
