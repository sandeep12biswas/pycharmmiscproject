import logging

from PySide6.QtCore import QObject, QTimer, Signal

from app.repositories.reminders_repo import RemindersRepository

logger = logging.getLogger(__name__)

POLL_INTERVAL_MS = 45_000  # 45s -- within the 30-60s range called for in tasklist.md


class ReminderScheduler(QObject):
    """Polls for due reminders and emits one signal per due reminder, marking
    each done immediately so it fires exactly once. Caveat: this only fires
    while the app process is running -- there is no OS-level scheduling, so a
    reminder due while the app is closed will simply fire (once) the next
    time the app is opened and this scheduler's first check_now() runs, not
    at the original due time."""

    reminderDue = Signal(int, str)  # note_id, message

    def __init__(self, repo: RemindersRepository, parent=None):
        super().__init__(parent)
        self._repo = repo
        self._timer = QTimer(self)
        self._timer.setInterval(POLL_INTERVAL_MS)
        self._timer.timeout.connect(self.check_now)

    def start(self) -> None:
        logger.debug("Reminder scheduler started (poll interval=%sms)", POLL_INTERVAL_MS)
        self._timer.start()
        self.check_now()  # catch anything already due at startup

    def stop(self) -> None:
        self._timer.stop()
        logger.debug("Reminder scheduler stopped")

    def check_now(self) -> None:
        for reminder in self._repo.list_due():
            logger.info("Reminder id=%s due for note id=%s", reminder.id, reminder.note_id)
            self._repo.mark_done(reminder.id)
            self.reminderDue.emit(reminder.note_id, reminder.message or "")
