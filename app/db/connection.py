import sqlite3
from pathlib import Path
from typing import Optional, Union

from app.config import get_db_path
from app.db.migrations import migrate


def get_connection(db_path: Optional[Union[Path, str]] = None) -> sqlite3.Connection:
    path = str(db_path) if db_path is not None else str(get_db_path())
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def open_database(db_path: Optional[Union[Path, str]] = None) -> sqlite3.Connection:
    """Open a connection and ensure the schema is migrated to the latest version."""
    conn = get_connection(db_path)
    migrate(conn)
    return conn
