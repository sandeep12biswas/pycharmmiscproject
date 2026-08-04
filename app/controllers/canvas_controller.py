import logging
from typing import Optional

from PySide6.QtCore import QObject

from app.repositories.tiles_repo import TilesRepository
from app.ui.canvas import CanvasWidget

logger = logging.getLogger(__name__)


class CanvasController(QObject):
    """Mediates CanvasWidget <-> TilesRepository, mirroring how NoteController
    mediates the note editor <-> NotesRepository: the widget only emits
    signals, this is the only thing that writes tiles to the DB."""

    def __init__(self, tiles_repo: TilesRepository, canvas: CanvasWidget, parent=None):
        super().__init__(parent)
        self._tiles_repo = tiles_repo
        self._canvas = canvas
        self._current_note_id: Optional[int] = None

        self._canvas.tileCreateRequested.connect(self._on_tile_create_requested)
        self._canvas.tileMoved.connect(self._on_tile_moved)

    def load_note(self, note_id: int) -> None:
        self._current_note_id = note_id
        self._canvas.clear()
        for tile in self._tiles_repo.list_for_note(note_id):
            self._canvas.add_tile(tile)

    def clear(self) -> None:
        self._current_note_id = None
        self._canvas.clear()

    def _on_tile_create_requested(self, x: float, y: float, width: float, height: float) -> None:
        if self._current_note_id is None:
            return
        tile = self._tiles_repo.create(self._current_note_id, x=x, y=y, width=width, height=height)
        self._canvas.add_tile(tile)
        logger.debug("Tile id=%s created on note_id=%s via drag-create", tile.id, self._current_note_id)

    def _on_tile_moved(self, tile_id: int, x: float, y: float) -> None:
        tile = self._tiles_repo.get(tile_id)
        if tile is None:
            return
        self._tiles_repo.update_geometry(tile_id, x=x, y=y, width=tile.width, height=tile.height)
        logger.debug("Tile id=%s moved to (%s, %s)", tile_id, x, y)
