import logging
import sqlite3
from typing import List, Optional

from app.models.note import Note
from app.search.fts import search_note_ids

logger = logging.getLogger(__name__)


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
        logger.debug("Created note id=%s", cursor.lastrowid)
        return self.get(cursor.lastrowid)

    def get(self, note_id: int) -> Optional[Note]:
        row = self._conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        return Note.from_row(row) if row else None

    def list_all(
        self,
        folder_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        search_text: Optional[str] = None,
        favorites_only: bool = False,
    ) -> List[Note]:
        ranked_ids: Optional[List[int]] = None
        if search_text and search_text.strip():
            ranked_ids = search_note_ids(self._conn, search_text)
            if not ranked_ids:
                return []

        query = "SELECT notes.* FROM notes"
        conditions = ["notes.is_trashed = 0"]
        params: List = []
        if tag_id is not None:
            query += " JOIN note_tags ON note_tags.note_id = notes.id"
            conditions.append("note_tags.tag_id = ?")
            params.append(tag_id)
        if folder_id is not None:
            conditions.append("notes.folder_id = ?")
            params.append(folder_id)
        if favorites_only:
            conditions.append("notes.is_favorite = 1")
        if ranked_ids is not None:
            conditions.append(f"notes.id IN ({','.join('?' * len(ranked_ids))})")
            params.extend(ranked_ids)
        query += " WHERE " + " AND ".join(conditions)
        if ranked_ids is None:
            query += " ORDER BY notes.is_pinned DESC, notes.updated_at DESC"

        rows = self._conn.execute(query, params).fetchall()
        notes = [Note.from_row(row) for row in rows]
        if ranked_ids is not None:
            rank = {note_id: i for i, note_id in enumerate(ranked_ids)}
            notes.sort(key=lambda note: rank[note.id])
        return notes

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
        logger.debug("Autosaved note id=%s (title=%r)", note_id, title)

    def move_to_folder(self, note_id: int, folder_id: Optional[int]) -> None:
        self._conn.execute(
            "UPDATE notes SET folder_id = ?, updated_at = datetime('now') WHERE id = ?",
            (folder_id, note_id),
        )
        self._conn.commit()
        logger.debug("Moved note id=%s to folder_id=%s", note_id, folder_id)

    def toggle_pin(self, note_id: int) -> None:
        self._conn.execute(
            "UPDATE notes SET is_pinned = NOT is_pinned, updated_at = datetime('now') WHERE id = ?",
            (note_id,),
        )
        self._conn.commit()
        logger.debug("Toggled pin on note id=%s", note_id)

    def toggle_favorite(self, note_id: int) -> None:
        self._conn.execute(
            "UPDATE notes SET is_favorite = NOT is_favorite, updated_at = datetime('now') WHERE id = ?",
            (note_id,),
        )
        self._conn.commit()
        logger.debug("Toggled favorite on note id=%s", note_id)

    def trash(self, note_id: int) -> None:
        self._conn.execute(
            "UPDATE notes SET is_trashed = 1, updated_at = datetime('now') WHERE id = ?",
            (note_id,),
        )
        self._conn.commit()
        logger.info("Trashed note id=%s", note_id)

    def restore(self, note_id: int) -> None:
        self._conn.execute(
            "UPDATE notes SET is_trashed = 0, updated_at = datetime('now') WHERE id = ?",
            (note_id,),
        )
        self._conn.commit()
        logger.info("Restored note id=%s from trash", note_id)

    def list_trashed(self) -> List[Note]:
        rows = self._conn.execute(
            "SELECT * FROM notes WHERE is_trashed = 1 ORDER BY updated_at DESC"
        ).fetchall()
        return [Note.from_row(row) for row in rows]

    def delete_permanently(self, note_id: int) -> None:
        self._conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self._conn.commit()
        logger.info("Permanently deleted note id=%s", note_id)
