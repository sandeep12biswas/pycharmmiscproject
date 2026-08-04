from PySide6.QtGui import QFont, QFontDatabase, QImage, QTextCursor

from app.ui import font_prefs
from app.ui.editor import CHECKBOX_CHECKED, CHECKBOX_UNCHECKED, NoteEditorWidget


def _make_editor(qtbot):
    editor = NoteEditorWidget()
    qtbot.addWidget(editor)
    editor.set_enabled(True)
    return editor


def test_load_does_not_trigger_content_changed(qtbot):
    editor = _make_editor(qtbot)

    with qtbot.assertNotEmitted(editor.contentChanged, wait=200):
        editor.load("Title", "<p>body</p>", [])

    assert editor.title() == "Title"
    assert "body" in editor.html()


def test_typing_triggers_content_changed(qtbot):
    editor = _make_editor(qtbot)

    with qtbot.waitSignal(editor.contentChanged, timeout=1000):
        editor._body_edit.setPlainText("hello")


def test_clear_resets_title_body_and_tags(qtbot):
    editor = _make_editor(qtbot)
    editor.load("Title", "<p>body</p>", [])

    editor.clear()

    assert editor.title() == ""
    assert editor.plain_text() == ""


def test_bold_toolbar_action_applies_formatting(qtbot):
    editor = _make_editor(qtbot)
    editor._body_edit.setPlainText("bold me")
    editor._body_edit.selectAll()

    editor._bold_action.trigger()

    fmt = editor._body_edit.textCursor().charFormat()
    assert fmt.fontWeight() == QFont.Weight.Bold
    assert "<b" in editor.html().lower() or "font-weight" in editor.html().lower()


def test_heading_combo_applies_semantic_heading_level(qtbot):
    editor = _make_editor(qtbot)
    editor._body_edit.setPlainText("Section Title")

    editor._heading_combo.setCurrentIndex(1)  # "Heading 1"

    block_format = editor._body_edit.textCursor().blockFormat()
    assert block_format.headingLevel() == 1


def test_bullet_list_toolbar_action_creates_a_list(qtbot):
    editor = _make_editor(qtbot)
    editor._body_edit.setPlainText("item one")

    for action in editor._toolbar.actions():
        if action.text() == "• List":
            action.trigger()
            break

    assert editor._body_edit.textCursor().currentList() is not None


def test_checklist_insert_and_toggle(qtbot):
    editor = _make_editor(qtbot)

    editor._insert_checklist_item()
    assert editor._body_edit.toPlainText().startswith(CHECKBOX_UNCHECKED)

    block = editor._body_edit.document().firstBlock()
    editor._body_edit._toggle_checkbox(block)
    assert editor._body_edit.toPlainText().startswith(CHECKBOX_CHECKED)


def test_checklist_button_removes_checkbox_when_pressed_again(qtbot):
    editor = _make_editor(qtbot)
    editor._body_edit.setPlainText("Buy milk")

    editor._insert_checklist_item()
    assert editor._body_edit.toPlainText() == f"{CHECKBOX_UNCHECKED} Buy milk"

    cursor = editor._body_edit.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    editor._body_edit.setTextCursor(cursor)

    editor._insert_checklist_item()
    assert editor._body_edit.toPlainText() == "Buy milk"


def test_checklist_button_removes_checked_checkbox_too(qtbot):
    editor = _make_editor(qtbot)
    editor._body_edit.setPlainText("Buy milk")

    editor._insert_checklist_item()
    block = editor._body_edit.document().firstBlock()
    editor._body_edit._toggle_checkbox(block)
    assert editor._body_edit.toPlainText() == f"{CHECKBOX_CHECKED} Buy milk"

    cursor = editor._body_edit.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    editor._body_edit.setTextCursor(cursor)

    editor._insert_checklist_item()
    assert editor._body_edit.toPlainText() == "Buy milk"


def test_insert_image_embeds_base64_data_uri(qtbot):
    editor = _make_editor(qtbot)
    image = QImage(4, 4, QImage.Format.Format_RGB32)
    image.fill(0xFF0000)

    editor.insert_image(image)

    assert "data:image/png;base64," in editor.html()


def test_large_image_is_downscaled(qtbot):
    editor = _make_editor(qtbot)
    image = QImage(editor.MAX_IMAGE_WIDTH * 2, 100, QImage.Format.Format_RGB32)
    image.fill(0x00FF00)

    editor.insert_image(image)

    assert f'width="{editor.MAX_IMAGE_WIDTH}"' in editor.html()


def test_tag_chip_editor_forwards_add_request(qtbot):
    editor = _make_editor(qtbot)

    with qtbot.waitSignal(editor.tagAddRequested, timeout=1000) as blocker:
        editor._tags_widget._input.setText("urgent")
        editor._tags_widget._input.returnPressed.emit()

    assert blocker.args == ["urgent"]


def test_tag_chip_editor_forwards_remove_request(qtbot):
    editor = _make_editor(qtbot)

    with qtbot.waitSignal(editor.tagRemoveRequested, timeout=1000) as blocker:
        editor._tags_widget.tagRemoveRequested.emit(42)

    assert blocker.args == [42]


def test_set_enabled_disables_all_child_widgets(qtbot):
    editor = _make_editor(qtbot)

    editor.set_enabled(False)

    assert not editor._title_edit.isEnabled()
    assert not editor._body_edit.isEnabled()
    assert not editor._toolbar.isEnabled()


def test_editor_applies_remembered_font_on_construction(qtbot, monkeypatch, tmp_path):
    monkeypatch.setattr(font_prefs, "get_settings_path", lambda: tmp_path / "settings.ini")
    remembered = QFontDatabase.families()[0]
    font_prefs.save_font_family(remembered)

    editor = _make_editor(qtbot)

    assert editor._font_combo.currentFont().family() == remembered
    assert editor._body_edit.document().defaultFont().family() == remembered


def test_font_combo_selection_applies_formatting_and_persists(qtbot, monkeypatch, tmp_path):
    monkeypatch.setattr(font_prefs, "get_settings_path", lambda: tmp_path / "settings.ini")

    editor = _make_editor(qtbot)
    editor._body_edit.setPlainText("pick a font")
    editor._body_edit.selectAll()

    families = QFontDatabase.families()
    target = next(f for f in families if f != editor._font_combo.currentFont().family())

    editor._font_combo.setCurrentFont(QFont(target))

    fmt = editor._body_edit.textCursor().charFormat()
    assert fmt.font().family() == target
    assert font_prefs.load_font_family() == target


def test_cursor_position_sync_reflects_font_under_cursor(qtbot, monkeypatch, tmp_path):
    monkeypatch.setattr(font_prefs, "get_settings_path", lambda: tmp_path / "settings.ini")

    editor = _make_editor(qtbot)
    editor._body_edit.setPlainText("mixed fonts")
    editor._body_edit.selectAll()

    families = QFontDatabase.families()
    target = next(f for f in families if f != editor._font_combo.currentFont().family())
    editor._font_combo.setCurrentFont(QFont(target))

    cursor = editor._body_edit.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    editor._body_edit.setTextCursor(cursor)

    assert editor._font_combo.currentFont().family() == target
