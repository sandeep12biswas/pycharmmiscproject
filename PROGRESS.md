# Progress Status — Desktop Note-Taking App

Last updated: 2026-07-31. Use this file as the starting point for the next session —
read this first, then `tasklist.md` for the full task breakdown and
`/home/sandeep/.claude/plans/you-are-a-seninor-cryptic-spindle.md` for the original
architecture plan. `requirements.md` has the FR/NFR list everything traces back to.

## Status: 9 / 24 tasks complete — Phase 1 and Phase 2 done

- [x] 1. Scaffold project structure and dependencies
- [x] 2. Implement SQLite schema, connection, and migrations
- [x] 3. Implement Note model and NotesRepository CRUD
- [x] 4. Build MainWindow skeleton with note list and plain editor
- [x] 5. Verify Phase 1 milestone: CRUD persists across restart
- [x] 6. Build rich text formatting toolbar
- [x] 7. Add inline image embedding to editor
- [x] 8. Implement HTML persistence and debounced autosave
- [x] 9. Verify Phase 2 milestone: rich formatting round-trips
- [ ] **10. Implement FoldersRepository and sidebar folder tree UI  ← START HERE NEXT**
- [ ] 11. Implement TagsRepository and tag assignment UI
- [ ] 12. Implement FTS5 full-text search with live debounce
- [ ] 13. Combine folder/tag/search filters in note list
- [ ] 14. Verify Phase 3 milestone: organization and search work end-to-end
- [ ] 15. Implement ThemeManager with light/dark mode toggle
- [ ] 16. Implement pin/favorite toggles and Favorites view
- [ ] 17. Implement Markdown and PDF export
- [ ] 18. Implement reminders: repository, dialog, scheduler, tray notifications
- [ ] 19. Verify Phase 5 milestone: export and reminders work end-to-end
- [ ] 20. Implement Trash view (soft delete, restore, permanent delete)
- [ ] 21. Write pytest suite for repository layer
- [ ] 22. Write pytest-qt UI smoke tests
- [ ] 23. Verify NFR compliance (data dir, crash safety, performance)
- [ ] 24. Package the app with PyInstaller

(Full descriptions of each remaining task are in `tasklist.md`.)

## What exists right now

```
main.py                          # entry point: opens DB, builds NotesRepository, shows MainWindow
requirements.txt                 # PySide6>=6.11,<6.12, pytest>=8.0, pytest-qt>=4.4, pyinstaller>=6.10
app/
  config.py                      # app-data dir + DB path via QStandardPaths
  db/
    schema.sql                   # folders, notes, tags, note_tags, reminders, notes_fts (FTS5) + sync triggers
    connection.py                 # get_connection() (WAL + foreign_keys pragmas), open_database()
    migrations.py                 # PRAGMA user_version-based migration runner (currently version 1 = schema.sql)
  models/
    note.py                       # Note dataclass + from_row()
  repositories/
    notes_repo.py                 # NotesRepository: create/get/list_all/update_content/move_to_folder/
                                   #   trash/restore/list_trashed/delete_permanently
  controllers/
    note_controller.py            # NoteController: wires UI signals to NotesRepository, 1.5s debounced
                                   #   autosave via QTimer, flush_pending() on switch/new/close
  ui/
    models_qt.py                  # NoteListModel (QAbstractListModel), refresh()/refresh_note()
    note_list.py                  # NoteListWidget (QListView wrapper), noteSelected signal
    editor.py                     # NoteEditorWidget: title QLineEdit + rich-text NoteTextEdit body +
                                   #   formatting toolbar (bold/italic/underline/strike, headings H1-H3,
                                   #   bullet/numbered lists, checklist via ☐/☑ glyph, image embedding)
    main_window.py                 # MainWindow: QSplitter(sidebar placeholder | note list | editor),
                                   #   New Note / Delete Note toolbar actions, closeEvent flush
tests/                            # scaffolded (empty) — real suite is task 21/22, not started yet
resources/                        # scaffolded (icons/, styles/) — not populated yet (dark/light mode is task 15)
```

Not yet created: `app/search/`, `app/export/`, `app/reminders/` are empty scaffolds (`__init__.py` only) —
populated starting task 10 (folders live in `app/repositories/folders_repo.py`, not yet created).

## Key design decisions already made (don't redecide these)

- **No ORM** — raw `sqlite3` + repository classes returning dataclasses. Widgets never import `sqlite3`;
  repositories never import PySide6.
- **Autosave**: `NoteController` debounces via a single-shot `QTimer` (`AUTOSAVE_DEBOUNCE_MS = 1500`,
  in `note_controller.py`). `flush_pending()` is the one method that actually writes — it's called by
  the timer, on note switch, on `new_note()`, and from `MainWindow.closeEvent`. Never write to the repo
  directly from a UI signal handler; always go through `flush_pending()`/the timer.
- **Rich text persistence**: `content_html` (`QTextDocument.toHtml()`) is authoritative; `content_plain`
  (`toPlainText()`) is a denormalized cache for FTS5 only. `NoteEditorWidget.load()` uses `setHtml()`.
- **Checklists**: not a native Qt list type — implemented as a `☐ `/`☑ ` glyph prefix on a line, with
  `NoteTextEdit.mousePressEvent` overridden to toggle it on click. Constants `CHECKBOX_UNCHECKED` /
  `CHECKBOX_CHECKED` live in `app/ui/editor.py`.
- **Images**: embedded as base64 PNG `data:` URIs directly in `content_html` (no attachments table).
  Downscaled to `NoteEditorWidget.MAX_IMAGE_WIDTH = 480` px before encoding.
- **Headings**: use `QTextBlockFormat.setHeadingLevel()` (semantic), not just visual bold+size — this
  matters later for `QTextDocument.toMarkdown()` export (task 17) to emit correct `#`/`##`.
  `QTextBlockFormat.setHeadingLevel` and `QTextList.remove(block)` were both confirmed to exist in the
  installed PySide6 6.11.1 before relying on them.
- **DB path**: `QStandardPaths.AppDataLocation` → resolves to `~/.local/share/NoteApp/notes.db`. Only
  `QCoreApplication.applicationName()` is set (not `organizationName`) — setting both duplicated the
  path segment (`NoteApp/NoteApp`), fixed in `app/config.py`.
- **List model refresh**: `NoteListModel.refresh()` does a full reset (use for structural changes: new
  note, delete, filter change). `refresh_note(note_id)` updates one row in place via `dataChanged` —
  use this after autosave so the list selection/scroll position isn't disturbed.

## Environment notes

- Python 3.14.4 venv at `.venv/`. PySide6 6.11.1 installed via `abi3` wheel — works fine on 3.14, no
  interpreter downgrade needed.
- **No `sqlite3` CLI binary on this machine** — for raw DB inspection outside the app, use Python's
  stdlib `sqlite3` module directly (`python3 -c "import sqlite3; ..."`), not a `sqlite3 file.db` shell.
- All manual/headless verification so far has used `QT_QPA_PLATFORM=offscreen .venv/bin/python -c "..."`
  one-off scripts (no formal pytest suite exists yet — that's tasks 21/22). Milestone verifications
  (tasks 5, 9) ran the app as two separate process invocations against a real file-backed DB to
  simulate an actual restart, then cleaned up the temp DB file afterward from the scratchpad dir.
- Nothing has been committed to git yet — `git status` shows everything as untracked/modified. No
  commit has been requested by the user.

## How to resume next session

1. Read this file, then `tasklist.md` task 10 for exact scope.
2. Task 10 is `FoldersRepository` (`app/repositories/folders_repo.py`) + sidebar `QTreeView` UI
   (`app/ui/sidebar.py`, replacing the `QLabel` placeholder currently in `main_window.py`). Folders
   table (`folders`, self-referencing `parent_id`, `ON DELETE CASCADE`) already exists in `schema.sql`.
   `NotesRepository.move_to_folder()` already exists for assigning notes to folders.
3. Follow the same pattern used throughout: implement → headless-verify with a `QT_QPA_PLATFORM=offscreen`
   script (structural assertions, not just "it ran") → mark the task complete via TaskUpdate → brief
   summary to the user before moving to the next task.
