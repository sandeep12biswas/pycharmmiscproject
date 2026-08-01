import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QStandardPaths

APP_NAME = "NoteApp"
DB_FILENAME = "notes.db"
SETTINGS_FILENAME = "settings.ini"


def _resources_dir() -> Path:
    """In a PyInstaller-frozen build, bundled data files (see
    packaging/noteapp.spec's `datas`) are extracted to sys._MEIPASS at
    runtime, not laid out next to this source file -- that layout only
    exists in dev mode. Both cases put a `resources/` dir at the resolved
    root, so only the root itself differs."""
    if hasattr(sys, "_MEIPASS"):
        root = Path(sys._MEIPASS)
    else:
        root = Path(__file__).resolve().parent.parent
    return root / "resources"


RESOURCES_DIR = _resources_dir()


def get_app_data_dir() -> Path:
    """Re-asserts applicationName on every call rather than relying on a
    one-time import-time side effect: QCoreApplication pre-populates
    applicationName() from argv[0] by default, and other Qt-using code in the
    same process (observed with pytest-qt's own fixtures) can reset it after
    this module is first imported. Setting it here, right before resolving
    the path, keeps the app-data directory name fixed regardless of what ran
    before it or how the process was launched."""
    QCoreApplication.setApplicationName(APP_NAME)
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    path = Path(location)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_db_path() -> Path:
    return get_app_data_dir() / DB_FILENAME


def get_settings_path() -> Path:
    return get_app_data_dir() / SETTINGS_FILENAME
