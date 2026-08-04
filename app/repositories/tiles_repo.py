import logging
import sqlite3
from typing import List, Optional

from app.models.tile import Tile

logger = logging.getLogger(__name__)

# AC3's minimum -- referenced by AC1 ("default minimum size") too, so tiles
# created here already land on the size later resize handling (SCRUM-12)
# will enforce as a floor.
MIN_TILE_WIDTH = 150
MIN_TILE_HEIGHT = 100


class TilesRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(
        self,
        note_id: int,
        x: float,
        y: float,
        width: float = MIN_TILE_WIDTH,
        height: float = MIN_TILE_HEIGHT,
        title: str = "",
        content_html: str = "",
        content_plain: str = "",
    ) -> Tile:
        z_index = self._next_z_index(note_id)
        cursor = self._conn.execute(
            """
            INSERT INTO note_tiles (note_id, x, y, width, height, z_index, title, content_html, content_plain)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (note_id, x, y, max(width, MIN_TILE_WIDTH), max(height, MIN_TILE_HEIGHT), z_index, title,
             content_html, content_plain),
        )
        self._conn.commit()
        logger.debug("Created tile id=%s for note_id=%s", cursor.lastrowid, note_id)
        return self.get(cursor.lastrowid)

    def get(self, tile_id: int) -> Optional[Tile]:
        row = self._conn.execute("SELECT * FROM note_tiles WHERE id = ?", (tile_id,)).fetchone()
        return Tile.from_row(row) if row else None

    def list_for_note(self, note_id: int) -> List[Tile]:
        rows = self._conn.execute(
            "SELECT * FROM note_tiles WHERE note_id = ? ORDER BY z_index ASC, id ASC",
            (note_id,),
        ).fetchall()
        return [Tile.from_row(row) for row in rows]

    def update_geometry(self, tile_id: int, x: float, y: float, width: float, height: float) -> None:
        self._conn.execute(
            """
            UPDATE note_tiles
            SET x = ?, y = ?, width = ?, height = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (x, y, max(width, MIN_TILE_WIDTH), max(height, MIN_TILE_HEIGHT), tile_id),
        )
        self._conn.commit()
        logger.debug("Updated geometry for tile id=%s", tile_id)

    def delete(self, tile_id: int) -> None:
        self._conn.execute("DELETE FROM note_tiles WHERE id = ?", (tile_id,))
        self._conn.commit()
        logger.info("Deleted tile id=%s", tile_id)

    def _next_z_index(self, note_id: int) -> int:
        row = self._conn.execute(
            "SELECT COALESCE(MAX(z_index), -1) + 1 AS next_z FROM note_tiles WHERE note_id = ?",
            (note_id,),
        ).fetchone()
        return row["next_z"]
