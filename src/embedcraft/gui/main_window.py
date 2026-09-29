"""Main application window uniting Sidebar, Header, and modular Views."""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from embedcraft import __version__
from embedcraft.gui.components.header import HeaderBar
from embedcraft.gui.components.sidebar import Sidebar
from embedcraft.gui.views.collections_view import CollectionsView
from embedcraft.gui.views.dashboard_view import DashboardView
from embedcraft.gui.views.doctor_view import DoctorView
from embedcraft.gui.views.monitor_view import MonitorView
from embedcraft.gui.views.preview_view import PreviewView
from embedcraft.gui.views.projects_view import ProjectsView


class MainWindow(QMainWindow):
    """Primary desktop window with integrated navigation and responsive workspace."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"EmbedCraft RAG Studio v{__version__}")
        self.resize(1200, 800)
        self.setMinimumSize(960, 640)

        # Central layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = Sidebar(self)
        root_layout.addWidget(self.sidebar)

        # 2. Right Workspace container
        right_container = QWidget(self)
        right_container.setObjectName("workspace")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Header bar
        self.header = HeaderBar(self)
        right_layout.addWidget(self.header)

        # Stacked Views
        self.stack = QStackedWidget(self)
        self.views: dict[str, QWidget] = {}

        self._init_views()
        right_layout.addWidget(self.stack)

        root_layout.addWidget(right_container)

        # Status Bar
        status_bar = QStatusBar(self)
        status_bar.setStyleSheet("background-color: #FFFFFF; color: #64748B; font-size: 11px;")
        status_bar.showMessage(f"EmbedCraft RAG Studio v{__version__} | Base de datos SQLite WAL | Vector Engine LanceDB")
        self.setStatusBar(status_bar)

        # Connect navigation signals
        self.sidebar.view_changed.connect(self._on_navigation_changed)
        self.header.project_selected.connect(self._on_project_changed)

        # Select initial project
        initial_proj_id = self.header.get_current_project_id()
        if initial_proj_id:
            self._on_project_changed(initial_proj_id)

    def _init_views(self):
        # 1. Dashboard
        dash = DashboardView(self)
        dash.navigate_to.connect(self._navigate_from_dashboard)
        self._register_view("dashboard", dash, "Inicio / Dashboard")

        # 2. Projects
        proj = ProjectsView(self)
        proj.project_created.connect(self._on_project_created)
        self._register_view("projects", proj, "Proyectos RAG")

        # 3. Monitor
        mon = MonitorView(self)
        self._register_view("monitor", mon, "Ingestión & Monitor")

        # 4. Preview
        prev = PreviewView(self)
        self._register_view("preview", prev, "Previsualización Documental")

        # 5. Collections
        cols = CollectionsView(self)
        self._register_view("collections", cols, "Colecciones e Índices")

        # 6. Doctor
        doc = DoctorView(self)
        self._register_view("doctor", doc, "Diagnóstico del Sistema")

    def _register_view(self, key: str, widget: QWidget, title: str):
        self.stack.addWidget(widget)
        self.views[key] = widget
        widget.setProperty("title", title)

    def _on_navigation_changed(self, key: str):
        if key in self.views:
            widget = self.views[key]
            self.stack.setCurrentWidget(widget)
            self.header.set_title(widget.property("title") or key.capitalize())

            # Auto-refresh view data when navigated to
            if hasattr(widget, "refresh_data"):
                widget.refresh_data()
            elif hasattr(widget, "reload_projects"):
                widget.reload_projects()
            elif hasattr(widget, "reload_documents"):
                widget.reload_documents()
            elif hasattr(widget, "reload_data"):
                widget.reload_data()

    def _navigate_from_dashboard(self, target_key: str):
        self.sidebar.set_active(target_key)
        self._on_navigation_changed(target_key)

    def _on_project_changed(self, project_id: str):
        # Broadcast project change to views that require active project context
        for v in self.views.values():
            if hasattr(v, "set_project"):
                v.set_project(project_id)

    def _on_project_created(self, project_id: str):
        self.header.reload_projects()
        self.header.project_combo.blockSignals(True)
        # Select newly created project
        for idx in range(self.header.project_combo.count()):
            if self.header.project_combo.itemData(idx) == project_id:
                self.header.project_combo.setCurrentIndex(idx)
                break
        self.header.project_combo.blockSignals(False)
        self._on_project_changed(project_id)
