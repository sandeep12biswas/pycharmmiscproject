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
        self._tag_id: Optional[int] = None
        self._search_text: str = ""
        self._favorites_only: bool = False
        self._trash_mode: bool = False

    def set_folder_filter(self, folder_id: Optional[int]) -> None:
        self._folder_id = folder_id
        self.refresh()

    def set_tag_filter(self, tag_id: Optional[int]) -> None:
        self._tag_id = tag_id
        self.refresh()

    def set_search_filter(self, search_text: str) -> None:
        self._search_text = search_text
        self.refresh()

    def set_favorites_filter(self, favorites_only: bool) -> None:
        self._favorites_only = favorites_only
        self.refresh()

    def set_trash_mode(self, enabled: bool) -> None:
        """Trash is a separate listing (NotesRepository.list_trashed()), not
        another AND-able filter -- folder/tag/search/favorites are ignored
        while active, matching the other three filters' non-effect on trash
        (trashed notes are excluded from list_all() regardless)."""
        self._trash_mode = enabled
        self.refresh()

    def refresh(self) -> None:
        self.beginResetModel()
        if self._trash_mode:
            self._notes = self._repo.list_trashed()
        else:
            self._notes = self._repo.list_all(
                folder_id=self._folder_id,
                tag_id=self._tag_id,
                search_text=self._search_text,
                favorites_only=self._favorites_only,
            )
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
            prefix = ("📌 " if note.is_pinned else "") + ("★ " if note.is_favorite else "")
            return prefix + (note.title or "Untitled")
        if role == Qt.ItemDataRole.UserRole:
            return note.id
        return None

    def note_at(self, row: int) -> Optional[Note]:
        if 0 <= row < len(self._notes):
            return self._notes[row]
        return None
