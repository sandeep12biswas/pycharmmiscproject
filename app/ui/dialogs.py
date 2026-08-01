from pathlib import Path
from typing import Optional

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.export.markdown_export import export_markdown
from app.export.pdf_export import export_pdf
from app.repositories.notes_repo import NotesRepository
from app.repositories.reminders_repo import RemindersRepository

EXPORT_FILTER = "Markdown Files (*.md);;PDF Files (*.pdf)"
REMINDER_DATETIME_FORMAT = "yyyy-MM-dd HH:mm:ss"


def export_note_via_dialog(parent: QWidget, title: str, content_html: str) -> None:
    """Prompt for a destination file — format chosen via the file dialog's
    filter (Markdown vs. PDF) — and export the note's title/content there."""
    file_path, selected_filter = QFileDialog.getSaveFileName(
        parent, "Export Note", _default_filename(title), EXPORT_FILTER
    )
    if not file_path:
        return

    path = Path(file_path)
    if "pdf" in selected_filter.lower():
        if path.suffix.lower() != ".pdf":
            path = path.with_suffix(".pdf")
        export_pdf(title, content_html, path)
    else:
        if path.suffix.lower() != ".md":
            path = path.with_suffix(".md")
        export_markdown(title, content_html, path)


def _default_filename(title: str) -> str:
    safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in (title or "Untitled")).strip()
    return safe or "Untitled"


def _utc_string_to_local_display(remind_at_utc: str) -> str:
    dt = QDateTime.fromString(remind_at_utc, REMINDER_DATETIME_FORMAT)
    dt.setTimeSpec(Qt.TimeSpec.UTC)
    return dt.toLocalTime().toString("yyyy-MM-dd hh:mm ap")


class ReminderDialog(QDialog):
    """Date/time picker (local time, defaults to one hour from now) + optional
    message for attaching a reminder to a note (FR-21)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Reminder")

        self._datetime_edit = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600), self)
        self._datetime_edit.setCalendarPopup(True)
        self._datetime_edit.setMinimumDateTime(QDateTime.currentDateTime())

        self._message_edit = QLineEdit(self)
        self._message_edit.setPlaceholderText("Reminder message (optional)")

        form = QFormLayout()
        form.addRow("When:", self._datetime_edit)
        form.addRow("Message:", self._message_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def remind_at_utc(self) -> str:
        return self._datetime_edit.dateTime().toUTC().toString(REMINDER_DATETIME_FORMAT)

    def message(self) -> Optional[str]:
        text = self._message_edit.text().strip()
        return text or None


class RemindersListDialog(QDialog):
    """View/manage upcoming (not-yet-fired) reminders across all notes (FR-23)."""

    def __init__(self, reminders_repo: RemindersRepository, notes_repo: NotesRepository, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Upcoming Reminders")
        self.resize(420, 320)
        self._reminders_repo = reminders_repo
        self._notes_repo = notes_repo

        self._list = QListWidget(self)

        mark_done_button = QPushButton("Mark Done", self)
        mark_done_button.clicked.connect(self._mark_selected_done)
        delete_button = QPushButton("Delete", self)
        delete_button.clicked.connect(self._delete_selected)
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.accept)

        button_row = QHBoxLayout()
        button_row.addWidget(mark_done_button)
        button_row.addWidget(delete_button)
        button_row.addStretch(1)
        button_row.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self._list)
        layout.addLayout(button_row)

        self.refresh()

    def refresh(self) -> None:
        self._list.clear()
        for reminder in self._reminders_repo.list_upcoming():
            note = self._notes_repo.get(reminder.note_id)
            note_title = note.title if note else "(deleted note)"
            label = f"{_utc_string_to_local_display(reminder.remind_at)} — {note_title}"
            if reminder.message:
                label += f": {reminder.message}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, reminder.id)
            self._list.addItem(item)

    def _selected_reminder_id(self) -> Optional[int]:
        item = self._list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else None

    def _mark_selected_done(self) -> None:
        reminder_id = self._selected_reminder_id()
        if reminder_id is not None:
            self._reminders_repo.mark_done(reminder_id)
            self.refresh()

    def _delete_selected(self) -> None:
        reminder_id = self._selected_reminder_id()
        if reminder_id is not None:
            self._reminders_repo.delete(reminder_id)
            self.refresh()
