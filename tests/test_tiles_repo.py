from app.repositories.tiles_repo import MIN_TILE_HEIGHT, MIN_TILE_WIDTH


def test_create_and_get_roundtrip(notes_repo, tiles_repo):
    note = notes_repo.create(title="Canvas note")
    tile = tiles_repo.create(note.id, x=10, y=20, width=200, height=150, title="Section A")

    fetched = tiles_repo.get(tile.id)

    assert fetched.note_id == note.id
    assert fetched.x == 10
    assert fetched.y == 20
    assert fetched.width == 200
    assert fetched.height == 150
    assert fetched.title == "Section A"
    assert fetched.content_html == ""
    assert fetched.content_plain == ""


def test_get_missing_tile_returns_none(tiles_repo):
    assert tiles_repo.get(9999) is None


def test_create_enforces_minimum_size(notes_repo, tiles_repo):
    note = notes_repo.create(title="Canvas note")
    tile = tiles_repo.create(note.id, x=0, y=0, width=10, height=10)

    assert tile.width == MIN_TILE_WIDTH
    assert tile.height == MIN_TILE_HEIGHT


def test_create_assigns_incrementing_z_index(notes_repo, tiles_repo):
    note = notes_repo.create(title="Canvas note")
    first = tiles_repo.create(note.id, x=0, y=0)
    second = tiles_repo.create(note.id, x=50, y=50)

    assert first.z_index == 0
    assert second.z_index == 1


def test_list_for_note_orders_by_z_index(notes_repo, tiles_repo):
    note = notes_repo.create(title="Canvas note")
    first = tiles_repo.create(note.id, x=0, y=0, title="First")
    second = tiles_repo.create(note.id, x=50, y=50, title="Second")

    tiles = tiles_repo.list_for_note(note.id)

    assert [t.id for t in tiles] == [first.id, second.id]


def test_list_for_note_excludes_other_notes(notes_repo, tiles_repo):
    note_a = notes_repo.create(title="A")
    note_b = notes_repo.create(title="B")
    tiles_repo.create(note_a.id, x=0, y=0)

    assert tiles_repo.list_for_note(note_b.id) == []


def test_update_geometry(notes_repo, tiles_repo):
    note = notes_repo.create(title="Canvas note")
    tile = tiles_repo.create(note.id, x=0, y=0, width=200, height=150)

    tiles_repo.update_geometry(tile.id, x=30, y=40, width=250, height=180)

    updated = tiles_repo.get(tile.id)
    assert (updated.x, updated.y, updated.width, updated.height) == (30, 40, 250, 180)


def test_update_geometry_enforces_minimum_size(notes_repo, tiles_repo):
    note = notes_repo.create(title="Canvas note")
    tile = tiles_repo.create(note.id, x=0, y=0, width=200, height=150)

    tiles_repo.update_geometry(tile.id, x=0, y=0, width=10, height=10)

    updated = tiles_repo.get(tile.id)
    assert (updated.width, updated.height) == (MIN_TILE_WIDTH, MIN_TILE_HEIGHT)


def test_delete_removes_tile(notes_repo, tiles_repo):
    note = notes_repo.create(title="Canvas note")
    tile = tiles_repo.create(note.id, x=0, y=0)

    tiles_repo.delete(tile.id)

    assert tiles_repo.get(tile.id) is None


def test_deleting_note_cascades_to_tiles(conn, notes_repo, tiles_repo):
    note = notes_repo.create(title="Canvas note")
    tile = tiles_repo.create(note.id, x=0, y=0)

    conn.execute("DELETE FROM notes WHERE id = ?", (note.id,))
    conn.commit()

    assert tiles_repo.get(tile.id) is None
