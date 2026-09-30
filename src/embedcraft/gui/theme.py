"""Design tokens, color palettes, and reactive theme management for EmbedCraft RAG Studio."""

from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QObject, Signal


class ThemeMode(str, Enum):
    """Supported UI theme modes."""

    LIGHT = "light"
    DARK = "dark"


@dataclass(frozen=True)
class Palette:
    """Color palette and design tokens for UI styling."""

    # Workspace Surfaces & Backgrounds
    BG_BASE: str
    BG_CARD: str
    BG_HOVER: str
    BG_INPUT: str

    # Borders & Dividers
    BORDER: str
    BORDER_HOVER: str
    BORDER_FOCUS: str

    # Typography Hierarchy
    TEXT_PRIMARY: str
    TEXT_SECONDARY: str
    TEXT_MUTED: str
    TEXT_INVERSE: str

    # Brand Colors (Violet / Indigo)
    PRIMARY: str
    PRIMARY_HOVER: str
    PRIMARY_ACTIVE: str
    PRIMARY_LIGHT: str

    # Functional Status Colors
    SUCCESS: str
    SUCCESS_LIGHT: str
    WARNING: str
    WARNING_LIGHT: str
    ERROR: str
    ERROR_LIGHT: str
    INFO: str
    INFO_LIGHT: str

    # Sidebar Navigation
    SIDEBAR_BG: str
    SIDEBAR_BORDER: str
    SIDEBAR_TEXT: str
    SIDEBAR_TEXT_MUTED: str
    SIDEBAR_ITEM_HOVER: str
    SIDEBAR_ITEM_ACTIVE: str

    # Header Bar
    HEADER_BG: str
    HEADER_BORDER: str

    # Code & Terminal
    CODE_BG: str
    CODE_TEXT: str
    CODE_BORDER: str


DARK_PALETTE = Palette(
    BG_BASE="#0B0F19",
    BG_CARD="#111827",
    BG_HOVER="#1F2937",
    BG_INPUT="#1F2937",
    BORDER="#374151",
    BORDER_HOVER="#4B5563",
    BORDER_FOCUS="#6366F1",
    TEXT_PRIMARY="#F9FAFB",
    TEXT_SECONDARY="#E5E7EB",
    TEXT_MUTED="#9CA3AF",
    TEXT_INVERSE="#0B0F19",
    PRIMARY="#6366F1",
    PRIMARY_HOVER="#4F46E5",
    PRIMARY_ACTIVE="#4338CA",
    PRIMARY_LIGHT="#1E1B4B",
    SUCCESS="#10B981",
    SUCCESS_LIGHT="#064E3B",
    WARNING="#F59E0B",
    WARNING_LIGHT="#78350F",
    ERROR="#EF4444",
    ERROR_LIGHT="#7F1D1D",
    INFO="#06B6D4",
    INFO_LIGHT="#164E63",
    SIDEBAR_BG="#0B0F19",
    SIDEBAR_BORDER="#1F2937",
    SIDEBAR_TEXT="#E5E7EB",
    SIDEBAR_TEXT_MUTED="#9CA3AF",
    SIDEBAR_ITEM_HOVER="#1F2937",
    SIDEBAR_ITEM_ACTIVE="#374151",
    HEADER_BG="#111827",
    HEADER_BORDER="#1F2937",
    CODE_BG="#030712",
    CODE_TEXT="#F3F4F6",
    CODE_BORDER="#1F2937",
)

LIGHT_PALETTE = Palette(
    BG_BASE="#F8FAFC",
    BG_CARD="#FFFFFF",
    BG_HOVER="#F1F5F9",
    BG_INPUT="#FFFFFF",
    BORDER="#E2E8F0",
    BORDER_HOVER="#CBD5E1",
    BORDER_FOCUS="#4F46E5",
    TEXT_PRIMARY="#0F172A",
    TEXT_SECONDARY="#334155",
    TEXT_MUTED="#64748B",
    TEXT_INVERSE="#FFFFFF",
    PRIMARY="#6366F1",
    PRIMARY_HOVER="#4F46E5",
    PRIMARY_ACTIVE="#4338CA",
    PRIMARY_LIGHT="#EEF2FF",
    SUCCESS="#10B981",
    SUCCESS_LIGHT="#ECFDF5",
    WARNING="#F59E0B",
    WARNING_LIGHT="#FFFBEB",
    ERROR="#EF4444",
    ERROR_LIGHT="#FEF2F2",
    INFO="#06B6D4",
    INFO_LIGHT="#ECFEFF",
    SIDEBAR_BG="#FFFFFF",
    SIDEBAR_BORDER="#E2E8F0",
    SIDEBAR_TEXT="#334155",
    SIDEBAR_TEXT_MUTED="#64748B",
    SIDEBAR_ITEM_HOVER="#F1F5F9",
    SIDEBAR_ITEM_ACTIVE="#E2E8F0",
    HEADER_BG="#FFFFFF",
    HEADER_BORDER="#E2E8F0",
    CODE_BG="#0F172A",
    CODE_TEXT="#F8FAFC",
    CODE_BORDER="#334155",
)


def get_palette(mode: ThemeMode | str = ThemeMode.DARK) -> Palette:
    """Return the design Palette corresponding to the specified theme mode."""
    if isinstance(mode, str):
        try:
            mode = ThemeMode(mode)
        except ValueError:
            mode = ThemeMode.DARK
    if mode == ThemeMode.LIGHT:
        return LIGHT_PALETTE
    return DARK_PALETTE


# Backwards compatibility
THEME = DARK_PALETTE

FONT_FAMILY = "Segoe UI, -apple-system, BlinkMacSystemFont, 'Segoe UI Emoji', sans-serif"
FONT_CODE = "'Cascadia Code', 'Consolas', 'Courier New', monospace"


class ThemeManager(QObject):
    """Reactive manager for theme changes across the application."""

    theme_changed = Signal(str)

    def __init__(self, default_mode: ThemeMode | str = ThemeMode.DARK) -> None:
        super().__init__()
        if isinstance(default_mode, str):
            try:
                self._mode = ThemeMode(default_mode)
            except ValueError:
                self._mode = ThemeMode.DARK
        else:
            self._mode = default_mode

    @property
    def mode(self) -> ThemeMode:
        """Current theme mode."""
        return self._mode

    def set_mode(self, mode: ThemeMode | str) -> None:
        """Set the active theme mode and emit theme_changed if the mode changed."""
        if isinstance(mode, str):
            try:
                target_mode = ThemeMode(mode)
            except ValueError:
                target_mode = ThemeMode.DARK
        else:
            target_mode = mode

        if self._mode != target_mode:
            self._mode = target_mode
            self.theme_changed.emit(self._mode.value)

    def toggle_theme(self) -> ThemeMode:
        """Toggle between Dark and Light mode, emitting theme_changed."""
        new_mode = ThemeMode.LIGHT if self._mode == ThemeMode.DARK else ThemeMode.DARK
        self.set_mode(new_mode)
        return self._mode


# Global reactive theme manager instance
theme_manager = ThemeManager()
