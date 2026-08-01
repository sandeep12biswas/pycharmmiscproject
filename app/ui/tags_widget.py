from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCompleter,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.tag import Tag
from app.repositories.tags_repo import TagsRepository

TAG_ID_ROLE = Qt.ItemDataRole.UserRole + 1


class _TagChip(QWidget):
    removeRequested = Signal(int)  # tag_id

    def __init__(self, tag: Tag, parent=None):
        super().__init__(parent)
        self._tag_id = tag.id
        self.setObjectName("tagChip")
        self.setStyleSheet("#tagChip { background: palette(midlight); border-radius: 8px; }")

        label = QLabel(tag.name, self)
        remove_button = QPushButton("×", self)
        remove_button.setFixedSize(16, 16)
        remove_button.setFlat(True)
        remove_button.clicked.connect(lambda: self.removeRequested.emit(self._tag_id))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 4, 2)
        layout.setSpacing(4)
        layout.addWidget(label)
        layout.addWidget(remove_button)


class TagChipEditor(QWidget):
    """Shows a note's assigned tags as removable chips, plus an input for adding
    a tag by name. Name resolution (reuse an existing tag vs. create a new one)
    is left to the caller via TagsRepository.get_or_create — this widget only
    emits the requested name/id, it never talks to the database."""

    tagAddRequested = Signal(str)  # tag name typed by the user
    tagRemoveRequested = Signal(int)  # tag_id

    def __init__(self, parent=None):
        super().__init__(parent)

        self._chip_container = QWidget(self)
        self._chip_layout = QHBoxLayout(self._chip_container)
        self._chip_layout.setContentsMargins(0, 0, 0, 0)
        self._chip_layout.setSpacing(4)

        self._input = QLineEdit(self)
        self._input.setPlaceholderText("Add tag…")
        self._input.setMaximumWidth(140)
        self._input.returnPressed.connect(self._on_return_pressed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._chip_container)
        layout.addWidget(self._input)
        layout.addStretch(1)

    def set_available_tag_names(self, names: List[str]) -> None:
        completer = QCompleter(names, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._input.setCompleter(completer)

    def set_tags(self, tags: List[Tag]) -> None:
        while self._chip_layout.count():
            item = self._chip_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for tag in tags:
            chip = _TagChip(tag, self._chip_container)
            chip.removeRequested.connect(self.tagRemoveRequested)
            self._chip_layout.addWidget(chip)

    def _on_return_pressed(self) -> None:
        name = self._input.text().strip()
        if not name:
            return
        self._input.clear()
        self.tagAddRequested.emit(name)

    def set_enabled(self, enabled: bool) -> None:
        self.setEnabled(enabled)


class TagFilterWidget(QWidget):
    """Sidebar list of all tags (plus "All Tags") used to filter the note list."""

    tagSelected = Signal(object)  # Optional[int]; None means no tag filter

    def __init__(self, repo: TagsRepository, parent=None):
        super().__init__(parent)
        self._repo = repo
        self._items: Dict[Optional[int], QStandardItem] = {}

        self._model = QStandardItemModel(self)
        self._list = QListView(self)
        self._list.setModel(self._model)
        self._list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list)

        self.refresh()
        self._list.selectionModel().currentChanged.connect(self._on_current_changed)

    def refresh(self) -> None:
        previous = self._current_tag_id()
        self._model.clear()
        self._items = {}

        all_item = QStandardItem("All Tags")
        all_item.setEditable(False)
        all_item.setData(None, TAG_ID_ROLE)
        self._model.appendRow(all_item)
        self._items[None] = all_item

        for tag in self._repo.list_all():
            item = QStandardItem(tag.name)
            item.setEditable(False)
            item.setData(tag.id, TAG_ID_ROLE)
            self._model.appendRow(item)
            self._items[tag.id] = item

        target = previous if previous in self._items else None
        self._list.setCurrentIndex(self._items[target].index())

    def _current_tag_id(self) -> Optional[int]:
        index = self._list.currentIndex()
        if not index.isValid():
            return None
        return index.data(TAG_ID_ROLE)

    def _on_current_changed(self, current, _previous) -> None:
        tag_id = current.data(TAG_ID_ROLE) if current.isValid() else None
        self.tagSelected.emit(tag_id)
