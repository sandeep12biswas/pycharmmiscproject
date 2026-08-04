from typing import Dict, Optional

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QFrame, QWidget

from app.models.tile import Tile
from app.repositories.tiles_repo import MIN_TILE_HEIGHT, MIN_TILE_WIDTH


class TileWidget(QFrame):
    """An inert bordered tile shell positioned by absolute geometry on a
    CanvasWidget. Dragging to reposition (SCRUM-11), resize handles
    (SCRUM-12), and in-tile rich text editing (SCRUM-13) are each their own
    follow-up sub-task -- this is deliberately just the visible border +
    geometry AC1 asks for."""

    def __init__(self, tile: Tile, parent=None):
        super().__init__(parent)
        self.tile_id = tile.id
        self.setObjectName("tileWidget")
        self.setStyleSheet(
            "#tileWidget { border: 1px solid palette(mid); border-radius: 4px; background: palette(base); }"
        )


class CanvasWidget(QWidget):
    """Free-form canvas for a single note in canvas mode (SCRUM-9/AC1).
    Emits signals only -- never touches sqlite3 -- and leaves persistence to
    whatever controller owns a TilesRepository, matching how the rest of
    app/ui/ mediates writes."""

    tileCreateRequested = Signal(float, float, float, float)  # x, y, width, height

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self._drag_origin: Optional[QPoint] = None
        self._drag_rect: Optional[QRect] = None
        self._tiles: Dict[int, TileWidget] = {}

    def mousePressEvent(self, event) -> None:
        pos = event.position().toPoint()
        if event.button() == Qt.MouseButton.LeftButton and self.childAt(pos) is None:
            self._drag_origin = pos
            self._drag_rect = QRect(self._drag_origin, self._drag_origin)
            self.update()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_origin is not None:
            self._drag_rect = QRect(self._drag_origin, event.position().toPoint()).normalized()
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._drag_origin is None:
            super().mouseReleaseEvent(event)
            return

        rect = self._drag_rect if self._drag_rect is not None else QRect(self._drag_origin, self._drag_origin)
        self._drag_origin = None
        self._drag_rect = None
        self.update()

        width = max(rect.width(), MIN_TILE_WIDTH)
        height = max(rect.height(), MIN_TILE_HEIGHT)
        self.tileCreateRequested.emit(float(rect.x()), float(rect.y()), float(width), float(height))

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self._drag_rect is None or self._drag_rect.isNull():
            return

        painter = QPainter(self)
        pen = QPen(self.palette().color(self.foregroundRole()))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(2)
        painter.setPen(pen)
        fill = self.palette().color(self.backgroundRole())
        painter.setBrush(fill)
        painter.setOpacity(0.5)
        painter.drawRect(self._drag_rect)
        painter.end()

    def add_tile(self, tile: Tile) -> TileWidget:
        widget = TileWidget(tile, self)
        widget.setGeometry(int(tile.x), int(tile.y), int(tile.width), int(tile.height))
        widget.show()
        self._tiles[tile.id] = widget
        return widget

    def clear(self) -> None:
        for widget in self._tiles.values():
            widget.deleteLater()
        self._tiles.clear()
        self.update()

    def tile_ids(self) -> list:
        return list(self._tiles.keys())
