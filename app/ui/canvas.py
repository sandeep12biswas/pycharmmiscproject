from typing import Dict, Optional

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget

from app.models.tile import Tile
from app.repositories.tiles_repo import MIN_TILE_HEIGHT, MIN_TILE_WIDTH


class _TileHeader(QWidget):
    """Drag handle strip at the top of a TileWidget (SCRUM-11/AC2 -- tiles
    move by their header/title bar, not by clicking anywhere in the body).
    Just a bare strip for now; SCRUM-15 drops a title field + delete icon
    into this same widget rather than building its own header."""

    HEIGHT = 22

    def __init__(self, parent: "TileWidget"):
        super().__init__(parent)
        self.setFixedHeight(self.HEIGHT)
        self.setObjectName("tileHeader")
        self.setStyleSheet(
            "#tileHeader { background: palette(midlight);"
            " border-top-left-radius: 4px; border-top-right-radius: 4px; }"
        )
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self._drag_start_global: Optional[QPoint] = None
        self._drag_start_tile_pos: Optional[QPoint] = None

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        self._drag_start_global = event.globalPosition().toPoint()
        self._drag_start_tile_pos = self.parentWidget().pos()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_start_global is None:
            super().mouseMoveEvent(event)
            return
        delta = event.globalPosition().toPoint() - self._drag_start_global
        new_pos = self._drag_start_tile_pos + delta
        new_pos.setX(max(new_pos.x(), 0))
        new_pos.setY(max(new_pos.y(), 0))
        self.parentWidget().move(new_pos)

    def mouseReleaseEvent(self, event) -> None:
        if self._drag_start_global is None:
            super().mouseReleaseEvent(event)
            return
        self._drag_start_global = None
        self._drag_start_tile_pos = None
        self.parentWidget().notify_position_changed()


class TileWidget(QFrame):
    """A bordered tile positioned by absolute geometry on a CanvasWidget:
    a drag-handle header (SCRUM-11) on top, an empty body below (resize
    handles are SCRUM-12, in-tile rich text editing is SCRUM-13)."""

    positionChanged = Signal(int, float, float)  # tile_id, x, y

    def __init__(self, tile: Tile, parent=None):
        super().__init__(parent)
        self.tile_id = tile.id
        self.setObjectName("tileWidget")
        self.setStyleSheet(
            "#tileWidget { border: 1px solid palette(mid); border-radius: 4px; background: palette(base); }"
        )

        self._header = _TileHeader(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._header)
        layout.addStretch()

    def notify_position_changed(self) -> None:
        self.positionChanged.emit(self.tile_id, float(self.x()), float(self.y()))


class CanvasWidget(QWidget):
    """Free-form canvas for a single note in canvas mode (SCRUM-9/AC1).
    Emits signals only -- never touches sqlite3 -- and leaves persistence to
    whatever controller owns a TilesRepository, matching how the rest of
    app/ui/ mediates writes."""

    tileCreateRequested = Signal(float, float, float, float)  # x, y, width, height
    tileMoved = Signal(int, float, float)  # tile_id, x, y

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
        widget.positionChanged.connect(self.tileMoved)
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
