from app.ui.main_window import MainWindow

AUTOSAVE_DEBOUNCE_MS = 1500


def _make_window(qtbot, notes_repo, folders_repo, tags_repo, reminders_repo):
    window = MainWindow(notes_repo, folders_repo, tags_repo, reminders_repo)
    qtbot.addWidget(window)
    return window


def test_app_launches_with_empty_state(qtbot, notes_repo, folders_repo, tags_repo, reminders_repo):
    window = _make_window(qtbot, notes_repo, folders_repo, tags_repo, reminders_repo)

    assert window.windowTitle() == "Notes"
    assert window._model.rowCount() == 0
    assert window._controller._current_note_id is None


def test_new_note_flow_creates_and_selects_a_note(
    qtbot, notes_repo, folders_repo, tags_repo, reminders_repo
):
    window = _make_window(qtbot, notes_repo, folders_repo, tags_repo, reminders_repo)

    window._controller.new_note()

    assert window._model.rowCount() == 1
    note = window._model.note_at(0)
    assert note.title == "Untitled"
    assert window._controller._current_note_id == note.id
    assert notes_repo.get(note.id) is not None


def test_delete_note_soft_deletes_and_clears_editor(
    qtbot, notes_repo, folders_repo, tags_repo, reminders_repo
):
    window = _make_window(qtbot, notes_repo, folders_repo, tags_repo, reminders_repo)
    window._controller.new_note()
    note_id = window._controller._current_note_id

    window._controller.delete_current_note()

    assert window._controller._current_note_id is None
    assert window._model.rowCount() == 0
    assert notes_repo.get(note_id).is_trashed is True


def test_autosave_persists_edited_content_via_flush_pending(
    qtbot, notes_repo, folders_repo, tags_repo, reminders_repo
):
    """flush_pending() is what the debounce timer, note-switch, and window
    close all funnel through -- exercised directly here so the test doesn't
    need to wait out the real debounce interval. The timer itself firing on
    its own is covered separately below."""
    window = _make_window(qtbot, notes_repo, folders_repo, tags_repo, reminders_repo)
    window._controller.new_note()
    note_id = window._controller._current_note_id

    editor = window._controller._editor
    editor._title_edit.setText("Meeting notes")
    editor._body_edit.setPlainText("hello world")

    window._controller.flush_pending()

    saved = notes_repo.get(note_id)
    assert saved.title == "Meeting notes"
    assert "hello world" in saved.content_plain


def test_autosave_debounce_timer_fires_on_its_own(
    qtbot, notes_repo, folders_repo, tags_repo, reminders_repo
):
    """Types content and waits for NoteController's real QTimer to fire (not
    a manual flush_pending() call), proving the production autosave path
    actually saves without user intervention."""
    window = _make_window(qtbot, notes_repo, folders_repo, tags_repo, reminders_repo)
    window._controller.new_note()
    note_id = window._controller._current_note_id

    editor = window._controller._editor
    editor._body_edit.setPlainText("typed content, waiting on the real timer")

    with qtbot.waitSignal(
        window._controller._autosave_timer.timeout, timeout=AUTOSAVE_DEBOUNCE_MS + 1500
    ):
        pass

    saved = notes_repo.get(note_id)
    assert "typed content, waiting on the real timer" in saved.content_plain


def test_close_event_flushes_pending_edits(qtbot, notes_repo, folders_repo, tags_repo, reminders_repo):
    window = _make_window(qtbot, notes_repo, folders_repo, tags_repo, reminders_repo)
    window._controller.new_note()
    note_id = window._controller._current_note_id
    window._controller._editor._body_edit.setPlainText("saved on close")

    window.close()

    saved = notes_repo.get(note_id)
    assert "saved on close" in saved.content_plain


def test_switching_notes_flushes_the_previous_one(
    qtbot, notes_repo, folders_repo, tags_repo, reminders_repo
):
    window = _make_window(qtbot, notes_repo, folders_repo, tags_repo, reminders_repo)
    window._controller.new_note()
    first_id = window._controller._current_note_id
    window._controller._editor._body_edit.setPlainText("first note content")

    window._controller.new_note()

    assert notes_repo.get(first_id).content_plain == "first note content"
    assert window._controller._current_note_id != first_id


def test_pin_and_favorite_toggle_via_controller(
    qtbot, notes_repo, folders_repo, tags_repo, reminders_repo
):
    window = _make_window(qtbot, notes_repo, folders_repo, tags_repo, reminders_repo)
    window._controller.new_note()
    note_id = window._controller._current_note_id

    window._controller.toggle_pin_current()
    assert notes_repo.get(note_id).is_pinned is True

    window._controller.toggle_favorite_current()
    assert notes_repo.get(note_id).is_favorite is True


def test_trash_view_toggle_disables_normal_mode_actions(
    qtbot, notes_repo, folders_repo, tags_repo, reminders_repo
):
    window = _make_window(qtbot, notes_repo, folders_repo, tags_repo, reminders_repo)

    window._on_trash_selected(True)
    assert all(not action.isEnabled() for action in window._normal_mode_actions)

    window._on_trash_selected(False)
    assert all(action.isEnabled() for action in window._normal_mode_actions)
