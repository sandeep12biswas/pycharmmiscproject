import sqlite3
from typing import List, Optional

from app.models.tag import Tag


class TagsRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(self, name: str, color: Optional[str] = None) -> Tag:
        cursor = self._conn.execute("INSERT INTO tags (name, color) VALUES (?, ?)", (name, color))
        self._conn.commit()
        return self.get(cursor.lastrowid)

    def get(self, tag_id: int) -> Optional[Tag]:
        row = self._conn.execute("SELECT * FROM tags WHERE id = ?", (tag_id,)).fetchone()
        return Tag.from_row(row) if row else None

    def get_by_name(self, name: str) -> Optional[Tag]:
        row = self._conn.execute("SELECT * FROM tags WHERE name = ? COLLATE NOCASE", (name,)).fetchone()
        return Tag.from_row(row) if row else None

    def get_or_create(self, name: str) -> Tag:
        existing = self.get_by_name(name)
        return existing if existing is not None else self.create(name)

    def list_all(self) -> List[Tag]:
        rows = self._conn.execute("SELECT * FROM tags ORDER BY name COLLATE NOCASE").fetchall()
        return [Tag.from_row(row) for row in rows]

    def list_for_note(self, note_id: int) -> List[Tag]:
        rows = self._conn.execute(
            """
            SELECT tags.* FROM tags
            JOIN note_tags ON note_tags.tag_id = tags.id
            WHERE note_tags.note_id = ?
            ORDER BY tags.name COLLATE NOCASE
            """,
            (note_id,),
        ).fetchall()
        return [Tag.from_row(row) for row in rows]

    def assign(self, note_id: int, tag_id: int) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)", (note_id, tag_id)
        )
        self._conn.commit()

    def unassign(self, note_id: int, tag_id: int) -> None:
        self._conn.execute(
            "DELETE FROM note_tags WHERE note_id = ? AND tag_id = ?", (note_id, tag_id)
        )
        self._conn.commit()

    def rename(self, tag_id: int, name: str) -> None:
        self._conn.execute("UPDATE tags SET name = ? WHERE id = ?", (name, tag_id))
        self._conn.commit()

    def delete(self, tag_id: int) -> None:
        self._conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        self._conn.commit()
