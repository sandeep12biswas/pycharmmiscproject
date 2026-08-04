"""Central logging setup for the whole app.

`configure_logging()` is called exactly once, from `main.py`, before anything
else logs. Every other module just does `logger = logging.getLogger(__name__)`
at import time and logs through it -- no per-module handler setup, so the
format/destination/rotation policy lives in exactly one place.

Deliberately stdlib-only (no PySide6, no app.config import) so this module
stays safe to import from app/repositories/ and app/models/, which
tests/test_architecture_boundaries.py forbids from importing PySide6
directly -- the caller resolves the log directory (via
app.config.get_app_data_dir()) and passes it in.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
LOG_FILENAME = "noteapp.log"
MAX_BYTES = 2 * 1024 * 1024  # 2 MB per file
BACKUP_COUNT = 3

_configured = False


def configure_logging(log_dir: Path, level: int = logging.INFO) -> None:
    """Attach a rotating file handler (log_dir/noteapp.log) and a console
    handler to the root logger. Idempotent -- a second call is a no-op, so
    it's safe even if something ends up importing/running main() more than
    once in the same process."""
    global _configured
    if _configured:
        return
    _configured = True

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / LOG_FILENAME
    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        log_file, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    logging.getLogger(__name__).info("Logging configured (level=%s, file=%s)", logging.getLevelName(level), log_file)


def install_excepthook() -> None:
    """Log uncaught exceptions before they hit the default handler, so a
    crash is still captured in the log file (ties to NFR-2: no silent data
    loss) instead of only ever appearing on a console the user isn't
    watching. Falls back to the previous hook afterwards so behavior
    (traceback on stderr, process exit) is unchanged."""
    logger = logging.getLogger("app.uncaught")
    previous_hook = sys.excepthook

    def _hook(exc_type, exc_value, exc_tb):
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))
        previous_hook(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook
