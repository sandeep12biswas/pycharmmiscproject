# NoteApp

A single-user, offline-first desktop note-taking app with rich text editing, folders, tags,
full-text search, reminders, and export to Markdown/PDF — built with **PySide6** (Qt for Python)
and a local **SQLite** database (no ORM, no cloud sync).

## Features

- **Rich text editing** — bold, italic, underline, strikethrough, headings, bullet/numbered
  lists, checklists, and inline embedded images.
- **Autosave** — debounced, no explicit "Save" button; content is flushed on note switch and app
  close so nothing is lost.
- **Organization** — nested folders plus cross-cutting tags; move notes between folders and
  add/remove tags without losing content.
- **Full-text search** — live, debounced, relevance-ranked (SQLite FTS5), combinable with
  folder/tag filters.
- **Pin & favorites** — pin notes to the top of a list; a dedicated Favorites view.
- **Trash** — soft delete with restore, or permanent delete.
- **Export** — export any note to Markdown (`.md`) or PDF (`.pdf`) with formatting preserved.
- **Reminders** — attach a date/time reminder to a note; a system tray notification fires while
  the app is running (no OS-level scheduling — see [Limitations](#limitations)).
- **Light/dark theme**, persisted across restarts.
- **Fully offline** — no network access anywhere in the app.

## Requirements

- Python 3.10+
- Linux (primary target/dev environment); a Windows installer is also provided (see
  [Packaging](#packaging)). macOS is not currently packaged.

## Getting started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python main.py
```

The SQLite database is created automatically on first launch in the OS-standard per-user
app-data directory (on Linux: `~/.local/share/NoteApp/notes.db`), not next to the executable —
this keeps packaged/installed builds working correctly.

## Running the tests

```bash
source .venv/bin/activate
QT_QPA_PLATFORM=offscreen pytest
```

`QT_QPA_PLATFORM=offscreen` is required for any Qt code path (including plain repository tests)
when there's no display server available, since UI test fixtures live in the same process.

Run a single file or test:

```bash
QT_QPA_PLATFORM=offscreen pytest tests/test_notes_repo.py
QT_QPA_PLATFORM=offscreen pytest tests/test_notes_repo.py::test_create_and_get -v
```

The suite (170+ tests) covers the repository/data-access layer headlessly, plus `pytest-qt`
smoke tests for the UI, and a static architecture-boundary check (see below).

## Packaging

### Linux — standalone build

```bash
pyinstaller packaging/noteapp.spec   # must be run from the repo root
```

Output: `dist/NoteApp/NoteApp` (+ `dist/NoteApp/_internal/`).

### Linux — `.deb` package

```bash
packaging/build_deb.sh [version]     # defaults to 1.0.0; runs PyInstaller itself
```

Output: `dist/noteapp_<version>_<arch>.deb`.

### Windows — installer

`packaging/windows/noteapp.iss` (Inno Setup) must be compiled on a Windows machine — it can't be
built from this Linux dev environment. See the comment header in that file for exact steps.

### App icons

The icon set under `resources/icons/` is generated, not hand-drawn. Regenerate it only if the
design changes (requires Pillow + numpy):

```bash
python packaging/gen_icon.py
```

## Architecture

Strict layering is enforced at test time — `tests/test_architecture_boundaries.py` statically
AST-scans imports and fails the build on violations:

- `app/repositories/` and `app/models/` never import PySide6.
- `app/ui/` and `app/controllers/` never import `sqlite3` directly — UI talks only to
  repositories.
- No network modules anywhere in `app/` (`socket`, `urllib`, `requests`,
  `PySide6.QtNetwork`, etc. are all banned) — the app is fully offline.

```
app/ui/            QWidget subclasses only — emit signals, never touch sqlite3
app/controllers/    NoteController: mediates ui/ <-> repositories/, owns autosave debounce
app/repositories/   One class per table-ish concern; raw SQL, returns app/models/ dataclasses
app/models/         Plain dataclasses (Note, Folder, Tag, Reminder) + from_row()
app/db/             connection.py (WAL + foreign_keys pragmas), migrations.py
                    (PRAGMA user_version), schema.sql (folders, notes, tags, note_tags,
                    reminders, notes_fts FTS5 + triggers)
app/search/         fts.py: builds safe quoted/prefixed FTS5 MATCH queries, bm25-ranked
app/export/         markdown_export.py, pdf_export.py (via QTextDocument/QPrinter)
app/reminders/      scheduler.py: QTimer-polling ReminderScheduler (45s interval), in-process only
app/config.py       QStandardPaths-based app-data dir, DB path, RESOURCES_DIR (frozen-build-aware)
app/logging_config.py  configure_logging()/install_excepthook(); stdlib-only so it's safe to use
                        from repositories/ and models/ too
```

`main.py` opens a single `sqlite3.Connection`, constructs one instance of each repository
(`NotesRepository`, `FoldersRepository`, `TagsRepository`, `RemindersRepository`), and passes
them into `MainWindow`. `MainWindow` wires UI widgets to `NoteController`, the only component
that writes note content to the database.

## Logging

`main.py` calls `configure_logging()` once at startup, before anything else runs. Every module
gets its own logger via the standard `logger = logging.getLogger(__name__)` pattern and logs
through it — no other module touches handlers directly.

- **Destination**: a rotating log file at `<app-data-dir>/logs/noteapp.log` (2 MB × 3 backups),
  plus a console (stderr) handler for `python main.py` runs.
  On Linux that's `~/.local/share/NoteApp/logs/noteapp.log`.
- **Level**: `INFO` by default — lifecycle events (DB open/migration, note trash/restore/delete,
  reminders firing, exports, window close) are logged at `INFO`; frequent/low-signal events
  (autosave writes, pin/tag toggles) are logged at `DEBUG` and stay quiet unless you raise the
  level.
- **Crashes**: `install_excepthook()` routes any uncaught exception into the log at `CRITICAL`
  (with traceback) before falling through to the default handler, so a crash is never silent —
  it's recorded even if no one was watching the console (ties to NFR-2, data integrity).

## Limitations (v1)

- No cloud sync, multi-device sync, or accounts.
- No real-time collaboration or multi-user editing.
- Reminders only fire while the app is running (in-app `QTimer` polling, no OS-level scheduler)
  — a deliberate v1 scope decision, not a bug.
- No mobile or web clients.
- Only inline images are supported as attachments (no other file/audio attachment types).
- No version history / undo beyond the current session.

## Project documentation

- `requirements.md` — full functional/non-functional spec (FR-1..FR-25, NFR-1..NFR-6).
- `PROGRESS.md` — authoritative build log and key design decisions (autosave, theming, filtering,
  DB path, PyInstaller bundling) with the reasoning/bugs behind them.
- `tasklist.md` — original phased task breakdown (v1 is complete).
- `CLAUDE.md` — guidance for AI-assisted development on this codebase.

## License

No license file is currently included; all rights reserved by default.