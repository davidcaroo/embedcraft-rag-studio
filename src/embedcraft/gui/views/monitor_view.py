"""Real-time ingestion monitor view with non-blocking Qt worker execution."""

from datetime import UTC, datetime

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from embedcraft.gui.components.card import Card, StatBox
from embedcraft.gui.workers.async_workers import IngestionWorker


class MonitorView(QWidget):
    """Monitor view tracking live discovery, extraction, chunking, and logging."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("workspace")
        self._current_project_id: str | None = None
        self._worker_thread: QThread | None = None
        self._worker: IngestionWorker | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 1. Pipeline Stage Flow Indicator
        stage_card = Card("Pipeline Documental", "Etapa actual de procesamiento", self)
        stage_layout = QHBoxLayout()
        stage_layout.setSpacing(12)

        self.pill_disc = self._create_stage_pill("1. Descubrir", active=True)
        self.pill_extr = self._create_stage_pill("2. Extraer")
        self.pill_norm = self._create_stage_pill("3. Normalizar")
        self.pill_frag = self._create_stage_pill("4. Fragmentar")

        stage_layout.addWidget(self.pill_disc)
        stage_layout.addWidget(QLabel("→", self))
        stage_layout.addWidget(self.pill_extr)
        stage_layout.addWidget(QLabel("→", self))
        stage_layout.addWidget(self.pill_norm)
        stage_layout.addWidget(QLabel("→", self))
        stage_layout.addWidget(self.pill_frag)
        stage_layout.addStretch()

        stage_card.add_layout(stage_layout)
        layout.addWidget(stage_card)

        # 2. Progress and metrics row
        metrics_layout = QHBoxLayout()
        self.stat_docs = StatBox("Documentos", "0 / 0", "📄", self)
        self.stat_chunks = StatBox("Fragmentos", "0", "🧩", self)
        self.stat_status = StatBox("Estado", "En espera", "⏳", self)

        metrics_layout.addWidget(self.stat_docs)
        metrics_layout.addWidget(self.stat_chunks)
        metrics_layout.addWidget(self.stat_status)
        layout.addLayout(metrics_layout)

        # 3. Progress Bar card
        prog_card = Card("Progreso de Ejecución", "Avance acumulado del lote de documentos", self)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        prog_card.add_widget(self.progress_bar)

        self.lbl_current_file = QLabel("Listo para iniciar escaneo.", self)
        self.lbl_current_file.setStyleSheet("color: #64748B; font-size: 12px;")
        prog_card.add_widget(self.lbl_current_file)

        # Action buttons
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶ Iniciar Ingestión", self)
        self.btn_start.setProperty("class", "primaryBtn")
        self.btn_start.clicked.connect(self.start_ingestion)
        btn_layout.addWidget(self.btn_start)

        self.btn_cancel = QPushButton("⏹ Cancelar", self)
        self.btn_cancel.setProperty("class", "dangerBtn")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_ingestion)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_clear = QPushButton("Limpiar Registro", self)
        self.btn_clear.clicked.connect(self._clear_logs)
        btn_layout.addWidget(self.btn_clear)

        btn_layout.addStretch()
        prog_card.add_layout(btn_layout)
        layout.addWidget(prog_card)

        # 4. Live log console
        log_card = Card("Registro de Eventos en Vivo", "Salida de trazabilidad estructurada", self)
        self.log_console = QPlainTextEdit(self)
        self.log_console.setObjectName("codeConsole")
        self.log_console.setReadOnly(True)
        log_card.add_widget(self.log_console)
        layout.addWidget(log_card)

    def _create_stage_pill(self, text: str, active: bool = False) -> QLabel:
        lbl = QLabel(text, self)
        lbl.setStyleSheet(
            f"padding: 6px 12px; border-radius: 6px; font-weight: 600; font-size: 12px; "
            f"background-color: {'#6366F1' if active else '#E2E8F0'}; "
            f"color: {'#FFFFFF' if active else '#64748B'};"
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
        self.stat_status.lbl_val.setStyleSheet("font-size: 26px; font-weight: 700; color: #6366F1;")

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

    def _on_finished(self, summary: dict):
        self.progress_bar.setValue(100)
        self.stat_status.set_value("Completado")
        self.stat_status.lbl_val.setStyleSheet("font-size: 26px; font-weight: 700; color: #10B981;")
        self.stat_chunks.set_value(str(summary.get("generated_chunks", 0)))
        self.lbl_current_file.setText("Proceso finalizado.")
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self._cleanup_worker()

    def _on_failed(self, error: str):
        self.stat_status.set_value("Error")
        self.stat_status.lbl_val.setStyleSheet("font-size: 26px; font-weight: 700; color: #EF4444;")
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
        color = "#94A3B8"
        if level == "SUCCESS":
            color = "#34D399"
        elif level == "WARNING":
            color = "#FBBF24"
        elif level == "ERROR":
            color = "#F87171"
        elif level == "INFO":
            color = "#60A5FA"

        html = f"<span style='color: #64748B;'>[{ts}]</span> <span style='color: {color}; font-weight: bold;'>[{level}]</span> {text}"
        self.log_console.appendHtml(html)

    def _clear_logs(self):
        self.log_console.clear()
