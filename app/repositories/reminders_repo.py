import logging
import sqlite3
from typing import List, Optional

from app.models.reminder import Reminder

logger = logging.getLogger(__name__)


class RemindersRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(self, note_id: int, remind_at: str, message: Optional[str] = None) -> Reminder:
        cursor = self._conn.execute(
            "INSERT INTO reminders (note_id, remind_at, message) VALUES (?, ?, ?)",
            (note_id, remind_at, message),
        )
        self._conn.commit()
        logger.info("Created reminder id=%s for note id=%s at %s", cursor.lastrowid, note_id, remind_at)
        return self.get(cursor.lastrowid)

    def get(self, reminder_id: int) -> Optional[Reminder]:
        row = self._conn.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
        return Reminder.from_row(row) if row else None

    def list_for_note(self, note_id: int) -> List[Reminder]:
        rows = self._conn.execute(
            "SELECT * FROM reminders WHERE note_id = ? ORDER BY remind_at", (note_id,)
        ).fetchall()
        return [Reminder.from_row(row) for row in rows]

    def list_upcoming(self) -> List[Reminder]:
        rows = self._conn.execute(
            "SELECT * FROM reminders WHERE is_done = 0 ORDER BY remind_at"
        ).fetchall()
        return [Reminder.from_row(row) for row in rows]

    def list_due(self) -> List[Reminder]:
        """Reminders whose remind_at has passed, not yet marked done. Uses
        SQLite's own datetime('now') (UTC) as the clock, so this is robust to
        Python/DB clock skew as long as remind_at was stored in the same UTC
        format."""
        rows = self._conn.execute(
            "SELECT * FROM reminders WHERE is_done = 0 AND remind_at <= datetime('now') "
            "ORDER BY remind_at"
        ).fetchall()
        return [Reminder.from_row(row) for row in rows]

    def mark_done(self, reminder_id: int) -> None:
        self._conn.execute("UPDATE reminders SET is_done = 1 WHERE id = ?", (reminder_id,))
        self._conn.commit()
        logger.debug("Marked reminder id=%s done", reminder_id)

    def delete(self, reminder_id: int) -> None:
        self._conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        self._conn.commit()
        logger.debug("Deleted reminder id=%s", reminder_id)
