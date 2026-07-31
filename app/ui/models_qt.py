from typing import List, Optional

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from app.models.note import Note
from app.repositories.notes_repo import NotesRepository


class NoteListModel(QAbstractListModel):
    def __init__(self, repo: NotesRepository, parent=None):
        super().__init__(parent)
        self._repo = repo
        self._notes: List[Note] = []
        self._folder_id: Optional[int] = None

    def set_folder_filter(self, folder_id: Optional[int]) -> None:
        self._folder_id = folder_id
        self.refresh()

    def refresh(self) -> None:
        self.beginResetModel()
        self._notes = self._repo.list_all(folder_id=self._folder_id)
        self.endResetModel()

    def refresh_note(self, note_id: int) -> None:
        """Re-fetch a single note in place, without resetting the whole list
        (a full reset would clear the view's current selection/scroll position)."""
        for row, note in enumerate(self._notes):
            if note.id == note_id:
                updated = self._repo.get(note_id)
                if updated is None:
                    return
                self._notes[row] = updated
                index = self.index(row, 0)
                self.dataChanged.emit(index, index)
                return

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._notes)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        note = self._notes[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return note.title or "Untitled"
        if role == Qt.ItemDataRole.UserRole:
            return note.id
        return None

    def note_at(self, row: int) -> Optional[Note]:
        if 0 <= row < len(self._notes):
            return self._notes[row]
        return None
