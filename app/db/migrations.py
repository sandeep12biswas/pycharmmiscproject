import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
CURRENT_VERSION = 1


def get_user_version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def set_user_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(f"PRAGMA user_version = {version}")


def migrate(conn: sqlite3.Connection) -> None:
    """Bring the database schema up to CURRENT_VERSION using PRAGMA user_version
    to track what has already been applied. Add new `if version < N` steps here
    as the schema evolves; never edit schema.sql retroactively for existing users.
    """
    version = get_user_version(conn)
    if version < 1:
        conn.executescript(SCHEMA_PATH.read_text())
        set_user_version(conn, 1)
    conn.commit()
