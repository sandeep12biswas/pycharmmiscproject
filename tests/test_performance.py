"""NFR-1: note list, search, and editor interactions must stay responsive
with at least several thousand notes. Thresholds here are deliberately
generous (order-of-magnitude headroom over what's actually observed) so this
guards against real regressions -- e.g. an accidentally-quadratic query or a
missing index -- without being flaky on a slower CI machine."""

import time

import pytest

from app.search.fts import SEARCH_LIMIT

NOTE_COUNT = 3000


@pytest.fixture
def seeded(notes_repo, folders_repo, tags_repo, conn):
    folders = [folders_repo.create(f"Folder {i}") for i in range(20)]
    tags = [tags_repo.create(f"tag-{i}") for i in range(30)]

    for i in range(NOTE_COUNT):
        note = notes_repo.create(
            title=f"Note {i} about widgets and gadgets",
            content_html=f"<p>Body text for note {i} discussing quarterly planning.</p>",
            content_plain=f"Body text for note {i} discussing quarterly planning.",
            folder_id=folders[i % len(folders)].id,
        )
        tags_repo.assign(note.id, tags[i % len(tags)].id)
        if i % 50 == 0:
            notes_repo.toggle_pin(note.id)
        if i % 30 == 0:
            notes_repo.toggle_favorite(note.id)

    conn.commit()
    return {"folders": folders, "tags": tags}


def test_list_all_stays_fast_with_thousands_of_notes(notes_repo, seeded):
    start = time.perf_counter()
    results = notes_repo.list_all()
    elapsed = time.perf_counter() - start

    assert len(results) == NOTE_COUNT
    assert elapsed < 1.0, f"list_all() took {elapsed:.3f}s for {NOTE_COUNT} notes"


def test_filtered_list_all_stays_fast(notes_repo, seeded):
    folder = seeded["folders"][0]
    tag = seeded["tags"][0]

    start = time.perf_counter()
    notes_repo.list_all(folder_id=folder.id, tag_id=tag.id, favorites_only=False)
    elapsed = time.perf_counter() - start

    assert elapsed < 1.0, f"filtered list_all() took {elapsed:.3f}s"


def test_search_stays_fast_with_thousands_of_notes(notes_repo, seeded):
    start = time.perf_counter()
    results = notes_repo.list_all(search_text="quarterly")
    elapsed = time.perf_counter() - start

    # every seeded note mentions "quarterly", but search_note_ids() caps at
    # SEARCH_LIMIT (a deliberate sanity cap, not a bug) -- results should hit
    # that cap, not silently return fewer due to some other truncation.
    assert len(results) == SEARCH_LIMIT
    assert elapsed < 1.0, f"FTS search took {elapsed:.3f}s for {NOTE_COUNT} notes"


def test_editor_load_stays_fast_for_a_large_note(qtbot):
    from app.ui.editor import NoteEditorWidget

    editor = NoteEditorWidget()
    qtbot.addWidget(editor)

    large_html = "<p>" + ("Lorem ipsum dolor sit amet. " * 2000) + "</p>"

    start = time.perf_counter()
    editor.load("Large note", large_html, [])
    elapsed = time.perf_counter() - start

    assert elapsed < 1.0, f"loading a large note into the editor took {elapsed:.3f}s"
    assert "Lorem ipsum" in editor.plain_text()


def test_note_list_model_refresh_stays_fast(qtbot, notes_repo, seeded):
    from app.ui.models_qt import NoteListModel

    model = NoteListModel(notes_repo)
    start = time.perf_counter()
    model.refresh()
    elapsed = time.perf_counter() - start

    assert model.rowCount() == NOTE_COUNT
    assert elapsed < 1.0, f"NoteListModel.refresh() took {elapsed:.3f}s for {NOTE_COUNT} notes"
