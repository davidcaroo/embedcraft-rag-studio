"""Top navigation header bar with project context and title."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from embedcraft.bootstrap.container import container


class HeaderBar(QWidget):
    """Header widget displaying active section title and project context selector."""

    project_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("headerBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        # Title
        self.title_label = QLabel("Inicio / Dashboard", self)
        self.title_label.setObjectName("headerTitle")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Project Context selector
        lbl_proj = QLabel("Proyecto Activo:", self)
        lbl_proj.setStyleSheet("color: #64748B; font-weight: 600; font-size: 12px;")
        layout.addWidget(lbl_proj)

        self.project_combo = QComboBox(self)
        self.project_combo.setMinimumWidth(220)
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        layout.addWidget(self.project_combo)

        # Refresh project list
        self.reload_projects()

    def set_title(self, title: str):
        self.title_label.setText(title)

    def reload_projects(self):
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        try:
            with container.get_session() as session:
                proj_repo = container.get_project_repository(session)
                projects = proj_repo.list_all()
                if not projects:
                    self.project_combo.addItem("Sin proyectos creados", "")
                else:
                    for p in projects:
                        self.project_combo.addItem(f"📁 {p.name}", p.id)
        except Exception:
            self.project_combo.addItem("Error cargando proyectos", "")
        self.project_combo.blockSignals(False)

    def _on_project_changed(self, index: int):
        proj_id = self.project_combo.currentData()
        if proj_id:
            self.project_selected.emit(proj_id)

    def get_current_project_id(self) -> str | None:
        data = self.project_combo.currentData()
        return str(data) if data else None
