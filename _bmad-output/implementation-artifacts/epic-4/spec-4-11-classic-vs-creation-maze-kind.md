---
title: 'Story 4.11: Classic vs. Creation maze kind'
type: 'feature'
created: '2026-08-27'
status: 'done'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The legacy app ships with two separate maze folders: `Labyrinthes_classiques/` (dev-authored mazes included with the game) and `Labyrinthes_creation/` (mazes the player builds and saves). The rewrite's `MazeKind` enum only has `CLASSIC` and `SAVED_RANDOM` as id-eligible kinds, so a maze saved from the Builder currently becomes `CLASSIC` — conflating dev-authored content with player creations. FR-35 requires a distinct `CREATION` kind so provenance is preserved and "Classic" stays reserved for shipped mazes.

**Approach:** Add `MazeKind.CREATION` to the domain enum. Update the Builder's "Save as Maze" flow to produce `CREATION` instead of `CLASSIC`. Extend `MazeRepository` id-minting to include `CREATION` (same rule as `CLASSIC`/`SAVED_RANDOM`). `RecordsService` eligibility (Epic 6) will extend to `CREATION` on the same terms.

## Boundaries & Constraints

**Always:** `MazeKind` is a pure `domain/` enum — no UI or storage concerns leak into it. The `CREATION` kind is added as a fifth member alongside `CLASSIC`, `SKETCH`, `SAVED_RANDOM`, `GENERATED`. `_ID_ELIGIBLE_KINDS` extends to include `CREATION` in all three locations (`domain/maze.py`, `adapters/storage/csv_maze_format.py`, `adapters/storage/csv_maze_repository.py`). The on-disk folder for `CREATION` mazes is `mazes/creation/` (derived from `kind.value` in `paths.py` — no new code). `MazeId` minting uses the shared `mint_maze_id()` function identically for `CLASSIC`, `SAVED_RANDOM`, and `CREATION`. The Builder's save flow sets `kind=CREATION` (not `CLASSIC`) when the exit is set. No automatic reclassification of existing `CLASSIC`-folder test fixtures — manual cleanup is acceptable for dev scratch data.

**Ask First:** None — the kind name, id-eligibility, and folder naming follow directly from FR-35 and the existing patterns.

**Never:** Never add a new `MazeKind` beyond `CREATION`. Never change the `MazeId` format or minting logic. Never make `CREATION` mazes load from or write to the `classic` folder. Never add a `name` field to the `Maze` domain value (name remains a storage-layer concept, per Story 4.13). Never duplicate the `_ID_ELIGIBLE_KINDS` logic — it stays in the three canonical locations only.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Builder saves a finished maze (entry+exit set) | `Maze` with `kind=SKETCH` or `GENERATED`, exit set | Saved maze has `kind=CREATION`, `id` minted, file at `mazes/creation/<name>.csv` | N/A |
| Builder re-saves an existing `CREATION` maze | `Maze` with `kind=CREATION`, `id` already set | Existing `id` carried forward, file overwritten at `mazes/creation/<name>.csv` | N/A |
| Load a `CREATION` maze by name | `load(name, MazeKind.CREATION)` | Returns `Maze` with `kind=CREATION`, `id` from file | `MazeNotFoundError` if missing |
| `find_by_id` lookup | `MazeId` from a `CREATION` maze | Scans `creation/` folder alongside `classic/` and `saved-random/`, returns matching `Maze` or `None` | Skips corrupt files, continues scan |
| List `CREATION` names | `list_names(MazeKind.CREATION)` | Returns sorted names from `mazes/creation/` | Returns `[]` if folder missing |
| `Maze` validation | `Maze(kind=CREATION, id=None)` | Valid (id minted on save) | N/A |
| `Maze` validation | `Maze(kind=CREATION, id=some_id)` | Valid | N/A |
| `Maze` validation | `Maze(kind=SKETCH, id=some_id)` | Invalid — raises `DomainValidationError` | Enforced by `__post_init__` |

</frozen-after-approval>

## Code Map

- `src/labyrinthes/domain/maze.py` -- `MazeKind` enum (line 12-18): add `CREATION = "creation"`; `_ID_ELIGIBLE_KINDS` (line 21): extend to include `MazeKind.CREATION`
- `src/labyrinthes/adapters/storage/csv_maze_format.py` -- `_ID_ELIGIBLE_KINDS` (line 35): extend to include `MazeKind.CREATION`; `read_maze_csv`/`write_maze_csv` already use this set for id line presence
- `src/labyrinthes/adapters/storage/csv_maze_repository.py` -- `_ID_ELIGIBLE_KINDS` (line 21): extend to include `MazeKind.CREATION`; `_ID_LOOKUP_KINDS` (line 23): extend tuple to include `MazeKind.CREATION` for `find_by_id` scan order
- `src/labyrinthes/adapters/tkinter/builder/edit_area.py` -- `_ID_ELIGIBLE_KINDS` (line 115): extend to include `MazeKind.CREATION`; `save_maze`/`_open_save_dialog_for_maze` (lines 715-751): change target kind from `MazeKind.CLASSIC` to `MazeKind.CREATION` when promoting a non-id-eligible maze
- `src/labyrinthes/adapters/storage/paths.py` -- `maze_file_path` (line 22): no change needed — uses `kind.value` which will be `"creation"` for the new enum member
- `src/labyrinthes/application/maze_repository.py` -- docstring (lines 22-23, 48-50): update comments to include `CREATION` alongside `CLASSIC`/`SAVED_RANDOM` as id-eligible kinds

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/domain/maze.py` -- add `CREATION = "creation"` to `MazeKind` enum, extend `_ID_ELIGIBLE_KINDS` frozenset -- AC 1, 2
- [x] `src/labyrinthes/adapters/storage/csv_maze_format.py` -- extend `_ID_ELIGIBLE_KINDS` frozenset -- AC 1, 2
- [x] `src/labyrinthes/adapters/storage/csv_maze_repository.py` -- extend `_ID_ELIGIBLE_KINDS` and `_ID_LOOKUP_KINDS` -- AC 1, 2, 3, 4, 5
- [x] `src/labyrinthes/adapters/tkinter/builder/edit_area.py` -- extend local `_ID_ELIGIBLE_KINDS`, change save promotion target from `CLASSIC` to `CREATION` -- AC 1, 2
- [x] `src/labyrinthes/application/maze_repository.py` -- update port docstrings to include `CREATION` in id-eligible kinds -- AC 1, 2
- [x] Tests -- verify `CREATION` kind works end-to-end: save from Builder → file in `mazes/creation/`, load back, `find_by_id` finds it, `list_names` lists it -- AC 1-5
- [x] Run `ruff check src/`, `ruff format --check src/`, `pytest` (relevant tests) -- all green

**Acceptance Criteria:**
- Given the Builder's "Save as Maze" flow with a maze that has entry and exit set, when confirmed, then the resulting `Maze` carries `MazeKind.CREATION` (not `CLASSIC`).
- Given a `CREATION` maze saved via `MazeRepository.save()`, when the write completes, then a `MazeId` is minted via the shared `mint_maze_id()` and the file lands at `mazes/creation/<name>.csv`.
- Given a `CREATION` maze persisted on disk, when `MazeRepository.load(name, MazeKind.CREATION)` is called, then it returns the `Maze` with `kind=CREATION` and the minted `id`.
- Given a `CREATION` maze with a minted `MazeId`, when `MazeRepository.find_by_id(maze_id)` is called, then it scans the `creation/` folder and returns the matching `Maze`.
- Given the `CREATION` kind, when `MazeRepository.list_names(MazeKind.CREATION)` is called, then it returns the sorted names from the `mazes/creation/` directory.
- Given a `Maze(kind=CREATION, id=None)`, when constructed, then it passes validation; when `Maze(kind=SKETCH, id=some_id)` is constructed, then it raises `DomainValidationError`.

## Design Notes

The change is additive: `CREATION` joins `CLASSIC` and `SAVED_RANDOM` as a third id-eligible kind. All three share the exact same `MazeId` minting rule (one global namespace, no per-kind prefix). The folder name `creation` comes from `MazeKind.CREATION.value` — no new path logic needed. The Builder's save promotion logic (`_open_save_dialog_for_maze`) previously defaulted to `CLASSIC` for any non-id-eligible kind (in practice only `SKETCH`); now it defaults to `CREATION`. An existing `CREATION` maze (from a future Edit-in-Builder round-trip, Story 3.9) is detected by `target_kind in _ID_ELIGIBLE_KINDS` and its existing id is preserved — no re-minting.

Epic 6's `RecordsService.record_completion` will extend its eligibility check from `kind in {CLASSIC, SAVED_RANDOM}` to `kind in {CLASSIC, SAVED_RANDOM, CREATION}` — same terms, no separate PR. Epic 5's migration script MazeId backfill (Story 5.3) will also extend to `CREATION` mazes.

## Verification

**Commands:**
- `ruff check .` -- expected: no errors
- `ruff format --check .` -- expected: no reformatting needed
- `pytest -q` -- expected: all tests pass, including new `CREATION` kind tests

**Manual checks (if no CLI):**
- Launch app, open Builder, create a maze with entry+exit, save as Maze → file appears in `mazes/creation/`, reload app, open Player selection → maze appears in Creations section (once Story 4.14 lands).
- Verify `find_by_id` works for a `CREATION` maze's id.
- Verify `list_names(CREATION)` returns the saved maze name.