# Task List: Desktop Note-Taking App Implementation

Derived from `requirements.md` and the approved implementation plan. Tasks are grouped by build
phase and listed in the order they should be executed. Each task notes the Functional/Non-Functional
Requirements (FR/NFR) it satisfies.

## Phase 1 — Skeleton (DB + basic CRUD)

- [ ] **1. Scaffold project structure and dependencies**
  Create the `app/` package layout (`db`, `models`, `repositories`, `search`, `export`, `reminders`,
  `controllers`, `ui`), `resources/` folder, `tests/` folder. Add `requirements.txt`
  (`PySide6>=6.11,<6.12`, `pytest>=8.0`, `pytest-qt>=4.4`, `pyinstaller>=6.10`). Install deps into
  the existing `.venv`. Replace `main.py` boilerplate with a real `QApplication` entry point stub.

- [ ] **2. Implement SQLite schema, connection, and migrations**
  Create `app/db/schema.sql` with `folders`, `notes`, `tags`, `note_tags`, `reminders` tables and
  the `notes_fts` FTS5 virtual table + sync triggers. Create `app/db/connection.py`
  (`get_connection` with WAL + foreign_keys pragmas, DB path via `QStandardPaths` app-data dir per
  NFR-3). Create `app/db/migrations.py` using `PRAGMA user_version`.

- [ ] **3. Implement Note model and NotesRepository CRUD**
  Create `app/models/note.py` dataclass. Create `app/repositories/notes_repo.py` with
  create/read/update/delete/list_all, soft-delete (`is_trashed`) and restore/permanent-delete.
  *(FR-1, FR-2, FR-3, FR-5)*

- [ ] **4. Build MainWindow skeleton with note list and plain editor**
  Create `app/ui/main_window.py` (`QMainWindow` + `QSplitter`), `app/ui/note_list.py`
  (`QListView` + `QAbstractListModel` backed by `NotesRepository`), plain `QTextEdit` editor
  placeholder, sidebar placeholder panel. Wire New Note / Delete Note actions and note selection to
  load/save via `NotesRepository` through a thin controller (`app/controllers/note_controller.py`).

- [ ] **5. Verify Phase 1 milestone: CRUD persists across restart**
  Manually run the app, create/edit/delete notes, restart, confirm state via `sqlite3` CLI against
  the DB file.

## Phase 2 — Rich editor + autosave

- [ ] **6. Build rich text formatting toolbar**
  Extend `app/ui/editor.py`: `QTextEdit` subclass with a toolbar for bold/italic/underline/
  strikethrough, headings, bullet lists, numbered lists, and checklists, acting via
  `QTextCursor`/`QTextCharFormat`/`QTextListFormat`. *(FR-6, FR-7)*

- [ ] **7. Add inline image embedding to editor**
  Support inserting images into the `QTextDocument`, embedded as base64 data URIs within the saved
  HTML (no attachments table in v1). *(FR-8)*

- [ ] **8. Implement HTML persistence and debounced autosave**
  Persist `content_html` (`QTextDocument.toHtml()`) and `content_plain` (`toPlainText()`, for FTS)
  to the `notes` table. Debounce autosave via `QTimer` on `contentsChanged` (1-2s idle), plus flush
  on note switch and on `MainWindow.closeEvent`. Block signals during `setHtml()` on note load to
  avoid spurious dirty state. *(FR-4, FR-9, NFR-2)*

- [ ] **9. Verify Phase 2 milestone: rich formatting round-trips**
  Manually verify bold/italic/lists/checklists/images survive save + app restart without corruption.

## Phase 3 — Organization + search

- [ ] **10. Implement FoldersRepository and sidebar folder tree UI**
  Create `app/repositories/folders_repo.py` (CRUD, nested tree fetch, `ON DELETE CASCADE` for
  sub-folders, notes unfiled via `ON DELETE SET NULL`). Create `app/ui/sidebar.py`
  (`QTreeView` + `QStandardItemModel`) supporting create/rename/delete/move/nest folders and
  assigning notes to a folder. *(FR-10, FR-12, FR-13)*

- [ ] **11. Implement TagsRepository and tag assignment UI**
  Create `app/repositories/tags_repo.py` (CRUD for tags, link/unlink `note_tags`). Add tag chip UI
  in the editor/note view and a tag filter list in the sidebar. *(FR-11, FR-12)*

- [ ] **12. Implement FTS5 full-text search with live debounce**
  Create `app/search/fts.py` with query helpers against `notes_fts` (bm25 ranking). Add search box
  to note list wired via ~250ms debounced `QTimer`. *(FR-14, FR-15)*

- [ ] **13. Combine folder/tag/search filters in note list**
  Update `app/ui/models_qt.py` `NoteListModel` and `note_controller.py` to support simultaneous
  folder selection, tag filter, and search text narrowing the visible note list. *(FR-16)*

- [ ] **14. Verify Phase 3 milestone: organization and search work end-to-end**
  Manually verify folder nesting/move, tag assign/filter, and FTS search ranking behave correctly
  together.

## Phase 4 — Theming + pin/favorites

- [ ] **15. Implement ThemeManager with light/dark mode toggle**
  Create `app/ui/theme.py` (`QPalette` + `resources/styles/{light,dark}.qss`), a View-menu/toolbar
  toggle, and persistence via `QSettings`. Apply theme at startup before `MainWindow` is shown.
  *(FR-24, FR-25)*

- [ ] **16. Implement pin/favorite toggles and Favorites view**
  Add `toggle_pin`/`toggle_favorite` to `NotesRepository`, context-menu/toolbar actions, note list
  sort by `is_pinned DESC, updated_at DESC`, and a sidebar "Favorites" smart view.
  *(FR-17, FR-18)*

## Phase 5 — Export + reminders

- [ ] **17. Implement Markdown and PDF export**
  Create `app/export/markdown_export.py` (`QTextDocument.toMarkdown()`) and
  `app/export/pdf_export.py` (`QPrinter` + `document.print_()`). Add export menu/dialog
  (`app/ui/dialogs.py`) to trigger per-note export. *(FR-19, FR-20)*

- [ ] **18. Implement reminders: repository, dialog, scheduler, tray notifications**
  Create `app/repositories/reminders_repo.py` (CRUD + due-reminder query), `app/ui/dialogs.py`
  `ReminderDialog` (`QDateTimeEdit`), `app/reminders/scheduler.py` (`QTimer` polling every 30-60s),
  `app/ui/tray.py` (`QSystemTrayIcon` setup + `showMessage` on due reminders + Show/Hide/Quit
  context menu). Document the caveat that reminders only fire while the app is running (out of
  scope: OS-level scheduling). *(FR-21, FR-22, FR-23)*

- [ ] **19. Verify Phase 5 milestone: export and reminders work end-to-end**
  Manually export a note to `.md` and `.pdf` and open both in an external viewer to confirm
  formatting. Set a reminder 1 minute out and confirm a tray notification fires while the app runs.

## Phase 6 — Polish, testing, packaging

- [ ] **20. Implement Trash view (soft delete, restore, permanent delete)**
  Add a sidebar "Trash" view listing `is_trashed` notes, with Restore and Permanently Delete (and
  Empty Trash) actions, completing FR-3 fully.

- [ ] **21. Write pytest suite for repository layer**
  Create `tests/conftest.py` with an in-memory sqlite fixture (schema applied fresh per test) and
  tests for `notes_repo`, `folders_repo`, `tags_repo`, `reminders_repo`, and fts search (including
  cascade/set-null behavior and due-reminder boundary conditions). *(NFR-6)*

- [ ] **22. Write pytest-qt UI smoke tests**
  Create `tests/ui/test_main_window_smoke.py` and `test_editor_widget.py` using `qtbot`, runnable
  headlessly via `QT_QPA_PLATFORM=offscreen`. Verify app launch, New Note flow, and
  autosave-to-DB behavior. *(NFR-6)*

- [ ] **23. Verify NFR compliance (data dir, crash safety, performance)**
  Confirm DB lives under `QStandardPaths` per-user app-data directory (NFR-3), autosave
  flush-on-close prevents data loss on abrupt exit (NFR-2), and note list/search stay responsive
  with a few thousand seeded notes (NFR-1).

- [ ] **24. Package the app with PyInstaller**
  Add `packaging/noteapp.spec` bundling `resources/` (icons, `.qss`) via `datas`, add a
  resource-path helper working in both dev and frozen (`sys._MEIPASS`) modes. Build and smoke-test
  the packaged executable on a clean setup. Final acceptance criteria from `requirements.md`
  section 6.
