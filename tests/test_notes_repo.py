def test_create_and_get_roundtrip(notes_repo):
    note = notes_repo.create(title="Groceries", content_html="<p>milk</p>", content_plain="milk")
    fetched = notes_repo.get(note.id)

    assert fetched.title == "Groceries"
    assert fetched.content_html == "<p>milk</p>"
    assert fetched.content_plain == "milk"
    assert fetched.folder_id is None
    assert fetched.is_pinned is False
    assert fetched.is_favorite is False
    assert fetched.is_trashed is False


def test_get_missing_note_returns_none(notes_repo):
    assert notes_repo.get(9999) is None


def test_update_content(notes_repo):
    note = notes_repo.create(title="Old", content_html="<p>old</p>", content_plain="old")
    notes_repo.update_content(note.id, "New", "<p>new</p>", "new")

    updated = notes_repo.get(note.id)
    assert updated.title == "New"
    assert updated.content_html == "<p>new</p>"
    assert updated.content_plain == "new"


def test_list_all_excludes_trashed_by_default(notes_repo):
    kept = notes_repo.create(title="Kept")
    trashed = notes_repo.create(title="Trashed")
    notes_repo.trash(trashed.id)

    titles = [n.title for n in notes_repo.list_all()]
    assert titles == ["Kept"]


def test_list_all_orders_pinned_first(notes_repo):
    first = notes_repo.create(title="First created")
    second = notes_repo.create(title="Second created")
    notes_repo.toggle_pin(second.id)

    titles = [n.title for n in notes_repo.list_all()]
    assert titles[0] == "Second created"
    assert "First created" in titles


def test_list_all_folder_filter(notes_repo, folders_repo):
    work = folders_repo.create("Work")
    in_folder = notes_repo.create(title="In Work", folder_id=work.id)
    notes_repo.create(title="Unfiled")

    titles = [n.title for n in notes_repo.list_all(folder_id=work.id)]
    assert titles == ["In Work"]
    assert notes_repo.get(in_folder.id).folder_id == work.id


def test_list_all_tag_filter(notes_repo, tags_repo):
    tagged = notes_repo.create(title="Tagged")
    notes_repo.create(title="Untagged")
    tag = tags_repo.create("urgent")
    tags_repo.assign(tagged.id, tag.id)

    titles = [n.title for n in notes_repo.list_all(tag_id=tag.id)]
    assert titles == ["Tagged"]


def test_list_all_favorites_only(notes_repo):
    fav = notes_repo.create(title="Fav")
    notes_repo.create(title="Not fav")
    notes_repo.toggle_favorite(fav.id)

    titles = [n.title for n in notes_repo.list_all(favorites_only=True)]
    assert titles == ["Fav"]


def test_list_all_combines_folder_tag_and_favorites(notes_repo, folders_repo, tags_repo):
    work = folders_repo.create("Work")
    tag = tags_repo.create("urgent")

    matches = notes_repo.create(title="Matches all", folder_id=work.id)
    tags_repo.assign(matches.id, tag.id)
    notes_repo.toggle_favorite(matches.id)

    wrong_folder = notes_repo.create(title="Wrong folder")
    tags_repo.assign(wrong_folder.id, tag.id)
    notes_repo.toggle_favorite(wrong_folder.id)

    right_folder_untagged = notes_repo.create(title="Right folder, untagged", folder_id=work.id)
    notes_repo.toggle_favorite(right_folder_untagged.id)

    titles = [
        n.title
        for n in notes_repo.list_all(folder_id=work.id, tag_id=tag.id, favorites_only=True)
    ]
    assert titles == ["Matches all"]


def test_list_all_search_text_filters_and_ranks(notes_repo):
    title_match = notes_repo.create(
        title="python tips", content_html="<p>stuff</p>", content_plain="stuff"
    )
    content_match = notes_repo.create(
        title="misc", content_html="<p>a brief mention of python</p>", content_plain="a brief mention of python"
    )
    notes_repo.create(title="unrelated", content_html="<p>nothing</p>", content_plain="nothing")

    results = notes_repo.list_all(search_text="python")
    assert [n.id for n in results] == [title_match.id, content_match.id]


def test_list_all_search_text_empty_or_blank_returns_everything(notes_repo):
    notes_repo.create(title="A")
    notes_repo.create(title="B")

    assert len(notes_repo.list_all(search_text="")) == 2
    assert len(notes_repo.list_all(search_text="   ")) == 2


def test_move_to_folder(notes_repo, folders_repo):
    work = folders_repo.create("Work")
    personal = folders_repo.create("Personal")
    note = notes_repo.create(title="N", folder_id=work.id)

    notes_repo.move_to_folder(note.id, personal.id)
    assert notes_repo.get(note.id).folder_id == personal.id

    notes_repo.move_to_folder(note.id, None)
    assert notes_repo.get(note.id).folder_id is None


def test_toggle_pin_and_favorite(notes_repo):
    note = notes_repo.create(title="N")

    notes_repo.toggle_pin(note.id)
    assert notes_repo.get(note.id).is_pinned is True
    notes_repo.toggle_pin(note.id)
    assert notes_repo.get(note.id).is_pinned is False

    notes_repo.toggle_favorite(note.id)
    assert notes_repo.get(note.id).is_favorite is True
    notes_repo.toggle_favorite(note.id)
    assert notes_repo.get(note.id).is_favorite is False


def test_set_canvas_mode(notes_repo):
    note = notes_repo.create(title="N")
    assert notes_repo.get(note.id).is_canvas is False

    notes_repo.set_canvas_mode(note.id, True)
    assert notes_repo.get(note.id).is_canvas is True

    notes_repo.set_canvas_mode(note.id, False)
    assert notes_repo.get(note.id).is_canvas is False


def test_trash_and_restore(notes_repo):
    note = notes_repo.create(title="N")

    notes_repo.trash(note.id)
    assert notes_repo.get(note.id).is_trashed is True
    assert [n.title for n in notes_repo.list_all()] == []
    assert [n.title for n in notes_repo.list_trashed()] == ["N"]

    notes_repo.restore(note.id)
    assert notes_repo.get(note.id).is_trashed is False
    assert [n.title for n in notes_repo.list_all()] == ["N"]
    assert notes_repo.list_trashed() == []


def test_delete_permanently_removes_note(notes_repo):
    note = notes_repo.create(title="N")
    notes_repo.delete_permanently(note.id)
    assert notes_repo.get(note.id) is None


def test_delete_permanently_cascades_tags_and_reminders(notes_repo, tags_repo, reminders_repo):
    note = notes_repo.create(title="N")
    tag = tags_repo.create("urgent")
    tags_repo.assign(note.id, tag.id)
    reminders_repo.create(note.id, "2099-01-01 00:00:00", "far future")

    notes_repo.delete_permanently(note.id)

    assert tags_repo.list_for_note(note.id) == []
    assert reminders_repo.list_for_note(note.id) == []
    # the tag itself is untouched -- only the note_tags link is cascaded
    assert tags_repo.get(tag.id) is not None


def test_folder_delete_unfiles_notes(notes_repo, folders_repo):
    work = folders_repo.create("Work")
    note = notes_repo.create(title="N", folder_id=work.id)

    folders_repo.delete(work.id)

    assert notes_repo.get(note.id).folder_id is None
