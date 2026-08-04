# Progress Status — Desktop Note-Taking App

Last updated: 2026-08-01. Use this file as the starting point for any future session —
read this first, then `tasklist.md` for the full task breakdown and
`/home/sandeep/.claude/plans/you-are-a-seninor-cryptic-spindle.md` for the original
architecture plan. `requirements.md` has the FR/NFR list everything traces back to.

## Status: 24 / 24 tasks complete — ALL PHASES DONE. v1 acceptance criteria met.

- [x] 1. Scaffold project structure and dependencies
- [x] 2. Implement SQLite schema, connection, and migrations
- [x] 3. Implement Note model and NotesRepository CRUD
- [x] 4. Build MainWindow skeleton with note list and plain editor
- [x] 5. Verify Phase 1 milestone: CRUD persists across restart
- [x] 6. Build rich text formatting toolbar
- [x] 7. Add inline image embedding to editor
- [x] 8. Implement HTML persistence and debounced autosave
- [x] 9. Verify Phase 2 milestone: rich formatting round-trips
- [x] 10. Implement FoldersRepository and sidebar folder tree UI
- [x] 11. Implement TagsRepository and tag assignment UI
- [x] 12. Implement FTS5 full-text search with live debounce
- [x] 13. Combine folder/tag/search filters in note list
- [x] 14. Verify Phase 3 milestone: organization and search work end-to-end
- [x] 15. Implement ThemeManager with light/dark mode toggle
- [x] 16. Implement pin/favorite toggles and Favorites view
- [x] 17. Implement Markdown and PDF export
- [x] 18. Implement reminders: repository, dialog, scheduler, tray notifications
- [x] 19. Verify Phase 5 milestone: export and reminders work end-to-end
- [x] 20. Implement Trash view (soft delete, restore, permanent delete)
- [x] 21. Write pytest suite for repository layer
- [x] 22. Write pytest-qt UI smoke tests
- [x] 23. Verify NFR compliance (data dir, crash safety, performance)
- [x] 24. Package the app with PyInstaller

Per `requirements.md` section 6 ("Acceptance Criteria (v1 done)"): all FR-1..FR-25 implemented and
manually/headlessly verified, the full pytest suite passes (170/170), and a packaged PyInstaller
build launches and operates correctly under a simulated clean machine (isolated `$HOME`, no dev
environment). **There is no next task in `tasklist.md`.** See "What's genuinely left" near the
bottom of this file for optional, non-required follow-ups.

## What exists right now

```
main.py                          # entry point: applies persisted theme, opens DB, builds
                                   #   Notes/Folders/Tags/RemindersRepository, shows MainWindow
requirements.txt                 # PySide6>=6.11,<6.12, pytest>=8.0, pytest-qt>=4.4, pyinstaller>=6.10
app/
  config.py                      # app-data dir + DB path via QStandardPaths; RESOURCES_DIR,
                                   #   get_settings_path() (QSettings INI colocated with the DB)
  db/
    schema.sql                   # folders, notes, tags, note_tags, reminders, notes_fts (FTS5) + sync triggers
    connection.py                 # get_connection() (WAL + foreign_keys pragmas), open_database()
    migrations.py                 # PRAGMA user_version-based migration runner (currently version 1 = schema.sql)
  models/
    note.py                       # Note dataclass + from_row()
    folder.py                     # Folder dataclass + from_row()
    tag.py                        # Tag dataclass + from_row()
    reminder.py                   # Reminder dataclass + from_row() (remind_at stored as UTC "yyyy-MM-dd HH:mm:ss")
  repositories/
    notes_repo.py                 # NotesRepository: create/get/update_content/move_to_folder/trash/restore/
                                   #   list_trashed/delete_permanently/toggle_pin/toggle_favorite, and
                                   #   list_all(folder_id, tag_id, search_text, favorites_only) which combines
                                   #   all four filters in one SQL query (search_text routes through
                                   #   app/search/fts.py and preserves bm25 relevance order)
    folders_repo.py                # FoldersRepository: create/get/list_all (flat, UI builds tree from
                                   #   parent_id)/rename/move/delete (cascade + notes SET NULL via DB)
    tags_repo.py                   # TagsRepository: create/get/get_by_name/get_or_create (case-insensitive
                                   #   reuse)/list_all/list_for_note/assign/unassign/rename/delete
    reminders_repo.py              # RemindersRepository: create/get/list_for_note/list_upcoming/list_due
                                   #   (via SQLite's own datetime('now'), not Python's clock)/mark_done/delete
  search/
    fts.py                        # search_note_ids(conn, query): builds a safe FTS5 MATCH expression (each
                                   #   word quoted + prefix-matched) against notes_fts, ranked by bm25()
  export/
    markdown_export.py            # note_to_markdown()/export_markdown(): title as "# " heading +
                                   #   QTextDocument.toMarkdown() body
    pdf_export.py                  # export_pdf(): title + content_html rendered via QTextDocument + QPrinter
                                   #   (PdfFormat), preserving rich formatting incl. inline images
  reminders/
    scheduler.py                   # ReminderScheduler(QObject): QTimer polling every 45s (POLL_INTERVAL_MS),
                                   #   reminderDue(note_id, message) signal, marks each reminder done the
                                   #   instant it fires so it can't refire; check_now() also runs once on
                                   #   start() to catch anything already due. Caveat documented in its
                                   #   docstring: only fires while this process is running, no OS scheduling.
  controllers/
    note_controller.py            # NoteController: wires UI signals to NotesRepository, 1.5s debounced
                                   #   autosave via QTimer, flush_pending() on switch/new/close,
                                   #   _on_note_folder_change_requested() for the "Move to Folder" menu,
                                   #   _on_tag_add_requested()/_on_tag_remove_requested() for the tag chip UI
                                   #   (persist immediately, not debounced), tagsChanged signal for the sidebar,
                                   #   toggle_pin/toggle_favorite (+ *_current() variants for the toolbar),
                                   #   current_note() (flushes pending, returns the open Note — used by export
                                   #   and "Set Reminder" so they always see live unsaved content)
  ui/
    theme.py                      # Theme enum (LIGHT/DARK); build_palette(), apply_theme(app, theme) (sets
                                   #   QPalette + loads resources/styles/{theme}.qss); load_theme()/save_theme()
                                   #   via QSettings INI
    models_qt.py                  # NoteListModel (QAbstractListModel), refresh()/refresh_note(),
                                   #   set_folder_filter/set_tag_filter/set_search_filter/set_favorites_filter —
                                   #   all four combine; DisplayRole prepends 📌/★ markers for pinned/favorite
    note_list.py                  # NoteListWidget (QListView wrapper): noteSelected signal, right-click menu
                                   #   with Pin/Unpin + Favorite/Unfavorite (→ notePinToggleRequested/
                                   #   noteFavoriteToggleRequested) and "Move to Folder" submenu (→
                                   #   noteFolderChangeRequested), search box wired via a 250ms debounced
                                   #   QTimer (SEARCH_DEBOUNCE_MS)
    sidebar.py                     # SidebarWidget: folder QTreeView ("All Notes" + "★ Favorites" smart view +
                                   #   tree built from FoldersRepository.list_all(), keyed by parent_id) +
                                   #   embedded TagFilterWidget below it; folderSelected/tagSelected(Optional[int])/
                                   #   favoritesSelected(bool) signals drive NoteListModel; right-click
                                   #   New/Rename/Delete on folders (not on Favorites); refresh_tags()
    tags_widget.py                 # TagChipEditor (removable tag chips + autocomplete add box, used inside
                                   #   NoteEditorWidget) and TagFilterWidget (sidebar "All Tags" + tag list,
                                   #   single-select, used inside SidebarWidget)
    editor.py                     # NoteEditorWidget: title QLineEdit + TagChipEditor + rich-text NoteTextEdit
                                   #   body + formatting toolbar (bold/italic/underline/strike, headings H1-H3,
                                   #   bullet/numbered lists, checklist via ☐/☑ glyph, image embedding)
    dialogs.py                     # export_note_via_dialog() (QFileDialog with a Markdown/PDF filter, auto
                                   #   extension); ReminderDialog (QDateTimeEdit defaulting +1h, local↔UTC
                                   #   conversion via remind_at_utc()); RemindersListDialog (view/mark-done/
                                   #   delete upcoming reminders across all notes)
    tray.py                        # TrayIcon(QSystemTrayIcon): Show/Hide/Quit context menu,
                                   #   notify_reminder(title, message) → showMessage()
    main_window.py                 # MainWindow(repo, folders_repo, tags_repo, reminders_repo):
                                   #   QSplitter(SidebarWidget | note list | editor), toolbar
                                   #   (New/Delete/Pin/Favorite/Export/Set Reminder), File menu (Export),
                                   #   View menu (Dark Theme toggle), Reminders menu (Set/View Upcoming),
                                   #   tray icon + ReminderScheduler wired to it, Trash smart view wiring
                                   #   (disables New/Delete/Pin/Favorite/Export/Set Reminder while active),
                                   #   closeEvent flush
tests/                             # 170 tests total, all passing headlessly (QT_QPA_PLATFORM=offscreen)
  conftest.py                      # in-memory `conn` fixture (full schema applied) + one fixture per repo
  test_notes_repo.py               # 17 tests: CRUD, filters (folder/tag/search/favorites, combined),
                                   #   trash/restore/delete, pin/favorite, cascades
  test_folders_repo.py             # 8 tests: CRUD, nesting, cascade delete, transitive unfiling
  test_tags_repo.py                # 10 tests: CRUD, case-insensitive get_or_create, assign idempotency
  test_reminders_repo.py           # 9 tests: CRUD, due-boundary conditions (past/exactly-now/future), cascade
  test_search.py                   # 7 tests: FTS prefix matching, ranking, blank/no-match, special chars
  test_performance.py              # 5 tests (NFR-1): list/filter/search/model-refresh/editor-load timing
                                   #   with 3000 seeded notes, generous thresholds (<1s; real numbers are
                                   #   single-digit ms) so it guards regressions without being flaky
  test_architecture_boundaries.py  # 90 tests (NFR-4, NFR-5): repositories/models never import PySide6,
                                   #   ui/controllers never import sqlite3 directly, no network modules or
                                   #   PySide6.QtNetwork imported anywhere in app/ -- ast-based import scan,
                                   #   parametrized per file, mutation-tested to confirm real bite
  ui/
    test_main_window_smoke.py      # 9 tests: app launch, New Note, soft delete, autosave (incl. the real
                                   #   debounce QTimer firing on its own), close/switch flush, pin/favorite,
                                   #   trash-mode toolbar disabling
    test_editor_widget.py          # 12 tests: load() vs typing signal behavior, bold/heading/list toolbar
                                   #   actions, checklist toggle, image embed+downscale, tag chip signals
    test_config_data_dir.py        # 3 tests (NFR-3): get_app_data_dir() forces the fixed app name even if
                                   #   something else in-process reset it; matches QStandardPaths exactly
resources/
  styles/light.qss, dark.qss     # loaded by app/ui/theme.py; use palette(...) refs so custom widgets
                                   #   (e.g. the tag chip background) adapt automatically with the palette
  icons/                          # still empty — no custom icons anywhere; tray/toolbar use Qt's built-in
                                   #   standard icons where an icon is needed at all
packaging/
  noteapp.spec                    # PyInstaller spec (onedir build): bundles resources/ AND app/db/schema.sql
                                   #   (a non-.py data file PyInstaller doesn't auto-include) via `datas`
build/, dist/                     # PyInstaller output -- gitignored, not committed, safe to `rm -rf` and
                                   #   regenerate via `pyinstaller packaging/noteapp.spec` from repo root
```

Every `app/` subpackage from the original plan has real content, a full pytest suite exists (170 tests),
and the app builds + runs as a standalone PyInstaller executable. Nothing is scaffolded-but-empty anymore
except `resources/icons/` (never became necessary).

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
- **Folder tree**: `FoldersRepository.list_all()` returns a flat list (ordered by `sort_order, name`);
  `SidebarWidget.refresh()` builds the `QStandardItemModel` tree client-side from `parent_id`, keyed in
  `self._items: Dict[Optional[int], QStandardItem]` (`None` key = the synthetic "All Notes" root item,
  a sibling of top-level folders, not their parent). `folder_id=None` passed to
  `NotesRepository.list_all()`/`NoteListModel.set_folder_filter()` means **all notes**, not "unfiled
  only" — there's no separate "Unfiled" smart view yet. Folder delete relies entirely on DB-level
  `ON DELETE CASCADE` (sub-folders) and `ON DELETE SET NULL` (notes) from `schema.sql` — the repository
  just does a bare `DELETE FROM folders`, no manual reparenting/unfiling logic in Python.
- **Moving a note between folders**: `NoteListWidget` right-click → "Move to Folder" submenu (built from
  `FoldersRepository.list_all()`, indented by nesting depth) emits
  `noteFolderChangeRequested(note_id, folder_id)`, handled by
  `NoteController._on_note_folder_change_requested()`. No drag-and-drop; the sidebar tree only filters,
  it doesn't accept drops.
- **Tags persist immediately, not via autosave debounce**: unlike title/body, `_on_tag_add_requested`/
  `_on_tag_remove_requested` in `note_controller.py` write to `TagsRepository` the instant a chip is
  added/removed — tags aren't part of `content_html`/`content_plain` so there's nothing to batch.
  `TagsRepository.get_or_create()` reuses an existing tag by name (case-insensitive, matching the
  `tags.name UNIQUE COLLATE NOCASE` schema constraint) instead of creating a duplicate.
- **Sidebar `TagFilterWidget` owns its own selection state independently of `NoteListModel`** — don't
  drive `model.set_tag_filter()`/`set_folder_filter()` directly from anywhere except the sidebar's own
  signals. `NoteController.tagsChanged` → `SidebarWidget.refresh_tags()` → `TagFilterWidget.refresh()`
  restores selection from `TagFilterWidget`'s own remembered index, so if something else changed the
  model's filter out from under it, refresh would silently stomp it back. This was caught during task 11
  verification: a test that called `model.set_tag_filter()` directly (bypassing the sidebar widget) saw
  its filter reset to "All Tags" on the next `refresh_tags()` — not a real bug, just proof the sidebar
  widget must stay the single source of truth for its own selection.
- **Combined filtering lives in `NotesRepository.list_all(folder_id, tag_id, search_text)`** — one method,
  one SQL query per call, ANDing whichever filters are non-None together. When `search_text` is set,
  results are restricted to `app.search.fts.search_note_ids()`'s ranked ids and re-sorted to match that
  bm25 order (ignoring the normal `is_pinned DESC, updated_at DESC` ordering); otherwise the normal
  ordering applies. This is also why task 13 ("combine filters") needed no new code — task 12 built the
  combination in from the start.
- **FTS query building** (`app/search/fts.py`): each whitespace-split word becomes a quoted, prefixed
  term (`"word"*`), ANDed via FTS5's implicit space-separated AND. This both enables live prefix search
  (matches as you type, before the word is finished) and makes arbitrary user input safe — quoting sidesteps
  FTS5 syntax errors from raw operators/punctuation (`AND`, `-`, `*`, `:`, unbalanced quotes, etc.), verified
  during task 12.
- **Known rough edge (not yet fixed)**: `NoteController.new_note()` always creates the note unfiled and
  untagged. If a folder/tag/favorites filter is active when "New Note" is pressed, the new note won't
  appear in the filtered list and `note_list.select_note()` silently no-ops. Predates task 10-13; flagged
  during task 13 but out of scope for it. Revisit during Phase 6 polish if it bothers real usage.
- **Theme settings live in their own `QSettings` INI, not the DB**: `get_settings_path()` in
  `app/config.py` puts `settings.ini` next to `notes.db` in the app-data dir, using
  `QSettings(path, QSettings.Format.IniFormat)` explicitly rather than the implicit
  `QSettings()`/organizationName-based default — `organizationName` is deliberately left unset (see the
  DB-path decision above), so the implicit constructor would resolve inconsistently. Theme is applied via
  `apply_theme(app, load_theme())` in `main.py` *before* `MainWindow` is constructed, then re-applied live
  from `MainWindow`'s View ▸ Dark Theme toggle.
- **Custom widget styling should reference `palette(...)` in stylesheets, not hardcoded colors** — e.g.
  `_TagChip` (`app/ui/tags_widget.py`) uses `background: palette(midlight)`, so it repaints correctly
  under both `light.qss`/`dark.qss` without any theme-specific code of its own. Keep doing this for any
  new custom-painted widget rather than hardcoding hex colors that would go stale under the other theme.
- **Favorites is a sidebar smart view, not a filter combinable with folder browsing**: selecting
  "★ Favorites" in `SidebarWidget`'s folder `QTreeView` (same tree, not a separate list) emits
  `favoritesSelected(True)` *and* `folderSelected(None)` together, and selecting any real folder/"All
  Notes" emits `favoritesSelected(False)`. This mirrors typical note-app UX (Favorites and folder
  browsing are mutually exclusive, both independent of the Tags filter and search, which still combine
  normally). `SidebarWidget._items` is keyed by `folder_id` (`None` = "All Notes") except the Favorites
  node, which uses the sentinel string `FAVORITES_KEY = "__favorites__"` — don't reuse `None` for it, it
  would collide with "All Notes" in the previous-selection-preservation logic in `refresh()`.
- **Pin/favorite toggles persist immediately** (like tags, unlike title/body) via
  `NotesRepository.toggle_pin`/`toggle_favorite` (`UPDATE ... SET x = NOT x`), reachable from the note-list
  right-click menu (any note, via `notePinToggleRequested`/`noteFavoriteToggleRequested`) or the toolbar
  (`toggle_pin_current`/`toggle_favorite_current`, acting on `NoteController._current_note_id`). Both
  bump `updated_at`, matching the existing precedent set by `move_to_folder`/`trash`/`restore` (all
  metadata mutations bump it, not just content edits).
- **`NoteListModel.data(DisplayRole)`** now prepends `📌 ` / `★ ` to the title for pinned/favorite notes
  — the only visual affordance for those two states right now (no icons yet; `resources/icons/` is still
  empty).
- **Export always reflects live unsaved content, not stale DB state**: `NoteController.current_note()`
  calls `flush_pending()` before returning the note, and both the export action and "Set Reminder" go
  through it rather than reading `self._repo.get(...)` directly. Verified during task 17: editing a note's
  body without waiting for the 1.5s autosave debounce, then exporting immediately, still exports the
  edited text.
- **Reminder times are stored as UTC strings (`"yyyy-MM-dd HH:mm:ss"`), matching SQLite's own
  `datetime('now')` format** — `ReminderDialog.remind_at_utc()` converts the user's local-time
  `QDateTimeEdit` value via `.dateTime().toUTC().toString(REMINDER_DATETIME_FORMAT)`, and
  `RemindersRepository.list_due()` compares against `datetime('now')` in SQL rather than Python's clock,
  so due-ness is judged consistently regardless of Python/DB clock skew. Display converts back via
  `_utc_string_to_local_display()` in `app/ui/dialogs.py`. Verified with a real cross-timezone round-trip
  (local UTC+5:30 → stored UTC → correct local display) during task 19.
- **`ReminderScheduler` marks a reminder done the instant it fires, before emitting the signal** — so it
  cannot double-fire even if a slow signal handler causes overlapping `check_now()` calls. A reminder due
  while the app isn't running fires once, late, on the next `start()` call (documented as a caveat in the
  scheduler's own docstring, per the task instructions) — there's no OS-level scheduling.
- **`TrayIcon` construction is guarded, not its `.show()` call being skipped entirely**: `MainWindow`
  always constructs `TrayIcon` (safe even headless/offscreen — confirmed in task 18/19 testing) but only
  calls `.show()` when `QSystemTrayIcon.isSystemTrayAvailable()` is true, so the app doesn't crash or spam
  warnings on a system/CI environment without a tray.
- **Closing the main window still quits the app** — reminders/tray were added without changing
  `closeEvent`'s behavior (still just flushes pending edits and lets the window close normally). No
  hide-to-tray-on-close was implemented; only the tray's own Quit action and closing the window both exit
  the app. If minimize-to-tray-on-close is wanted later, that's a deliberate behavior change to raise with
  the user, not an oversight.
- **Trash is a separate listing, not another AND-able filter** (unlike folder/tag/search/favorites, which
  all combine): `NoteListModel.set_trash_mode(True)` makes `refresh()` call
  `NotesRepository.list_trashed()` instead of `list_all(...)`, ignoring every other filter's state while
  active. `NoteController.set_trash_mode()` also flushes/clears/disables the editor and makes the note
  list read-only-via-context-menu-only — clicking a trashed note in `NoteListWidget` does **not** load it
  into the live-editing/autosave flow (`_on_note_selected` early-returns when `self._trash_mode`).
  `MainWindow._on_trash_selected` additionally disables New/Delete/Pin/Favorite/Export/Set Reminder
  toolbar actions while Trash is active (none apply there) via `self._normal_mode_actions`.
- **Trash smart view follows the exact Favorites pattern**: another item in `SidebarWidget`'s folder
  `QTreeView` (not a separate list), its own sentinel key (`TRASH_KEY = "__trash__"`, `TRASH_ROLE`),
  mutually exclusive with Favorites/folder selection by construction (single-selection tree). Right-click
  on the Trash node offers **Empty Trash** (with a confirmation `QMessageBox`) instead of folder actions —
  same right-click-context-menu pattern already used for folders.
- **Gotcha: `QMenu.exec` cannot be monkeypatched at the class level in tests** — unlike `QDialog.exec` on
  a Python subclass (works fine) or `QMessageBox.question` (a static-style call, also works fine),
  assigning `QMenu.exec = fake_function` silently does **not** intercept calls on `QMenu` instances — the
  real `exec()` still runs and hangs forever in a headless/offscreen environment waiting for a click that
  will never come. The working pattern (used in `note_list.py`'s and `sidebar.py`'s context-menu tests,
  task 20): reassign the `QMenu` **name in the target module's namespace**
  (`app.ui.note_list.QMenu = FakeMenuSubclass`) to a real Python subclass with `exec()` overridden — since
  `_on_context_menu` resolves `QMenu` via its module's globals at call time, this correctly intercepts the
  instantiation. Always restore the original afterward. `qtbot`-based tests in `tests/ui/` sidestep this
  entirely by calling controller/repo methods or emitting signals directly rather than triggering context
  menus through real right-clicks.
- **`app/config.py`'s `get_app_data_dir()` re-asserts `QCoreApplication.setApplicationName()` on every
  call, not once at import time** — a real bug found during task 23's NFR-3 verification: Qt
  pre-populates `applicationName()` from `argv[0]`'s basename by default (e.g. `"main.py"` when launched
  via `python main.py`, `"pytest-qt-qapp"` when `pytest-qt`'s own fixtures touch it during tests), so the
  original `if not QCoreApplication.applicationName(): setApplicationName(APP_NAME)` guard never actually
  fired (the value was never falsy) — meaning the DB would land under `~/.local/share/main.py/notes.db`,
  not the intended `~/.local/share/NoteApp/notes.db`. Fixed by making the assignment unconditional *and*
  moving it inside `get_app_data_dir()` so it self-corrects on every call regardless of what else in the
  process touched `applicationName()` beforehand. Covered by `tests/ui/test_config_data_dir.py`.
- **PyInstaller only bundles `.py` sources into the PYZ archive — plain data files sitting next to a
  module need their own explicit `datas` entry in the `.spec` file**, or they're silently missing from
  the frozen build even though nothing errors at build time. Found the hard way in task 24:
  `app/db/schema.sql` (read via `Path(__file__).parent / "schema.sql"` in `migrations.py`) wasn't bundled
  by default, and the packaged executable crashed with `FileNotFoundError` on first launch. Fixed by
  adding `(SCHEMA_SQL, "app/db")` to `packaging/noteapp.spec`'s `datas` alongside `resources/`. Verified
  by actually launching the built executable (not just checking the build succeeded) — a build that
  compiles cleanly is not evidence it runs.
- **`app/config.py`'s `RESOURCES_DIR`/`_resources_dir()` is frozen-build-aware**: checks
  `hasattr(sys, "_MEIPASS")` and resolves under PyInstaller's runtime extraction root when frozen, falling
  back to the dev-mode `Path(__file__).resolve().parent.parent / "resources"` otherwise. This is the
  "resource-path helper working in both dev and frozen modes" `tasklist.md` called for.
- **Editor font preference is a global `QSettings` value, not per-note** (SCRUM-8): `app/ui/font_prefs.py`
  follows `app/ui/theme.py`'s exact pattern — `load_font_family()`/`save_font_family()` against the same
  `settings.ini` via `get_settings_path()`. `resolve_default_font_family()` returns `"Aptos"` only if
  `QFontDatabase.families()` actually reports it installed (it's a Windows 11/Office 2021+ font, not a
  Linux system font and not guaranteed on older Windows), else falls back to `QGuiApplication.font().family()`
  — no bundled font file, no licensing entanglement. `load_font_family()` also re-validates a previously
  saved family is still installed before trusting it (covers moving the settings file to a machine/profile
  without that font). `NoteEditorWidget` is a single reused instance across note switches (constructed once
  in `MainWindow.__init__`), so applying the remembered font once at construction (`_apply_default_font()`)
  is sufficient to satisfy "reopen with the same font selected" — no per-note DB column needed; per-note
  font formatting (when explicitly applied via the toolbar) already rides along inside `content_html` the
  same way bold/italic do.
- **Gotcha: `QTextCharFormat.fontFamily()` (Qt's deprecated accessor) segfaults when read repeatedly from
  inside `currentCharFormatChanged`/`cursorPositionChanged` handlers**, confirmed with a minimal repro
  outside pytest (a bare `QTextEdit` + repeated `setPlainText()` calls, no `QFontComboBox` involved) on
  PySide6 6.11.1 in this environment — not specific to `QFontComboBox` or to this codebase's wiring, and
  not a reentrancy problem with the *setter* (`setFontFamily()` works, just deprecated). Found via
  `test_editor_load_stays_fast_for_a_large_note` (`tests/test_performance.py`) crashing the whole pytest
  process rather than failing normally. Fixed by reading `fmt.font().family()` instead, and writing via
  `fmt.setFontFamilies([family])` instead of `setFontFamily()` — both are the non-deprecated replacements
  and don't crash under the same repro. If a future `currentCharFormatChanged`/`cursorPositionChanged`
  handler needs any other deprecated `QTextCharFormat.font*()` accessor, verify it the same way (a tight
  `setPlainText()` loop outside pytest) before trusting it under load — the existing bold/italic/underline/
  strikethrough getters (`fontWeight()`, `fontItalic()`, etc.) were checked and are fine, only
  `fontFamily()` reproduces the crash. Also added an early return in
  `NoteEditorWidget._sync_toolbar_from_format()` for `self._loading` (skips toolbar sync entirely while
  `load()` is running) — a genuine perf win on top of the crash fix, since `setHtml()` on a large note
  fires these signals once per block.

## Environment notes

- Python 3.14.4 venv at `.venv/`. PySide6 6.11.1 installed via `abi3` wheel — works fine on 3.14, no
  interpreter downgrade needed.
- **No `sqlite3` CLI binary on this machine** — for raw DB inspection outside the app, use Python's
  stdlib `sqlite3` module directly (`python3 -c "import sqlite3; ..."`), not a `sqlite3 file.db` shell.
- All manual/headless verification so far has used `QT_QPA_PLATFORM=offscreen .venv/bin/python -c "..."`
  one-off scripts (no formal pytest suite exists yet — that's tasks 21/22). Milestone verifications
  (tasks 5, 9, 14, 19) ran the app as two separate process invocations against a real file-backed DB to
  simulate an actual restart, then cleaned up the temp DB file afterward from the scratchpad dir.
  For UI interaction in these scripts, prefer driving the actual widgets (e.g.
  `sidebar._tree.setCurrentIndex(...)`, `note_list._search_box.setText(...)`) over calling
  repository/model methods directly — task 11 showed that bypassing a stateful widget (like
  `TagFilterWidget`) to poke the model underneath it can produce misleading failures that don't
  reflect real user interaction. `QTest.qWait(ms)` is needed (not just `app.processEvents()`) to let a
  debounce `QTimer` (search box, 250ms) or the reminder scheduler's real polling `QTimer` actually elapse
  — task 19 verified a reminder firing through the scheduler's *actual* `QTimer` (temporarily sped up to
  ~300ms and let a real ~2.5s wall-clock wait pass via `QTest.qWait`), not just by calling `check_now()`
  manually, to prove the production polling path genuinely works, not just the logic it calls.
- Modal `QDialog`s (`ReminderDialog`, file-save dialogs) can't be driven by a script waiting on `.exec()`
  to return, since nothing will click their buttons. The pattern used in task 17/18/19: monkeypatch the
  static/instance method that would normally block (`QFileDialog.getSaveFileName`, `ReminderDialog.exec`)
  to set up the desired state and return the accepted result directly, always restoring the original in a
  `finally` block. No PDF-parsing library is installed (`pypdf`/`PyPDF2`/`pdfminer.six` all absent) — PDF
  export is verified structurally (valid `%PDF-` header, `%%EOF` trailer, non-trivial size), not by
  extracting and asserting on rendered text; don't add such a dependency without asking first.
- Nothing has been committed to git yet — `git status` shows everything as untracked/modified. No
  commit has been requested by the user.
- Building the packaged app: `pyinstaller packaging/noteapp.spec` from the repo root (not from inside
  `packaging/`) — the spec resolves `PROJECT_ROOT` via `Path(SPECPATH).parent`, so it must be invoked in
  a way that leaves `SPECPATH` pointing at `packaging/`. Output lands in `build/` and `dist/` (both
  gitignored). `dist/NoteApp/NoteApp` is the onedir build's executable; `dist/NoteApp/_internal/` holds
  bundled resources/data — a `find dist/NoteApp/_internal -iname '*.qss' -o -iname 'schema.sql'` is a
  quick sanity check that `datas` bundling didn't silently drop something after a spec-file edit.
- Smoke-testing the packaged build headlessly: launch with `QT_QPA_PLATFORM=offscreen` and an isolated
  `HOME=/some/scratch/dir` (simulates a clean machine without touching the real `~/.local/share/NoteApp`),
  background it, `sleep` a few seconds, then check the process is still alive (`kill -0 $PID`) and that
  the DB/schema landed where expected — a build that compiles is not evidence it runs; task 24 caught a
  bundling bug (`schema.sql` missing) exactly this way, that a clean `pyinstaller` build with no errors
  had completely missed.

## What's genuinely left (all optional — not part of the accepted v1 plan)

Nothing in `tasklist.md` remains. If asked to keep going, these are the honest gaps, in rough priority:
- **Git**: nothing has been committed yet. First commit is a substantial, deliberate action — confirm
  scope/message with the user rather than assuming "commit everything" from a bare "commit" request.
- **`resources/icons/`**: still empty. The app works fully without custom icons (tray/toolbar fall back
  to Qt's built-in standard icons), but a real app icon (window/taskbar/tray) would need one added here
  plus wiring into `noteapp.spec` (`icon=` on `EXE`) and `MainWindow.setWindowIcon()`.
  `resources/icons/` was scaffolded in task 1 for this and never populated.
- **The two documented rough edges**: (1) `NoteController.new_note()` doesn't account for an active
  folder/tag/favorites filter (new note can end up invisible in the current view — see the design
  decisions above); (2) reminders due while the app isn't running fire once, late, on next launch (an
  explicitly accepted, documented caveat per `tasklist.md`'s own wording, not really a "gap").
- **Cross-platform packaging**: `packaging/noteapp.spec` has only been built/tested on Linux in this
  sandbox. Windows/macOS builds would need their own smoke-test pass (icon format differences, code
  signing/notarization on macOS, etc.) — `requirements.md` doesn't scope a specific target platform, but
  it's worth clarifying with the user before assuming Linux-only is sufficient.
