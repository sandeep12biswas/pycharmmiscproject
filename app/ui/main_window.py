from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import QLabel, QMainWindow, QSplitter, QToolBar

from app.controllers.note_controller import NoteController
from app.repositories.notes_repo import NotesRepository
from app.ui.editor import NoteEditorWidget
from app.ui.models_qt import NoteListModel
from app.ui.note_list import NoteListWidget


class MainWindow(QMainWindow):
    def __init__(self, repo: NotesRepository, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Notes")
        self.resize(1100, 720)

        self._model = NoteListModel(repo)
        note_list = NoteListWidget(self._model)
        editor = NoteEditorWidget()

        sidebar = QLabel("Folders\n(coming soon)")
        sidebar.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(sidebar)
        splitter.addWidget(note_list)
        splitter.addWidget(editor)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 4)
        self.setCentralWidget(splitter)

        self._controller = NoteController(repo, self._model, note_list, editor, parent=self)

        toolbar = QToolBar("Main", self)
        self.addToolBar(toolbar)

        new_action = QAction("New Note", self)
        new_action.triggered.connect(self._controller.new_note)
        toolbar.addAction(new_action)

        delete_action = QAction("Delete Note", self)
        delete_action.triggered.connect(self._controller.delete_current_note)
        toolbar.addAction(delete_action)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._controller.flush_pending()
        super().closeEvent(event)
