import base64
from typing import List

from PySide6.QtCore import QBuffer, QIODevice, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QFont,
    QImage,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextListFormat,
)
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLineEdit,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.models.tag import Tag
from app.ui.tags_widget import TagChipEditor

CHECKBOX_UNCHECKED = "☐"  # ☐
CHECKBOX_CHECKED = "☑"  # ☑


class NoteTextEdit(QTextEdit):
    """QTextEdit that turns a click on a leading checkbox glyph into a toggle,
    giving checklists without a custom QTextObjectInterface implementation."""

    def mousePressEvent(self, event) -> None:
        cursor = self.cursorForPosition(event.pos())
        block = cursor.block()
        text = block.text()
        if text[:1] in (CHECKBOX_UNCHECKED, CHECKBOX_CHECKED):
            offset_in_block = cursor.position() - block.position()
            if offset_in_block <= 1:
                self._toggle_checkbox(block)
                return
        super().mousePressEvent(event)

    def _toggle_checkbox(self, block) -> None:
        new_char = CHECKBOX_CHECKED if block.text()[0] == CHECKBOX_UNCHECKED else CHECKBOX_UNCHECKED
        toggle_cursor = QTextCursor(block)
        toggle_cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        toggle_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
        toggle_cursor.insertText(new_char)


class NoteEditorWidget(QWidget):
    """Rich-text note editor: title field + formatting toolbar + body editor."""

    contentChanged = Signal()
    tagAddRequested = Signal(str)  # tag name typed by the user
    tagRemoveRequested = Signal(int)  # tag_id

    HEADING_LEVELS = ["Normal", "Heading 1", "Heading 2", "Heading 3"]
    HEADING_SIZES = {0: None, 1: 22, 2: 18, 3: 15}
    MAX_IMAGE_WIDTH = 480  # downscale large photos so base64 blobs stay reasonably sized in SQLite

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loading = False

        self._title_edit = QLineEdit(self)
        self._title_edit.setPlaceholderText("Title")

        self._body_edit = NoteTextEdit(self)

        self._tags_widget = TagChipEditor(self)
        self._tags_widget.tagAddRequested.connect(self.tagAddRequested)
        self._tags_widget.tagRemoveRequested.connect(self.tagRemoveRequested)

        self._toolbar = self._build_toolbar()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._title_edit)
        layout.addWidget(self._tags_widget)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._body_edit)

        self._title_edit.textChanged.connect(self._emit_changed)
        self._body_edit.textChanged.connect(self._emit_changed)
        self._body_edit.currentCharFormatChanged.connect(self._sync_toolbar_from_format)
        self._body_edit.cursorPositionChanged.connect(self._sync_toolbar_from_cursor)

    def _build_toolbar(self) -> QToolBar:
        toolbar = QToolBar(self)

        self._bold_action = QAction("B", self)
        self._bold_action.setCheckable(True)
        self._bold_action.triggered.connect(self._toggle_bold)
        toolbar.addAction(self._bold_action)

        self._italic_action = QAction("I", self)
        self._italic_action.setCheckable(True)
        self._italic_action.triggered.connect(self._toggle_italic)
        toolbar.addAction(self._italic_action)

        self._underline_action = QAction("U", self)
        self._underline_action.setCheckable(True)
        self._underline_action.triggered.connect(self._toggle_underline)
        toolbar.addAction(self._underline_action)

        self._strike_action = QAction("S", self)
        self._strike_action.setCheckable(True)
        self._strike_action.triggered.connect(self._toggle_strikethrough)
        toolbar.addAction(self._strike_action)

        toolbar.addSeparator()

        self._heading_combo = QComboBox(self)
        self._heading_combo.addItems(self.HEADING_LEVELS)
        self._heading_combo.currentIndexChanged.connect(self._apply_heading)
        toolbar.addWidget(self._heading_combo)

        toolbar.addSeparator()

        bullet_action = QAction("• List", self)
        bullet_action.triggered.connect(lambda: self._toggle_list(QTextListFormat.Style.ListDisc))
        toolbar.addAction(bullet_action)

        numbered_action = QAction("1. List", self)
        numbered_action.triggered.connect(lambda: self._toggle_list(QTextListFormat.Style.ListDecimal))
        toolbar.addAction(numbered_action)

        checklist_action = QAction(f"{CHECKBOX_UNCHECKED} Check", self)
        checklist_action.triggered.connect(self._insert_checklist_item)
        toolbar.addAction(checklist_action)

        toolbar.addSeparator()

        image_action = QAction("Insert Image", self)
        image_action.triggered.connect(self._insert_image)
        toolbar.addAction(image_action)

        return toolbar

    # -- character formatting --------------------------------------------------

    def _merge_format(self, fmt: QTextCharFormat) -> None:
        cursor = self._body_edit.textCursor()
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        self._body_edit.mergeCurrentCharFormat(fmt)

    def _toggle_bold(self, checked: bool) -> None:
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal)
        self._merge_format(fmt)

    def _toggle_italic(self, checked: bool) -> None:
        fmt = QTextCharFormat()
        fmt.setFontItalic(checked)
        self._merge_format(fmt)

    def _toggle_underline(self, checked: bool) -> None:
        fmt = QTextCharFormat()
        fmt.setFontUnderline(checked)
        self._merge_format(fmt)

    def _toggle_strikethrough(self, checked: bool) -> None:
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(checked)
        self._merge_format(fmt)

    def _sync_toolbar_from_cursor(self) -> None:
        self._sync_toolbar_from_format(self._body_edit.currentCharFormat())

    def _sync_toolbar_from_format(self, fmt: QTextCharFormat) -> None:
        for action, is_active in (
            (self._bold_action, fmt.fontWeight() == QFont.Weight.Bold),
            (self._italic_action, fmt.fontItalic()),
            (self._underline_action, fmt.fontUnderline()),
            (self._strike_action, fmt.fontStrikeOut()),
        ):
            action.blockSignals(True)
            action.setChecked(is_active)
            action.blockSignals(False)

    # -- block formatting (headings) --------------------------------------------

    def _apply_heading(self, level: int) -> None:
        cursor = self._body_edit.textCursor()
        cursor.beginEditBlock()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)

        block_fmt = QTextBlockFormat()
        block_fmt.setHeadingLevel(level)
        cursor.mergeBlockFormat(block_fmt)

        char_fmt = QTextCharFormat()
        char_fmt.setFontWeight(QFont.Weight.Bold if level else QFont.Weight.Normal)
        char_fmt.setFontPointSize(self.HEADING_SIZES.get(level) or self.font().pointSize())
        cursor.mergeCharFormat(char_fmt)

        cursor.endEditBlock()

    # -- lists --------------------------------------------------------------

    def _toggle_list(self, style: QTextListFormat.Style) -> None:
        cursor = self._body_edit.textCursor()
        cursor.beginEditBlock()
        current_list = cursor.currentList()
        if current_list is not None and current_list.format().style() == style:
            current_list.remove(cursor.block())
            block_fmt = cursor.blockFormat()
            block_fmt.setIndent(0)
            cursor.mergeBlockFormat(block_fmt)
        else:
            list_fmt = current_list.format() if current_list else QTextListFormat()
            list_fmt.setStyle(style)
            cursor.createList(list_fmt)
        cursor.endEditBlock()

    def _insert_checklist_item(self) -> None:
        cursor = self._body_edit.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        if not cursor.block().text().startswith((CHECKBOX_UNCHECKED, CHECKBOX_CHECKED)):
            cursor.insertText(f"{CHECKBOX_UNCHECKED} ")
        cursor.endEditBlock()

    # -- images ---------------------------------------------------------------

    def _insert_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Insert Image", "", "Images (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if not file_path:
            return
        image = QImage(file_path)
        if image.isNull():
            return
        self.insert_image(image)

    def insert_image(self, image: QImage) -> None:
        """Embed an image as a base64 PNG data URI directly in the note's HTML,
        so the note stays a single self-contained blob (no attachments table
        in v1, per the plan)."""
        if image.width() > self.MAX_IMAGE_WIDTH:
            image = image.scaledToWidth(self.MAX_IMAGE_WIDTH, Qt.TransformationMode.SmoothTransformation)

        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        b64 = base64.b64encode(bytes(buffer.data())).decode("ascii")
        data_uri = f"data:image/png;base64,{b64}"

        cursor = self._body_edit.textCursor()
        cursor.insertHtml(f'<img src="{data_uri}" width="{image.width()}" height="{image.height()}" />')

    # -- signals / lifecycle --------------------------------------------------

    def _emit_changed(self) -> None:
        if not self._loading:
            self.contentChanged.emit()

    def load(self, title: str, content_html: str, tags: List[Tag] = ()) -> None:
        """Load a note into the editor. Signals are suppressed for the duration
        (via self._loading) so programmatic loading never triggers autosave."""
        self._loading = True
        self._title_edit.setText(title)
        self._body_edit.setHtml(content_html)
        self._tags_widget.set_tags(list(tags))
        self._loading = False

    def clear(self) -> None:
        self.load("", "", [])

    def set_tags(self, tags: List[Tag]) -> None:
        self._tags_widget.set_tags(tags)

    def set_available_tag_names(self, names: List[str]) -> None:
        self._tags_widget.set_available_tag_names(names)

    def title(self) -> str:
        return self._title_edit.text()

    def html(self) -> str:
        return self._body_edit.toHtml()

    def plain_text(self) -> str:
        return self._body_edit.toPlainText()

    def set_enabled(self, enabled: bool) -> None:
        self._title_edit.setEnabled(enabled)
        self._body_edit.setEnabled(enabled)
        self._toolbar.setEnabled(enabled)
        self._tags_widget.set_enabled(enabled)
