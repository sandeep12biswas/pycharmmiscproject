def test_create_and_get_roundtrip(tags_repo):
    tag = tags_repo.create("urgent")
    fetched = tags_repo.get(tag.id)

    assert fetched.name == "urgent"


def test_get_by_name_is_case_insensitive(tags_repo):
    tag = tags_repo.create("Home")

    assert tags_repo.get_by_name("home").id == tag.id
    assert tags_repo.get_by_name("HOME").id == tag.id
    assert tags_repo.get_by_name("missing") is None


def test_get_or_create_reuses_existing_tag_case_insensitively(tags_repo):
    first = tags_repo.get_or_create("Home")
    second = tags_repo.get_or_create("home")

    assert first.id == second.id
    assert len(tags_repo.list_all()) == 1


def test_get_or_create_creates_when_missing(tags_repo):
    tag = tags_repo.get_or_create("new-tag")
    assert tags_repo.get(tag.id).name == "new-tag"


def test_list_all_ordered_by_name(tags_repo):
    tags_repo.create("zebra")
    tags_repo.create("apple")

    names = [t.name for t in tags_repo.list_all()]
    assert names == ["apple", "zebra"]


def test_assign_and_list_for_note(notes_repo, tags_repo):
    note = notes_repo.create(title="N")
    urgent = tags_repo.create("urgent")
    later = tags_repo.create("later")

    tags_repo.assign(note.id, urgent.id)
    tags_repo.assign(note.id, later.id)

    names = sorted(t.name for t in tags_repo.list_for_note(note.id))
    assert names == ["later", "urgent"]


def test_assign_is_idempotent(notes_repo, tags_repo):
    note = notes_repo.create(title="N")
    tag = tags_repo.create("urgent")

    tags_repo.assign(note.id, tag.id)
    tags_repo.assign(note.id, tag.id)  # assigning twice should not duplicate the link

    assert len(tags_repo.list_for_note(note.id)) == 1


def test_unassign(notes_repo, tags_repo):
    note = notes_repo.create(title="N")
    tag = tags_repo.create("urgent")
    tags_repo.assign(note.id, tag.id)

    tags_repo.unassign(note.id, tag.id)

    assert tags_repo.list_for_note(note.id) == []
    assert tags_repo.get(tag.id) is not None  # unassigning doesn't delete the tag itself


def test_rename(tags_repo):
    tag = tags_repo.create("old-name")
    tags_repo.rename(tag.id, "new-name")

    assert tags_repo.get(tag.id).name == "new-name"


def test_delete_cascades_note_tags(notes_repo, tags_repo):
    note = notes_repo.create(title="N")
    tag = tags_repo.create("urgent")
    tags_repo.assign(note.id, tag.id)

    tags_repo.delete(tag.id)

    assert tags_repo.get(tag.id) is None
    assert tags_repo.list_for_note(note.id) == []
