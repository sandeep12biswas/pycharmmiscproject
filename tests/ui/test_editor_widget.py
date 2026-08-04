from PySide6.QtGui import QColor, QFont, QFontDatabase, QImage, QTextCursor

from app.ui import font_prefs
from app.ui import editor as editor_module
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


def test_font_color_action_applies_to_selection_and_persists_in_html(qtbot, monkeypatch):
    monkeypatch.setattr(editor_module.QColorDialog, "getColor", lambda *a, **k: QColor("#ff0000"))

    editor = _make_editor(qtbot)
    editor._body_edit.setPlainText("colour me")
    editor._body_edit.selectAll()

    editor._font_color_action.trigger()

    fmt = editor._body_edit.textCursor().charFormat()
    assert fmt.foreground().color() == QColor("#ff0000")
    assert "#ff0000" in editor.html().lower()


def test_font_color_applies_before_typing(qtbot, monkeypatch):
    """A colour picked with no selection (an empty cursor) should apply to
    text typed afterwards -- covers the "select a colour before typing"
    acceptance criterion."""
    monkeypatch.setattr(editor_module.QColorDialog, "getColor", lambda *a, **k: QColor("#00ff00"))

    editor = _make_editor(qtbot)

    editor._font_color_action.trigger()
    editor._body_edit.setPlainText("green text")

    fmt = editor._body_edit.textCursor().charFormat()
    assert fmt.foreground().color() == QColor("#00ff00")


def test_font_color_cancelled_dialog_leaves_format_unchanged(qtbot, monkeypatch):
    monkeypatch.setattr(editor_module.QColorDialog, "getColor", lambda *a, **k: QColor())  # invalid == cancelled

    editor = _make_editor(qtbot)
    editor._body_edit.setPlainText("unchanged")
    editor._body_edit.selectAll()

    editor._font_color_action.trigger()

    fmt = editor._body_edit.textCursor().charFormat()
    assert fmt.foreground().style().name == "NoBrush"


def test_font_color_round_trips_through_load(qtbot):
    """A note re-opened after being saved with an explicit font colour
    (content_html is the authoritative store) keeps that colour."""
    editor = _make_editor(qtbot)

    editor.load("Title", '<p><span style="color:#0000ff;">blue text</span></p>', [])

    cursor = editor._body_edit.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
    fmt = cursor.charFormat()
    assert fmt.foreground().color() == QColor("#0000ff")


def test_font_color_swatch_icon_updates_after_pick(qtbot, monkeypatch):
    monkeypatch.setattr(editor_module.QColorDialog, "getColor", lambda *a, **k: QColor("#123456"))

    editor = _make_editor(qtbot)
    editor._body_edit.setPlainText("swatch")
    editor._body_edit.selectAll()

    editor._font_color_action.trigger()

    assert not editor._font_color_action.icon().isNull()
