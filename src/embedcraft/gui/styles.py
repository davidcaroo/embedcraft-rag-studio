"""Modern, production-grade QSS stylesheet generator for EmbedCraft RAG Studio."""

from embedcraft.gui.theme import FONT_CODE, FONT_FAMILY, THEME


def get_application_stylesheet() -> str:
    """Generate global application QSS stylesheet conforming to enterprise standards."""
    return f"""
    * {{
        font-family: {FONT_FAMILY};
        font-size: 13px;
        color: {THEME.TEXT_PRIMARY};
    }}

    QMainWindow, QDialog {{
        background-color: {THEME.BG_BASE};
    }}

    /* Sidebar Navigation (Dark) */
    QWidget#sidebar {{
        background-color: {THEME.SIDEBAR_BG};
        border-right: 1px solid {THEME.SIDEBAR_BORDER};
    }}

    QLabel#sidebarBrand {{
        color: #FFFFFF;
        font-size: 16px;
        font-weight: 700;
        padding: 18px 16px 10px 16px;
    }}

    QLabel#sidebarSection {{
        color: {THEME.SIDEBAR_TEXT_MUTED};
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        padding: 14px 16px 6px 16px;
        letter-spacing: 0.5px;
    }}

    QPushButton.sidebarNavBtn {{
        background-color: transparent;
        color: {THEME.SIDEBAR_TEXT};
        text-align: left;
        padding: 9px 16px;
        border: none;
        border-radius: 6px;
        margin: 2px 10px;
        font-size: 13px;
        font-weight: 500;
    }}

    QPushButton.sidebarNavBtn:hover {{
        background-color: {THEME.SIDEBAR_ITEM_HOVER};
        color: #FFFFFF;
    }}

    QPushButton.sidebarNavBtn:checked, QPushButton.sidebarNavBtn[active="true"] {{
        background-color: {THEME.PRIMARY};
        color: #FFFFFF;
        font-weight: 600;
    }}

    /* Workspace and Views (Light) */
    QWidget#workspace {{
        background-color: {THEME.BG_BASE};
    }}

    /* Header Bar */
    QWidget#headerBar {{
        background-color: #FFFFFF;
        border-bottom: 1px solid {THEME.BORDER};
        padding: 0px 24px;
        min-height: 56px;
        max-height: 56px;
    }}

    QLabel#headerTitle {{
        font-size: 16px;
        font-weight: 700;
        color: {THEME.TEXT_PRIMARY};
    }}

    /* Cards */
    QFrame.card {{
        background-color: {THEME.BG_CARD};
        border: 1px solid {THEME.BORDER};
        border-radius: 8px;
    }}

    QLabel#cardTitle {{
        font-size: 15px;
        font-weight: 600;
        color: {THEME.TEXT_PRIMARY};
    }}

    QLabel#cardSubtitle {{
        font-size: 12px;
        color: {THEME.TEXT_MUTED};
    }}

    /* Buttons */
    QPushButton {{
        background-color: #FFFFFF;
        color: {THEME.TEXT_PRIMARY};
        border: 1px solid {THEME.BORDER};
        border-radius: 6px;
        padding: 7px 14px;
        font-size: 13px;
        font-weight: 500;
    }}

    QPushButton:hover {{
        background-color: #F1F5F9;
        border-color: {THEME.BORDER_HOVER};
    }}

    QPushButton:pressed {{
        background-color: #E2E8F0;
    }}

    QPushButton:disabled {{
        background-color: #F8FAFC;
        color: #94A3B8;
        border-color: #E2E8F0;
    }}

    QPushButton.primaryBtn {{
        background-color: {THEME.PRIMARY};
        color: #FFFFFF;
        border: 1px solid {THEME.PRIMARY};
        font-weight: 600;
    }}

    QPushButton.primaryBtn:hover {{
        background-color: {THEME.PRIMARY_HOVER};
        border-color: {THEME.PRIMARY_HOVER};
    }}

    QPushButton.primaryBtn:pressed {{
        background-color: {THEME.PRIMARY_ACTIVE};
    }}

    QPushButton.dangerBtn {{
        background-color: {THEME.ERROR};
        color: #FFFFFF;
        border: 1px solid {THEME.ERROR};
        font-weight: 600;
    }}

    QPushButton.dangerBtn:hover {{
        background-color: #DC2626;
        border-color: #DC2626;
    }}

    /* Form Controls */
    QLineEdit, QComboBox, QSpinBox {{
        background-color: #FFFFFF;
        border: 1px solid {THEME.BORDER};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 13px;
        color: {THEME.TEXT_PRIMARY};
        selection-background-color: {THEME.PRIMARY_LIGHT};
        selection-color: {THEME.PRIMARY};
    }}

    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border-color: {THEME.BORDER_FOCUS};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QTextEdit, QPlainTextEdit {{
        background-color: #FFFFFF;
        border: 1px solid {THEME.BORDER};
        border-radius: 6px;
        padding: 8px;
        font-size: 13px;
        color: {THEME.TEXT_PRIMARY};
    }}

    QTextEdit#codeConsole, QPlainTextEdit#codeConsole {{
        font-family: {FONT_CODE};
        font-size: 12px;
        background-color: #0F172A;
        color: #F8FAFC;
        border-radius: 6px;
        border: 1px solid #334155;
    }}

    /* Tables */
    QTableWidget {{
        background-color: #FFFFFF;
        border: 1px solid {THEME.BORDER};
        border-radius: 6px;
        gridline-color: #F1F5F9;
        selection-background-color: {THEME.PRIMARY_LIGHT};
        selection-color: {THEME.TEXT_PRIMARY};
    }}

    QTableWidget::item {{
        padding: 6px 10px;
        border-bottom: 1px solid #F1F5F9;
    }}

    QHeaderView::section {{
        background-color: #F8FAFC;
        color: {THEME.TEXT_MUTED};
        font-weight: 600;
        font-size: 12px;
        border: none;
        border-bottom: 1px solid {THEME.BORDER};
        padding: 8px 10px;
    }}

    /* Progress Bar */
    QProgressBar {{
        background-color: #E2E8F0;
        border-radius: 4px;
        text-align: center;
        font-size: 11px;
        font-weight: 600;
        color: {THEME.TEXT_PRIMARY};
        height: 14px;
    }}

    QProgressBar::chunk {{
        background-color: {THEME.PRIMARY};
        border-radius: 4px;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        border: none;
        background: transparent;
        width: 8px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: #CBD5E1;
        min-height: 24px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: #94A3B8;
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* Splitters */
    QSplitter::handle {{
        background-color: {THEME.BORDER};
    }}

    QSplitter::handle:hover {{
        background-color: {THEME.PRIMARY};
    }}

    /* Status Badges */
    QLabel.badgeSuccess {{
        background-color: {THEME.SUCCESS_LIGHT};
        color: #065F46;
        border: 1px solid #A7F3D0;
        border-radius: 4px;
        padding: 2px 8px;
        font-weight: 600;
        font-size: 11px;
    }}

    QLabel.badgeWarning {{
        background-color: {THEME.WARNING_LIGHT};
        color: #92400E;
        border: 1px solid #FDE68A;
        border-radius: 4px;
        padding: 2px 8px;
        font-weight: 600;
        font-size: 11px;
    }}

    QLabel.badgeError {{
        background-color: {THEME.ERROR_LIGHT};
        color: #991B1B;
        border: 1px solid #FECACA;
        border-radius: 4px;
        padding: 2px 8px;
        font-weight: 600;
        font-size: 11px;
    }}
    """
