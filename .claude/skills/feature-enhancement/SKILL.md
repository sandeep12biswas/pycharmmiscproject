---
name: feature-enhancement
description: Implement a feature enhancement for the NoteApp project starting from any Jira issue key in the SCRUM project (SCRUM-1, SCRUM-42, SCRUM-<any number>, etc.) or a jira link like https://sandeep12biswas.atlassian.net/browse/SCRUM-<number>. Fetches and summarizes the story, gets explicit user confirmation before writing any code, implements the change following this repo's architecture rules, and finishes by writing/running unit tests. Use this whenever the user says things like "implement SCRUM-12", "work on this jira ticket", "pick up the story at <jira link>", or "start the enhancement for <issue key>" — not for bug fixes with no Jira ticket, and not for ad-hoc requests that don't reference a Jira issue.
arguments : JIRA-number
---

# Feature Enhancement (Jira-driven)

Turns a Jira story into a reviewed, tested code change for this repo. The whole point of
this skill is the confirmation gate in step 3: never start editing code before the user has
seen a plain-language summary of what the ticket is asking for and explicitly said to proceed.
Stories get reworded, mis-scoped, or contain assumptions that don't fit this codebase — catching
that *before* writing code is cheaper than catching it after.

## Input

The user gives a Jira issue key $SCRUM# (`SCRUM-<number>` — any number, this isn't limited to a specific
issue) or a full issue URL (`https://sandeep12biswas.atlassian.net/browse/SCRUM-<number>`). If
neither is present in the request, ask for it before doing anything else — don't guess an issue
key, and don't assume it's always the same one from a previous run of this skill.

Extract the key from a URL with the pattern `/browse/([A-Z]+-\d+)`; otherwise the input is
already the key. This pattern matches any project prefix, not just SCRUM, in case the site ever
has more than one project.

## Step 1 — Fetch the issue

1. Resolve `cloudId`: try the site hostname (`sandeep12biswas.atlassian.net`) directly as
   `cloudId` first. If that fails, call `mcp__atlassian__getAccessibleAtlassianResources` and use
   the returned `id`.
2. Call `mcp__atlassian__getJiraIssue` with the resolved `cloudId`, the issue key, and
   `fields: ["summary","description","status","issuetype","priority","labels","components","assignee","reporter"]`.
3. If the issue has linked sub-tasks or an epic that materially changes scope, it's fine to
   fetch those too, but don't go spelunking through the whole project — one issue is the unit of
   work here.
4. Change the jira status from 'TODO' to 'In Progress' 

If the issue can't be found (bad key, no access), say so plainly and stop — don't fall back to
inventing requirements.

## Step 2 — Summarize

Present a short, plain-language summary before anything else — no code, no file exploration
beyond what's needed to sanity-check feasibility. Cover:

- **What's being asked**, in your own words (don't just paste the Jira description back).
- **Where it likely lands** in this codebase's layers (`app/ui`, `app/controllers`,
  `app/repositories`, `app/models`, `app/db`, etc.) — see the architecture section of
  `CLAUDE.md`. This is a quick read of the ticket against the layering, not a full design doc.
- **Anything ambiguous or underspecified** in the story — acceptance criteria that seem to
  contradict `requirements.md`, missing detail on edge cases, or scope that seems bigger than a
  single story. Ask about these now, before the confirmation step, if they'd change what "done"
  means.
- Check `requirements.md` and `PROGRESS.md`'s "Key design decisions already made" section for
  anything relevant to the feature (autosave, theming, filtering, DB-path, PyInstaller bundling
  are the areas explicitly called out there) — flag it if the story looks like it conflicts with
  an existing decision, rather than silently overriding it.

## Step 3 — Confirm before starting (hard gate)

Use `AskUserQuestion` to get an explicit go-ahead. Something like:

- **Question**: "Ready to start implementing `<the resolved issue key>` as summarized above?"
  (use the actual key from step 1, e.g. `SCRUM-23` — never a hardcoded example key)
- **Options**: proceed as scoped / hold off (I want to change something first) / narrow or
  adjust the scope

Do not write, edit, or run anything beyond read-only exploration until the user confirms. If
they want changes to scope, update the summary and ask again — don't silently reinterpret.

## Step 4 — Implement

Once confirmed, implement the change following this repo's rules from `CLAUDE.md`:

- Respect the strict layering (`app/ui/` and `app/controllers/` never import `sqlite3`;
  `app/repositories/` and `app/models/` never import `PySide6`; no networking modules anywhere in
  `app/`). `tests/test_architecture_boundaries.py` enforces this at build time, so a violation
  isn't just style — it fails the suite.
- Keep the change scoped to what was confirmed in step 3. If while implementing you discover the
  story needs more than expected (e.g. a schema/migration change nobody flagged), stop and check
  with the user rather than expanding scope unilaterally.
- Follow existing patterns in the touched files rather than introducing a new style — this
  codebase has consistent conventions per layer (dataclasses + `from_row()` in `app/models/`, one
  repository method per table-ish concern, controller-mediated writes, etc.).

## Step 5 — Unit testing

Once the change is implemented:

1. Write or extend tests under `tests/` matching the existing conventions for the layer touched
   (plain `conn`-fixture tests for repositories, `qtbot`-driven tests under `tests/ui/` for
   widgets — see the "Testing conventions" section of `CLAUDE.md`, including the notes on
   `QTest.qWait` for debounce/polling timers and driving real widgets instead of calling
   controller methods directly).
2. Run the full suite: `QT_QPA_PLATFORM=offscreen pytest`. Don't stop at "the new test passes" —
   a layering or autosave change can break unrelated tests.
3. If anything fails, fix it and rerun until the suite is green. Report the actual pass/fail
   counts — don't claim success without having run it.

## Step 6 — Wrap up

- Summarize what changed: files touched, and a one-line mapping back to the story's acceptance
  criteria (does each point from the ticket have a corresponding change?).
- Report the final test run result verbatim (counts, not just "tests pass").
- `PROGRESS.md`/`tasklist.md` get updated per *phase*, not per individual task/story — don't
  update them reflexively here. If this story completes a phase of work, ask the user whether
  they want those docs updated now.
- Optionally offer (don't do it unasked) to post a summary comment back on the Jira issue via
  `mcp__atlassian__addCommentToJiraIssue`, or transition its status via
  `mcp__atlassian__getTransitionsForJiraIssue` + `mcp__atlassian__transitionJiraIssue`.