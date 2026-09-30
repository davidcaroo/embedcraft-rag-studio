"""Real-time ingestion monitor view with non-blocking Qt worker execution."""

from datetime import UTC, datetime

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from embedcraft.gui.components.card import Card, StatBox
from embedcraft.gui.icons import get_icon
from embedcraft.gui.theme import get_palette, theme_manager
from embedcraft.gui.workers.async_workers import IndexingWorker, IngestionWorker


class MonitorView(QWidget):
    """Monitor view tracking live discovery, extraction, chunking, and logging."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("workspace")
        self._current_project_id: str | None = None
        self._worker_thread: QThread | None = None
        self._worker: IngestionWorker | None = None

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root_layout.addWidget(scroll)

        content_widget = QWidget()
        content_widget.setObjectName("workspace")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        scroll.setWidget(content_widget)

        # Header Title
        header = QHBoxLayout()
        title = QLabel("Ingestión y Monitorización", content_widget)
        title.setObjectName("viewTitle")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # 1. Pipeline Stage Flow Indicator
        stage_card = Card("Pipeline Documental", "Etapa actual de procesamiento", content_widget)
        stage_layout = QHBoxLayout()
        stage_layout.setSpacing(12)

        self.pill_disc = self._create_stage_pill("1. Descubrir", active=True)
        self.pill_extr = self._create_stage_pill("2. Extraer")
        self.pill_norm = self._create_stage_pill("3. Normalizar")
        self.pill_frag = self._create_stage_pill("4. Fragmentar")
        self.pill_index = self._create_stage_pill("5. Indexar")

        stage_layout.addWidget(self.pill_disc)
        stage_layout.addWidget(QLabel("->", content_widget))
        stage_layout.addWidget(self.pill_extr)
        stage_layout.addWidget(QLabel("->", content_widget))
        stage_layout.addWidget(self.pill_norm)
        stage_layout.addWidget(QLabel("->", content_widget))
        stage_layout.addWidget(self.pill_frag)
        stage_layout.addWidget(QLabel("->", content_widget))
        stage_layout.addWidget(self.pill_index)
        stage_layout.addStretch()

        stage_card.add_layout(stage_layout)
        layout.addWidget(stage_card)

        # 2. Progress and metrics row
        metrics_layout = QHBoxLayout()
        self.stat_docs = StatBox("Documentos", "0 / 0", "file", content_widget)
        self.stat_chunks = StatBox("Fragmentos", "0", "layers", content_widget)
        self.stat_status = StatBox("Estado", "En espera", "activity", content_widget)

        metrics_layout.addWidget(self.stat_docs)
        metrics_layout.addWidget(self.stat_chunks)
        metrics_layout.addWidget(self.stat_status)
        layout.addLayout(metrics_layout)

        # 3. Progress Bar card
        prog_card = Card("Progreso de Ejecución", "Avance acumulado del lote de documentos", content_widget)
        self.progress_bar = QProgressBar(content_widget)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        prog_card.add_widget(self.progress_bar)

        self.lbl_current_file = QLabel("Listo para iniciar escaneo.", content_widget)
        palette = get_palette(theme_manager.mode)
        self.lbl_current_file.setStyleSheet(f"color: {palette.TEXT_MUTED}; font-size: 12px;")
        prog_card.add_widget(self.lbl_current_file)

        # Action buttons
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("Iniciar Ingestión Incremental", content_widget)
        self.btn_start.setIcon(get_icon("play"))
        self.btn_start.setProperty("class", "primaryBtn")
        self.btn_start.clicked.connect(self.start_ingestion)
        btn_layout.addWidget(self.btn_start)

        self.btn_cancel = QPushButton("Cancelar Proceso", content_widget)
        self.btn_cancel.setIcon(get_icon("stop"))
        self.btn_cancel.setProperty("class", "dangerBtn")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_ingestion)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_publish_index = QPushButton("Publicar Índice Ahora", content_widget)
        self.btn_publish_index.setIcon(get_icon("layers"))
        self.btn_publish_index.clicked.connect(self.publish_index)
        btn_layout.addWidget(self.btn_publish_index)

        self.btn_clear = QPushButton("Limpiar Registro", content_widget)
        self.btn_clear.clicked.connect(self._clear_logs)
        btn_layout.addWidget(self.btn_clear)

        btn_layout.addStretch()
        prog_card.add_layout(btn_layout)

        # Auto-publish option row
        opt_layout = QHBoxLayout()
        self.chk_auto_publish = QCheckBox("Publicar índice automáticamente al terminar ingestión", content_widget)
        self.chk_auto_publish.setChecked(True)
        opt_layout.addWidget(self.chk_auto_publish)
        opt_layout.addStretch()
        prog_card.add_layout(opt_layout)

        layout.addWidget(prog_card)

        # 4. Live log console
        log_card = Card("Registro de Eventos en Vivo", "Salida de trazabilidad estructurada", content_widget)
        self.log_console = QPlainTextEdit(content_widget)
        self.log_console.setObjectName("codeConsole")
        self.log_console.setReadOnly(True)
        log_card.add_widget(self.log_console)
        layout.addWidget(log_card)

    def _create_stage_pill(self, text: str, active: bool = False) -> QLabel:
        lbl = QLabel(text, self)
        palette = get_palette(theme_manager.mode)
        bg = palette.PRIMARY if active else palette.BG_CARD
        fg = palette.TEXT_INVERSE if active else palette.TEXT_SECONDARY
        border = palette.PRIMARY if active else palette.BORDER
        lbl.setStyleSheet(
            f"padding: 6px 12px; border-radius: 6px; font-weight: 600; font-size: 12px; "
            f"background-color: {bg}; color: {fg}; border: 1px solid {border};"
        )
        return lbl

    def set_project(self, project_id: str):
        self._current_project_id = project_id
        self.lbl_current_file.setText(f"Proyecto activo: {project_id}")

    def start_ingestion(self):
        if not self._current_project_id:
            self._append_log("Debe seleccionar un proyecto activo en el encabezado antes de iniciar.", "WARNING")
            return

        if self._worker_thread and self._worker_thread.isRunning():
            return

        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setValue(0)
        self.stat_status.set_value("Procesando")
        palette = get_palette(theme_manager.mode)
        self.stat_status.lbl_val.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {palette.PRIMARY};")

        self._worker_thread = QThread()
        self._worker = IngestionWorker(self._current_project_id)
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.run)
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.log_emitted.connect(self._append_log)
        self._worker.job_finished.connect(self._on_finished)
        self._worker.job_failed.connect(self._on_failed)

        self._worker_thread.start()

    def cancel_ingestion(self):
        if self._worker:
            self._worker.cancel()
            self._append_log("Solicitud de cancelación enviada...", "WARNING")
            self.btn_cancel.setEnabled(False)

    def _on_progress(self, current: int, total: int, filename: str):
        pct = int((current / max(1, total)) * 100)
        self.progress_bar.setValue(pct)
        self.stat_docs.set_value(f"{current} / {total}")
        self.lbl_current_file.setText(f"Procesando: {filename}")

    def _set_stage_active(self, pill: QLabel, active: bool):
        palette = get_palette(theme_manager.mode)
        bg = palette.PRIMARY if active else palette.BG_CARD
        fg = palette.TEXT_INVERSE if active else palette.TEXT_SECONDARY
        border = palette.PRIMARY if active else palette.BORDER
        pill.setStyleSheet(
            f"padding: 6px 12px; border-radius: 6px; font-weight: 600; font-size: 12px; "
            f"background-color: {bg}; color: {fg}; border: 1px solid {border};"
        )

    def _on_finished(self, summary: dict):
        self.progress_bar.setValue(100)
        self.stat_status.set_value("Ingestado")
        palette = get_palette(theme_manager.mode)
        self.stat_status.lbl_val.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {palette.SUCCESS};")
        self.stat_chunks.set_value(str(summary.get("generated_chunks", 0)))
        self.lbl_current_file.setText("Ingestión completada.")
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self._cleanup_worker()

        if self.chk_auto_publish.isChecked() and self._current_project_id:
            self._append_log("Iniciando publicación automática de índice...", "INFO")
            self.publish_index()
        else:
            self._append_log("Ingestión completada. Presione 'Publicar Índice Ahora' para habilitar consultas en el Chat.", "INFO")

    def publish_index(self):
        if not self._current_project_id:
            self._append_log("Debe seleccionar un proyecto activo antes de publicar el índice.", "WARNING")
            return

        if self._worker_thread and self._worker_thread.isRunning():
            return

        self.btn_start.setEnabled(False)
        self.btn_publish_index.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.stat_status.set_value("Indexando...")
        palette = get_palette(theme_manager.mode)
        self.stat_status.lbl_val.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {palette.PRIMARY};")
        self._set_stage_active(self.pill_index, True)

        self._append_log("Generando embeddings e indexando vectores y léxico en segundo plano...", "INFO")

        self._worker_thread = QThread()
        self._worker = IndexingWorker(self._current_project_id)
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.run)
        self._worker.log_emitted.connect(self._append_log)
        self._worker.job_finished.connect(self._on_indexing_finished)
        self._worker.job_failed.connect(self._on_indexing_failed)
        self._worker_thread.start()

    def _on_indexing_finished(self, rev_dict: dict):
        self.stat_status.set_value("Índice Activo")
        palette = get_palette(theme_manager.mode)
        self.stat_status.lbl_val.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {palette.SUCCESS};")
        self.btn_start.setEnabled(True)
        self.btn_publish_index.setEnabled(True)
        self._cleanup_worker()
        rev_num = rev_dict.get("revision_number", 1)
        self._append_log(f"Revisión #{rev_num} publicada y activa con éxito. El proyecto está listo para consultas en el Chat.", "SUCCESS")

    def _on_indexing_failed(self, error: str):
        self.stat_status.set_value("Error Índice")
        palette = get_palette(theme_manager.mode)
        self.stat_status.lbl_val.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {palette.ERROR};")
        self.btn_start.setEnabled(True)
        self.btn_publish_index.setEnabled(True)
        self._cleanup_worker()

    def _on_failed(self, error: str):
        self.stat_status.set_value("Error")
        palette = get_palette(theme_manager.mode)
        self.stat_status.lbl_val.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {palette.ERROR};")
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self._cleanup_worker()

    def _cleanup_worker(self):
        if self._worker_thread:
            self._worker_thread.quit()
            self._worker_thread.wait()
            self._worker_thread = None
            self._worker = None

    def _append_log(self, text: str, level: str = "INFO"):
        ts = datetime.now(UTC).strftime("%H:%M:%S")
        palette = get_palette(theme_manager.mode)
        color = palette.TEXT_MUTED
        if level == "SUCCESS":
            color = palette.SUCCESS
        elif level == "WARNING":
            color = palette.WARNING
        elif level == "ERROR":
            color = palette.ERROR
        elif level == "INFO":
            color = palette.INFO

        html = f"<span style='color: {palette.TEXT_MUTED};'>[{ts}]</span> <span style='color: {color}; font-weight: bold;'>[{level}]</span> {text}"
        self.log_console.appendHtml(html)

    def _clear_logs(self):
        self.log_console.clear()

