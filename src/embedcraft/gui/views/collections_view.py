"""Collections and atomic index revisions explorer view."""

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from embedcraft.bootstrap.container import container
from embedcraft.gui.components.card import Card
from embedcraft.gui.workers.async_workers import IndexingWorker


class CollectionsView(QWidget):
    """View to inspect collections, index revisions, trigger atomic publishing and rollbacks."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("workspace")
        self._current_project_id: str | None = None
        self._worker_thread: QThread | None = None
        self._worker: IndexingWorker | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header action bar
        action_bar = QHBoxLayout()
        title = QLabel("Colecciones e Índices Vectoriales", self)
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0F172A;")
        action_bar.addWidget(title)
        action_bar.addStretch()

        self.btn_publish = QPushButton("🚀 Publicar Nueva Revisión", self)
        self.btn_publish.setProperty("class", "primaryBtn")
        self.btn_publish.clicked.connect(self._publish_revision)
        action_bar.addWidget(self.btn_publish)

        self.btn_rollback = QPushButton("↩ Hacer Rollback", self)
        self.btn_rollback.clicked.connect(self._rollback_revision)
        action_bar.addWidget(self.btn_rollback)

        layout.addLayout(action_bar)

        # Splitter: Collections on left, Revisions on right
        splitter = QSplitter(self)

        # 1. Collections Card
        col_card = Card("Colecciones del Proyecto", "Espacios vectoriales configurados", self)
        self.col_table = QTableWidget(self)
        self.col_table.setColumnCount(3)
        self.col_table.setHorizontalHeaderLabels(["Colección", "Modelo Embedding", "Dim"])
        self.col_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.col_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.col_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        col_card.add_widget(self.col_table)
        splitter.addWidget(col_card)

        # 2. Index Revisions Card
        rev_card = Card("Revisiones de Índice", "Historial de publicaciones y estado activo", self)
        self.rev_table = QTableWidget(self)
        self.rev_table.setColumnCount(5)
        self.rev_table.setHorizontalHeaderLabels(["Rev #", "Estado", "Activa", "Docs", "Chunks"])
        self.rev_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.rev_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.rev_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.rev_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.rev_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.rev_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rev_table.setSelectionMode(QTableWidget.SingleSelection)
        rev_card.add_widget(self.rev_table)
        splitter.addWidget(rev_card)

        splitter.setSizes([380, 520])
        layout.addWidget(splitter)

    def set_project(self, project_id: str):
        self._current_project_id = project_id
        self.reload_data()

    def reload_data(self):
        self.col_table.setRowCount(0)
        self.rev_table.setRowCount(0)

        if not self._current_project_id:
            return

        try:
            with container.get_session() as session:
                col_repo = container.get_collection_repository(session)
                rev_repo = container.get_revision_repository(session)
                proj_repo = container.get_project_repository(session)

                project = proj_repo.get_by_id(self._current_project_id)
                active_rev_id = project.active_revision_id if project else None

                # Collections
                cols = col_repo.list_by_project(self._current_project_id)
                self.col_table.setRowCount(len(cols))
                for idx, c in enumerate(cols):
                    self.col_table.setItem(idx, 0, QTableWidgetItem(c.name))
                    self.col_table.setItem(idx, 1, QTableWidgetItem(c.embedding_model))
                    self.col_table.setItem(idx, 2, QTableWidgetItem(str(c.dimension)))

                # Revisions
                revs = rev_repo.list_by_project(self._current_project_id)
                self.rev_table.setRowCount(len(revs))
                for idx, r in enumerate(revs):
                    item_num = QTableWidgetItem(f"#{r.revision_number}")
                    item_num.setData(32, r.id)
                    self.rev_table.setItem(idx, 0, item_num)
                    self.rev_table.setItem(idx, 1, QTableWidgetItem(r.status.value))
                    is_active = "✔ ACTIVA" if r.id == active_rev_id else "—"
                    self.rev_table.setItem(idx, 2, QTableWidgetItem(is_active))
                    self.rev_table.setItem(idx, 3, QTableWidgetItem(str(r.total_documents)))
                    self.rev_table.setItem(idx, 4, QTableWidgetItem(str(r.total_chunks)))

        except Exception:
            pass

    def _publish_revision(self):
        if not self._current_project_id:
            QMessageBox.warning(self, "Atención", "Seleccione un proyecto activo.")
            return

        self.btn_publish.setEnabled(False)
        self.btn_publish.setText("Indexando...")

        self._worker_thread = QThread()
        self._worker = IndexingWorker(self._current_project_id)
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.run)
        self._worker.job_finished.connect(self._on_publish_finished)
        self._worker.job_failed.connect(self._on_publish_failed)

        self._worker_thread.start()

    def _on_publish_finished(self, rev_dict: dict):
        self.btn_publish.setEnabled(True)
        self.btn_publish.setText("🚀 Publicar Nueva Revisión")
        self._cleanup_worker()
        self.reload_data()
        QMessageBox.information(
            self,
            "Publicación Exitosa",
            f"La revisión #{rev_dict.get('revision_number')} ha sido validada y activada atómicamente.",
        )

    def _on_publish_failed(self, error: str):
        self.btn_publish.setEnabled(True)
        self.btn_publish.setText("🚀 Publicar Nueva Revisión")
        self._cleanup_worker()
        QMessageBox.critical(self, "Error de Indexación", error)

    def _cleanup_worker(self):
        if self._worker_thread:
            self._worker_thread.quit()
            self._worker_thread.wait()
            self._worker_thread = None
            self._worker = None

    def _rollback_revision(self):
        selected = self.rev_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Atención", "Seleccione una revisión de la lista para hacer rollback.")
            return

        rev_id = selected[0].data(32)
        confirm = QMessageBox.question(
            self,
            "Confirmar Rollback",
            f"¿Desea cambiar la revisión activa del proyecto a '{rev_id}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            try:
                with container.get_session() as session:
                    indexing_svc = container.get_indexing_service(session)
                    indexing_svc.rollback_revision(self._current_project_id, rev_id)
                    session.commit()
                    self.reload_data()
                    QMessageBox.information(self, "Rollback Exitoso", "La revisión activa ha sido restaurada.")
            except Exception as e:
                QMessageBox.critical(self, "Error de Rollback", str(e))
