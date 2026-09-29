"""Design tokens, color palettes, and typography for EmbedCraft RAG Studio."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    # Sidebar (Dark theme)
    SIDEBAR_BG: str = "#181825"
    SIDEBAR_BORDER: str = "#313244"
    SIDEBAR_TEXT: str = "#CDD6F4"
    SIDEBAR_TEXT_MUTED: str = "#A6ADC8"
    SIDEBAR_ITEM_HOVER: str = "#313244"
    SIDEBAR_ITEM_ACTIVE: str = "#45475A"

    # Workspace (Light theme)
    BG_BASE: str = "#F8FAFC"
    BG_CARD: str = "#FFFFFF"
    BORDER: str = "#E2E8F0"
    BORDER_HOVER: str = "#CBD5E1"
    BORDER_FOCUS: str = "#6366F1"

    # Text hierarchy
    TEXT_PRIMARY: str = "#0F172A"
    TEXT_SECONDARY: str = "#334155"
    TEXT_MUTED: str = "#64748B"
    TEXT_INVERSE: str = "#F8FAFC"

    # Brand Colors (Violet / Indigo)
    PRIMARY: str = "#6366F1"
    PRIMARY_HOVER: str = "#4F46E5"
    PRIMARY_ACTIVE: str = "#4338CA"
    PRIMARY_LIGHT: str = "#EEF2FF"

    # Functional Status Colors
    SUCCESS: str = "#10B981"
    SUCCESS_LIGHT: str = "#ECFDF5"
    WARNING: str = "#F59E0B"
    WARNING_LIGHT: str = "#FFFBEB"
    ERROR: str = "#EF4444"
    ERROR_LIGHT: str = "#FEF2F2"
    INFO: str = "#06B6D4"
    INFO_LIGHT: str = "#ECFEFF"


THEME = Palette()

FONT_FAMILY = "Segoe UI, -apple-system, BlinkMacSystemFont, 'Segoe UI Emoji', sans-serif"
FONT_CODE = "'Cascadia Code', 'Consolas', 'Courier New', monospace"
