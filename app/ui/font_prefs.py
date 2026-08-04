from typing import List

from PySide6.QtCore import QSettings
from PySide6.QtGui import QFontDatabase, QGuiApplication

from app.config import get_settings_path

FONT_SETTINGS_KEY = "editor/font_family"

# Aptos ships with Windows 11 / Office 2021+ but isn't a Linux system font and
# isn't guaranteed on older Windows installs -- used only if actually present.
DEFAULT_FONT_FAMILY = "Aptos"


def _settings() -> QSettings:
    return QSettings(str(get_settings_path()), QSettings.Format.IniFormat)


def available_font_families() -> List[str]:
    return QFontDatabase.families()


def resolve_default_font_family() -> str:
    """Aptos if installed, else whatever font the application already
    defaults to -- no bundled font file, no hard OS dependency."""
    if DEFAULT_FONT_FAMILY in QFontDatabase.families():
        return DEFAULT_FONT_FAMILY
    return QGuiApplication.font().family()


def load_font_family() -> str:
    value = _settings().value(FONT_SETTINGS_KEY, "")
    if value and value in QFontDatabase.families():
        return value
    return resolve_default_font_family()


def save_font_family(family: str) -> None:
    settings = _settings()
    settings.setValue(FONT_SETTINGS_KEY, family)
    settings.sync()
