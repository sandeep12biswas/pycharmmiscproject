import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
CURRENT_VERSION = 2

# v1 -> v2 (SCRUM-10): canvas tiling is a per-note opt-in mode, not a new note
# type -- existing notes and their single content_html are untouched. Kept as
# inline SQL here rather than folded into schema.sql, per the migrate()
# docstring below: schema.sql is the fresh-install baseline for version 1,
# and already-migrated (version >= 1) databases only ever move forward via
# incremental steps like this one.
_MIGRATION_V2_SQL = """
ALTER TABLE notes ADD COLUMN is_canvas INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS note_tiles (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id       INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    x             REAL NOT NULL DEFAULT 0,
    y             REAL NOT NULL DEFAULT 0,
    width         REAL NOT NULL DEFAULT 150,
    height        REAL NOT NULL DEFAULT 100,
    z_index       INTEGER NOT NULL DEFAULT 0,
    title         TEXT NOT NULL DEFAULT '',
    content_html  TEXT NOT NULL DEFAULT '',
    content_plain TEXT NOT NULL DEFAULT '',
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_note_tiles_note ON note_tiles(note_id);
"""


def get_user_version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def set_user_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(f"PRAGMA user_version = {version}")


def migrate(conn: sqlite3.Connection) -> None:
    """Bring the database schema up to CURRENT_VERSION using PRAGMA user_version
    to track what has already been applied. Add new `if version < N` steps here
    as the schema evolves; never edit schema.sql retroactively for existing users.
    `version` is reassigned after each step (rather than re-read from the DB) so
    a fresh install runs every step in this same call without re-querying.
    """
    version = get_user_version(conn)
    if version < 1:
        logger.info("Applying schema migration: user_version %s -> 1", version)
        conn.executescript(SCHEMA_PATH.read_text())
        set_user_version(conn, 1)
        version = 1
    if version < 2:
        logger.info("Applying schema migration: user_version %s -> 2", version)
        conn.executescript(_MIGRATION_V2_SQL)
        set_user_version(conn, 2)
        version = 2
    conn.commit()
