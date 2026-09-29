"""Entrypoint for the EmbedCraft RAG Studio desktop application."""

import sys

from PySide6.QtWidgets import QApplication

from embedcraft.gui.main_window import MainWindow
from embedcraft.gui.styles import get_application_stylesheet


def run_gui() -> int:
    """Initialize and run the PySide6 Desktop GUI."""
    # Ensure Windows console encoding compatibility
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setApplicationName("EmbedCraft RAG Studio")
    app.setOrganizationName("EmbedCraft")

    # Apply global modern stylesheet
    app.setStyleSheet(get_application_stylesheet())

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run_gui())
