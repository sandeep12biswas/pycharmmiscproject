import logging
from pathlib import Path
from typing import Union

from PySide6.QtGui import QTextDocument

logger = logging.getLogger(__name__)


def note_to_markdown(title: str, content_html: str) -> str:
    """Render a note to Markdown via QTextDocument.toMarkdown(). The title lives
    in a separate field from content_html, so it's prepended here as the
    level-1 heading rather than assumed to already be in the body."""
    document = QTextDocument()
    document.setHtml(content_html)
    body = document.toMarkdown().strip()
    heading = f"# {title or 'Untitled'}"
    return f"{heading}\n\n{body}\n" if body else f"{heading}\n"


def export_markdown(title: str, content_html: str, file_path: Union[str, Path]) -> None:
    Path(file_path).write_text(note_to_markdown(title, content_html), encoding="utf-8")
    logger.info("Exported note %r to Markdown: %s", title, file_path)
