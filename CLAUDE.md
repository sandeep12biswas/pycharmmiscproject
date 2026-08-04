# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-user, offline-first desktop note-taking app (PySide6 + SQLite, no ORM, no cloud sync).
Full functional/non-functional spec is in `requirements.md` (FR-1..FR-25, NFR-1..NFR-6) — read it
before adding a feature, since most "should this do X" questions are already answered there.
`PROGRESS.md` is the authoritative build log: it has a "Key design decisions already made (don't
redecide these)" section that documents non-obvious choices and the reasoning/bugs behind them —
check it before changing autosave, theming, filtering, DB-path, or PyInstaller-bundling behavior.
`tasklist.md` has the original phased task breakdown (all 24 tasks are complete; v1 is done).

## Commands

```bash
source .venv/bin/activate

# Run the app
python main.py

# Run the full test suite (170+ tests, headless-safe)
QT_QPA_PLATFORM=offscreen pytest

# Run a single test file / test
QT_QPA_PLATFORM=offscreen pytest tests/test_notes_repo.py
QT_QPA_PLATFORM=offscreen pytest tests/test_notes_repo.py::test_create_and_get -v

# Package as a standalone executable (PyInstaller, onedir build)
pyinstaller packaging/noteapp.spec        # must run from repo root, not from packaging/
# output: dist/NoteApp/NoteApp (+ dist/NoteApp/_internal/)

# Build a .deb (Linux) — runs PyInstaller itself, no need to run it first
packaging/build_deb.sh [version]          # defaults to 1.0.0 -> dist/noteapp_<version>_<arch>.deb

# Regenerate the app icon set (only needed if the design changes)
python packaging/gen_icon.py              # needs Pillow + numpy; writes resources/icons/*
```

There's no `pytest.ini`/`pyproject.toml` — pytest runs with defaults from the repo root.
`QT_QPA_PLATFORM=offscreen` is required for any Qt code path (including plain repository tests,
since `conftest.py`'s fixtures live in the same process as pytest-qt) when there's no display.

Windows installer (`packaging/windows/noteapp.iss`, Inno Setup) must be built on Windows — see the
comment header in that file for the exact steps; it can't be compiled from this Linux dev box.

## Architecture

Strict layering, and it's not just convention — `tests/test_architecture_boundaries.py` statically
AST-scans imports and fails the build if it's violated:

- **`app/repositories/` and `app/models/` never import PySide6.** Repositories take a raw
  `sqlite3.Connection` and return dataclasses; no ORM.
- **`app/ui/` and `app/controllers/` never import `sqlite3` directly.** UI code only talks to
  repositories.
- **No network modules anywhere in `app/`** (`socket`, `urllib`, `requests`, `PySide6.QtNetwork`,
  etc. are all banned) — enforces NFR-4 (fully offline).

Data flow: `main.py` opens one `sqlite3.Connection` (`app/db/connection.py`), constructs one
instance of each repository (`NotesRepository`, `FoldersRepository`, `TagsRepository`,
`RemindersRepository`), and passes them into `MainWindow`. `MainWindow` wires UI widgets to
`NoteController`, which is the only thing that writes note content to the DB — UI signal handlers
never call the repository directly for note content (see autosave note below).

Layers, top to bottom:

```
app/ui/            QWidget subclasses only — emit signals, never touch sqlite3
app/controllers/    NoteController: mediates ui/ <-> repositories/, owns autosave debounce
app/repositories/   One class per table-ish concern; raw SQL, returns app/models/ dataclasses
app/models/         Plain dataclasses (Note, Folder, Tag, Reminder) + from_row()
app/db/             connection.py (WAL + foreign_keys pragmas), migrations.py (PRAGMA user_version),
                    schema.sql (folders, notes, tags, note_tags, reminders, notes_fts FTS5 + triggers)
app/search/         fts.py: builds safe quoted/prefixed FTS5 MATCH queries, bm25-ranked
app/export/         markdown_export.py, pdf_export.py (via QTextDocument/QPrinter)
app/reminders/      scheduler.py: QTimer-polling ReminderScheduler (45s interval), in-process only
app/config.py       QStandardPaths-based app-data dir, DB path, RESOURCES_DIR (frozen-build-aware)
```

Non-obvious behaviors worth knowing before touching related code (full detail + the bugs that
motivated them is in `PROGRESS.md`'s design-decisions section):

- **Autosave**: `NoteController` debounces writes via a single-shot `QTimer`
  (`AUTOSAVE_DEBOUNCE_MS = 1500`). `flush_pending()` is the only method that actually writes to the
  repo, and is called by the timer, on note switch, on `new_note()`, and from
  `MainWindow.closeEvent`. Tags and pin/favorite toggles bypass the debounce and persist
  immediately (they're not part of `content_html`).
  `content_html` (`QTextDocument.toHtml()`) is authoritative; `content_plain` is a denormalized
  cache kept only for FTS5.
- **Filtering**: `NotesRepository.list_all(folder_id, tag_id, search_text, favorites_only)` is one
  method, one query, ANDing whichever filters are non-`None`. Trash is a separate listing
  (`list_trashed()`), not another AND-able filter. Favorites/Trash are mutually-exclusive sidebar
  "smart views" living in the same `QTreeView` as real folders, keyed by sentinel strings
  (`FAVORITES_KEY`, `TRASH_KEY`) rather than a real `folder_id`.
- **DB path**: `QStandardPaths.AppDataLocation` → `~/.local/share/NoteApp/notes.db`. Only
  `QCoreApplication.applicationName()` is set (not `organizationName`); it's re-asserted on every
  `get_app_data_dir()` call rather than once at import, because Qt/pytest-qt can silently reset it
  mid-process.
- **Checklists** are not a native Qt list type — a `☐ `/`☑ ` glyph prefix on a line, toggled via an
  overridden `mousePressEvent`.
- **Images** are embedded as downscaled (max width 480px) base64 PNG `data:` URIs directly in
  `content_html` — no attachments table.
- **PyInstaller data files**: anything read via `Path(__file__).parent / "..."` at runtime (e.g.
  `schema.sql`) needs an explicit entry in `packaging/noteapp.spec`'s `datas` — PyInstaller only
  auto-bundles `.py` sources into the PYZ archive, not plain data files, and this fails silently at
  build time (only breaks at runtime).
- **Reminders only fire while the app is running** (`QTimer` polling, no OS-level scheduling) — an
  accepted v1 limitation, not a bug to silently "fix" by adding a scheduling dependency.

## Testing conventions

- `tests/conftest.py`'s `conn` fixture is a fresh in-memory (`:memory:`) DB with the full schema
  applied per test, via the real `open_database()` path — not hand-rolled SQL setup.
- UI tests (`tests/ui/`) use `pytest-qt`'s `qtbot` and must run with `QT_QPA_PLATFORM=offscreen`.
  Prefer driving real widgets (e.g. `sidebar._tree.setCurrentIndex(...)`) over calling
  controller/model methods directly underneath a stateful widget — bypassing the widget can produce
  failures that don't reflect real user interaction (see `PROGRESS.md` for a concrete example with
  `TagFilterWidget`).
- To let a debounce/polling `QTimer` actually elapse in a test, use `QTest.qWait(ms)`, not
  `app.processEvents()`.
- `QMenu.exec()` cannot be monkeypatched on the class; to intercept a context menu in a test,
  reassign `QMenu` in the *target module's* namespace to a fake subclass instead.
- Modal dialogs (`ReminderDialog`, `QFileDialog`) can't be driven by waiting on `.exec()` to return
  in a script — monkeypatch the blocking static/instance method to return the desired result
  directly, restoring it in a `finally` block.
- No PDF-parsing library is installed; PDF export is verified structurally (`%PDF-` header,
  `%%EOF` trailer, non-trivial size), not by extracting rendered text. Don't add such a dependency
  without asking first.
