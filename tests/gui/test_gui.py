"""Automated headless tests for PySide6 GUI views and MainWindow navigation."""

import os

import pytest

# Ensure headless execution on CI and developer machines
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from embedcraft.gui.main_window import MainWindow
from embedcraft.gui.views.chat_view import ChatView
from embedcraft.gui.views.collections_view import CollectionsView
from embedcraft.gui.views.dashboard_view import DashboardView
from embedcraft.gui.views.doctor_view import DoctorView
from embedcraft.gui.views.monitor_view import MonitorView
from embedcraft.gui.views.preview_view import PreviewView
from embedcraft.gui.views.projects_view import ProjectsView


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single persistent QApplication instance exists for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_initialization_and_navigation(qapp):
    window = MainWindow()
    assert "EmbedCraft RAG Studio" in window.windowTitle()

    # Verify all 7 views are registered in stacked widget
    assert len(window.views) == 7
    assert isinstance(window.views["dashboard"], DashboardView)
    assert isinstance(window.views["projects"], ProjectsView)
    assert isinstance(window.views["monitor"], MonitorView)
    assert isinstance(window.views["preview"], PreviewView)
    assert isinstance(window.views["collections"], CollectionsView)
    assert isinstance(window.views["chat"], ChatView)
    assert isinstance(window.views["doctor"], DoctorView)

    # Test navigation to each view
    for key in ["projects", "monitor", "preview", "collections", "chat", "doctor", "dashboard"]:
        window.sidebar._on_btn_clicked(key)
        assert window.stack.currentWidget() == window.views[key]

    window.close()


def test_dashboard_view_rendering(qapp):
    dash = DashboardView()
    assert dash.stat_projects.lbl_val.text() != ""
    assert dash.stat_docs.lbl_val.text() != ""
    assert dash.table.columnCount() == 4
    dash.close()


def test_doctor_view_execution(qapp):
    doc = DoctorView()
    assert doc.table.columnCount() == 4
    # Check that doctor ran checks and populated table
    assert doc.table.rowCount() > 0
    doc.close()


def test_monitor_view_controls(qapp):
    mon = MonitorView()
    assert mon.progress_bar.value() == 0
    assert mon.btn_start.isEnabled() is True
    assert mon.btn_cancel.isEnabled() is False
    mon.set_project("test-project-id")
    assert mon._current_project_id == "test-project-id"
    mon.close()


def test_preview_view_empty_state(qapp):
    prev = PreviewView()
    assert prev.doc_table.columnCount() == 2
    assert prev.chunk_table.columnCount() == 3
    prev.set_project("non-existent-project")
    assert prev.doc_table.rowCount() == 0
    prev.close()


def test_collections_view_empty_state(qapp):
    cols = CollectionsView()
    assert cols.col_table.columnCount() == 3
    assert cols.rev_table.columnCount() == 5
    cols.set_project("dummy-proj")
    assert cols.col_table.rowCount() == 0
    cols.close()


def test_chat_view_rendering_and_interaction(qapp):
    chat = ChatView()
    assert chat.cite_table.columnCount() == 3
    assert chat.spin_topk.value() == 5
    chat.set_project("test-chat-proj")
    assert chat._current_project_id == "test-chat-proj"
    chat.close()


def test_sidebar_vector_icons_and_clean_labels(qapp):
    from embedcraft.gui.components.sidebar import Sidebar

    sidebar = Sidebar()
    expected_labels = {
        "dashboard": "Inicio / Métricas",
        "projects": "Proyectos RAG",
        "monitor": "Ingestión & Monitor",
        "preview": "Previews & Chunks",
        "collections": "Colecciones & Índices",
        "chat": "Chat de Prueba",
        "doctor": "Diagnóstico Doctor",
    }

    emojis = ["📊", "📁", "⚡", "🔍", "📚", "💬", "🩺"]

    for key, expected_text in expected_labels.items():
        assert key in sidebar._buttons
        btn = sidebar._buttons[key]
        assert btn.text() == expected_text
        for emoji in emojis:
            assert emoji not in btn.text(), f"Emoji '{emoji}' found in sidebar button '{key}'"
        assert not btn.icon().isNull(), f"Button '{key}' should have a valid vector QIcon"

    # Verify refresh_icons method works and updates icons
    sidebar.refresh_icons("light")
    for key in expected_labels:
        assert not sidebar._buttons[key].icon().isNull()

    sidebar.refresh_icons("dark")
    for key in expected_labels:
        assert not sidebar._buttons[key].icon().isNull()

    sidebar.close()


def test_header_bar_theme_toggle_and_clean_projects(qapp):
    from embedcraft.gui.components.header import HeaderBar
    from embedcraft.gui.theme import ThemeMode, theme_manager

    # Reset theme to dark for predictable test starting state
    theme_manager.set_mode(ThemeMode.DARK)

    header = HeaderBar()
    assert hasattr(header, "btn_theme"), "HeaderBar must have a btn_theme button"
    assert header.btn_theme.objectName() == "btnThemeToggle"
    assert not header.btn_theme.icon().isNull()
    assert header.btn_theme.toolTip() == "Cambiar a Modo Claro"

    # Test toggling theme via clicking btn_theme
    header.btn_theme.click()
    assert theme_manager.mode == ThemeMode.LIGHT
    assert header.btn_theme.toolTip() == "Cambiar a Modo Oscuro"
    assert not header.btn_theme.icon().isNull()

    # Toggle back
    header.btn_theme.click()
    assert theme_manager.mode == ThemeMode.DARK
    assert header.btn_theme.toolTip() == "Cambiar a Modo Claro"

    # Verify project combo doesn't have emoji 📁
    for idx in range(header.project_combo.count()):
        text = header.project_combo.itemText(idx)
        assert "📁" not in text, f"Emoji 📁 found in project combo item: {text}"

    header.close()


def test_main_window_theme_reactivity(qapp):
    from embedcraft.gui.theme import ThemeMode, theme_manager

    theme_manager.set_mode(ThemeMode.DARK)
    window = MainWindow()

    app = QApplication.instance()
    assert app is not None
    initial_stylesheet = app.styleSheet()
    assert len(initial_stylesheet) > 0, "MainWindow should apply the global stylesheet on init"
    assert "#0B0F19" in initial_stylesheet or "#111827" in initial_stylesheet

    # Toggle to light mode
    theme_manager.toggle_theme()
    assert theme_manager.mode == ThemeMode.LIGHT
    light_stylesheet = app.styleSheet()
    assert "#F8FAFC" in light_stylesheet or "#FFFFFF" in light_stylesheet

    # Check status bar style update
    assert window.statusBar() is not None

    # Toggle back to dark
    theme_manager.set_mode(ThemeMode.DARK)
    window.close()


def test_statbox_vector_icons_and_styling(qapp):
    from embedcraft.gui.components.card import StatBox

    stat = StatBox("Proyectos", "12", icon="projects")
    assert stat.lbl_title.objectName() == "statTitle"
    assert stat.lbl_val.objectName() == "statValue"
    assert hasattr(stat, "lbl_icon")
    assert stat.lbl_icon.pixmap() is not None
    assert not stat.lbl_icon.pixmap().isNull()
    assert "📁" not in stat.lbl_title.text()
    stat.close()


def test_no_emojis_in_base_views(qapp):
    from PySide6.QtWidgets import QLabel, QPushButton, QScrollArea

    forbidden_emojis = ["📊", "📁", "⚡", "🔍", "📚", "💬", "🩺", "✔", "⚠", "✖", "📥", "📤", "📄", "🧩", "🔄", "➕"]

    # 1. DashboardView
    dash = DashboardView()
    scroll_areas = dash.findChildren(QScrollArea)
    assert len(scroll_areas) > 0, "DashboardView must have a QScrollArea for responsiveness"
    assert scroll_areas[0].widgetResizable() is True

    dash_buttons = dash.findChildren(QPushButton)
    assert len(dash_buttons) >= 4
    for btn in dash_buttons:
        text = btn.text()
        for emoji in forbidden_emojis:
            assert emoji not in text, f"Emoji '{emoji}' found in Dashboard button: '{text}'"
        assert not btn.icon().isNull(), f"Dashboard button '{text}' must have a valid vector QIcon"

    dash_labels = dash.findChildren(QLabel)
    for lbl in dash_labels:
        text = lbl.text()
        for emoji in forbidden_emojis:
            assert emoji not in text, f"Emoji '{emoji}' found in Dashboard label: '{text}'"
    dash.close()

    # 2. ProjectsView
    proj_view = ProjectsView()
    proj_buttons = proj_view.findChildren(QPushButton)
    assert len(proj_buttons) >= 5
    for btn in proj_buttons:
        text = btn.text()
        for emoji in forbidden_emojis:
            assert emoji not in text, f"Emoji '{emoji}' found in ProjectsView button: '{text}'"
        assert not btn.icon().isNull(), f"ProjectsView button '{text}' must have a valid vector QIcon"

    proj_labels = proj_view.findChildren(QLabel)
    for lbl in proj_labels:
        text = lbl.text()
        for emoji in forbidden_emojis:
            assert emoji not in text, f"Emoji '{emoji}' found in ProjectsView label: '{text}'"
    proj_view.close()

    # 3. DoctorView
    doc_view = DoctorView()
    assert not doc_view.btn_run.icon().isNull(), "DoctorView run button must have a valid vector QIcon"
    assert "🔄" not in doc_view.btn_run.text()
    for row in range(doc_view.table.rowCount()):
        status_item = doc_view.table.item(row, 2)
        if status_item:
            text = status_item.text()
            for emoji in forbidden_emojis:
                assert emoji not in text, f"Emoji '{emoji}' found in DoctorView status item: '{text}'"
            assert text in ("OK", "ADVERTENCIA", "ERROR", "FALLO")
    doc_view.close()


