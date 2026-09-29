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
