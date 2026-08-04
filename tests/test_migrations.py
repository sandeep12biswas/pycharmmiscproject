import sqlite3

from app.db.migrations import CURRENT_VERSION, get_user_version, migrate


def _bare_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def test_fresh_database_lands_on_current_version():
    conn = _bare_connection()

    migrate(conn)

    assert get_user_version(conn) == CURRENT_VERSION
    # note_tiles and notes.is_canvas exist on a brand new install too, not
    # just via the incremental v1->v2 step.
    conn.execute("INSERT INTO notes (title) VALUES ('n')")
    conn.execute("SELECT is_canvas FROM notes")
    conn.execute("SELECT * FROM note_tiles")


def test_migrate_is_idempotent_when_rerun():
    conn = _bare_connection()

    migrate(conn)
    migrate(conn)  # must not raise (duplicate column / table errors)

    assert get_user_version(conn) == CURRENT_VERSION


def test_v1_database_upgrades_to_v2_without_losing_data():
    """Simulates a database that was already migrated under the old
    CURRENT_VERSION = 1 (before SCRUM-10), then reopened with the new code."""
    conn = _bare_connection()
    from app.db.migrations import SCHEMA_PATH

    conn.executescript(SCHEMA_PATH.read_text())
    conn.execute("PRAGMA user_version = 1")
    conn.execute("INSERT INTO notes (title, content_html) VALUES ('Existing note', '<p>hi</p>')")
    conn.commit()

    migrate(conn)

    assert get_user_version(conn) == 2
    row = conn.execute("SELECT title, content_html, is_canvas FROM notes").fetchone()
    assert row["title"] == "Existing note"
    assert row["content_html"] == "<p>hi</p>"
    assert row["is_canvas"] == 0  # existing notes default to non-canvas, untouched
