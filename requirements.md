# Requirements: Desktop Note-Taking Application

## 1. Overview

A cross-platform desktop note-taking application, built in Python, offering a rich text-editing
experience comparable to modern note apps (e.g. Notion/Evernote-lite), backed by a local SQLite
database. Single-user, offline-first, no cloud sync in v1.

- **GUI toolkit**: PySide6 (Qt for Python)
- **Storage**: SQLite (local file, stdlib `sqlite3`, no ORM)
- **Target OS**: Linux first (current dev environment); Windows/macOS packaging is a later milestone
- **Distribution**: standalone packaged executable via PyInstaller

## 2. Functional Requirements

### 2.1 Note management
- FR-1: User can create a new note.
- FR-2: User can edit a note's title and body.
- FR-3: User can delete a note (soft delete to a Trash view; permanent delete from Trash).
- FR-4: Notes autosave while typing (debounced, no explicit "Save" button required).
- FR-5: Notes persist across application restarts.

### 2.2 Rich text editing
- FR-6: Editor supports bold, italic, underline, strikethrough formatting.
- FR-7: Editor supports headings, bullet lists, numbered lists, and checklists.
- FR-8: Editor supports embedding images inline within a note.
- FR-9: Formatting persists correctly through save/reload (no data loss on round-trip).

### 2.3 Organization
- FR-10: User can organize notes into folders (hierarchical, nested).
- FR-11: User can assign one or more tags to a note (cross-cutting labels independent of folders).
- FR-12: User can move a note between folders and add/remove tags without losing content.
- FR-13: Deleting a folder does not delete its notes; notes become unfiled (or move to parent) instead.

### 2.4 Search
- FR-14: User can perform full-text search across note titles and content.
- FR-15: Search results update live as the user types (debounced), ranked by relevance.
- FR-16: User can filter the note list by folder and/or tag, optionally combined with search.

### 2.5 Pinning and favorites
- FR-17: User can pin a note so it stays at the top of its list view.
- FR-18: User can mark a note as a favorite, viewable via a dedicated "Favorites" view.

### 2.6 Export
- FR-19: User can export a single note to Markdown (`.md`).
- FR-20: User can export a single note to PDF (`.pdf`), preserving formatting.

### 2.7 Reminders
- FR-21: User can attach a reminder (date/time) to a note.
- FR-22: When a reminder is due and the app is running, a system tray notification is shown.
- FR-23: User can view/manage upcoming reminders.

### 2.8 Appearance
- FR-24: User can toggle between light and dark theme.
- FR-25: The chosen theme persists across restarts.

## 3. Non-Functional Requirements

- NFR-1 (Performance): Note list, search, and editor interactions remain responsive (no noticeable
  lag) with at least several thousand notes.
- NFR-2 (Data integrity): No data loss on crash or unexpected exit — autosave flushes on note
  switch and on application close.
- NFR-3 (Portability): Application data (SQLite DB) is stored in the OS-standard per-user app-data
  directory, not next to the executable, so packaged builds work correctly when installed.
- NFR-4 (Offline): Application requires no network access; fully functional offline.
- NFR-5 (Maintainability): Clear separation between UI, data-access, and model layers so features
  can be added without entangling SQL with widget code.
- NFR-6 (Testability): Data-access logic is unit-testable without a display server; UI has smoke-test
  coverage runnable headlessly (e.g. `QT_QPA_PLATFORM=offscreen`) for CI.

## 4. Out of Scope (v1)

- Cloud sync / multi-device sync / accounts.
- Real-time collaboration or multi-user editing.
- Reminders firing while the application is not running (would require OS-level scheduling —
  cron / Task Scheduler / background service — not just in-app `QTimer` polling).
- Mobile or web clients.
- Attachment types other than embedded images (e.g. file attachments, audio notes).
- Version history / undo-beyond-session for notes.

## 5. Key Dependencies

| Package     | Purpose                                              |
|-------------|-------------------------------------------------------|
| PySide6     | GUI toolkit; rich text editing, PDF export, tray icon |
| pytest      | Test runner                                            |
| pytest-qt   | Qt-aware test fixtures for UI smoke tests              |
| pyinstaller | Packaging into a standalone executable (build-time)    |

No ORM, Markdown library, PDF library, task-scheduler library, or notification library — Qt's
native `QTextDocument`, `QPrinter`, `QTimer`, and `QSystemTrayIcon` cover these needs directly.

## 6. Acceptance Criteria (v1 "done")

- All Functional Requirements above (FR-1 through FR-25) are implemented and manually verified.
- Full `pytest` suite (repository layer + UI smoke tests) passes.
- A packaged build (PyInstaller) launches and operates correctly on a clean machine without the
  development environment installed.
