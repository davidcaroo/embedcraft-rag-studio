"""Card and StatBox reusable layout components."""

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        top_layout = QHBoxLayout()
        self.lbl_title = QLabel(title, self)
        self.lbl_title.setStyleSheet("color: #64748B; font-weight: 600; font-size: 12px; text-transform: uppercase;")
        top_layout.addWidget(self.lbl_title)
        top_layout.addStretch()

        if icon:
            self.lbl_icon = QLabel(icon, self)
            self.lbl_icon.setStyleSheet("font-size: 16px;")
            top_layout.addWidget(self.lbl_icon)

        layout.addLayout(top_layout)

        self.lbl_val = QLabel(value, self)
        self.lbl_val.setStyleSheet("font-size: 26px; font-weight: 700; color: #0F172A;")
        layout.addWidget(self.lbl_val)

    def set_value(self, val: str):
        self.lbl_val.setText(val)
