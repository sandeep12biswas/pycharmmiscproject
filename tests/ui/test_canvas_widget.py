from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from app.models.tile import Tile
from app.repositories.tiles_repo import MIN_TILE_HEIGHT, MIN_TILE_WIDTH
from app.ui.canvas import CanvasWidget, TileWidget


def _make_tile(tile_id=1, note_id=1, x=0, y=0, width=200, height=150) -> Tile:
    return Tile(
        id=tile_id,
        note_id=note_id,
        x=x,
        y=y,
        width=width,
        height=height,
        z_index=0,
        title="",
        content_html="",
        content_plain="",
        created_at="",
        updated_at="",
    )


def _drag(widget, start: QPoint, end: QPoint) -> None:
    QTest.mousePress(widget, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(widget, pos=end)
    QTest.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=end)


def test_drag_on_empty_canvas_emits_tile_create_requested(qtbot):
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)

    with qtbot.waitSignal(canvas.tileCreateRequested, timeout=1000) as blocker:
        _drag(canvas, QPoint(20, 30), QPoint(219, 179))  # QRect(topLeft, bottomRight) is inclusive

    x, y, width, height = blocker.args
    assert (x, y) == (20, 30)
    assert (width, height) == (200, 150)


def test_small_drag_clamps_to_minimum_tile_size(qtbot):
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)

    with qtbot.waitSignal(canvas.tileCreateRequested, timeout=1000) as blocker:
        _drag(canvas, QPoint(10, 10), QPoint(20, 20))

    _, _, width, height = blocker.args
    assert width == MIN_TILE_WIDTH
    assert height == MIN_TILE_HEIGHT


def test_add_tile_creates_positioned_child_widget(qtbot):
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)
    tile = _make_tile(x=15, y=25, width=200, height=150)

    widget = canvas.add_tile(tile)

    assert isinstance(widget, TileWidget)
    assert widget.tile_id == tile.id
    assert (widget.x(), widget.y()) == (15, 25)
    assert (widget.width(), widget.height()) == (200, 150)
    assert canvas.tile_ids() == [tile.id]


def test_clear_removes_all_tiles(qtbot):
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)
    canvas.add_tile(_make_tile(tile_id=1))
    canvas.add_tile(_make_tile(tile_id=2))

    canvas.clear()

    assert canvas.tile_ids() == []


def test_dragging_starting_on_an_existing_tile_does_not_create_a_new_one(qtbot):
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)
    canvas.add_tile(_make_tile(x=0, y=0, width=200, height=150))
    canvas.show()

    with qtbot.assertNotEmitted(canvas.tileCreateRequested, wait=200):
        _drag(canvas, QPoint(50, 50), QPoint(250, 200))


def test_dragging_the_header_repositions_the_tile(qtbot):
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)
    canvas.show()
    widget = canvas.add_tile(_make_tile(x=0, y=0, width=200, height=150))

    with qtbot.waitSignal(canvas.tileMoved, timeout=1000) as blocker:
        _drag(widget._header, QPoint(10, 10), QPoint(60, 40))

    tile_id, x, y = blocker.args
    assert tile_id == widget.tile_id
    assert (x, y) == (50.0, 30.0)
    assert (widget.x(), widget.y()) == (50, 30)


def test_dragging_the_body_does_not_move_the_tile(qtbot):
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)
    canvas.show()
    widget = canvas.add_tile(_make_tile(x=0, y=0, width=200, height=150))
    original_pos = widget.pos()

    with qtbot.assertNotEmitted(canvas.tileMoved, wait=200):
        # well below the header strip (_TileHeader.HEIGHT == 22)
        _drag(widget, QPoint(50, 100), QPoint(90, 130))

    assert widget.pos() == original_pos


def test_dragging_the_header_clamps_position_to_non_negative(qtbot):
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)
    canvas.show()
    widget = canvas.add_tile(_make_tile(x=10, y=10, width=200, height=150))

    with qtbot.waitSignal(canvas.tileMoved, timeout=1000) as blocker:
        _drag(widget._header, QPoint(5, 5), QPoint(-200, -200))

    _, x, y = blocker.args
    assert (x, y) == (0.0, 0.0)
