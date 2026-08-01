from typing import Dict, Optional

from PySide6.QtCore import QModelIndex, Qt, QTimer, Signal
from PySide6.QtWidgets import QLineEdit, QListView, QMenu, QMessageBox, QVBoxLayout, QWidget

from app.models.folder import Folder
from app.repositories.folders_repo import FoldersRepository
from app.ui.models_qt import NoteListModel

SEARCH_DEBOUNCE_MS = 250


class NoteListWidget(QWidget):
    noteSelected = Signal(int)  # note_id, or -1 when nothing is selected
    noteFolderChangeRequested = Signal(int, object)  # note_id, folder_id (Optional[int])
    notePinToggleRequested = Signal(int)  # note_id
    noteFavoriteToggleRequested = Signal(int)  # note_id
    noteRestoreRequested = Signal(int)  # note_id
    notePermanentDeleteRequested = Signal(int)  # note_id

    def __init__(
        self,
        model: NoteListModel,
        folders_repo: Optional[FoldersRepository] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._model = model
        self._folders_repo = folders_repo
        self._trash_mode = False

        self._search_box = QLineEdit(self)
        self._search_box.setPlaceholderText("Search notes…")
        self._search_box.textChanged.connect(self._on_search_text_changed)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._apply_search)

        self._list_view = QListView(self)
        self._list_view.setModel(model)
        self._list_view.selectionModel().currentChanged.connect(self._on_current_changed)
        self._list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list_view.customContextMenuRequested.connect(self._on_context_menu)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._search_box)
        layout.addWidget(self._list_view)

    def set_trash_mode(self, enabled: bool) -> None:
        self._trash_mode = enabled
        self._search_box.setEnabled(not enabled)

    def _on_search_text_changed(self, _text: str) -> None:
        self._search_timer.start()

    def _apply_search(self) -> None:
        self._model.set_search_filter(self._search_box.text())

    def _on_context_menu(self, pos) -> None:
        index = self._list_view.indexAt(pos)
        if not index.isValid():
            return
        note = self._model.note_at(index.row())
        if note is None:
            return

        if self._trash_mode:
            menu = QMenu(self)
            restore_action = menu.addAction("Restore")
            delete_action = menu.addAction("Delete Permanently")
            chosen = menu.exec(self._list_view.viewport().mapToGlobal(pos))
            if chosen == restore_action:
                self.noteRestoreRequested.emit(note.id)
            elif chosen == delete_action:
                reply = QMessageBox.question(
                    self,
                    "Delete Permanently",
                    f'Permanently delete "{note.title or "Untitled"}"? This cannot be undone.',
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.notePermanentDeleteRequested.emit(note.id)
            return

        menu = QMenu(self)
        pin_action = menu.addAction("Unpin" if note.is_pinned else "Pin")
        favorite_action = menu.addAction(
            "Remove from Favorites" if note.is_favorite else "Add to Favorites"
        )

        folder_actions = {}
        unfiled_action = None
        if self._folders_repo is not None:
            folders = self._folders_repo.list_all()
            by_id = {folder.id: folder for folder in folders}
            move_menu = menu.addMenu("Move to Folder")
            unfiled_action = move_menu.addAction("Unfiled")
            for folder in folders:
                action = move_menu.addAction("  " * self._depth(folder, by_id) + folder.name)
                folder_actions[action] = folder.id

        chosen = menu.exec(self._list_view.viewport().mapToGlobal(pos))
        if chosen is None:
            return
        if chosen == pin_action:
            self.notePinToggleRequested.emit(note.id)
        elif chosen == favorite_action:
            self.noteFavoriteToggleRequested.emit(note.id)
        elif chosen == unfiled_action:
            self.noteFolderChangeRequested.emit(note.id, None)
        elif chosen in folder_actions:
            self.noteFolderChangeRequested.emit(note.id, folder_actions[chosen])

    @staticmethod
    def _depth(folder: Folder, by_id: Dict[int, Folder]) -> int:
        depth = 0
        parent_id = folder.parent_id
        while parent_id is not None and parent_id in by_id:
            depth += 1
            parent_id = by_id[parent_id].parent_id
        return depth

    def _on_current_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if not current.isValid():
            self.noteSelected.emit(-1)
            return
        note = self._model.note_at(current.row())
        self.noteSelected.emit(note.id if note else -1)

    def select_note(self, note_id: int) -> None:
        for row in range(self._model.rowCount()):
            note = self._model.note_at(row)
            if note and note.id == note_id:
                self._list_view.setCurrentIndex(self._model.index(row, 0))
                return

    def refresh(self) -> None:
        self._model.refresh()
