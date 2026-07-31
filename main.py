import sys

from PySide6.QtWidgets import QApplication

from app.db.connection import open_database
from app.repositories.notes_repo import NotesRepository
from app.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    conn = open_database()
    repo = NotesRepository(conn)
    window = MainWindow(repo)
    window.show()
    exit_code = app.exec()
    conn.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
