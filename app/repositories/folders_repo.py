import logging
import sqlite3
from typing import List, Optional

from app.models.folder import Folder

logger = logging.getLogger(__name__)


class FoldersRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(self, name: str, parent_id: Optional[int] = None) -> Folder:
        cursor = self._conn.execute(
            "INSERT INTO folders (name, parent_id) VALUES (?, ?)",
            (name, parent_id),
        )
        self._conn.commit()
        logger.debug("Created folder id=%s name=%r parent_id=%s", cursor.lastrowid, name, parent_id)
        return self.get(cursor.lastrowid)

    def get(self, folder_id: int) -> Optional[Folder]:
        row = self._conn.execute("SELECT * FROM folders WHERE id = ?", (folder_id,)).fetchone()
        return Folder.from_row(row) if row else None

    def list_all(self) -> List[Folder]:
        rows = self._conn.execute(
            "SELECT * FROM folders ORDER BY sort_order, name COLLATE NOCASE"
        ).fetchall()
        return [Folder.from_row(row) for row in rows]

    def rename(self, folder_id: int, name: str) -> None:
        self._conn.execute("UPDATE folders SET name = ? WHERE id = ?", (name, folder_id))
        self._conn.commit()
        logger.debug("Renamed folder id=%s to %r", folder_id, name)

    def move(self, folder_id: int, parent_id: Optional[int]) -> None:
        self._conn.execute("UPDATE folders SET parent_id = ? WHERE id = ?", (parent_id, folder_id))
        self._conn.commit()
        logger.debug("Moved folder id=%s to parent_id=%s", folder_id, parent_id)

    def delete(self, folder_id: int) -> None:
        """Sub-folders cascade-delete (ON DELETE CASCADE on folders.parent_id);
        notes directly or transitively inside become unfiled (ON DELETE SET NULL
        on notes.folder_id), per FR-13."""
        self._conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
        self._conn.commit()
        logger.info("Deleted folder id=%s (sub-folders cascade, notes become unfiled)", folder_id)
