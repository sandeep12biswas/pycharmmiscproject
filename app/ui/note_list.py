from PySide6.QtCore import QModelIndex, Signal
from PySide6.QtWidgets import QListView, QVBoxLayout, QWidget

from app.ui.models_qt import NoteListModel


class NoteListWidget(QWidget):
    noteSelected = Signal(int)  # note_id, or -1 when nothing is selected

    def __init__(self, model: NoteListModel, parent=None):
        super().__init__(parent)
        self._model = model

        self._list_view = QListView(self)
        self._list_view.setModel(model)
        self._list_view.selectionModel().currentChanged.connect(self._on_current_changed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list_view)

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
