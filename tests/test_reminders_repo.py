def _sql_now(conn, offset=None):
    if offset is None:
        return conn.execute("SELECT datetime('now')").fetchone()[0]
    return conn.execute("SELECT datetime('now', ?)", (offset,)).fetchone()[0]


def test_create_and_get_roundtrip(notes_repo, reminders_repo, conn):
    note = notes_repo.create(title="N")
    remind_at = _sql_now(conn, "+1 hour")

    reminder = reminders_repo.create(note.id, remind_at, "call back")
    fetched = reminders_repo.get(reminder.id)

    assert fetched.note_id == note.id
    assert fetched.remind_at == remind_at
    assert fetched.message == "call back"
    assert fetched.is_done is False


def test_create_without_message(notes_repo, reminders_repo, conn):
    note = notes_repo.create(title="N")
    reminder = reminders_repo.create(note.id, _sql_now(conn, "+1 hour"))
    assert reminders_repo.get(reminder.id).message is None


def test_list_for_note(notes_repo, reminders_repo, conn):
    note = notes_repo.create(title="N")
    other = notes_repo.create(title="Other")
    reminders_repo.create(note.id, _sql_now(conn, "+1 hour"), "a")
    reminders_repo.create(note.id, _sql_now(conn, "+2 hour"), "b")
    reminders_repo.create(other.id, _sql_now(conn, "+1 hour"), "not this one")

    reminders = reminders_repo.list_for_note(note.id)
    assert sorted(r.message for r in reminders) == ["a", "b"]


def test_list_upcoming_excludes_done(notes_repo, reminders_repo, conn):
    note = notes_repo.create(title="N")
    pending = reminders_repo.create(note.id, _sql_now(conn, "+1 hour"), "pending")
    done = reminders_repo.create(note.id, _sql_now(conn, "+2 hour"), "done")
    reminders_repo.mark_done(done.id)

    upcoming = reminders_repo.list_upcoming()
    assert [r.id for r in upcoming] == [pending.id]


def test_list_due_boundary_conditions(notes_repo, reminders_repo, conn):
    note = notes_repo.create(title="N")

    past = reminders_repo.create(note.id, _sql_now(conn, "-1 hour"), "past")
    at_now = reminders_repo.create(note.id, _sql_now(conn), "at now")
    future = reminders_repo.create(note.id, _sql_now(conn, "+1 hour"), "future")

    due_ids = {r.id for r in reminders_repo.list_due()}

    assert past.id in due_ids, "a reminder in the past must be due"
    assert at_now.id in due_ids, "a reminder due exactly now must be due (inclusive boundary)"
    assert future.id not in due_ids, "a reminder in the future must not be due"


def test_list_due_excludes_already_done(notes_repo, reminders_repo, conn):
    note = notes_repo.create(title="N")
    reminder = reminders_repo.create(note.id, _sql_now(conn, "-1 hour"), "past")
    reminders_repo.mark_done(reminder.id)

    assert reminders_repo.list_due() == []


def test_mark_done(notes_repo, reminders_repo, conn):
    note = notes_repo.create(title="N")
    reminder = reminders_repo.create(note.id, _sql_now(conn, "+1 hour"))

    reminders_repo.mark_done(reminder.id)

    assert reminders_repo.get(reminder.id).is_done is True
    assert reminders_repo.list_upcoming() == []


def test_delete(notes_repo, reminders_repo, conn):
    note = notes_repo.create(title="N")
    reminder = reminders_repo.create(note.id, _sql_now(conn, "+1 hour"))

    reminders_repo.delete(reminder.id)

    assert reminders_repo.get(reminder.id) is None


def test_cascade_delete_when_note_deleted(notes_repo, reminders_repo, conn):
    note = notes_repo.create(title="N")
    reminder = reminders_repo.create(note.id, _sql_now(conn, "+1 hour"))

    notes_repo.delete_permanently(note.id)

    assert reminders_repo.get(reminder.id) is None
