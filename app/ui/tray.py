from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon, QWidget


class TrayIcon(QSystemTrayIcon):
    """System tray icon with Show/Hide/Quit actions and reminder notifications
    (FR-22). Notifications only fire while this process is running -- see the
    caveat documented on ReminderScheduler."""

    def __init__(self, window: QWidget, parent=None):
        icon = window.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        super().__init__(icon, parent)
        self._window = window
        self.setToolTip("Notes")

        menu = QMenu()
        show_action = menu.addAction("Show")
        show_action.triggered.connect(self._show_window)
        hide_action = menu.addAction("Hide")
        hide_action.triggered.connect(window.hide)
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self._quit)
        self.setContextMenu(menu)

        self.activated.connect(self._on_activated)

    def _show_window(self) -> None:
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    def _quit(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_window()

    def notify_reminder(self, note_title: str, message: str) -> None:
        body = message or "Reminder due"
        self.showMessage(note_title or "Reminder", body, QSystemTrayIcon.MessageIcon.Information, 8000)
