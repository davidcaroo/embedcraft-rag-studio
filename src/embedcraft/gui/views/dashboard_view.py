"""Dashboard view displaying system overview, metrics, and quick actions."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from embedcraft.bootstrap.container import container
from embedcraft.gui.components.card import Card, StatBox


class DashboardView(QWidget):
    """Studio home overview with live metrics and quick access."""

    navigate_to = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("workspace")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # 1. Stat boxes row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.stat_projects = StatBox("Proyectos", "0", "📁", self)
        self.stat_docs = StatBox("Documentos", "0", "📄", self)
        self.stat_chunks = StatBox("Fragmentos", "0", "🧩", self)
        self.stat_status = StatBox("Motor Vectorial", "Activo", "⚡", self)

        stats_layout.addWidget(self.stat_projects)
        stats_layout.addWidget(self.stat_docs)
        stats_layout.addWidget(self.stat_chunks)
        stats_layout.addWidget(self.stat_status)

        layout.addLayout(stats_layout)

        # 2. Quick actions card
        actions_card = Card("Acciones Rápidas", "Comandos directos de administración del estudio", self)
        act_row = QHBoxLayout()
        act_row.setSpacing(12)

        btn_new_proj = QPushButton("+ Crear Nuevo Proyecto", self)
        btn_new_proj.setProperty("class", "primaryBtn")
        btn_new_proj.clicked.connect(lambda: self.navigate_to.emit("projects"))
        act_row.addWidget(btn_new_proj)

        btn_monitor = QPushButton("⚡ Ingestión de Documentos", self)
        btn_monitor.clicked.connect(lambda: self.navigate_to.emit("monitor"))
        act_row.addWidget(btn_monitor)

        btn_preview = QPushButton("🔍 Explorar Previews", self)
        btn_preview.clicked.connect(lambda: self.navigate_to.emit("preview"))
        act_row.addWidget(btn_preview)

        btn_doctor = QPushButton("🩺 Diagnóstico del Sistema", self)
        btn_doctor.clicked.connect(lambda: self.navigate_to.emit("doctor"))
        act_row.addWidget(btn_doctor)

        act_row.addStretch()
        actions_card.add_layout(act_row)
        layout.addWidget(actions_card)

        # 3. Recent projects card
        table_card = Card("Proyectos Recientes", "Catálogo local de proyectos RAG configurados", self)
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Nombre del Proyecto", "Descripción", "Revisión Activa", "Fecha"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)

        table_card.add_widget(self.table)
        layout.addWidget(table_card)

        self.refresh_data()

    def refresh_data(self):
        try:
            with container.get_session() as session:
                proj_repo = container.get_project_repository(session)
                doc_repo = container.get_document_repository(session)

                projects = proj_repo.list_all()
                self.stat_projects.set_value(str(len(projects)))

                total_docs = 0
                for p in projects:
                    total_docs += doc_repo.count_by_project(p.id)
                self.stat_docs.set_value(str(total_docs))

                # Populate table
                self.table.setRowCount(len(projects))
                for row_idx, p in enumerate(projects):
                    self.table.setItem(row_idx, 0, QTableWidgetItem(p.name))
                    self.table.setItem(row_idx, 1, QTableWidgetItem(p.description or "—"))
                    active_rev = p.active_revision_id[:8] if p.active_revision_id else "Sin revisión"
                    self.table.setItem(row_idx, 2, QTableWidgetItem(active_rev))
                    date_str = p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "—"
                    self.table.setItem(row_idx, 3, QTableWidgetItem(date_str))

        except Exception:
            pass
