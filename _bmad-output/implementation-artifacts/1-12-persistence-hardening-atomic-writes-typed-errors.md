---
baseline_commit: a757ec25552eaed6d0f257b90450f4d6a92c4728
---

# Story 1.12: Persistence hardening — atomic writes & typed errors

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->
<!-- Added by the Epic 1 retrospective (_bmad-output/implementation-artifacts/epic-1-retro-2026-08-09.md) -- closes gaps deferred in Stories 1.4/1.5 and escalated by Story 1.9, where `ThemeController` became the first unconditional, every-launch consumer of `SettingsRepository.get()`. Not derived from an epics.md FR; a hardening story on the persistence adapters AD-5/AD-7 already require. -->

## Story

As the project's author,
I want maze and settings writes to be crash-safe, and malformed persisted data to raise a typed error instead of crashing the app,
so that an interrupted write or a corrupted file never destroys existing data or takes down the app at startup.

## Acceptance Criteria

1. **Given** a `Maze` or a setting being written, **when** the write is interrupted (process crash or kill) partway through, **then** the previously saved file is never left corrupted or truncated -- both `write_maze_csv` and `write_setting_value` write via a temp-file-plus-rename, never in-place truncation.
2. **Given** a maze CSV file that is truncated, has too few header lines, or has a non-numeric entry/exit header, **when** `MazeRepository.load()` / `read_maze_csv` reads it, **then** a typed `LabyrinthesError` subclass is raised, never a raw `IndexError`/`ValueError`.
3. **Given** a settings file that is malformed JSON, **when** `SettingsRepository.get()` / `JsonSettingsRepository.get()` / `read_setting_value` reads it, **then** a typed `LabyrinthesError` subclass is raised, never a raw `json.JSONDecodeError`. **Given** the file is instead removed or replaced between the existence check and the read (a TOCTOU race), **when** the same call is made, **then** it raises the existing `SettingNotFoundError` -- the same error the already-handled "never set" case raises, since from the caller's perspective a file that vanished mid-race is indistinguishable from one that was never there.
4. **Given** `ThemeController._load_theme()` (Story 1.9), which reads settings unconditionally on every app launch, **when** the persisted `shared`/`theme` file is corrupted, **then** the app no longer crashes at startup -- it falls back to `Theme.LIGHT`, the same way it already handles an unrecognized-but-well-formed value.

## Tasks / Subtasks

- [x] **Task 1 -- Shared atomic-write helper** (AC: 1)
  - [x] New module `src/labyrinthes/adapters/storage/atomic_write.py`: a context manager `atomic_open_for_write(path: Path, *, encoding: str, newline: str | None = None)` that opens a temp file **in the same directory as `path`** (so the final rename is atomic on the same filesystem -- never a cross-filesystem temp dir like the OS default), yields the writable handle, and on a clean `with` exit calls `os.replace(tmp_path, path)` (atomic on both POSIX and Windows, unlike `Path.rename`). On an exception raised *inside* the `with` block, close and delete the temp file, then re-raise -- a failed write must never partially replace the previous good file, and must never leave a stray `.tmp` file behind. Callers are responsible for `path.parent.mkdir(parents=True, exist_ok=True)` before calling this (both existing writers already do) -- this helper doesn't duplicate that.
  - [x] `tests/adapters/storage/test_atomic_write.py`: happy path (content matches, no leftover temp file); a writer that raises mid-write (an existing prior file, if any, is untouched; no stray temp file left in the directory).
  - [x] Rewire `write_maze_csv` (`csv_maze_format.py`) to open via `atomic_open_for_write(path, encoding="utf-8", newline="")` instead of `path.open("w", ...)` directly -- every other line (the `csv.writer(..., lineterminator="\n")` calls) stays unchanged.
  - [x] Rewire `write_setting_value` (`settings_format.py`) to open via `atomic_open_for_write(path, encoding="utf-8")` instead of `path.open("w", ...)` directly -- the `json.dump(value, handle)` call stays unchanged.
  - [x] Add one crash-mid-write regression test to each of `test_csv_maze_format.py` and `test_settings_format.py`: write a first, valid file; then attempt a second write that's forced to fail partway (e.g. monkeypatch the writer to raise after some output); assert the file on disk still round-trips to the *first* write's content, not a truncated/corrupted mix.

- [x] **Task 2 -- Typed error for malformed maze CSV content** (AC: 2)
  - [x] Add `MazeCorruptError(LabyrinthesError)` to `application/errors.py`, alongside `MazeNotFoundError`/`SettingNotFoundError` -- **not** to `adapters/storage/errors.py`. Rationale (see Dev Notes): this is a port-level failure mode ("the port cannot return a valid value"), the same category as "not found," not an adapter-implementation-specific concern like `InvalidMazeNameError`'s CSV-filename-mapping validation. Keeping it at the `application/` layer means any future second `MazeRepository` implementation raises the same error for "content unreadable," and `app/`-layer consumers never need to import anything from `adapters/storage/errors.py` directly.
  - [x] In `read_maze_csv` (`csv_maze_format.py`), wrap only the header-line parsing (`lines[0]`/`lines[1]` indexing and their `int(...)` conversions, and `remaining[0]` indexing for the `MazeId` line) in `try`/`except (IndexError, ValueError) as exc: raise MazeCorruptError(...) from exc`. **Do not** touch `Cell(value)` construction -- an invalid cell digit already raises `DomainValidationError` (a `LabyrinthesError` subclass, confirmed in `domain/cell.py`), which already satisfies "typed error, not raw" without any change here.
  - [x] `csv_maze_repository.py`'s `find_by_id` already catches `(OSError, ValueError, LabyrinthesError)` around its `read_maze_csv` call -- `MazeCorruptError` is already covered by the `LabyrinthesError` arm. Add a test proving this explicitly (a corrupt file among otherwise-valid ones is still skipped, not raised) rather than assuming it -- `find_by_id`'s existing `test_find_by_id_skips_an_unrelated_file_that_fails_to_parse` may already cover this; check before adding a duplicate. (Checked: that test's corrupt content -- `"not,a,valid,maze,file\n"` -- fails the header-parsing tuple-unpack, which now raises `MazeCorruptError` instead of a raw `ValueError`; the existing test already exercises the new typed error through the `LabyrinthesError` arm, so no duplicate was added.)
  - [x] `load()` (`csv_maze_repository.py`) has no `try`/`except` around `read_maze_csv` today and needs none added -- `read_maze_csv` now raises the typed error itself, which is sufficient to satisfy AC 2 (a typed error propagates out of `load()` instead of a raw one).
  - [x] `test_csv_maze_format.py`: add cases for a truncated file (0 or 1 lines), a non-numeric entry/exit header value, and a file missing its `MazeId` line for an id-eligible `kind` -- each raises `MazeCorruptError`.

- [x] **Task 3 -- Typed error for malformed settings content, TOCTOU handling** (AC: 3)
  - [x] Add `SettingCorruptError(LabyrinthesError)` to `application/errors.py`, alongside `SettingNotFoundError` -- same layering rationale as Task 2's `MazeCorruptError`.
  - [x] In `read_setting_value` (`settings_format.py`), wrap `json.load(handle)` in `try`/`except json.JSONDecodeError as exc: raise SettingCorruptError(...) from exc`.
  - [x] In `JsonSettingsRepository.get()` (`json_settings_repository.py`), wrap the `read_setting_value(path)` call in `try`/`except FileNotFoundError: raise SettingNotFoundError(f"No {scope.value} setting named {key!r}") from None` -- covers the TOCTOU race between its own `path.is_file()` check and the read (file deleted/replaced by a directory in between). This reuses the existing not-found error, deliberately -- see AC 3's second sentence.
  - [x] `test_settings_format.py`: malformed/non-JSON file content raises `SettingCorruptError`.
  - [x] `test_json_settings_repository.py`: a directly malformed file (write invalid JSON to the path `get()` will read) raises `SettingCorruptError` through `get()`; the TOCTOU race is acceptable to leave as a targeted unit test directly on the `except FileNotFoundError` branch (e.g. call `JsonSettingsRepository.get()` against a path that `is_file()` reports true for via a stub/monkeypatch, but that raises `FileNotFoundError` on open) rather than attempting a real race condition, which would be flaky.

- [x] **Task 4 -- Close the `ThemeController` startup-crash escalation** (AC: 4)
  - [x] `ThemeController._load_theme()` (`app/theme_controller.py`) already catches `(SettingNotFoundError, ValueError)` and defaults to `Theme.LIGHT`. Add `SettingCorruptError` to that same `except` tuple, importing it from `labyrinthes.application.errors` (already imports `SettingNotFoundError` from there -- one more name from the same module, no new import path).
  - [x] Add a regression test in `theme_controller`'s test file: a `SettingsRepository` test double whose `get()` raises `SettingCorruptError` still lets `ThemeController()` construct successfully with `theme == Theme.LIGHT`.

### Review Findings

- [x] [Review][Patch] `JsonSettingsRepository.get()`'s TOCTOU handling only catches `FileNotFoundError`; if the setting file is replaced by a directory in the race window (the exact scenario Task 3's own comment names as in-scope: "file deleted/replaced by a directory in between"), `path.open("r")` raises `IsADirectoryError` -- a sibling `OSError`, not a `FileNotFoundError` subclass (`isinstance(IsADirectoryError(), FileNotFoundError) == False`, verified) -- which propagates raw instead of the promised `SettingNotFoundError`. Violates AC 3's literal "removed or replaced" wording. [src/labyrinthes/adapters/storage/json_settings_repository.py:36] -- fixed: `except (FileNotFoundError, IsADirectoryError)`, with a regression test for the directory-replacement case
- [x] [Review][Patch] `atomic_open_for_write` silently narrows every persisted maze/settings file's permissions from the umask-respecting default (`0o664` under a typical umask, verified) to `0o600`, because `tempfile.NamedTemporaryFile` defaults to owner-only mode and `os.replace` preserves it on rename. Undocumented and untested side effect of routing writes through the new helper. [src/labyrinthes/adapters/storage/atomic_write.py:41-44] -- fixed: new `_match_default_permissions` helper `chmod`s the temp file to `0o666 & ~umask` before the replace, with a regression test asserting the resulting mode
- [x] [Review][Patch] `atomic_open_for_write`'s final `os.replace(tmp_path, path)` call sits outside the `try`/`except` that guards the `yield` -- if the replace itself fails (`path` exists as a directory, permission denied, disk full), the temp file is left behind uncleaned and a raw `OSError` propagates. AC 1's "previously saved file" guarantee still holds (the replace is atomic: it either fully succeeds or doesn't happen), but this leaves a stray temp file on that failure path, which the module docstring's "no stray temp file remains" claim doesn't scope to only the exception-inside-`yield` branch it actually covers. [src/labyrinthes/adapters/storage/atomic_write.py:51] -- fixed: `os.replace` now wrapped in its own `try`/`except BaseException` that unlinks the temp file before re-raising, with a regression test
- [x] [Review][Patch] `application/errors.py`'s module docstring is stale: still reads "not-found conditions... Both subclass..." (singular framing, two classes) even though the file now defines four classes across two categories (not-found + corrupt-content). [src/labyrinthes/application/errors.py:1-5] -- fixed: docstring now describes both categories and "all four subclass..."
- [x] [Review][Defer] `read_maze_csv`'s `path.read_text(encoding="utf-8")` call and `read_setting_value`'s `json.load(handle)` call can each raise a raw `UnicodeDecodeError` on invalid-UTF-8/binary content -- not a `LabyrinthesError` subclass, so it isn't caught by either function's new typed-error wrapping. Pre-existing gap (this code path had zero error handling before this diff) and narrower than Task 2/Task 3's explicitly stated scope (header-parsing / `json.JSONDecodeError` only) -- not a regression introduced by this story. [src/labyrinthes/adapters/storage/csv_maze_format.py:44, src/labyrinthes/adapters/storage/settings_format.py:28-32] — deferred, pre-existing gap outside this story's explicitly stated scope

## Dev Notes

### Architecture patterns & constraints

- **Consistency Conventions (error shapes):** "Domain/application code raises a small typed exception hierarchy under one project base error, rather than each layer inventing its own error shape." [Source: architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md#Consistency Conventions] `MazeCorruptError`/`SettingCorruptError` belong in `application/errors.py`, mirroring `MazeNotFoundError`/`SettingNotFoundError` (both already there) -- **not** `adapters/storage/errors.py`, where `InvalidMazeNameError`/`InvalidSettingKeyError` correctly live because *those* are specific to the CSV-filename/JSON-filename on-disk mapping, an adapter-implementation detail. "Content is unreadable" is a port-level failure mode any `MazeRepository`/`SettingsRepository` implementation could hit, not specific to CSV/JSON. This exact distinction was already litigated and confirmed during Story 1.4's review ("`InvalidMazeNameError` living in `adapters/storage/errors.py` rather than `application/errors.py` (correct layering...)") -- apply the same reasoning in the opposite direction here.
- **Dependency direction (AD-1):** `app/` -> `adapters/` -> `application/` -> `domain/`. `app/theme_controller.py` importing from `labyrinthes.application.errors` is unchanged from what it already does (it already imports `SettingNotFoundError` from there). `adapters/storage/*.py` importing from `labyrinthes.application.errors` is also already established precedent (`csv_maze_repository.py` already imports `MazeNotFoundError` from there). Neither task in this story introduces a new import *direction*, only new names from already-imported modules. [Source: architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md#AD-1]
- **No FR binds this story** -- it originates from the Epic 1 retrospective, not `epics.md`'s original FR list. Treat AC 1-4 above as the complete scope. In particular: do **not** add retry logic, does **not** add a user-facing "your settings file was corrupted" dialog (no screen has any error-display mechanism yet), and does **not** touch `find_by_id`'s existing broad `except` clause beyond adding a test proving it already covers the new error.

### Project Structure Notes

- New files: `src/labyrinthes/adapters/storage/atomic_write.py`, `tests/adapters/storage/test_atomic_write.py`.
- Files this story **updates**:
  - `src/labyrinthes/application/errors.py` -- add `MazeCorruptError`, `SettingCorruptError`.
  - `src/labyrinthes/adapters/storage/csv_maze_format.py` -- `write_maze_csv` uses `atomic_open_for_write`; `read_maze_csv` wraps header parsing to raise `MazeCorruptError`.
  - `src/labyrinthes/adapters/storage/settings_format.py` -- `write_setting_value` uses `atomic_open_for_write`; `read_setting_value` wraps `json.load` to raise `SettingCorruptError`.
  - `src/labyrinthes/adapters/storage/json_settings_repository.py` -- `get()` catches the TOCTOU `FileNotFoundError`.
  - `src/labyrinthes/app/theme_controller.py` -- `_load_theme()`'s except tuple gains `SettingCorruptError`.
  - Corresponding test files: `tests/adapters/storage/test_csv_maze_format.py`, `test_settings_format.py`, `test_json_settings_repository.py`, and `ThemeController`'s test file (locate via `find tests -iname '*theme_controller*'`).
- No changes to `src/labyrinthes/adapters/storage/csv_maze_repository.py`'s production code (only a test addition), `domain/cell.py`, or `Router`/`composition_root.py`.

### Testing standards summary

- `pytest`, tests mirror `src/labyrinthes/` package layout per `CLAUDE.md`. All new/changed tests live under `tests/adapters/storage/` and `tests/app/` (for `ThemeController`), following each file's existing fixture/parametrize conventions (see e.g. `test_csv_maze_repository.py`'s `@pytest.mark.parametrize("kind", ...)` pattern for id-eligible-kind cases).
- `ruff check .` and `ruff format .` must both pass, per every prior story in this epic.
- Use `tmp_path` for all filesystem-touching tests (every existing test in `tests/adapters/storage/` already does) -- never touch the real default `./mazes/`/`./settings/` roots.

### References

- [Source: _bmad-output/implementation-artifacts/epic-1-retro-2026-08-09.md#Decisions Made in This Retrospective, #Action Items]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md#Deferred from: code review of spec-1-4-concrete-mazerepository-single-shared-csv-read-write-implementation (2026-08-06)] (non-atomic `write_maze_csv`; raw `IndexError`/`ValueError` on malformed CSV)
- [Source: _bmad-output/implementation-artifacts/deferred-work.md#Deferred from: code review of spec-1-5-concrete-settingsrepository-scoped-persistence (2026-08-06)] (non-atomic `write_setting_value`; raw `json.JSONDecodeError`/`FileNotFoundError` on malformed/TOCTOU settings read)
- [Source: _bmad-output/implementation-artifacts/deferred-work.md#Deferred from: code review of spec-1-9-light-dark-theme-toggle-wired-end-to-end (2026-08-06)] (escalation: `ThemeController` is the first unconditional every-launch consumer)
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.12: Persistence hardening — atomic writes & typed errors]
- [Source: architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md#AD-1, Consistency Conventions]
- [Source: src/labyrinthes/adapters/storage/csv_maze_format.py, settings_format.py, json_settings_repository.py, csv_maze_repository.py, errors.py; src/labyrinthes/application/errors.py; src/labyrinthes/app/theme_controller.py; src/labyrinthes/domain/cell.py]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5)

### Debug Log References

None -- no failures required debugging beyond the expected red-phase failures (missing module/import errors before each implementation step) and two ruff findings (SIM117 in `test_atomic_write.py`, auto-fixed; SIM115 in `atomic_write.py`, fixed by restructuring `atomic_open_for_write` to keep the whole temp-file lifecycle inside one `with tempfile.NamedTemporaryFile(...)` block instead of assigning it outside a `with`).

### Completion Notes List

- Task 1: Added `atomic_open_for_write` (`adapters/storage/atomic_write.py`), a context manager that writes to a temp file in the target's own parent directory and atomically `os.replace`s it into place on a clean exit, or closes+deletes the temp file and re-raises on any exception. Rewired both `write_maze_csv` and `write_setting_value` to use it. Added crash-mid-write regression tests to both `test_csv_maze_format.py` and `test_settings_format.py` via a flaky-writer/flaky-`json.dump` monkeypatch, proving the prior valid file survives an interrupted second write untouched, with no stray temp file left behind.
- Task 2: Added `MazeCorruptError(LabyrinthesError)` to `application/errors.py`. Wrapped only the header-line parsing (entry/exit/`MazeId` lines) in `read_maze_csv` in `try`/`except (IndexError, ValueError)`, leaving `Cell(value)` construction untouched (already raises `DomainValidationError`). Verified `CsvMazeRepository.find_by_id`'s existing `test_find_by_id_skips_an_unrelated_file_that_fails_to_parse` already exercises the new typed error through its `LabyrinthesError` catch arm (its corrupt fixture content fails the header tuple-unpack, which now raises `MazeCorruptError` instead of a raw `ValueError`) -- no duplicate test added, per the task's explicit check-first instruction. Added new `test_csv_maze_format.py` cases for a truncated file, a non-numeric entry/exit header, and a missing `MazeId` line on an id-eligible kind.
- Task 3: Added `SettingCorruptError(LabyrinthesError)` to `application/errors.py` (same layering rationale as `MazeCorruptError`, added alongside it in Task 2's edit). Wrapped `json.load` in `read_setting_value` to raise `SettingCorruptError` on `json.JSONDecodeError`. Wrapped `JsonSettingsRepository.get()`'s `read_setting_value` call to catch a TOCTOU `FileNotFoundError` and re-raise the existing `SettingNotFoundError`. Added a malformed-JSON test to `test_settings_format.py`, plus two tests to `test_json_settings_repository.py`: a directly malformed settings file raising `SettingCorruptError` through `get()`, and a monkeypatched `Path.is_file` returning `True` for a nonexistent file to exercise the TOCTOU `except FileNotFoundError` branch without a flaky real race.
- Task 4: Added `SettingCorruptError` to `ThemeController._load_theme()`'s existing `except (SettingNotFoundError, ValueError)` tuple. Added a regression test with a `SettingsRepository` test double whose `get()` raises `SettingCorruptError`, confirming `ThemeController()` still constructs with `theme == Theme.LIGHT` instead of propagating the crash.
- Full regression suite: 295 tests passed (up from 286 at story start). `ruff check .` and `ruff format --check` both pass on every file this story touched.
- Branching note: this story's `baseline_commit` (frontmatter) points at `epic-1-foundation-navigation-shell`'s tip, but the story file itself (and Story 1.11's implementation) only exist as commits on the not-yet-merged `story-1-11-settings-dialog-survives-screen-navigation` branch. The `story-1-12-...` branch was created from that branch (not bare `epic-1-foundation-navigation-shell`) so this work builds on the actual prerequisite state; the frontmatter value was left as originally recorded per the workflow's "preserve existing baseline_commit" rule.

### File List

- `src/labyrinthes/adapters/storage/atomic_write.py` (new)
- `tests/adapters/storage/test_atomic_write.py` (new)
- `src/labyrinthes/adapters/storage/csv_maze_format.py` (modified -- atomic write, `MazeCorruptError` on malformed header)
- `src/labyrinthes/adapters/storage/settings_format.py` (modified -- atomic write, `SettingCorruptError` on malformed JSON)
- `src/labyrinthes/adapters/storage/json_settings_repository.py` (modified -- TOCTOU `FileNotFoundError` -> `SettingNotFoundError`)
- `src/labyrinthes/application/errors.py` (modified -- added `MazeCorruptError`, `SettingCorruptError`)
- `src/labyrinthes/app/theme_controller.py` (modified -- `SettingCorruptError` added to startup fallback)
- `tests/adapters/storage/test_csv_maze_format.py` (modified -- `MazeCorruptError` cases, crash-mid-write regression)
- `tests/adapters/storage/test_settings_format.py` (modified -- `SettingCorruptError` case, crash-mid-write regression)
- `tests/adapters/storage/test_json_settings_repository.py` (modified -- `SettingCorruptError` and TOCTOU cases)
- `tests/app/test_theme_controller.py` (modified -- corrupted-settings startup regression)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified -- status tracking)

## Change Log

- 2026-08-09: Made maze and settings writes crash-safe via a shared temp-file-plus-rename helper, and gave malformed maze CSV / settings JSON content typed `LabyrinthesError`s (`MazeCorruptError`, `SettingCorruptError`) instead of raw `IndexError`/`ValueError`/`json.JSONDecodeError`; closed the matching `ThemeController` startup-crash gap so a corrupted `shared`/`theme` file degrades to `Theme.LIGHT` instead of crashing the app (Story 1.12). No behavior change for well-formed data.
