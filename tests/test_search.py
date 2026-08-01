from app.search.fts import search_note_ids


def test_search_note_ids_matches_title_and_content(notes_repo, conn):
    title_match = notes_repo.create(title="python tips", content_html="", content_plain="stuff")
    content_match = notes_repo.create(
        title="misc", content_html="", content_plain="a brief mention of python"
    )
    notes_repo.create(title="unrelated", content_html="", content_plain="nothing relevant")

    ids = search_note_ids(conn, "python")
    assert set(ids) == {title_match.id, content_match.id}


def test_search_note_ids_supports_prefix_matching(notes_repo, conn):
    note = notes_repo.create(title="working notes", content_html="", content_plain="")

    assert note.id in search_note_ids(conn, "wor")


def test_search_note_ids_ranks_title_match_first(notes_repo, conn):
    title_match = notes_repo.create(title="python", content_html="", content_plain="stuff")
    content_match = notes_repo.create(
        title="misc", content_html="", content_plain="a brief mention of python here"
    )

    ids = search_note_ids(conn, "python")
    assert ids[0] == title_match.id
    assert content_match.id in ids


def test_search_note_ids_blank_query_returns_nothing(conn):
    assert search_note_ids(conn, "") == []
    assert search_note_ids(conn, "   ") == []


def test_search_note_ids_no_match_returns_empty(notes_repo, conn):
    notes_repo.create(title="apples", content_html="", content_plain="apples")
    assert search_note_ids(conn, "zzzznomatch") == []


def test_search_note_ids_handles_special_characters_safely(notes_repo, conn):
    notes_repo.create(title="normal note", content_html="", content_plain="normal note")

    for weird in ["AND", '"quoted"', "foo*bar", "colon:test", "-dash", "()", "OR NOT"]:
        search_note_ids(conn, weird)  # must not raise


def test_search_excludes_trashed_notes_via_notes_repo(notes_repo):
    trashed = notes_repo.create(title="findme", content_html="", content_plain="findme")
    notes_repo.trash(trashed.id)

    assert notes_repo.list_all(search_text="findme") == []
