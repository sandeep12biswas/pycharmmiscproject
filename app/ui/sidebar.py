from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from app.repositories.folders_repo import FoldersRepository
from app.repositories.tags_repo import TagsRepository
from app.ui.tags_widget import TagFilterWidget

FOLDER_ID_ROLE = Qt.ItemDataRole.UserRole + 1
FAVORITES_ROLE = Qt.ItemDataRole.UserRole + 2
TRASH_ROLE = Qt.ItemDataRole.UserRole + 3
FAVORITES_KEY = "__favorites__"  # self._items key for the Favorites smart view (distinct from folder_id=None)
TRASH_KEY = "__trash__"  # self._items key for the Trash smart view


class SidebarWidget(QWidget):
    folderSelected = Signal(object)  # Optional[int]; None means "All Notes"
    tagSelected = Signal(object)  # Optional[int]; None means no tag filter
    favoritesSelected = Signal(bool)  # True when the "Favorites" smart view is selected
    trashSelected = Signal(bool)  # True when the "Trash" smart view is selected
    emptyTrashRequested = Signal()

    def __init__(self, repo: FoldersRepository, tags_repo: TagsRepository, parent=None):
        super().__init__(parent)
        self._repo = repo
        self._items: Dict[Optional[int], QStandardItem] = {}

        self._model = QStandardItemModel(self)
        self._tree = QTreeView(self)
        self._tree.setModel(self._model)
        self._tree.setHeaderHidden(True)
        self._tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)

        self._tag_filter = TagFilterWidget(tags_repo, self)
        self._tag_filter.tagSelected.connect(self.tagSelected)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Folders", self))
        layout.addWidget(self._tree, stretch=2)
        layout.addWidget(QLabel("Tags", self))
        layout.addWidget(self._tag_filter, stretch=1)

        self.refresh()
        self._tree.selectionModel().currentChanged.connect(self._on_current_changed)

    def refresh_tags(self) -> None:
        self._tag_filter.refresh()

    def refresh(self) -> None:
        previous_selection = self._current_selection_key()
        self._model.clear()
        self._items = {}
        root = self._model.invisibleRootItem()

        all_item = QStandardItem("All Notes")
        all_item.setEditable(False)
        all_item.setData(None, FOLDER_ID_ROLE)
        root.appendRow(all_item)
        self._items[None] = all_item

        favorites_item = QStandardItem("★ Favorites")
        favorites_item.setEditable(False)
        favorites_item.setData(True, FAVORITES_ROLE)
        root.appendRow(favorites_item)
        self._items[FAVORITES_KEY] = favorites_item

        trash_item = QStandardItem("🗑 Trash")
        trash_item.setEditable(False)
        trash_item.setData(True, TRASH_ROLE)
        root.appendRow(trash_item)
        self._items[TRASH_KEY] = trash_item

        folders = self._repo.list_all()
        for folder in folders:
            item = QStandardItem(folder.name)
            item.setEditable(False)
            item.setData(folder.id, FOLDER_ID_ROLE)
            self._items[folder.id] = item

        for folder in folders:
            parent_item = root if folder.parent_id is None else self._items.get(folder.parent_id, root)
            parent_item.appendRow(self._items[folder.id])

        self._tree.expandAll()
        target = previous_selection if previous_selection in self._items else None
        self._tree.setCurrentIndex(self._items[target].index())

    def _current_selection_key(self):
        index = self._tree.currentIndex()
        if not index.isValid():
            return None
        if index.data(FAVORITES_ROLE):
            return FAVORITES_KEY
        if index.data(TRASH_ROLE):
            return TRASH_KEY
        return index.data(FOLDER_ID_ROLE)

    def _on_current_changed(self, current, _previous) -> None:
        if current.isValid() and current.data(FAVORITES_ROLE):
            self.favoritesSelected.emit(True)
            self.trashSelected.emit(False)
            self.folderSelected.emit(None)
            return
        if current.isValid() and current.data(TRASH_ROLE):
            self.trashSelected.emit(True)
            self.favoritesSelected.emit(False)
            self.folderSelected.emit(None)
            return
        folder_id = current.data(FOLDER_ID_ROLE) if current.isValid() else None
        self.favoritesSelected.emit(False)
        self.trashSelected.emit(False)
        self.folderSelected.emit(folder_id)

    def _on_context_menu(self, pos) -> None:
        index = self._tree.indexAt(pos)
        if index.isValid() and index.data(FAVORITES_ROLE):
            return  # no folder actions on the "Favorites" smart view
        if index.isValid() and index.data(TRASH_ROLE):
            menu = QMenu(self)
            empty_action = menu.addAction("Empty Trash")
            chosen = menu.exec(self._tree.viewport().mapToGlobal(pos))
            if chosen == empty_action:
                self._confirm_empty_trash()
            return
        folder_id = index.data(FOLDER_ID_ROLE) if index.isValid() else None

        menu = QMenu(self)
        new_action = menu.addAction("New Subfolder" if folder_id is not None else "New Folder")
        rename_action = menu.addAction("Rename") if folder_id is not None else None
        delete_action = menu.addAction("Delete") if folder_id is not None else None

        chosen = menu.exec(self._tree.viewport().mapToGlobal(pos))
        if chosen is None:
            return
        if chosen == new_action:
            self._create_folder(parent_id=folder_id)
        elif chosen == rename_action:
            self._rename_folder(folder_id)
        elif chosen == delete_action:
            self._delete_folder(folder_id)

    def _create_folder(self, parent_id: Optional[int]) -> None:
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        name = name.strip()
        if not ok or not name:
            return
        self._repo.create(name, parent_id=parent_id)
        self.refresh()

    def _rename_folder(self, folder_id: int) -> None:
        folder = self._repo.get(folder_id)
        if folder is None:
            return
        name, ok = QInputDialog.getText(self, "Rename Folder", "Folder name:", text=folder.name)
        name = name.strip()
        if not ok or not name:
            return
        self._repo.rename(folder_id, name)
        self.refresh()

    def _delete_folder(self, folder_id: int) -> None:
        reply = QMessageBox.question(
            self,
            "Delete Folder",
            "Delete this folder? Notes inside will become unfiled, and any "
            "subfolders will be deleted too.",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._repo.delete(folder_id)
        self.refresh()

    def _confirm_empty_trash(self) -> None:
        reply = QMessageBox.question(
            self,
            "Empty Trash",
            "Permanently delete all notes in Trash? This cannot be undone.",
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.emptyTrashRequested.emit()
