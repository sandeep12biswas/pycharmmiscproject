import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import QApplication, QDialog, QMainWindow, QSplitter, QSystemTrayIcon, QToolBar

from app.controllers.note_controller import NoteController
from app.reminders.scheduler import ReminderScheduler
from app.repositories.folders_repo import FoldersRepository
from app.repositories.notes_repo import NotesRepository
from app.repositories.reminders_repo import RemindersRepository
from app.repositories.tags_repo import TagsRepository
from app.ui.dialogs import ReminderDialog, RemindersListDialog, export_note_via_dialog
from app.ui.editor import NoteEditorWidget
from app.ui.models_qt import NoteListModel
from app.ui.note_list import NoteListWidget
from app.ui.sidebar import SidebarWidget
from app.ui.theme import Theme, apply_theme, load_theme, save_theme
from app.ui.tray import TrayIcon

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(
        self,
        repo: NotesRepository,
        folders_repo: FoldersRepository,
        tags_repo: TagsRepository,
        reminders_repo: RemindersRepository,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Notes")
        self.resize(1100, 720)

        self._repo = repo
        self._reminders_repo = reminders_repo
        self._model = NoteListModel(repo)
        note_list = NoteListWidget(self._model, folders_repo)
        editor = NoteEditorWidget()

        sidebar = SidebarWidget(folders_repo, tags_repo)
        sidebar.folderSelected.connect(self._model.set_folder_filter)
        sidebar.tagSelected.connect(self._model.set_tag_filter)
        sidebar.favoritesSelected.connect(self._model.set_favorites_filter)
        sidebar.trashSelected.connect(self._on_trash_selected)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(sidebar)
        splitter.addWidget(note_list)
        splitter.addWidget(editor)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 4)
        self.setCentralWidget(splitter)

        self._controller = NoteController(repo, self._model, note_list, editor, tags_repo, parent=self)
        self._controller.tagsChanged.connect(sidebar.refresh_tags)
        sidebar.emptyTrashRequested.connect(self._controller.empty_trash)

        toolbar = QToolBar("Main", self)
        self.addToolBar(toolbar)

        self._new_action = QAction("New Note", self)
        self._new_action.triggered.connect(self._controller.new_note)
        toolbar.addAction(self._new_action)

        self._delete_action = QAction("Delete Note", self)
        self._delete_action.triggered.connect(self._controller.delete_current_note)
        toolbar.addAction(self._delete_action)

        self._pin_action = QAction("Pin/Unpin Note", self)
        self._pin_action.triggered.connect(self._controller.toggle_pin_current)
        toolbar.addAction(self._pin_action)

        self._favorite_action = QAction("Favorite/Unfavorite Note", self)
        self._favorite_action.triggered.connect(self._controller.toggle_favorite_current)
        toolbar.addAction(self._favorite_action)

        self._export_action = QAction("Export Note…", self)
        self._export_action.triggered.connect(self._on_export_note)
        toolbar.addAction(self._export_action)

        self._set_reminder_action = QAction("Set Reminder…", self)
        self._set_reminder_action.triggered.connect(self._on_set_reminder)
        toolbar.addAction(self._set_reminder_action)

        self._normal_mode_actions = (  # disabled while browsing Trash -- none of these apply there
            self._new_action,
            self._delete_action,
            self._pin_action,
            self._favorite_action,
            self._export_action,
            self._set_reminder_action,
        )

        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(self._export_action)

        view_menu = self.menuBar().addMenu("View")
        self._dark_theme_action = QAction("Dark Theme", self)
        self._dark_theme_action.setCheckable(True)
        self._dark_theme_action.setChecked(load_theme() == Theme.DARK)
        self._dark_theme_action.toggled.connect(self._on_dark_theme_toggled)
        view_menu.addAction(self._dark_theme_action)

        reminders_menu = self.menuBar().addMenu("Reminders")
        reminders_menu.addAction(self._set_reminder_action)
        view_reminders_action = QAction("View Upcoming Reminders…", self)
        view_reminders_action.triggered.connect(self._on_view_reminders)
        reminders_menu.addAction(view_reminders_action)

        # Notifications only fire while this process is running -- see the
        # caveat documented on ReminderScheduler (no OS-level scheduling).
        self._tray = TrayIcon(self, parent=self)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray.show()

        self._scheduler = ReminderScheduler(reminders_repo, parent=self)
        self._scheduler.reminderDue.connect(self._on_reminder_due)
        self._scheduler.start()

    def _on_trash_selected(self, active: bool) -> None:
        self._controller.set_trash_mode(active)
        for action in self._normal_mode_actions:
            action.setEnabled(not active)

    def _on_dark_theme_toggled(self, checked: bool) -> None:
        theme = Theme.DARK if checked else Theme.LIGHT
        logger.debug("Theme switched to %s", theme)
        save_theme(theme)
        apply_theme(QApplication.instance(), theme)

    def _on_export_note(self) -> None:
        note = self._controller.current_note()
        if note is None:
            return
        export_note_via_dialog(self, note.title, note.content_html)

    def _on_set_reminder(self) -> None:
        note = self._controller.current_note()
        if note is None:
            return
        dialog = ReminderDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._reminders_repo.create(note.id, dialog.remind_at_utc(), dialog.message())

    def _on_view_reminders(self) -> None:
        RemindersListDialog(self._reminders_repo, self._repo, self).exec()

    def _on_reminder_due(self, note_id: int, message: str) -> None:
        note = self._repo.get(note_id)
        title = note.title if note else "Reminder"
        self._tray.notify_reminder(title, message)

    def closeEvent(self, event: QCloseEvent) -> None:
        logger.info("Main window closing; flushing pending autosave")
        self._controller.flush_pending()
        super().closeEvent(event)
