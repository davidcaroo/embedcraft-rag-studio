"""Top navigation header bar with project context and title."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from embedcraft.bootstrap.container import container
from embedcraft.gui.icons import get_icon
from embedcraft.gui.theme import ThemeMode, get_palette, theme_manager


class HeaderBar(QWidget):
    """Header widget displaying active section title, project context selector, and theme toggle."""

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
        self.lbl_proj = QLabel("Proyecto Activo:", self)
        self.lbl_proj.setStyleSheet("font-weight: 600; font-size: 12px;")
        layout.addWidget(self.lbl_proj)

        self.project_combo = QComboBox(self)
        self.project_combo.setMinimumWidth(220)
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        layout.addWidget(self.project_combo)

        # Theme toggle button
        self.btn_theme = QPushButton(self)
        self.btn_theme.setObjectName("btnThemeToggle")
        self.btn_theme.setFixedSize(36, 36)
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.clicked.connect(theme_manager.toggle_theme)
        layout.addWidget(self.btn_theme)

        # Connect reactive theme updates
        self.update_theme_icon(theme_manager.mode.value)
        theme_manager.theme_changed.connect(self.update_theme_icon)

        # Refresh project list
        self.reload_projects()

    def update_theme_icon(self, mode_str: str) -> None:
        """Update button icon and tooltip based on theme mode."""
        is_dark = mode_str == ThemeMode.DARK.value or mode_str == "dark"
        icon_name = "sun" if is_dark else "moon"
        icon_color = "#F59E0B" if is_dark else "#6366F1"
        tooltip = "Cambiar a Modo Claro" if is_dark else "Cambiar a Modo Oscuro"

        self.btn_theme.setIcon(get_icon(icon_name, color=icon_color, size=20))
        self.btn_theme.setIconSize(QSize(20, 20))
        self.btn_theme.setToolTip(tooltip)

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
                    folder_icon = get_icon("folder", color=get_palette(theme_manager.mode).PRIMARY, size=16)
                    for p in projects:
                        self.project_combo.addItem(folder_icon, p.name, p.id)
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

