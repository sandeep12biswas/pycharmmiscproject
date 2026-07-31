from typing import Optional

from PySide6.QtCore import QObject, QTimer

from app.repositories.notes_repo import NotesRepository
from app.ui.editor import NoteEditorWidget
from app.ui.models_qt import NoteListModel
from app.ui.note_list import NoteListWidget

AUTOSAVE_DEBOUNCE_MS = 1500


class NoteController(QObject):
    def __init__(
        self,
        repo: NotesRepository,
        model: NoteListModel,
        note_list: NoteListWidget,
        editor: NoteEditorWidget,
        parent=None,
    ):
        super().__init__(parent)
        self._repo = repo
        self._model = model
        self._note_list = note_list
        self._editor = editor
        self._current_note_id: Optional[int] = None

        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(AUTOSAVE_DEBOUNCE_MS)
        self._autosave_timer.timeout.connect(self.flush_pending)

        self._note_list.noteSelected.connect(self._on_note_selected)
        self._editor.contentChanged.connect(self._on_content_changed)

        self._model.refresh()
        self._editor.set_enabled(False)

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

    def _on_note_selected(self, note_id: int) -> None:
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
        self._editor.load(note.title, note.content_html)
        self._editor.set_enabled(True)

    def _on_content_changed(self) -> None:
        self._autosave_timer.start()
