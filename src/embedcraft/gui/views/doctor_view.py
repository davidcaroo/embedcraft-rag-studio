"""System diagnostics view displaying environment, storage, and dependency health."""

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from embedcraft.bootstrap.container import container
from embedcraft.gui.components.card import Card
from embedcraft.gui.icons import get_icon
from embedcraft.gui.theme import get_palette, theme_manager


class DoctorView(QWidget):
    """View to execute and display system health checks (EmbedCraft Doctor)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("workspace")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header action bar
        action_bar = QHBoxLayout()
        title = QLabel("Diagnóstico de Salud del Sistema (Doctor)", self)
        title.setObjectName("viewTitle")
        action_bar.addWidget(title)
        action_bar.addStretch()

        self.btn_run = QPushButton("Reejecutar Diagnóstico", self)
        self.btn_run.setIcon(get_icon("refresh"))
        self.btn_run.setProperty("class", "primaryBtn")
        self.btn_run.clicked.connect(self.run_diagnostics)
        action_bar.addWidget(self.btn_run)

        layout.addLayout(action_bar)

        # Card with diagnostic table
        card = Card("Verificaciones de Entorno y Almacenamiento", "Estado de SQLite WAL, LanceDB, Keyring y Python", self)
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Categoría", "Verificación", "Estado", "Mensaje / Detalle"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)

        card.add_widget(self.table)
        layout.addWidget(card)

        self.run_diagnostics()

    def run_diagnostics(self):
        self.btn_run.setEnabled(False)
        self.table.setRowCount(0)

        try:
            checks = container.system_service.run_doctor()
            self.table.setRowCount(len(checks))

            palette = get_palette(theme_manager.mode)
            for idx, c in enumerate(checks):
                self.table.setItem(idx, 0, QTableWidgetItem(c.category))
                self.table.setItem(idx, 1, QTableWidgetItem(c.name))

                # Clean status label with semantic color
                status_item = QTableWidgetItem()
                if c.status == "ok":
                    status_item.setText("OK")
                    status_item.setForeground(QColor(palette.SUCCESS))
                elif c.status == "warning":
                    status_item.setText("ADVERTENCIA")
                    status_item.setForeground(QColor(palette.WARNING))
                else:
                    status_item.setText("ERROR")
                    status_item.setForeground(QColor(palette.ERROR))
                self.table.setItem(idx, 2, status_item)

                detail = c.message
                if c.detail:
                    detail += f" ({c.detail})"
                self.table.setItem(idx, 3, QTableWidgetItem(detail))

        except Exception as e:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("Error"))
            self.table.setItem(0, 1, QTableWidgetItem("Ejecución"))
            err_item = QTableWidgetItem("FALLO")
            err_item.setForeground(QColor(get_palette(theme_manager.mode).ERROR))
            self.table.setItem(0, 2, err_item)
            self.table.setItem(0, 3, QTableWidgetItem(str(e)))
        finally:
            self.btn_run.setEnabled(True)

