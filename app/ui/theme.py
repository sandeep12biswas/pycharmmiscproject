from enum import Enum
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from app.config import RESOURCES_DIR, get_settings_path

THEME_SETTINGS_KEY = "appearance/theme"


class Theme(str, Enum):
    LIGHT = "light"
    DARK = "dark"


_PALETTE_COLORS = {
    Theme.LIGHT: {
        QPalette.ColorRole.Window: "#f5f5f5",
        QPalette.ColorRole.WindowText: "#202020",
        QPalette.ColorRole.Base: "#ffffff",
        QPalette.ColorRole.AlternateBase: "#eeeeee",
        QPalette.ColorRole.Text: "#202020",
        QPalette.ColorRole.Button: "#e8e8e8",
        QPalette.ColorRole.ButtonText: "#202020",
        QPalette.ColorRole.Highlight: "#2f6fed",
        QPalette.ColorRole.HighlightedText: "#ffffff",
        QPalette.ColorRole.ToolTipBase: "#ffffe1",
        QPalette.ColorRole.ToolTipText: "#202020",
        QPalette.ColorRole.PlaceholderText: "#8a8a8a",
        QPalette.ColorRole.Midlight: "#e0e0e0",
    },
    Theme.DARK: {
        QPalette.ColorRole.Window: "#2b2b2b",
        QPalette.ColorRole.WindowText: "#e6e6e6",
        QPalette.ColorRole.Base: "#1e1e1e",
        QPalette.ColorRole.AlternateBase: "#333333",
        QPalette.ColorRole.Text: "#e6e6e6",
        QPalette.ColorRole.Button: "#3a3a3a",
        QPalette.ColorRole.ButtonText: "#e6e6e6",
        QPalette.ColorRole.Highlight: "#3d7dfc",
        QPalette.ColorRole.HighlightedText: "#ffffff",
        QPalette.ColorRole.ToolTipBase: "#3a3a3a",
        QPalette.ColorRole.ToolTipText: "#e6e6e6",
        QPalette.ColorRole.PlaceholderText: "#9a9a9a",
        QPalette.ColorRole.Midlight: "#444444",
    },
}


def _settings() -> QSettings:
    return QSettings(str(get_settings_path()), QSettings.Format.IniFormat)


def load_theme() -> Theme:
    value = _settings().value(THEME_SETTINGS_KEY, Theme.LIGHT.value)
    try:
        return Theme(value)
    except ValueError:
        return Theme.LIGHT


def save_theme(theme: Theme) -> None:
    settings = _settings()
    settings.setValue(THEME_SETTINGS_KEY, theme.value)
    settings.sync()


def stylesheet_path(theme: Theme) -> Path:
    return RESOURCES_DIR / "styles" / f"{theme.value}.qss"


def build_palette(theme: Theme) -> QPalette:
    palette = QPalette()
    for role, hex_color in _PALETTE_COLORS[theme].items():
        palette.setColor(role, QColor(hex_color))
    return palette


def apply_theme(app: QApplication, theme: Theme) -> None:
    app.setPalette(build_palette(theme))
    path = stylesheet_path(theme)
    app.setStyleSheet(path.read_text() if path.exists() else "")
