"""Card and StatBox reusable layout components."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from embedcraft.gui.icons import get_pixmap
from embedcraft.gui.theme import get_palette, theme_manager


class Card(QFrame):
    """Clean surface card with optional header and flexible content layout."""

    def __init__(self, title: str = "", subtitle: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "card")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(14)

        if title or subtitle:
            header_layout = QVBoxLayout()
            header_layout.setSpacing(4)
            if title:
                self.title_lbl = QLabel(title, self)
                self.title_lbl.setObjectName("cardTitle")
                header_layout.addWidget(self.title_lbl)
            if subtitle:
                self.sub_lbl = QLabel(subtitle, self)
                self.sub_lbl.setObjectName("cardSubtitle")
                header_layout.addWidget(self.sub_lbl)
            self.main_layout.addLayout(header_layout)

    def add_widget(self, widget: QWidget):
        self.main_layout.addWidget(widget)

    def add_layout(self, layout):
        self.main_layout.addLayout(layout)


class StatBox(QFrame):
    """Metric card displaying a large number and descriptive label."""

    def __init__(self, title: str, value: str, icon: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setMinimumHeight(100)
        self._icon_name = icon

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        top_layout = QHBoxLayout()
        self.lbl_title = QLabel(title, self)
        self.lbl_title.setObjectName("statTitle")
        top_layout.addWidget(self.lbl_title)
        top_layout.addStretch()

        if icon:
            self.lbl_icon = QLabel(self)
            self._update_icon()
            top_layout.addWidget(self.lbl_icon)
            theme_manager.theme_changed.connect(self._on_theme_changed)

        layout.addLayout(top_layout)

        self.lbl_val = QLabel(value, self)
        self.lbl_val.setObjectName("statValue")
        layout.addWidget(self.lbl_val)

    def _update_icon(self) -> None:
        if self._icon_name and hasattr(self, "lbl_icon"):
            palette = get_palette(theme_manager.mode)
            self.lbl_icon.setPixmap(
                get_pixmap(self._icon_name, color=palette.PRIMARY, size=20)
            )

    def _on_theme_changed(self, mode: str) -> None:
        self._update_icon()

    def set_value(self, val: str):
        self.lbl_val.setText(val)

