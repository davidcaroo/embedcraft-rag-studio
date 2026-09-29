"""Sidebar navigation component for EmbedCraft RAG Studio."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QWidget):
    """Dark-themed navigation sidebar with Studio and Sistema sections."""

    view_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        self._buttons: dict[str, QPushButton] = {}
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(2)

        # Brand header
        brand = QLabel("EmbedCraft RAG", self)
        brand.setObjectName("sidebarBrand")
        sub_brand = QLabel("STUDIO", self)
        sub_brand.setObjectName("sidebarSection")
        sub_brand.setStyleSheet("padding-top: 0px; color: #818CF8; font-weight: 800;")

        layout.addWidget(brand)
        layout.addWidget(sub_brand)

        # Section: Studio
        lbl_studio = QLabel("STUDIO", self)
        lbl_studio.setObjectName("sidebarSection")
        layout.addWidget(lbl_studio)

        self._add_nav_item("dashboard", "📊 Inicio / Métricas", layout)
        self._add_nav_item("projects", "📁 Proyectos RAG", layout)
        self._add_nav_item("monitor", "⚡ Ingestión & Monitor", layout)
        self._add_nav_item("preview", "🔍 Previews & Chunks", layout)
        self._add_nav_item("collections", "📚 Colecciones & Índices", layout)
        self._add_nav_item("chat", "💬 Chat de Prueba", layout)

        layout.addSpacing(16)

        # Section: Sistema
        lbl_system = QLabel("SISTEMA", self)
        lbl_system.setObjectName("sidebarSection")
        layout.addWidget(lbl_system)

        self._add_nav_item("doctor", "🩺 Diagnóstico Doctor", layout)

        layout.addStretch()

        # Set default active
        self.set_active("dashboard")

    def _add_nav_item(self, key: str, label: str, layout: QVBoxLayout):
        btn = QPushButton(label, self)
        btn.setProperty("class", "sidebarNavBtn")
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self._on_btn_clicked(key))
        self._button_group.addButton(btn)
        self._buttons[key] = btn
        layout.addWidget(btn)

    def _on_btn_clicked(self, key: str):
        self.view_changed.emit(key)

    def set_active(self, key: str):
        if key in self._buttons:
            self._buttons[key].setChecked(True)
