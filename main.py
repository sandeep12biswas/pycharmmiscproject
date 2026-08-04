import logging
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.config import RESOURCES_DIR, get_app_data_dir
from app.db.connection import open_database
from app.logging_config import configure_logging, install_excepthook
from app.repositories.folders_repo import FoldersRepository
from app.repositories.notes_repo import NotesRepository
from app.repositories.reminders_repo import RemindersRepository
from app.repositories.tags_repo import TagsRepository
from app.repositories.tiles_repo import TilesRepository
from app.ui.main_window import MainWindow
from app.ui.theme import apply_theme, load_theme

logger = logging.getLogger(__name__)


def main() -> int:
    app = QApplication(sys.argv)
    configure_logging(get_app_data_dir() / "logs")
    install_excepthook()
    logger.info("NoteApp starting")

    app.setWindowIcon(QIcon(str(RESOURCES_DIR / "icons" / "icon.png")))
    apply_theme(app, load_theme())
    conn = open_database()
    repo = NotesRepository(conn)
    folders_repo = FoldersRepository(conn)
    tags_repo = TagsRepository(conn)
    reminders_repo = RemindersRepository(conn)
    tiles_repo = TilesRepository(conn)
    window = MainWindow(repo, folders_repo, tags_repo, reminders_repo, tiles_repo)
    window.show()
    exit_code = app.exec()
    conn.close()
    logger.info("NoteApp exiting (code=%s)", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
