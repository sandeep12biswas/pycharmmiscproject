import sqlite3
from dataclasses import dataclass
from typing import Optional


@dataclass
class Reminder:
    id: Optional[int]
    note_id: int
    remind_at: str  # UTC "yyyy-MM-dd HH:mm:ss", matching SQLite's datetime('now') format
    message: Optional[str]
    is_done: bool
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Reminder":
        return cls(
            id=row["id"],
            note_id=row["note_id"],
            remind_at=row["remind_at"],
            message=row["message"],
            is_done=bool(row["is_done"]),
            created_at=row["created_at"],
        )
