import sqlite3
from typing import List

SEARCH_LIMIT = 500


def search_note_ids(conn: sqlite3.Connection, query: str) -> List[int]:
    """Full-text search over notes_fts (title + content_plain), ranked by bm25
    (best match first). Returns [] for a blank query rather than matching
    everything."""
    match_query = _build_match_query(query)
    if not match_query:
        return []
    rows = conn.execute(
        "SELECT rowid FROM notes_fts WHERE notes_fts MATCH ? ORDER BY bm25(notes_fts) LIMIT ?",
        (match_query, SEARCH_LIMIT),
    ).fetchall()
    return [row[0] for row in rows]


def _build_match_query(query: str) -> str:
    """Turn free-typed user text into an FTS5 MATCH expression: each word becomes
    a quoted prefix term (so "wor" matches "word"/"working" as the user types),
    ANDed together via FTS5's implicit space-separated AND. Quoting each token
    also sidesteps FTS5 syntax errors from raw operators/punctuation the user
    might type (e.g. "AND", "-", "*")."""
    tokens = query.strip().split()
    terms = ['"{}"*'.format(token.replace('"', '""')) for token in tokens]
    return " ".join(terms)
