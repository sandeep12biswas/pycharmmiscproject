import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.config import RESOURCES_DIR
from app.db.connection import open_database
from app.repositories.folders_repo import FoldersRepository
from app.repositories.notes_repo import NotesRepository
from app.repositories.reminders_repo import RemindersRepository
from app.repositories.tags_repo import TagsRepository
from app.ui.main_window import MainWindow
from app.ui.theme import apply_theme, load_theme


def main() -> int:
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(RESOURCES_DIR / "icons" / "icon.png")))
    apply_theme(app, load_theme())
    conn = open_database()
    repo = NotesRepository(conn)
    folders_repo = FoldersRepository(conn)
    tags_repo = TagsRepository(conn)
    reminders_repo = RemindersRepository(conn)
    window = MainWindow(repo, folders_repo, tags_repo, reminders_repo)
    window.show()
    exit_code = app.exec()
    conn.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
