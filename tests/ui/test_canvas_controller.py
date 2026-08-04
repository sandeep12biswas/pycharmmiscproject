from app.controllers.canvas_controller import CanvasController
from app.ui.canvas import CanvasWidget


def _make_controller(qtbot, tiles_repo):
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)
    controller = CanvasController(tiles_repo, canvas)
    return controller, canvas


def test_load_note_populates_canvas_from_repo(qtbot, notes_repo, tiles_repo):
    note = notes_repo.create(title="Canvas note")
    tiles_repo.create(note.id, x=0, y=0, width=200, height=150)
    tiles_repo.create(note.id, x=250, y=0, width=200, height=150)
    controller, canvas = _make_controller(qtbot, tiles_repo)

    controller.load_note(note.id)

    assert len(canvas.tile_ids()) == 2


def test_load_note_clears_previous_notes_tiles(qtbot, notes_repo, tiles_repo):
    note_a = notes_repo.create(title="A")
    note_b = notes_repo.create(title="B")
    tiles_repo.create(note_a.id, x=0, y=0)
    tiles_repo.create(note_b.id, x=0, y=0)
    controller, canvas = _make_controller(qtbot, tiles_repo)

    controller.load_note(note_a.id)
    assert len(canvas.tile_ids()) == 1

    controller.load_note(note_b.id)
    assert len(canvas.tile_ids()) == 1  # not 2 -- note_a's tile was cleared, not appended to


def test_drag_create_on_canvas_persists_tile_via_repo(qtbot, notes_repo, tiles_repo):
    note = notes_repo.create(title="Canvas note")
    controller, canvas = _make_controller(qtbot, tiles_repo)
    controller.load_note(note.id)

    canvas.tileCreateRequested.emit(10.0, 20.0, 200.0, 150.0)

    persisted = tiles_repo.list_for_note(note.id)
    assert len(persisted) == 1
    assert (persisted[0].x, persisted[0].y, persisted[0].width, persisted[0].height) == (10.0, 20.0, 200.0, 150.0)
    assert canvas.tile_ids() == [persisted[0].id]


def test_clear_empties_canvas_and_forgets_current_note(qtbot, notes_repo, tiles_repo):
    note = notes_repo.create(title="Canvas note")
    tiles_repo.create(note.id, x=0, y=0)
    controller, canvas = _make_controller(qtbot, tiles_repo)
    controller.load_note(note.id)

    controller.clear()

    assert canvas.tile_ids() == []
    # a drag-create after clear() is a no-op (no current note to attach the tile to)
    before = len(tiles_repo.list_for_note(note.id))
    canvas.tileCreateRequested.emit(0.0, 0.0, 200.0, 150.0)
    assert len(tiles_repo.list_for_note(note.id)) == before
