import html
import logging
from pathlib import Path
from typing import Union

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter

logger = logging.getLogger(__name__)


def export_pdf(title: str, content_html: str, file_path: Union[str, Path]) -> None:
    """Render a note to PDF via QTextDocument + QPrinter, preserving the rich
    formatting already baked into content_html (bold/italic/lists/checklists/
    inline images)."""
    document = QTextDocument()
    heading = html.escape(title or "Untitled")
    document.setHtml(f"<h1>{heading}</h1>{content_html}")

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(file_path))
    document.print_(printer)
    logger.info("Exported note %r to PDF: %s", title, file_path)
