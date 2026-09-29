"""Interactive RAG chat and diagnostics view with citation inspection and JSON export."""

from datetime import UTC, datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from embedcraft.bootstrap.container import container
from embedcraft.domain.value_objects import SearchMode
from embedcraft.gui.components.card import Card


class ChatView(QWidget):
    """Interactive conversation and technical diagnostic view."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("workspace")
        self._current_project_id: str | None = None
        self._last_session_data = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Title
        header_layout = QHBoxLayout()
        title = QLabel("Chat de Prueba y Diagnóstico RAG", self)
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0F172A;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.btn_export = QPushButton("💾 Exportar Diagnóstico JSON", self)
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._export_json)
        header_layout.addWidget(self.btn_export)

        layout.addLayout(header_layout)

        # Splitter: Chat conversation on Left, Diagnostics Panel on Right
        splitter = QSplitter(self)

        # 1. Left Container: Chat Conversation
        chat_card = Card("Conversación", "Interacción en vivo fundamentada en el corpus", self)

        self.chat_history = QTextEdit(self)
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px;")
        chat_card.add_widget(self.chat_history)

        # Input Row
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)

        self.input_edit = QLineEdit(self)
        self.input_edit.setPlaceholderText("Escriba su pregunta sobre los documentos del proyecto...")
        self.input_edit.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_edit)

        self.btn_send = QPushButton("Enviar", self)
        self.btn_send.setProperty("class", "primaryBtn")
        self.btn_send.clicked.connect(self.send_message)
        input_layout.addWidget(self.btn_send)

        chat_card.add_layout(input_layout)

        # Options Row under input
        opt_layout = QHBoxLayout()
        self.chk_retrieval_only = QCheckBox("Modo Solo Recuperación (Auditar sin LLM)", self)
        opt_layout.addWidget(self.chk_retrieval_only)

        opt_layout.addStretch()
        btn_clear = QPushButton("Limpiar Chat", self)
        btn_clear.clicked.connect(self._clear_chat)
        opt_layout.addWidget(btn_clear)

        chat_card.add_layout(opt_layout)
        splitter.addWidget(chat_card)

        # 2. Right Container: Technical Diagnostics Inspector
        diag_card = Card("Inspector de Diagnóstico", "Trazabilidad técnica, latencias y citas", self)
        diag_card.setMinimumWidth(360)

        # Parameters Form
        param_form = QFormLayout()
        self.combo_mode = QComboBox(self)
        self.combo_mode.addItems(["hybrid", "vector", "lexical"])
        param_form.addRow("Modo de Búsqueda:", self.combo_mode)

        self.spin_topk = QSpinBox(self)
        self.spin_topk.setRange(1, 20)
        self.spin_topk.setValue(5)
        param_form.addRow("Top K Fragmentos:", self.spin_topk)

        self.chk_rerank = QCheckBox("Activar Reranker Léxico", self)
        param_form.addRow("", self.chk_rerank)

        diag_card.add_layout(param_form)

        # Latency & Token metrics box
        metrics_box = QWidget(self)
        metrics_box.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px;")
        mb_layout = QVBoxLayout(metrics_box)
        mb_layout.setContentsMargins(8, 8, 8, 8)
        mb_layout.setSpacing(4)

        self.lbl_lat_total = QLabel("Latencia Total: — ms", metrics_box)
        self.lbl_lat_total.setStyleSheet("font-weight: 700; color: #0F172A;")
        mb_layout.addWidget(self.lbl_lat_total)

        self.lbl_lat_breakdown = QLabel("Recuperación: — | Rerank: — | Gen: —", metrics_box)
        self.lbl_lat_breakdown.setStyleSheet("font-size: 11px; color: #64748B;")
        mb_layout.addWidget(self.lbl_lat_breakdown)

        self.lbl_tokens = QLabel("Tokens: Prompt: 0 | Comp: 0 | Total: 0", metrics_box)
        self.lbl_tokens.setStyleSheet("font-size: 11px; color: #64748B;")
        mb_layout.addWidget(self.lbl_tokens)

        diag_card.add_widget(metrics_box)

        # Citations Table
        lbl_cite_title = QLabel("Citas y Fuentes Utilizadas", self)
        lbl_cite_title.setStyleSheet("font-weight: 600; font-size: 12px; color: #334155; margin-top: 8px;")
        diag_card.add_widget(lbl_cite_title)

        self.cite_table = QTableWidget(self)
        self.cite_table.setColumnCount(3)
        self.cite_table.setHorizontalHeaderLabels(["#", "Documento", "Pág / Sec"])
        self.cite_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.cite_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.cite_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.cite_table.setSelectionBehavior(QTableWidget.SelectRows)
        diag_card.add_widget(self.cite_table)

        splitter.addWidget(diag_card)
        splitter.setSizes([600, 360])
        layout.addWidget(splitter)

        self._append_system_message("Bienvenido al Chat de Prueba RAG de EmbedCraft. Realice consultas fundamentadas en los documentos del proyecto activo.")

    def set_project(self, project_id: str):
        self._current_project_id = project_id
        self._append_system_message(f"Proyecto activo establecido: {project_id}")

    def send_message(self):
        query = self.input_edit.text().strip()
        if not query:
            return

        if not self._current_project_id:
            QMessageBox.warning(self, "Atención", "Seleccione un proyecto activo en el encabezado.")
            return

        self._append_user_message(query)
        self.input_edit.clear()
        self.btn_send.setEnabled(False)

        mode = SearchMode(self.combo_mode.currentText())
        top_k = self.spin_topk.value()
        use_rerank = self.chk_rerank.isChecked()
        retrieval_only = self.chk_retrieval_only.isChecked()

        try:
            with container.get_session() as session:
                chat_svc = container.get_chat_service(session)
                diag = chat_svc.ask(
                    project_identifier=self._current_project_id,
                    query=query,
                    mode=mode,
                    top_k=top_k,
                    use_reranker=use_rerank,
                    retrieval_only=retrieval_only,
                )
                self._last_session_data = diag
                self.btn_export.setEnabled(True)
                self._append_assistant_message(diag.answer, diag.citations)
                self._update_diagnostics(diag)

        except Exception as e:
            self._append_system_message(f"Error procesando consulta: {str(e)}")
        finally:
            self.btn_send.setEnabled(True)

    def _update_diagnostics(self, diag):
        lat = diag.latencies
        tok = diag.tokens

        self.lbl_lat_total.setText(f"Latencia Total: {lat.total_ms:.1f} ms")
        self.lbl_lat_breakdown.setText(
            f"Recuperación: {lat.retrieval_ms:.1f}ms | Rerank: {lat.rerank_ms:.1f}ms | Gen: {lat.generation_ms:.1f}ms"
        )
        self.lbl_tokens.setText(f"Tokens: Prompt: {tok.prompt_tokens} | Comp: {tok.completion_tokens} | Total: {tok.total_tokens}")

        # Update citations table
        self.cite_table.setRowCount(len(diag.citations))
        for idx, cite in enumerate(diag.citations, start=1):
            self.cite_table.setItem(idx - 1, 0, QTableWidgetItem(f"[{idx}]"))
            self.cite_table.setItem(idx - 1, 1, QTableWidgetItem(cite.document_path))
            pos = []
            if cite.page:
                pos.append(f"Pág. {cite.page}")
            if cite.section:
                pos.append(f"Sec. {cite.section}")
            self.cite_table.setItem(idx - 1, 2, QTableWidgetItem(" | ".join(pos) if pos else "—"))

    def _append_user_message(self, text: str):
        html = f"""
        <div style="margin: 8px 0px; text-align: right;">
            <div style="display: inline-block; background-color: #6366F1; color: #FFFFFF; padding: 10px 14px; border-radius: 12px; max-width: 80%; text-align: left;">
                <b>Usuario:</b><br>{text}
            </div>
        </div>
        """
        self.chat_history.append(html)

    def _append_assistant_message(self, text: str, citations: list):
        cite_badges = ""
        if citations:
            cite_badges = "<div style='margin-top: 8px; font-size: 11px; color: #64748B;'><b>Fuentes citadas:</b> "
            for i, c in enumerate(citations, start=1):
                cite_badges += f"<span style='background-color: #E0E7FF; color: #3730A3; padding: 2px 6px; border-radius: 4px; margin-right: 4px;'>[{i}] {c.document_path}</span>"
            cite_badges += "</div>"

        html = f"""
        <div style="margin: 8px 0px; text-align: left;">
            <div style="display: inline-block; background-color: #F1F5F9; color: #0F172A; padding: 10px 14px; border-radius: 12px; max-width: 85%; border: 1px solid #CBD5E1;">
                <b>EmbedCraft Assistant:</b><br>{text.replace(chr(10), '<br>')}
                {cite_badges}
            </div>
        </div>
        """
        self.chat_history.append(html)

    def _append_system_message(self, text: str):
        html = f"<div style='margin: 6px 0px; color: #64748B; font-size: 12px; font-style: italic;'>ℹ {text}</div>"
        self.chat_history.append(html)

    def _clear_chat(self):
        self.chat_history.clear()
        self._append_system_message("Conversación reiniciada.")

    def _export_json(self):
        if not self._last_session_data:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Sesión de Diagnóstico",
            f"diagnostico_rag_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json",
            "Archivos JSON (*.json)",
        )
        if file_path:
            try:
                content = self._last_session_data.model_dump_json(indent=2)
                Path(file_path).write_text(content, encoding="utf-8")
                QMessageBox.information(self, "Éxito", f"Diagnóstico exportado a: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo: {str(e)}")
