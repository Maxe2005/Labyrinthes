---
baseline_commit: a757ec25552eaed6d0f257b90450f4d6a92c4728
---

# Story 1.12: Persistence hardening — atomic writes & typed errors

Status: ready-for-dev

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

- [ ] **Task 1 -- Shared atomic-write helper** (AC: 1)
  - [ ] New module `src/labyrinthes/adapters/storage/atomic_write.py`: a context manager `atomic_open_for_write(path: Path, *, encoding: str, newline: str | None = None)` that opens a temp file **in the same directory as `path`** (so the final rename is atomic on the same filesystem -- never a cross-filesystem temp dir like the OS default), yields the writable handle, and on a clean `with` exit calls `os.replace(tmp_path, path)` (atomic on both POSIX and Windows, unlike `Path.rename`). On an exception raised *inside* the `with` block, close and delete the temp file, then re-raise -- a failed write must never partially replace the previous good file, and must never leave a stray `.tmp` file behind. Callers are responsible for `path.parent.mkdir(parents=True, exist_ok=True)` before calling this (both existing writers already do) -- this helper doesn't duplicate that.
  - [ ] `tests/adapters/storage/test_atomic_write.py`: happy path (content matches, no leftover temp file); a writer that raises mid-write (an existing prior file, if any, is untouched; no stray temp file left in the directory).
  - [ ] Rewire `write_maze_csv` (`csv_maze_format.py`) to open via `atomic_open_for_write(path, encoding="utf-8", newline="")` instead of `path.open("w", ...)` directly -- every other line (the `csv.writer(..., lineterminator="\n")` calls) stays unchanged.
  - [ ] Rewire `write_setting_value` (`settings_format.py`) to open via `atomic_open_for_write(path, encoding="utf-8")` instead of `path.open("w", ...)` directly -- the `json.dump(value, handle)` call stays unchanged.
  - [ ] Add one crash-mid-write regression test to each of `test_csv_maze_format.py` and `test_settings_format.py`: write a first, valid file; then attempt a second write that's forced to fail partway (e.g. monkeypatch the writer to raise after some output); assert the file on disk still round-trips to the *first* write's content, not a truncated/corrupted mix.

- [ ] **Task 2 -- Typed error for malformed maze CSV content** (AC: 2)
  - [ ] Add `MazeCorruptError(LabyrinthesError)` to `application/errors.py`, alongside `MazeNotFoundError`/`SettingNotFoundError` -- **not** to `adapters/storage/errors.py`. Rationale (see Dev Notes): this is a port-level failure mode ("the port cannot return a valid value"), the same category as "not found," not an adapter-implementation-specific concern like `InvalidMazeNameError`'s CSV-filename-mapping validation. Keeping it at the `application/` layer means any future second `MazeRepository` implementation raises the same error for "content unreadable," and `app/`-layer consumers never need to import anything from `adapters/storage/errors.py` directly.
  - [ ] In `read_maze_csv` (`csv_maze_format.py`), wrap only the header-line parsing (`lines[0]`/`lines[1]` indexing and their `int(...)` conversions, and `remaining[0]` indexing for the `MazeId` line) in `try`/`except (IndexError, ValueError) as exc: raise MazeCorruptError(...) from exc`. **Do not** touch `Cell(value)` construction -- an invalid cell digit already raises `DomainValidationError` (a `LabyrinthesError` subclass, confirmed in `domain/cell.py`), which already satisfies "typed error, not raw" without any change here.
  - [ ] `csv_maze_repository.py`'s `find_by_id` already catches `(OSError, ValueError, LabyrinthesError)` around its `read_maze_csv` call -- `MazeCorruptError` is already covered by the `LabyrinthesError` arm. Add a test proving this explicitly (a corrupt file among otherwise-valid ones is still skipped, not raised) rather than assuming it -- `find_by_id`'s existing `test_find_by_id_skips_an_unrelated_file_that_fails_to_parse` may already cover this; check before adding a duplicate.
  - [ ] `load()` (`csv_maze_repository.py`) has no `try`/`except` around `read_maze_csv` today and needs none added -- `read_maze_csv` now raises the typed error itself, which is sufficient to satisfy AC 2 (a typed error propagates out of `load()` instead of a raw one).
  - [ ] `test_csv_maze_format.py`: add cases for a truncated file (0 or 1 lines), a non-numeric entry/exit header value, and a file missing its `MazeId` line for an id-eligible `kind` -- each raises `MazeCorruptError`.

- [ ] **Task 3 -- Typed error for malformed settings content, TOCTOU handling** (AC: 3)
  - [ ] Add `SettingCorruptError(LabyrinthesError)` to `application/errors.py`, alongside `SettingNotFoundError` -- same layering rationale as Task 2's `MazeCorruptError`.
  - [ ] In `read_setting_value` (`settings_format.py`), wrap `json.load(handle)` in `try`/`except json.JSONDecodeError as exc: raise SettingCorruptError(...) from exc`.
  - [ ] In `JsonSettingsRepository.get()` (`json_settings_repository.py`), wrap the `read_setting_value(path)` call in `try`/`except FileNotFoundError: raise SettingNotFoundError(f"No {scope.value} setting named {key!r}") from None` -- covers the TOCTOU race between its own `path.is_file()` check and the read (file deleted/replaced by a directory in between). This reuses the existing not-found error, deliberately -- see AC 3's second sentence.
  - [ ] `test_settings_format.py`: malformed/non-JSON file content raises `SettingCorruptError`.
  - [ ] `test_json_settings_repository.py`: a directly malformed file (write invalid JSON to the path `get()` will read) raises `SettingCorruptError` through `get()`; the TOCTOU race is acceptable to leave as a targeted unit test directly on the `except FileNotFoundError` branch (e.g. call `JsonSettingsRepository.get()` against a path that `is_file()` reports true for via a stub/monkeypatch, but that raises `FileNotFoundError` on open) rather than attempting a real race condition, which would be flaky.

- [ ] **Task 4 -- Close the `ThemeController` startup-crash escalation** (AC: 4)
  - [ ] `ThemeController._load_theme()` (`app/theme_controller.py`) already catches `(SettingNotFoundError, ValueError)` and defaults to `Theme.LIGHT`. Add `SettingCorruptError` to that same `except` tuple, importing it from `labyrinthes.application.errors` (already imports `SettingNotFoundError` from there -- one more name from the same module, no new import path).
  - [ ] Add a regression test in `theme_controller`'s test file: a `SettingsRepository` test double whose `get()` raises `SettingCorruptError` still lets `ThemeController()` construct successfully with `theme == Theme.LIGHT`.

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

### Debug Log References

### Completion Notes List

### File List
