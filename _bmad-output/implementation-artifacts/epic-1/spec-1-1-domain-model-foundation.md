---
baseline_commit: d2cf2c86867211b365c50adb8704d7f14bab1a48
---

# Story 1.1: Domain model foundation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->
<!-- Story context: Ultimate context engine analysis completed - comprehensive developer guide created. -->

## Story

As a developer (the project's author),
I want a pinned, immutable domain model for mazes and gameplay concepts (Grid, Cell, Position, Maze, Level, Difficulty, Duration, MazeId),
so that every later feature builds on one shared, drift-free shape rather than each screen inventing its own.

## Acceptance Criteria

1. **Given** the `domain/` package, **when** Grid/Cell/Position/Level/Difficulty/Duration/Maze/MazeId are defined, **then** they are immutable value objects with no mutating methods, **and** Cell's wall booleans are computed properties derived from its `"0"`–`"3"` digit, never a separately stored representation.
2. **Given** a Maze value, **when** it is constructed, **then** it carries a kind tag (`classic`/`sketch`/`saved-random`/`generated`) and an `id: MazeId | None` consistent with the id-eligibility rule (non-`None` only for `classic`/`saved-random`).
3. **Given** the `domain/` package, **when** its imports are inspected, **then** it imports nothing from `adapters/` or any UI framework.

## Tasks / Subtasks

- [x] **Task 1 — Package skeleton & shared error hierarchy** (AC: 1, 3)
  - [x] Create `src/labyrinthes/domain/__init__.py`, re-exporting the public names built in this story (`Grid`, `Cell`, `Position`, `Level`, `Difficulty`, `Duration`, `Maze`, `MazeKind`, `MazeId`, plus the error types).
  - [x] Create `src/labyrinthes/domain/errors.py`: a single `LabyrinthesError(Exception)` project base error, plus one `DomainValidationError(LabyrinthesError)` used by every value object's constructor validation in this story (per the Architecture Spine's Consistency Conventions: "a small typed exception hierarchy under one project base error", not one bespoke exception per class).

- [x] **Task 2 — `Position`, `Duration`, `MazeId`** (AC: 1)
  - [x] `src/labyrinthes/domain/position.py`: frozen dataclass `Position(row: int, col: int)` — the one shared type for entry, exit, ball, and editing-cursor locations alike (AD-3). No validation of bounds here (a `Position` isn't aware of any `Grid`'s size).
  - [x] `src/labyrinthes/domain/duration.py`: frozen dataclass `Duration(milliseconds: int)`, rejecting negative values with `DomainValidationError`. Used later by the Timer (Story 2.9) and Personal Records (Story 6.1) — keep it minimal, no formatting/parsing helpers beyond what's needed now.
  - [x] `src/labyrinthes/domain/maze_id.py`: frozen dataclass `MazeId(value: str)` — an opaque identifier only. **Do not implement a minting/generation scheme here** — AD-3/AD-8 assign that to a single shared minting function consumed by `MazeRepository` (Story 1.4) and the migration script (Epic 5); this story only needs the *type*.

- [x] **Task 3 — `Level`, `Difficulty` ordinal types** (AC: 1)
  - [x] `src/labyrinthes/domain/level.py`: `class Level(enum.IntEnum)` with members `ONE=1, TWO=2, THREE=3, FOUR=4, MAX=5`. `IntEnum` gives correct ordering for free (`Level.MAX > Level.FOUR`), satisfying AD-3's "`MAX` above `4`" requirement without hand-rolled `__lt__`/`__gt__`.
  - [x] `src/labyrinthes/domain/difficulty.py`: `class Difficulty(enum.IntEnum)` with members `ONE=1, TWO=2, THREE=3`.
  - [x] Do not implement partition-size/reveal-threshold logic (Story 2.6/2.7's job) — this story only pins the ordinal *shape*.

- [x] **Task 4 — `Cell`** (AC: 1)
  - [x] `src/labyrinthes/domain/cell.py`: frozen dataclass `Cell(value: str)`. `__post_init__` raises `DomainValidationError` unless `value in ("0", "1", "2", "3")`.
  - [x] Computed properties `has_top_wall` and `has_left_wall`, derived from `int(self.value)` — bit 1 (`& 1`) = top wall, bit 2 (`& 2`) = left wall (see Dev Notes — this bit mapping is reverse-engineered from legacy code, not documented anywhere in the legacy comments, so get it exactly right: `"0"`→neither, `"1"`→top only, `"2"`→left only, `"3"`→both).
  - [x] Do **not** add `has_right_wall`/`has_bottom_wall` to `Cell` — those aren't encoded on the cell itself in the legacy scheme; they only exist via a neighboring cell's top/left bit, which is a `Grid`-level concern (see Dev Notes), out of this story's scope.

- [x] **Task 5 — `Grid`** (AC: 1)
  - [x] `src/labyrinthes/domain/grid.py`: frozen dataclass `Grid` wrapping an immutable `tuple[tuple[Cell, ...], ...]` of cells (never a `list[list[...]]` — lists are mutable and would violate AD-2).
  - [x] Expose `width: int` and `height: int` as the **playable** dimensions (what a user configures, e.g. FR-4's 3–50 columns / 3–35 rows) — not the raw array size.
  - [x] Internally, store `(height + 1)` rows × `(width + 1)` columns of `Cell` — one extra padding row/column, mirroring the legacy `grille_pleine`'s closed-border scheme (see Dev Notes). This is load-bearing for lossless round-trips through the maze CSV format (NFR2/AD-6) in Story 1.4 — do not "simplify" it away to a plain `height × width` grid.
  - [x] Provide a `cell_at(position: Position) -> Cell` accessor (raises `DomainValidationError` — or lets a natural `IndexError` propagate, developer's call, but be consistent — on an out-of-range position) and a `Grid.filled(width: int, height: int) -> Grid` factory that builds an all-filled grid with the closed border already in place (padding row = all `"1"`, padding column = all `"2"`, corner cell = `"0"` — see Dev Notes' quoted `grille_pleine`). Reject `width <= 0` or `height <= 0` with `DomainValidationError` (mirrors the legacy `assert x > 0 and y > 0`). Do **not** enforce FR-4's 3–50/3–35 bounds here — that's a `shared`-scope settings concern for a later story (Architecture Spine, Deferred section), not a `Grid` invariant.

- [x] **Task 6 — `MazeKind` and `Maze`** (AC: 2, 3)
  - [x] `src/labyrinthes/domain/maze.py`: `class MazeKind(enum.Enum)` with members `CLASSIC`, `SKETCH`, `SAVED_RANDOM`, `GENERATED`.
  - [x] Frozen dataclass `Maze(grid: Grid, entry: Position, exit: Position, kind: MazeKind, id: MazeId | None)`.
  - [x] `__post_init__` enforces the id-eligibility rule exactly as AC 2 states it (one-directional): if `id is not None`, `kind` must be `MazeKind.CLASSIC` or `MazeKind.SAVED_RANDOM`, else raise `DomainValidationError`. Do **not** additionally require `classic`/`saved-random` mazes to always carry a non-`None` id — a freshly-transitioned, not-yet-persisted `Maze` may legitimately have `id=None` until `MazeRepository.save()` mints one (Story 1.4's concern, not this story's).

- [x] **Task 7 — Tests** (AC: 1, 2, 3)
  - [x] `tests/domain/test_position.py`, `test_duration.py`, `test_maze_id.py`, `test_level.py`, `test_difficulty.py`, `test_cell.py`, `test_grid.py`, `test_maze.py` — mirror `src/labyrinthes/domain/` per project convention.
  - [x] For every frozen dataclass: assert attempting to set an attribute after construction raises (`dataclasses.FrozenInstanceError`), proving "no mutating methods" (AC 1).
  - [x] `test_cell.py`: parametrize all four digits `"0"`/`"1"`/`"2"`/`"3"` against expected `(has_top_wall, has_left_wall)`; assert an invalid value (e.g. `"4"`, `"x"`) raises `DomainValidationError`.
  - [x] `test_grid.py`: assert `Grid.filled(w, h)` produces `height + 1` rows of `width + 1` columns; assert the padding row is all `"1"` cells, the padding column all `"2"` cells, and the bottom-right corner is `"0"`; assert `width <= 0`/`height <= 0` raises.
  - [x] `test_level.py`: assert `Level.MAX > Level.FOUR > Level.THREE > ... > Level.ONE`.
  - [x] `test_maze.py`: assert a `classic`/`saved-random` `Maze` accepts both `id=None` and a real `MazeId`; assert a `sketch`/`generated` `Maze` with a non-`None` id raises `DomainValidationError`.
  - [x] No test needs to scan for forbidden imports — that automated guard is Story 1.2's deliverable. As a sanity check before marking this story done, manually confirm (e.g. `grep -rn "^import tkinter\|^from tkinter\|adapters" src/labyrinthes/domain/`) that nothing in `domain/` imports `tkinter` or `adapters` — Story 1.2 will make this permanent, not this one.
  - [x] Run `ruff check .`, `ruff format --check .`, and `pytest` — all green before marking the story done.

### Review Findings

- [x] [Review][Patch] `Grid` has no invariant enforcement on direct construction [src/labyrinthes/domain/grid.py:24] — fixed: added `__post_init__` rejecting empty/ragged `cells`
- [x] [Review][Patch] `Maze` does not validate `entry`/`exit` fall within `grid`'s bounds [src/labyrinthes/domain/maze.py:40] — fixed: `__post_init__` now calls `grid.cell_at(entry)`/`grid.cell_at(exit)`
- [x] [Review][Patch] `Maze.__post_init__`'s id-eligibility check uses a fragile string-name comparison instead of direct enum-member comparison [src/labyrinthes/domain/maze.py:11,41] — fixed: `_ID_ELIGIBLE_KINDS` now holds `MazeKind` members, compared directly
- [x] [Review][Patch] `cell_at` silently operates on raw padded indices (can return the internal-only padding row/column) with no docstring note [src/labyrinthes/domain/grid.py:39] — fixed: docstring added
- [x] [Review][Patch] No test covers `Grid.filled`'s smallest legal case (1×1) [tests/domain/test_grid.py] — fixed: `test_filled_smallest_legal_size` added
- [x] [Review][Defer] `Grid.filled` has no type validation; a non-`int` width/height raises a raw `TypeError` instead of `DomainValidationError` [src/labyrinthes/domain/grid.py:54] — deferred, pre-existing pattern across the whole diff (no value object in this story validates argument *types*, only business-domain invariants; consistent with the codebase having no static type-checker configured yet)
- [x] [Review][Defer] `MazeId` performs zero validation — an empty/whitespace string is accepted as a valid opaque id [src/labyrinthes/domain/maze_id.py:11] — deferred, the story explicitly scopes `MazeId` to "an opaque identifier only, no minting scheme here"; a validation rule is better decided alongside Story 1.4's minting function

## Dev Notes

### Architecture patterns & constraints

- **AD-1 (Domain/UI decoupling is structural):** `domain/` imports nothing from `adapters/` or any UI framework — this story establishes the package that AD-9's automated test (Story 1.2, landing next) will start guarding. [Source: architecture/.../ARCHITECTURE-SPINE.md#AD-1]
- **AD-2 (Domain state is immutable):** every value object is a frozen dataclass (or `enum.IntEnum`/`enum.Enum`, which are inherently immutable — an acceptable "or equivalent" per AD-2's own wording). No method mutates `self`; there are no engine *operations* in this story yet (generation/solving/wall-editing land in later epics) so there's nothing to make "pure functions" of here — just the state shapes those operations will later take and return. [Source: architecture/.../ARCHITECTURE-SPINE.md#AD-2]
- **AD-3 (Domain object shapes are pinned):** this story *is* AD-3 — implement it exactly as specified there (`Grid` `[row][col]` 0-origin; `Cell` wraps its digit only, wall booleans computed; `Position` shared for entry/exit/ball/cursor; `Maze` = `Grid` + entry/exit `Position` + kind tag + `id: MazeId | None`; `Level` 1–4 + `MAX` ordinal; `Difficulty` 1–3; `Duration` shared type). Read AD-3 in full before starting — it's the normative spec for this story, more precise than the epics.md AC wording alone. [Source: architecture/.../ARCHITECTURE-SPINE.md#AD-3]
- **AD-6 (Cell encoding is a preserved public contract):** `"0"`/`"1"`/`"2"`/`"3"`, bit 1 = top wall, bit 2 = left wall — do not reinterpret or re-encode. This is what Story 1.4's `MazeRepository` will read/write byte-for-byte compatible with existing `.csv` maze files. [Source: architecture/.../ARCHITECTURE-SPINE.md#AD-6]
- **NFR1 (Logic/UI decoupling):** stdlib only (`dataclasses`, `enum`) — no third-party dependency needed or wanted for `domain/`.
- **NFR4 (Language convention):** English identifiers/comments throughout, even though this ports from French-named legacy code (`grille`→`Grid`, `case`/digit→`Cell`, `niveau`→`Level`, `difficultée`→`Difficulty`, `labyrinthe`→`Maze`).
- **This is the very first story of the rewrite.** There is no existing `rewrite`-branch code to avoid breaking — `src/labyrinthes/` currently contains only `__init__.py` (`__version__ = "0.1.0"`) and `tests/test_package.py`. Nothing to preserve, nothing to migrate; build `domain/` from scratch per the spine.

### The legacy encoding this story ports (reference, not to be imported)

The cell-encoding bit mapping is **not** documented anywhere in the legacy code's comments/docstrings — it must be reverse-engineered from behavior. Quoted for exactness (from `Creer_labyrinthes.py`, identical logic in `Labyrinthes_copy.py`):

```python
# trace_grille — draws a top wall for "1"/"3", a left wall for "2"/"3"
if self.grille.lab[y][x] == "1" or self.grille.lab[y][x] == "3":
    self.barre_horizontale(...)  # top wall
if self.grille.lab[y][x] == "2" or self.grille.lab[y][x] == "3":
    self.barre_verticale(...)  # left wall
```

So `"0"` = no walls, `"1"` = top only, `"2"` = left only, `"3"` = both — this is exactly AC 1's "computed properties derived from its digit" requirement.

The grid's closed-border padding (`Lab_grille_crea.grille_pleine`, `Creer_labyrinthes.py:683-694`, duplicated in `Labyrinthes_copy.py`):

```python
def grille_pleine(self, x: int, y: int):
    assert x > 0 and y > 0
    g = []
    for i in range(y):
        g.append(["3"] * x + ["2"])  # each real row + a right-padding cell ("2" = left wall only)
    g.append(["1"] * x + ["0"])  # bottom-padding row ("1" = top wall only), corner "0"
    return g
```

This produces `y + 1` rows × `x + 1` columns for `x` × `y` real cells — the extra row/column exists purely so the right-most/bottom-most real cells can express a right/bottom wall via the *padding* cell's left/top bit (right and bottom walls are never stored directly on a cell; they're always read off a neighbor). `Grid` in this story must preserve this exact padding shape (Task 5) — collapsing it to a plain `height × width` array would make Story 1.4's CSV round-trip lossy and silently break AD-6.

**Known legacy bug, not to be reproduced:** the Player app (`Labyrinthes_copy.py`) and the Builder (`Creer_labyrinthes.py`) disagree about whether `x`/`y` mean "real cell count" or "full array size including padding" — the Player uses the full array size and compensates ad hoc downstream (`self.grille.x - 1` scattered through rendering code). This story's `Grid.width`/`Grid.height` are defined once, unambiguously, as the *playable* size — no downstream `-1` compensation should ever be needed again.

Size bounds (3–50 columns, 3–35 rows) are **duplicated** in the legacy code (hardcoded in the Builder, loaded from CSV in the Player — the FR-4 defect this rewrite fixes). Not this story's concern: `Grid.filled()` only rejects non-positive dimensions; the 3–50/3–35 bounds check belongs to a `shared`-scope settings value consumed by a later Builder/Player story.

### Project Structure Notes

- New files, all under `src/labyrinthes/domain/`: `__init__.py`, `errors.py`, `position.py`, `duration.py`, `maze_id.py`, `level.py`, `difficulty.py`, `cell.py`, `grid.py`, `maze.py`.
- New test files under `tests/domain/`, one per module above (except `errors.py`, which doesn't need a dedicated test — its two exception classes are exercised indirectly by every other module's validation tests).
- No `pyproject.toml` changes expected — `[tool.hatch.build.targets.wheel] packages = ["src/labyrinthes"]` already covers new subpackages, and `ruff`/`pytest` are already configured for `src/`/`tests/`.
- This story does **not** touch `application/`, `adapters/`, or `app/` — those directories don't exist yet and aren't created here (Story 1.3 defines the first `application/` ports).

### Testing standards summary

- `pytest`, tests under `tests/domain/` mirroring `src/labyrinthes/domain/` (per CLAUDE.md's "tests live under `tests/` and mirror the package layout").
- `ruff check .` (rules E, F, I, UP, B, SIM) and `ruff format .` must both pass — already configured in `pyproject.toml`, nothing to add.
- No `tkinter`, no I/O, no third-party imports anywhere in `domain/` or its tests.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1: Domain model foundation]
- [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements] (AD-2/AD-3 restated, package layout, one-way dependency direction)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md#AD-1, AD-2, AD-3, AD-6]
- [Source: _bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/addendum.md#Cell-encoding scheme (0/1/2/3) — the engine's core]
- [Source: Creer_labyrinthes.py (legacy reference only, not imported) — `trace_grille`, `grille_pleine`, `fleches`, `sortie_end`]
- [Source: CLAUDE.md#Rewrite branch (active development)]

## Dev Agent Record

### Agent Model Used

claude-sonnet-5 (Claude Code)

### Debug Log References

- Full validation run: `pytest -q` → 45 passed; `ruff check .` → all checks passed; `ruff format --check src/ tests/` → 20 files already formatted.
- `ruff format --check .` (whole repo) flags one pre-existing, out-of-scope issue: whitespace alignment inside the quoted legacy-code fence in this story's own Dev Notes section (`_bmad-output/implementation-artifacts/1-1-domain-model-foundation.md`), not in any file this story owns. Left untouched — editing Dev Notes prose/quotes is outside this workflow's permitted story-file edit areas, and the block is a verbatim quote of legacy code, not code under lint. Confirmed no other `.md` file in the repo is flagged.
- Forbidden-import sanity check: `grep -rn "^import tkinter\|^from tkinter\|adapters" src/labyrinthes/domain/` → only match is the word "adapters" inside `__init__.py`'s docstring prose, no actual import statement.

### Completion Notes List

- Implemented the full `domain/` package per Dev Notes/AD-3: `Position`, `Duration`, `MazeId`, `Level` (`IntEnum`), `Difficulty` (`IntEnum`), `Cell`, `Grid`, `MazeKind` + `Maze` — all frozen dataclasses (or `IntEnum`/`Enum`) per AD-2, stdlib-only per NFR1.
- Followed red-green-refactor per task: wrote a failing test file for each module (confirmed `ModuleNotFoundError`/collection errors), then implemented the minimal module to turn it green, before moving to the next task.
- `Cell.has_top_wall`/`has_left_wall` implement the exact bit mapping from Dev Notes (`"0"` neither, `"1"` top, `"2"` left, `"3"` both), parametrized-tested against all four digits plus invalid-value rejection.
- `Grid` stores `(height + 1) × (width + 1)` `Cell`s (tuple-of-tuples, immutable); `width`/`height` are computed properties over the *playable* size, never the raw array size. `Grid.filled()` builds an all-filled grid (`"3"` real cells — fully walled, a generator's starting point) with the closed-border padding (`"1"` padding row, `"2"` padding column, `"0"` corner) exactly as specified, rejecting non-positive dimensions.
- `Maze.__post_init__` enforces the one-directional id-eligibility rule (AC 2): non-`None` id requires `kind` in `{CLASSIC, SAVED_RANDOM}`; the reverse is not enforced, matching the not-yet-persisted case called out in the story.
- All AC 1/2/3 covered: immutability asserted via `dataclasses.FrozenInstanceError` for every frozen dataclass; `domain/` confirmed import-clean of `tkinter`/`adapters`.
- Full suite green: 45 tests pass, `ruff check .` clean, `ruff format --check` clean on all `src/`/`tests/` files (see Debug Log for the one unrelated pre-existing `.md` note).

### File List

- `src/labyrinthes/domain/__init__.py` (new)
- `src/labyrinthes/domain/errors.py` (new)
- `src/labyrinthes/domain/position.py` (new)
- `src/labyrinthes/domain/duration.py` (new)
- `src/labyrinthes/domain/maze_id.py` (new)
- `src/labyrinthes/domain/level.py` (new)
- `src/labyrinthes/domain/difficulty.py` (new)
- `src/labyrinthes/domain/cell.py` (new)
- `src/labyrinthes/domain/grid.py` (new)
- `src/labyrinthes/domain/maze.py` (new)
- `tests/domain/test_position.py` (new)
- `tests/domain/test_duration.py` (new)
- `tests/domain/test_maze_id.py` (new)
- `tests/domain/test_level.py` (new)
- `tests/domain/test_difficulty.py` (new)
- `tests/domain/test_cell.py` (new)
- `tests/domain/test_grid.py` (new)
- `tests/domain/test_maze.py` (new)
