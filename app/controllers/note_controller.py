from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal

from app.models.note import Note
from app.repositories.notes_repo import NotesRepository
from app.repositories.tags_repo import TagsRepository
from app.ui.editor import NoteEditorWidget
from app.ui.models_qt import NoteListModel
from app.ui.note_list import NoteListWidget

AUTOSAVE_DEBOUNCE_MS = 1500


class NoteController(QObject):
    tagsChanged = Signal()  # emitted after a tag is created/assigned/removed, for the sidebar to refresh

    def __init__(
        self,
        repo: NotesRepository,
        model: NoteListModel,
        note_list: NoteListWidget,
        editor: NoteEditorWidget,
        tags_repo: TagsRepository,
        parent=None,
    ):
        super().__init__(parent)
        self._repo = repo
        self._model = model
        self._note_list = note_list
        self._editor = editor
        self._tags_repo = tags_repo
        self._current_note_id: Optional[int] = None
        self._trash_mode = False

        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(AUTOSAVE_DEBOUNCE_MS)
        self._autosave_timer.timeout.connect(self.flush_pending)

        self._note_list.noteSelected.connect(self._on_note_selected)
        self._note_list.noteFolderChangeRequested.connect(self._on_note_folder_change_requested)
        self._note_list.notePinToggleRequested.connect(self.toggle_pin)
        self._note_list.noteFavoriteToggleRequested.connect(self.toggle_favorite)
        self._note_list.noteRestoreRequested.connect(self.restore_note)
        self._note_list.notePermanentDeleteRequested.connect(self.delete_note_permanently)
        self._editor.tagAddRequested.connect(self._on_tag_add_requested)
        self._editor.tagRemoveRequested.connect(self._on_tag_remove_requested)
        self._editor.contentChanged.connect(self._on_content_changed)

        self._model.refresh()
        self._editor.set_enabled(False)
        self._refresh_available_tag_names()

    def new_note(self) -> None:
        self.flush_pending()
        note = self._repo.create(title="Untitled")
        self._model.refresh()
        self._note_list.select_note(note.id)

    def delete_current_note(self) -> None:
        if self._current_note_id is None:
            return
        self._autosave_timer.stop()
        self._repo.trash(self._current_note_id)
        self._current_note_id = None
        self._model.refresh()
        self._editor.clear()
        self._editor.set_enabled(False)

    def flush_pending(self) -> None:
        """Write any in-progress edits to the repository immediately, bypassing
        the debounce timer. Called on note switch, on application close, and
        when the debounce timer itself fires, so nothing is lost (NFR-2)."""
        self._autosave_timer.stop()
        if self._current_note_id is None:
            return
        title = self._editor.title()
        html = self._editor.html()
        plain = self._editor.plain_text()
        self._repo.update_content(self._current_note_id, title, html, plain)
        self._model.refresh_note(self._current_note_id)

    def _on_note_folder_change_requested(self, note_id: int, folder_id: Optional[int]) -> None:
        self._repo.move_to_folder(note_id, folder_id)
        self._model.refresh()

    def set_trash_mode(self, enabled: bool) -> None:
        """Trash is read-only, not the live editing surface -- switching into
        it flushes/clears whatever was open rather than letting a trashed
        note load into the normal autosave-editing flow."""
        self.flush_pending()
        self._trash_mode = enabled
        self._current_note_id = None
        self._editor.clear()
        self._editor.set_enabled(False)
        self._note_list.set_trash_mode(enabled)
        self._model.set_trash_mode(enabled)

    def restore_note(self, note_id: int) -> None:
        self._repo.restore(note_id)
        self._model.refresh()

    def delete_note_permanently(self, note_id: int) -> None:
        self._repo.delete_permanently(note_id)
        self._model.refresh()

    def empty_trash(self) -> None:
        for note in self._repo.list_trashed():
            self._repo.delete_permanently(note.id)
        self._model.refresh()

    def current_note(self) -> Optional[Note]:
        """The currently open note, with any pending edits flushed first so
        callers (e.g. export) always see up-to-date content."""
        self.flush_pending()
        if self._current_note_id is None:
            return None
        return self._repo.get(self._current_note_id)

    def toggle_pin(self, note_id: int) -> None:
        self._repo.toggle_pin(note_id)
        self._model.refresh()

    def toggle_favorite(self, note_id: int) -> None:
        self._repo.toggle_favorite(note_id)
        self._model.refresh()

    def toggle_pin_current(self) -> None:
        if self._current_note_id is not None:
            self.toggle_pin(self._current_note_id)

    def toggle_favorite_current(self) -> None:
        if self._current_note_id is not None:
            self.toggle_favorite(self._current_note_id)

    def _on_tag_add_requested(self, name: str) -> None:
        if self._current_note_id is None:
            return
        tag = self._tags_repo.get_or_create(name)
        self._tags_repo.assign(self._current_note_id, tag.id)
        self._editor.set_tags(self._tags_repo.list_for_note(self._current_note_id))
        self._model.refresh()
        self._refresh_available_tag_names()
        self.tagsChanged.emit()

    def _on_tag_remove_requested(self, tag_id: int) -> None:
        if self._current_note_id is None:
            return
        self._tags_repo.unassign(self._current_note_id, tag_id)
        self._editor.set_tags(self._tags_repo.list_for_note(self._current_note_id))
        self._model.refresh()
        self.tagsChanged.emit()

    def _refresh_available_tag_names(self) -> None:
        self._editor.set_available_tag_names([tag.name for tag in self._tags_repo.list_all()])

    def _on_note_selected(self, note_id: int) -> None:
        if self._trash_mode:
            return  # trashed notes are not editable; the context menu (Restore/Delete) is the only action
        self.flush_pending()
        if note_id == -1:
            self._current_note_id = None
            self._editor.clear()
            self._editor.set_enabled(False)
            return
        note = self._repo.get(note_id)
        if note is None:
            return
        self._current_note_id = note.id
        self._editor.load(note.title, note.content_html, self._tags_repo.list_for_note(note.id))
        self._editor.set_enabled(True)

    def _on_content_changed(self) -> None:
        self._autosave_timer.start()
