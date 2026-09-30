"""Unit tests for theme architecture and dynamic QSS generator.

Tests ThemeMode, Palette tokens, DARK_PALETTE, LIGHT_PALETTE,
ThemeManager reactivity, and get_application_stylesheet.
"""

import sys

import pytest
from PySide6.QtWidgets import QApplication

from embedcraft.gui.styles import get_application_stylesheet
from embedcraft.gui.theme import (
    DARK_PALETTE,
    LIGHT_PALETTE,
    THEME,
    Palette,
    ThemeManager,
    ThemeMode,
    get_palette,
    theme_manager,
)


@pytest.fixture(scope="session")
def qapp():
    """Ensure a QApplication instance exists for QObject / Signal tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv if hasattr(sys, "argv") and sys.argv else ["pytest"])
    yield app


class TestThemeMode:
    """Tests for ThemeMode enum."""

    def test_theme_mode_values(self):
        assert ThemeMode.DARK == "dark"
        assert ThemeMode.LIGHT == "light"
        assert ThemeMode("dark") is ThemeMode.DARK
        assert ThemeMode("light") is ThemeMode.LIGHT


class TestPalettes:
    """Tests for Palette dataclass and predefined palettes."""

    def test_dark_palette_tokens(self):
        assert isinstance(DARK_PALETTE, Palette)
        assert DARK_PALETTE.BG_BASE == "#0B0F19"
        assert DARK_PALETTE.BG_CARD == "#111827"
        assert DARK_PALETTE.BG_HOVER == "#1F2937"
        assert DARK_PALETTE.BG_INPUT == "#1F2937"
        assert DARK_PALETTE.BORDER == "#374151"
        assert DARK_PALETTE.BORDER_HOVER == "#4B5563"
        assert DARK_PALETTE.BORDER_FOCUS == "#6366F1"
        assert DARK_PALETTE.TEXT_PRIMARY == "#F9FAFB"
        assert DARK_PALETTE.TEXT_SECONDARY == "#E5E7EB"
        assert DARK_PALETTE.TEXT_MUTED == "#9CA3AF"
        assert DARK_PALETTE.TEXT_INVERSE == "#0B0F19"
        assert DARK_PALETTE.SIDEBAR_BG == "#0B0F19"
        assert DARK_PALETTE.SIDEBAR_BORDER == "#1F2937"
        assert DARK_PALETTE.SIDEBAR_TEXT == "#E5E7EB"
        assert DARK_PALETTE.SIDEBAR_TEXT_MUTED == "#9CA3AF"
        assert DARK_PALETTE.HEADER_BG == "#111827"
        assert DARK_PALETTE.HEADER_BORDER == "#1F2937"
        assert DARK_PALETTE.CODE_BG == "#030712"
        assert DARK_PALETTE.CODE_TEXT == "#F3F4F6"
        assert DARK_PALETTE.CODE_BORDER == "#1F2937"

    def test_light_palette_tokens(self):
        assert LIGHT_PALETTE.BG_BASE == "#F8FAFC"
        assert LIGHT_PALETTE.BG_CARD == "#FFFFFF"
        assert LIGHT_PALETTE.BG_HOVER == "#F1F5F9"
        assert LIGHT_PALETTE.BG_INPUT == "#FFFFFF"
        assert LIGHT_PALETTE.BORDER == "#E2E8F0"
        assert LIGHT_PALETTE.BORDER_HOVER == "#CBD5E1"
        assert LIGHT_PALETTE.BORDER_FOCUS == "#4F46E5"
        assert LIGHT_PALETTE.TEXT_PRIMARY == "#0F172A"
        assert LIGHT_PALETTE.TEXT_SECONDARY == "#334155"
        assert LIGHT_PALETTE.TEXT_MUTED == "#64748B"
        assert LIGHT_PALETTE.TEXT_INVERSE == "#FFFFFF"
        assert LIGHT_PALETTE.SIDEBAR_BG == "#FFFFFF"
        assert LIGHT_PALETTE.SIDEBAR_BORDER == "#E2E8F0"
        assert LIGHT_PALETTE.SIDEBAR_TEXT == "#334155"
        assert LIGHT_PALETTE.SIDEBAR_TEXT_MUTED == "#64748B"
        assert LIGHT_PALETTE.HEADER_BG == "#FFFFFF"
        assert LIGHT_PALETTE.HEADER_BORDER == "#E2E8F0"
        assert LIGHT_PALETTE.CODE_BG == "#0F172A"
        assert LIGHT_PALETTE.CODE_TEXT == "#F8FAFC"
        assert LIGHT_PALETTE.CODE_BORDER == "#334155"

    def test_get_palette_resolution(self):
        assert get_palette() == DARK_PALETTE
        assert get_palette(ThemeMode.DARK) == DARK_PALETTE
        assert get_palette("dark") == DARK_PALETTE
        assert get_palette(ThemeMode.LIGHT) == LIGHT_PALETTE
        assert get_palette("light") == LIGHT_PALETTE

    def test_backwards_compatibility_theme(self):
        assert THEME == DARK_PALETTE


class TestThemeManager:
    """Tests for ThemeManager reactive state and signaling."""

    def test_initial_state(self, qapp):
        mgr = ThemeManager()
        assert mgr.mode == ThemeMode.DARK

    def test_set_mode_emits_signal(self, qapp):
        mgr = ThemeManager()
        emitted = []
        mgr.theme_changed.connect(lambda mode: emitted.append(mode))

        mgr.set_mode(ThemeMode.LIGHT)
        assert mgr.mode == ThemeMode.LIGHT
        assert emitted == ["light"]

        # Setting same mode should not re-emit
        mgr.set_mode(ThemeMode.LIGHT)
        assert emitted == ["light"]

        # Setting back to dark with string
        mgr.set_mode("dark")
        assert mgr.mode == ThemeMode.DARK
        assert emitted == ["light", "dark"]

    def test_toggle_theme(self, qapp):
        mgr = ThemeManager(ThemeMode.DARK)
        emitted = []
        mgr.theme_changed.connect(lambda mode: emitted.append(mode))

        new_mode = mgr.toggle_theme()
        assert new_mode == ThemeMode.LIGHT
        assert mgr.mode == ThemeMode.LIGHT
        assert emitted == ["light"]

        new_mode2 = mgr.toggle_theme()
        assert new_mode2 == ThemeMode.DARK
        assert mgr.mode == ThemeMode.DARK
        assert emitted == ["light", "dark"]

    def test_global_theme_manager_instance(self, qapp):
        assert isinstance(theme_manager, ThemeManager)


class TestStylesheetGeneration:
    """Tests for dynamic QSS generation."""

    def test_stylesheet_dark_mode(self):
        qss = get_application_stylesheet(ThemeMode.DARK)
        assert DARK_PALETTE.BG_BASE in qss
        assert DARK_PALETTE.BG_CARD in qss
        assert DARK_PALETTE.BORDER in qss
        assert DARK_PALETTE.TEXT_PRIMARY in qss
        assert "QWidget#sidebar" in qss
        assert "QWidget#headerBar" in qss
        assert "QFrame.card" in qss
        assert "QLabel#viewTitle" in qss

    def test_stylesheet_light_mode(self):
        qss = get_application_stylesheet(ThemeMode.LIGHT)
        assert LIGHT_PALETTE.BG_BASE in qss
        assert LIGHT_PALETTE.BG_CARD in qss
        assert LIGHT_PALETTE.BORDER in qss
        assert LIGHT_PALETTE.TEXT_PRIMARY in qss
        assert "QWidget#sidebar" in qss
        assert "QWidget#headerBar" in qss
        assert "QFrame.card" in qss
        assert "QLabel#viewTitle" in qss

    def test_dark_and_light_stylesheets_differ(self):
        dark_qss = get_application_stylesheet(ThemeMode.DARK)
        light_qss = get_application_stylesheet(ThemeMode.LIGHT)
        assert dark_qss != light_qss
