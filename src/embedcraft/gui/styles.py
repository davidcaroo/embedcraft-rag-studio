"""Modern, production-grade QSS stylesheet generator for EmbedCraft RAG Studio."""

from embedcraft.gui.theme import FONT_CODE, FONT_FAMILY, ThemeMode, get_palette


def get_application_stylesheet(mode: ThemeMode | str = ThemeMode.DARK) -> str:
    """Generate global application QSS stylesheet for the specified theme mode."""
    palette = get_palette(mode)

    return f"""
    * {{
        font-family: {FONT_FAMILY};
        font-size: 13px;
        color: {palette.TEXT_PRIMARY};
    }}

    QMainWindow, QDialog, QWidget#workspace {{
        background-color: {palette.BG_BASE};
    }}

    /* Sidebar Navigation */
    QWidget#sidebar {{
        background-color: {palette.SIDEBAR_BG};
        border-right: 1px solid {palette.SIDEBAR_BORDER};
    }}

    QLabel#sidebarBrand {{
        color: {palette.TEXT_PRIMARY};
        font-size: 16px;
        font-weight: 700;
        padding: 18px 16px 10px 16px;
    }}

    QLabel#sidebarSection {{
        color: {palette.SIDEBAR_TEXT_MUTED};
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        padding: 14px 16px 6px 16px;
        letter-spacing: 0.5px;
    }}

    QPushButton.sidebarNavBtn {{
        background-color: transparent;
        color: {palette.SIDEBAR_TEXT};
        text-align: left;
        padding: 9px 16px;
        border: none;
        border-radius: 6px;
        margin: 2px 10px;
        font-size: 13px;
        font-weight: 500;
    }}

    QPushButton.sidebarNavBtn:hover {{
        background-color: {palette.SIDEBAR_ITEM_HOVER};
        color: {palette.TEXT_PRIMARY};
    }}

    QPushButton.sidebarNavBtn:checked, QPushButton.sidebarNavBtn[active="true"] {{
        background-color: {palette.PRIMARY};
        color: #FFFFFF;
        font-weight: 600;
    }}

    /* Header Bar */
    QWidget#headerBar {{
        background-color: {palette.HEADER_BG};
        border-bottom: 1px solid {palette.HEADER_BORDER};
        padding: 0px 24px;
        min-height: 56px;
        max-height: 56px;
    }}

    QLabel#headerTitle {{
        font-size: 16px;
        font-weight: 700;
        color: {palette.TEXT_PRIMARY};
    }}

    QLabel#viewTitle {{
        color: {palette.TEXT_PRIMARY};
        font-size: 18px;
        font-weight: 700;
    }}

    /* Cards */
    QFrame.card {{
        background-color: {palette.BG_CARD};
        border: 1px solid {palette.BORDER};
        border-radius: 8px;
    }}

    QLabel#cardTitle {{
        font-size: 15px;
        font-weight: 600;
        color: {palette.TEXT_PRIMARY};
    }}

    QLabel#cardSubtitle {{
        font-size: 12px;
        color: {palette.TEXT_MUTED};
    }}

    /* Buttons */
    QPushButton {{
        background-color: {palette.BG_CARD};
        color: {palette.TEXT_PRIMARY};
        border: 1px solid {palette.BORDER};
        border-radius: 6px;
        padding: 7px 14px;
        font-size: 13px;
        font-weight: 500;
    }}

    QPushButton:hover {{
        background-color: {palette.BG_HOVER};
        border-color: {palette.BORDER_HOVER};
    }}

    QPushButton:pressed {{
        background-color: {palette.BORDER};
    }}

    QPushButton:disabled {{
        background-color: {palette.BG_BASE};
        color: {palette.TEXT_MUTED};
        border-color: {palette.BORDER};
    }}

    QPushButton.primaryBtn {{
        background-color: {palette.PRIMARY};
        color: #FFFFFF;
        border: 1px solid {palette.PRIMARY};
        font-weight: 600;
    }}

    QPushButton.primaryBtn:hover {{
        background-color: {palette.PRIMARY_HOVER};
        border-color: {palette.PRIMARY_HOVER};
    }}

    QPushButton.primaryBtn:pressed {{
        background-color: {palette.PRIMARY_ACTIVE};
    }}

    QPushButton.dangerBtn {{
        background-color: {palette.ERROR};
        color: #FFFFFF;
        border: 1px solid {palette.ERROR};
        font-weight: 600;
    }}

    QPushButton.dangerBtn:hover {{
        background-color: #DC2626;
        border-color: #DC2626;
    }}

    /* Form Controls */
    QLineEdit, QComboBox, QSpinBox {{
        background-color: {palette.BG_INPUT};
        border: 1px solid {palette.BORDER};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 13px;
        color: {palette.TEXT_PRIMARY};
        selection-background-color: {palette.PRIMARY_LIGHT};
        selection-color: {palette.PRIMARY};
    }}

    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border-color: {palette.BORDER_FOCUS};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QTextEdit, QPlainTextEdit {{
        background-color: {palette.BG_INPUT};
        border: 1px solid {palette.BORDER};
        border-radius: 6px;
        padding: 8px;
        font-size: 13px;
        color: {palette.TEXT_PRIMARY};
    }}

    QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {palette.BORDER_FOCUS};
    }}

    QTextEdit#codeConsole, QPlainTextEdit#codeConsole {{
        font-family: {FONT_CODE};
        font-size: 12px;
        background-color: {palette.CODE_BG};
        color: {palette.CODE_TEXT};
        border-radius: 6px;
        border: 1px solid {palette.CODE_BORDER};
    }}

    /* Tables */
    QTableWidget {{
        background-color: {palette.BG_CARD};
        border: 1px solid {palette.BORDER};
        border-radius: 6px;
        gridline-color: {palette.BORDER};
        color: {palette.TEXT_PRIMARY};
        selection-background-color: {palette.PRIMARY_LIGHT};
        selection-color: {palette.TEXT_PRIMARY};
    }}

    QTableWidget::item {{
        padding: 6px 10px;
        border-bottom: 1px solid {palette.BORDER};
    }}

    QHeaderView::section {{
        background-color: {palette.BG_BASE};
        color: {palette.TEXT_MUTED};
        font-weight: 600;
        font-size: 12px;
        border: none;
        border-bottom: 1px solid {palette.BORDER};
        padding: 8px 10px;
    }}

    /* Progress Bar */
    QProgressBar {{
        background-color: {palette.BORDER};
        border-radius: 4px;
        text-align: center;
        font-size: 11px;
        font-weight: 600;
        color: {palette.TEXT_PRIMARY};
        height: 14px;
    }}

    QProgressBar::chunk {{
        background-color: {palette.PRIMARY};
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
        background: {palette.BORDER_HOVER};
        min-height: 24px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {palette.BORDER_FOCUS};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* Splitters */
    QSplitter::handle {{
        background-color: {palette.BORDER};
    }}

    QSplitter::handle:hover {{
        background-color: {palette.PRIMARY};
    }}

    /* Status Badges */
    QLabel.badgeSuccess {{
        background-color: {palette.SUCCESS_LIGHT};
        color: {palette.SUCCESS};
        border: 1px solid {palette.SUCCESS};
        border-radius: 4px;
        padding: 2px 8px;
        font-weight: 600;
        font-size: 11px;
    }}

    QLabel.badgeWarning {{
        background-color: {palette.WARNING_LIGHT};
        color: {palette.WARNING};
        border: 1px solid {palette.WARNING};
        border-radius: 4px;
        padding: 2px 8px;
        font-weight: 600;
        font-size: 11px;
    }}

    QLabel.badgeError {{
        background-color: {palette.ERROR_LIGHT};
        color: {palette.ERROR};
        border: 1px solid {palette.ERROR};
        border-radius: 4px;
        padding: 2px 8px;
        font-weight: 600;
        font-size: 11px;
    }}

    QLabel.badgeInfo {{
        background-color: {palette.INFO_LIGHT};
        color: {palette.INFO};
        border: 1px solid {palette.INFO};
        border-radius: 4px;
        padding: 2px 8px;
        font-weight: 600;
        font-size: 11px;
    }}
    """
