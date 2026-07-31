import sqlite3
from typing import List, Optional

from app.models.note import Note


class NotesRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(
        self,
        title: str = "",
        content_html: str = "",
        content_plain: str = "",
        folder_id: Optional[int] = None,
    ) -> Note:
        cursor = self._conn.execute(
            """
            INSERT INTO notes (title, content_html, content_plain, folder_id)
            VALUES (?, ?, ?, ?)
            """,
            (title, content_html, content_plain, folder_id),
        )
        self._conn.commit()
        return self.get(cursor.lastrowid)

    def get(self, note_id: int) -> Optional[Note]:
        row = self._conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        return Note.from_row(row) if row else None

    def list_all(self, folder_id: Optional[int] = None) -> List[Note]:
        query = "SELECT * FROM notes WHERE is_trashed = 0"
        params: tuple = ()
        if folder_id is not None:
            query += " AND folder_id = ?"
            params = (folder_id,)
        query += " ORDER BY is_pinned DESC, updated_at DESC"
        rows = self._conn.execute(query, params).fetchall()
        return [Note.from_row(row) for row in rows]

    def update_content(self, note_id: int, title: str, content_html: str, content_plain: str) -> None:
        self._conn.execute(
            """
            UPDATE notes
            SET title = ?, content_html = ?, content_plain = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (title, content_html, content_plain, note_id),
        )
        self._conn.commit()

    def move_to_folder(self, note_id: int, folder_id: Optional[int]) -> None:
        self._conn.execute(
            "UPDATE notes SET folder_id = ?, updated_at = datetime('now') WHERE id = ?",
            (folder_id, note_id),
        )
        self._conn.commit()

    def trash(self, note_id: int) -> None:
        self._conn.execute(
            "UPDATE notes SET is_trashed = 1, updated_at = datetime('now') WHERE id = ?",
            (note_id,),
        )
        self._conn.commit()

    def restore(self, note_id: int) -> None:
        self._conn.execute(
            "UPDATE notes SET is_trashed = 0, updated_at = datetime('now') WHERE id = ?",
            (note_id,),
        )
        self._conn.commit()

    def list_trashed(self) -> List[Note]:
        rows = self._conn.execute(
            "SELECT * FROM notes WHERE is_trashed = 1 ORDER BY updated_at DESC"
        ).fetchall()
        return [Note.from_row(row) for row in rows]

    def delete_permanently(self, note_id: int) -> None:
        self._conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self._conn.commit()
