from pathlib import Path

from PySide6.QtCore import QCoreApplication, QStandardPaths

APP_NAME = "NoteApp"
DB_FILENAME = "notes.db"

if not QCoreApplication.applicationName():
    QCoreApplication.setApplicationName(APP_NAME)


def get_app_data_dir() -> Path:
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    path = Path(location)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_db_path() -> Path:
    return get_app_data_dir() / DB_FILENAME
