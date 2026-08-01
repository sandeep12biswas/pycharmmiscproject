def test_create_and_get_roundtrip(folders_repo):
    folder = folders_repo.create("Work")
    fetched = folders_repo.get(folder.id)

    assert fetched.name == "Work"
    assert fetched.parent_id is None


def test_create_nested_folder(folders_repo):
    parent = folders_repo.create("Work")
    child = folders_repo.create("Projects", parent_id=parent.id)

    assert folders_repo.get(child.id).parent_id == parent.id


def test_get_missing_folder_returns_none(folders_repo):
    assert folders_repo.get(9999) is None


def test_list_all_returns_every_folder(folders_repo):
    folders_repo.create("Work")
    folders_repo.create("Personal")

    names = sorted(f.name for f in folders_repo.list_all())
    assert names == ["Personal", "Work"]


def test_rename(folders_repo):
    folder = folders_repo.create("Old Name")
    folders_repo.rename(folder.id, "New Name")

    assert folders_repo.get(folder.id).name == "New Name"


def test_move_reparents_folder(folders_repo):
    a = folders_repo.create("A")
    b = folders_repo.create("B")
    child = folders_repo.create("Child", parent_id=a.id)

    folders_repo.move(child.id, b.id)
    assert folders_repo.get(child.id).parent_id == b.id

    folders_repo.move(child.id, None)
    assert folders_repo.get(child.id).parent_id is None


def test_delete_cascades_subfolders(folders_repo):
    parent = folders_repo.create("Parent")
    child = folders_repo.create("Child", parent_id=parent.id)
    grandchild = folders_repo.create("Grandchild", parent_id=child.id)

    folders_repo.delete(parent.id)

    assert folders_repo.get(parent.id) is None
    assert folders_repo.get(child.id) is None
    assert folders_repo.get(grandchild.id) is None


def test_delete_unfiles_notes_directly_and_transitively(notes_repo, folders_repo):
    parent = folders_repo.create("Parent")
    child = folders_repo.create("Child", parent_id=parent.id)
    note_in_parent = notes_repo.create(title="In parent", folder_id=parent.id)
    note_in_child = notes_repo.create(title="In child", folder_id=child.id)

    folders_repo.delete(parent.id)

    assert notes_repo.get(note_in_parent.id).folder_id is None
    assert notes_repo.get(note_in_child.id).folder_id is None
