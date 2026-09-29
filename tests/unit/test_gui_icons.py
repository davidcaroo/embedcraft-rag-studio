"""Unit tests for the vector SVG icon engine (embedcraft.gui.icons)."""

import sys

import pytest
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication

from embedcraft.gui.icons import (
    ICON_SVGS,
    get_icon,
    get_pixmap,
    list_available_icons,
)


@pytest.fixture(scope="session")
def qapp():
    """Ensure a QApplication instance exists for QPixmap / QPainter tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv if hasattr(sys, "argv") and sys.argv else ["pytest"])
    yield app


REQUIRED_ICONS = [
    "dashboard",
    "projects",
    "monitor",
    "preview",
    "collections",
    "chat",
    "doctor",
    "sun",
    "moon",
    "plus",
    "download",
    "upload",
    "play",
    "stop",
    "refresh",
    "check",
    "alert",
    "close",
    "folder",
    "file",
]


def test_list_available_icons():
    """Test that list_available_icons returns a set containing all required icon keys."""
    available = list_available_icons()
    assert isinstance(available, set)
    for icon_name in REQUIRED_ICONS:
        assert icon_name in available, f"Required icon '{icon_name}' missing from available icons"


def test_icon_svgs_structure():
    """Test that ICON_SVGS contains valid SVG templates with {color} and viewBox."""
    assert isinstance(ICON_SVGS, dict)
    for name, svg in ICON_SVGS.items():
        assert "{color}" in svg, f"Icon '{name}' template must contain '{{color}}' placeholder"
        assert 'viewBox="0 0 24 24"' in svg, f"Icon '{name}' must have viewBox='0 0 24 24'"


def test_get_pixmap_default(qapp):
    """Test get_pixmap returns a non-null QPixmap with default size and color."""
    pixmap = get_pixmap("dashboard")
    assert isinstance(pixmap, QPixmap)
    assert not pixmap.isNull()
    assert pixmap.width() == 18
    assert pixmap.height() == 18


def test_get_pixmap_custom_size_and_color(qapp):
    """Test get_pixmap with custom size and custom color."""
    pixmap = get_pixmap("chat", color="#10B981", size=32)
    assert isinstance(pixmap, QPixmap)
    assert not pixmap.isNull()
    assert pixmap.width() == 32
    assert pixmap.height() == 32


def test_get_pixmap_fallback_for_unknown_icon(qapp):
    """Test get_pixmap returns a safe fallback pixmap without raising an error."""
    pixmap = get_pixmap("unknown_icon_that_does_not_exist", size=24)
    assert isinstance(pixmap, QPixmap)
    assert not pixmap.isNull()
    assert pixmap.width() == 24
    assert pixmap.height() == 24


def test_get_icon(qapp):
    """Test get_icon returns a valid QIcon."""
    icon = get_icon("preview", color="#6366F1", size=20)
    assert isinstance(icon, QIcon)
    assert not icon.isNull()
    rendered_pixmap = icon.pixmap(20, 20)
    assert not rendered_pixmap.isNull()
    assert rendered_pixmap.width() == 20
    assert rendered_pixmap.height() == 20


@pytest.mark.parametrize("icon_name", REQUIRED_ICONS)
def test_all_required_icons_render_pixmaps(qapp, icon_name):
    """Test that every required icon renders cleanly to a QPixmap."""
    pixmap = get_pixmap(icon_name, size=24)
    assert not pixmap.isNull()
    assert pixmap.width() == 24
    assert pixmap.height() == 24
