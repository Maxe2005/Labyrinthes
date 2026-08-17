---
title: 'Story 2.2: Random maze generation with validation'
type: 'feature'
created: '2026-08-09'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-2/epic-2-context.md']
warnings: [oversized]
baseline_revision: 'b7e4d8b3cc863bbb9b96253916af374a4e357a43'
final_revision: '002d23a12309a5814e2abfce9ce3374fcda062b3'
---

<intent-contract>

## Intent

**Problem:** `ClassicMazeGallery`'s "Generate random" button (Story 2.1) is wired to a documented no-op placeholder — there is no dialog to configure a random maze's dimensions/starting position, no generation algorithm, and no shared-settings-backed source for the FR-4/FR-10 size bounds (`application/settings_keys.py`'s bound keys exist but nothing reads or defaults them yet).

**Approach:** Add a pure `domain/maze_generation.py` (randomized DFS/backtracker producing a perfect maze, exit = farthest cell from entry via BFS) plus `domain/maze_size_bounds.py` (the `MazeSizeBounds` value object, its `DEFAULT_MAZE_SIZE_BOUNDS` of 3–50 columns/3–35 rows, and a pure dimension validator) and a thin `application/maze_size_bounds.py` reader that resolves those bounds from `shared`-scope settings, falling back to the defaults field-by-field when unset. Build a new `GenerateRandomDialog` (`adapters/tkinter/player/`) with four numeric fields (columns, rows, start column, start row) validated live against those bounds/grid shape; wire `ClassicMazeGallery._on_generate_random` to open it and, on confirm, call the domain generator and hand the resulting `Maze` off through the exact same `navigate(ScreenId.PLAYER, maze)` path Story 2.1's "Play" already uses.

## Boundaries & Constraints

**Always:** `generate_random_maze(width, height, entry, rng)` lives in `domain/`, is pure (no I/O, no Tkinter), and returns a `Maze` with `kind=MazeKind.GENERATED`, `id=None`; it raises `DomainValidationError` only for structurally invalid input (`width <= 0`, `height <= 0`, or `entry` outside `[0, width) x [0, height)`) — it does **not** know about the FR-4 3–50/3–35 policy bounds, which are a UI/settings concern, not a domain invariant. The algorithm is an iterative (never recursive — up to 50×35=1750 cells would risk Python's recursion limit) randomized depth-first backtracker carving a spanning tree over the real (non-padding) cells, using the same wall-bit semantics `Grid.filled`/`Cell` already define (top wall cleared on the current cell for a "north" carve, on the neighbor for "south"; left wall cleared on the current cell for "west", on the neighbor for "east") — the outer closed border (`Grid`'s padding row/column) is never touched. The exit is the cell reached at maximum BFS distance from `entry` over the generated passages (ties broken by BFS visitation order, so the result is deterministic for a given `rng` sequence) — an interior/border real cell, not an out-of-grid position (unlike the legacy's now-obsolete negative-offset convention, not reproduced here). `MazeSizeBounds` (`min_columns`, `max_columns`, `min_rows`, `max_rows`) and `DEFAULT_MAZE_SIZE_BOUNDS = MazeSizeBounds(3, 50, 3, 35)` live in `domain/maze_size_bounds.py`; `application/maze_size_bounds.py`'s `read_maze_size_bounds(settings)` reads the four existing `shared`-scope keys (`settings_keys.MAZE_MIN_COLUMNS` etc.) and substitutes the matching default field, independently per field, on `SettingNotFoundError`/`SettingCorruptError`/`ValueError`/`TypeError` — mirroring `ThemeController._load_theme()`'s established fallback pattern — never raising out to the dialog. `GenerateRandomDialog` (`tk.Toplevel`, parented to the `ClassicMazeGallery` instance that opens it — not the app's persistent container; nothing here is worth surviving a navigate-away, unlike `SettingsWindow`) has four `tk.Entry` fields (columns, rows, start column, start row) that re-validate on every `<KeyRelease>` across all four (start-column/row bounds depend on the *currently entered* columns/rows, so a change to either re-checks all four), showing a per-field inline error (`typography.body_secondary`, `colors.exit`, per `DESIGN.md`'s inline-error convention) when invalid, and leaving the error visible with no navigation/generation performed if "Generate" (a primary `PillButton`) is clicked while any field is invalid — matching the existing jump-to-number widget's "no crash, no state change" convention, not a disabled-button pattern (no `common/` widget supports one). Each `Entry` binds `<Return>` to trigger Generate and local `<KeyPress-n>`/`<KeyPress-N>` returning `"break"`, mirroring Story 2.1's review-fixed focus-collision guard on `ClassicMazeGallery`'s own jump entry, so the global `generate_random` shortcut can't refire while typing. `Cancel` (default `PillButton`) and `<Escape>` both close the dialog with no side effect. On a valid "Generate", the dialog calls its `on_confirm(width, height, Position(row=start_row, col=start_col))` callback and destroys itself; `ClassicMazeGallery` supplies that callback, calls `generate_random_maze(...)` with a fresh `random.Random()`, and calls `self._navigate(ScreenId.PLAYER, maze)` — the identical hand-off `_on_play` already uses. `player/screen.py`'s `mount()` gains one more required, keyword-only `settings_repository: SettingsRepository` (mirrors `maze_repository`'s Story 2.1 precedent exactly), threaded into `ClassicMazeGallery`; `composition_root.build_app()`'s existing `functools.partial(mount_player, maze_repository=...)` gains `settings_repository=settings_repository` (already a `build_app()` parameter, just not yet threaded to Player).

**Block If:** None — every open question (bounds source, exit-placement rule, dialog modality, validation-gate mechanics, coordinate convention) is resolved by the choices above.

**Never:** Do not implement saving a generated maze (kind transition to `SAVED_RANDOM`, `MazeId` minting, duplicate-name handling) — Story 2.3. Do not render the generated maze's walls/HUD — it flows into the existing Story 2.1 gameplay-placeholder text-summary view unchanged; Story 2.4 builds real rendering. Do not seed/write the shared bound settings — `read_maze_size_bounds` only reads-with-fallback, never calls `settings.set(...)`. Do not reproduce the legacy algorithm's random-frontier-pick backtracking or its border-only/out-of-grid exit convention — both are explicitly superseded by the cleaner iterative-stack DFS + BFS-farthest-cell approach above. Do not add a disabled/greyed-out state to `PillButton` — out of this story's scope, not needed given the "gate on click, leave errors visible" pattern chosen.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Cold open | Dialog opens with default bounds | Fields pre-filled with valid values (e.g. `min_columns`/`min_rows`, start `0,0`), no inline errors | No error expected |
| Columns below/above bounds | Columns field set to `2` (min 3) or `99` (max 50) | Inline "Columns must be between 3 and 50." shown; Generate click does not navigate | No exception, no state change |
| Non-numeric field | Any field set to `"abc"` | Inline "Enter a whole number." for that field; Generate click does not navigate | No exception |
| Start position outside entered grid | Columns=`10`, start column=`15` | Inline "Start column must be between 0 and 9." shown | No exception |
| All fields valid | Columns=10, Rows=8, start=(0,0) | `navigate(ScreenId.PLAYER, maze)` called once; `maze.kind == GENERATED`, `maze.id is None`, `maze.grid.width==10`, `maze.grid.height==8`, `maze.entry == Position(0,0)`, `maze.exit != maze.entry` | No error expected |
| Cancel / Escape | Dialog open, Cancel clicked (or `<Escape>`) | Dialog destroyed, `navigate` never called | No error expected |
| Bounds settings entirely unset | Fresh `SettingsRepository`, no `MAZE_MIN/MAX_*` keys stored | `read_maze_size_bounds` returns `DEFAULT_MAZE_SIZE_BOUNDS` (3–50/3–35), dialog opens normally | No exception raised to the caller |
| Generated maze is solvable by construction | Any valid columns/rows | Every real cell reachable from `entry` (spanning tree — no unreachable cells, no disconnected pockets) | No error expected |

</intent-contract>

## Code Map

- `src/labyrinthes/domain/maze_size_bounds.py` -- new; `MazeSizeBounds` frozen dataclass, `DEFAULT_MAZE_SIZE_BOUNDS`, `validate_dimensions(bounds, width, height) -> list[str]`
- `src/labyrinthes/domain/maze_generation.py` -- new; `generate_random_maze(width, height, entry, rng) -> Maze` (iterative DFS backtracker + BFS farthest-cell exit), `validate_start_position(width, height, position) -> list[str]`
- `src/labyrinthes/domain/__init__.py` -- export `MazeSizeBounds`, `DEFAULT_MAZE_SIZE_BOUNDS`, `generate_random_maze`, `validate_dimensions`, `validate_start_position`
- `src/labyrinthes/application/maze_size_bounds.py` -- new; `read_maze_size_bounds(settings: SettingsRepository) -> MazeSizeBounds`, per-field fallback to defaults
- `src/labyrinthes/adapters/tkinter/player/generate_random_dialog.py` -- new; `GenerateRandomDialog(tk.Toplevel)` -- 4-field form, live validation, Generate/Cancel
- `src/labyrinthes/adapters/tkinter/player/classic_gallery.py` -- add `settings_repository` param; replace `_on_generate_random`'s no-op with opening `GenerateRandomDialog`; add `_on_generation_confirmed(width, height, entry)` calling `generate_random_maze` + `navigate`
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- `mount()` gains keyword-only `settings_repository: SettingsRepository`, threaded to `ClassicMazeGallery`
- `src/labyrinthes/app/composition_root.py` -- Player's `functools.partial(mount_player, ...)` gains `settings_repository=settings_repository`
- `tests/domain/test_maze_size_bounds.py` -- new; `validate_dimensions` I/O matrix rows, `DEFAULT_MAZE_SIZE_BOUNDS` values
- `tests/domain/test_maze_generation.py` -- new; solvability (every cell reachable), border never opened, exit farthest-from-entry, structural `DomainValidationError` cases, determinism under a seeded `rng`
- `tests/application/test_maze_size_bounds_reader.py` -- new; per-field fallback-to-default coverage (unset key, corrupt value, non-numeric stored value) -- named `_reader` to avoid a same-basename pytest collection collision with `tests/domain/test_maze_size_bounds.py`
- `tests/adapters/tkinter/player/test_generate_random_dialog.py` -- new; the I/O matrix's dialog rows directly against `GenerateRandomDialog`
- `tests/adapters/tkinter/player/test_classic_gallery.py` -- replace `test_generate_random_placeholder_is_a_no_op`; add dialog-open + confirm-hand-off coverage; update `_gallery()` helper for the new `settings_repository` param
- `tests/adapters/tkinter/player/test_player_screen.py` -- update existing `mount()` calls to add `settings_repository=`
- `tests/adapters/tkinter/player/conftest.py` -- add an in-memory `FakeSettingsRepository` test double + a fixture
- `tests/app/test_composition_root.py` -- existing Player-wiring tests already pass `settings_repository` to `build_app()`; no new test required beyond confirming they still pass with the widened partial

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/domain/maze_size_bounds.py` -- add `MazeSizeBounds`/`DEFAULT_MAZE_SIZE_BOUNDS`/`validate_dimensions` -- the one pure policy-bounds source both this dialog and future Builder/New-Maze reuse
- [x] `tests/domain/test_maze_size_bounds.py` -- unit-test the validator's I/O matrix rows
- [x] `src/labyrinthes/domain/maze_generation.py` -- add `generate_random_maze`/`validate_start_position` -- the pure generation algorithm and start-position shape check
- [x] `tests/domain/test_maze_generation.py` -- unit-test solvability, border-closure, exit placement, structural validation, determinism
- [x] `src/labyrinthes/domain/__init__.py` -- export the five new names
- [x] `src/labyrinthes/application/maze_size_bounds.py` -- add `read_maze_size_bounds` -- the settings-backed reader with per-field default fallback
- [x] `tests/application/test_maze_size_bounds_reader.py` -- unit-test the fallback matrix (renamed from `test_maze_size_bounds.py` during review to avoid a same-basename pytest collection collision with `tests/domain/test_maze_size_bounds.py`, since neither `tests/` subpackage has an `__init__.py`)
- [x] `src/labyrinthes/adapters/tkinter/player/generate_random_dialog.py` -- add `GenerateRandomDialog` -- the 4-field live-validated form
- [x] `tests/adapters/tkinter/player/conftest.py` -- add `FakeSettingsRepository` + fixture
- [x] `tests/adapters/tkinter/player/test_generate_random_dialog.py` -- unit-test the dialog against the I/O matrix
- [x] `src/labyrinthes/adapters/tkinter/player/classic_gallery.py` -- wire `_on_generate_random` to the dialog + confirm hand-off
- [x] `tests/adapters/tkinter/player/test_classic_gallery.py` -- replace the no-op test, add open/confirm coverage
- [x] `src/labyrinthes/adapters/tkinter/player/screen.py` -- thread `settings_repository` through `mount()`
- [x] `tests/adapters/tkinter/player/test_player_screen.py` -- update all `mount()` calls
- [x] `src/labyrinthes/app/composition_root.py` -- widen Player's `functools.partial` with `settings_repository`
- [x] `tests/app/test_composition_root.py` -- confirm existing Player-wiring tests still pass unmodified

**Acceptance Criteria:**
- Given the maze-selection screen, when "Generate random" is triggered, then a dialog opens for columns/rows/starting position, pre-filled with valid defaults and no inline errors
- Given invalid input in any field (out of bounds, non-numeric, start position outside the entered grid), when "Generate" is clicked, then no navigation occurs, the dialog stays open, and the relevant inline error is shown
- Given valid input, when "Generate" is clicked, then a solvable maze (every real cell reachable from the entry) is produced with `kind=GENERATED`, `id=None`, the exit at the cell farthest (by BFS distance) from the entry, and `navigate(ScreenId.PLAYER, maze)` is called with it exactly once
- Given no shared size-bound settings have ever been stored, when the dialog opens, then it uses the FR-4 defaults (3–50 columns, 3–35 rows) instead of raising

## Spec Change Log

## Review Triage Log

### 2026-08-09 — Review pass

- intent_gap: 0
- bad_spec: 0
- patch: 4 (medium 2, low 2)
- defer: 3 (low 3)
- reject: 2
- addressed_findings:
  - `[medium]` `[patch]` `read_maze_size_bounds`'s per-field-independent fallback could resolve an inverted pair (`min_columns > max_columns`, e.g. only `min_columns` overridden past the still-default `max_columns`) that `validate_dimensions` could never satisfy for any width/height -- permanently and silently soft-locking "Generate random" with no diagnostic. Reproduced directly. Fixed by checking each resolved pair for inversion after all four fields are read and falling the whole pair back to `DEFAULT_MAZE_SIZE_BOUNDS` together when inverted.
  - `[medium]` `[patch]` The same reader accepted a non-positive stored value (e.g. `min_columns=0`) as "successfully parsed", letting `validate_dimensions` wave through `width=0`, which `generate_random_maze` then rejects with an uncaught `DomainValidationError` on "Generate" click. Reproduced directly. Fixed by rejecting (falling back to default) any per-field value `< 1`, alongside the existing non-numeric/corrupt/unset cases.
  - `[low]` `[patch]` `GenerateRandomDialog._compute_errors` required *both* `columns`/`rows` (or both `start_col`/`start_row`) to parse before validating either, so a non-numeric value in one field masked an already-knowable out-of-bounds error in the other until the parse error was fixed first. Fixed by validating each field against the bounds/grid shape independently once it alone parses, substituting the other field's currently-parsed value (or a known-valid default) rather than requiring both.
  - `[low]` `[patch]` The dialog set no initial keyboard focus despite its otherwise keyboard-first design (`<Return>`-to-submit on every field, `<Escape>`-to-cancel). Fixed with `entries["columns"].focus_set()` after field construction; not covered by a new test since `focus_get()` is unreliable against this suite's withdrawn `tk_root` convention (same reasoning already documented for real X11 event synthesis).

Deferred (see `deferred-work.md`): a `GenerateRandomDialog` dedup guard (repeated "N"/re-triggering stacks independent non-modal dialogs) -- the same already-deferred `SettingsWindow` pattern (Story 1.11's entry), not a new failure class; a `_read_bound` float-truncation gap (`int(3.9) == 3` silently accepted rather than treated as corrupt) and a missing upper sanity ceiling on stored `max_columns`/`max_rows` (could freeze the UI during synchronous generation) -- both real but not reachable today, since nothing in the shipped app writes to these settings keys yet, only a hand-edited file could trigger either.

Rejected as noise or as already-deliberate, already-correct: `domain/__init__.py`'s updated `__all__` list flagged as "no longer alphabetically sorted" under a plain ASCII/ordinal sort -- on inspection it correctly follows this codebase's actual established convention (see `adapters/tkinter/common/__init__.py`'s identical shape): `SCREAMING_SNAKE_CASE` constants grouped first, then `PascalCase` classes, then `lowercase` functions, each group alphabetized internally -- not a regression. The dialog's per-field error routing via message-text prefix matching (`"Columns"`/`"Rows"`/`"Start column"`/`"Start row"`) flagged as a fragile untyped coupling to `domain/` message wording -- real as an architectural preference, but any wording drift is already caught loudly by the dialog's own existing test assertions (which pin exact message text per field), and changing `validate_dimensions`/`validate_start_position` to return structured `dict[str, str]` instead of `list[str]` would contradict the spec's explicitly pinned `-> list[str]` Code Map signature for no functional gain.

## Design Notes

**Exit placement diverges deliberately from the legacy algorithm, per the epic context's own framing ("exit placed at the cell farthest from the entry"), not by porting the legacy border-dead-end/out-of-grid convention.** The legacy `generateur_lab` only considered dead-end cells reached *during* generation that happened to sit on the border, appending an out-of-grid offset (`x+1`/`x-1`/`y+1`/`y-1`) as the exit — a convention this rewrite's `Grid` can't even represent symmetrically (it pads only right/bottom, never left/top; see `Grid`'s module docstring). A single post-generation BFS from `entry` over the finished spanning tree is simpler, always produces a real in-grid cell, and matches "farthest from the entry" literally rather than "farthest border dead-end the walk happened to hit" (which could, in the legacy version, occasionally leave `sortie_lab` unset entirely — a latent bug not reproduced here).

**Cross-field live validation, not per-field isolation.** Start-column/row validity depends on the *currently entered* columns/rows value, not the last-confirmed one — so every `<KeyRelease>` across all four entries re-runs the same `_validate()` pass over all four, rather than each field owning an independent, stale view of the others. This mirrors the "recompute fresh, don't cache" lesson already noted in `deferred-work.md`'s `IconButton` entry, applied prospectively here instead of retrofitted later.

## Verification

**Commands:**
- `ruff check .` -- expected: no new lint violations
- `ruff format --check .` -- expected: no formatting diffs
- `pytest` -- expected: full suite green, including the new generation/bounds/dialog tests and the updated `ClassicMazeGallery`/Player-screen/composition-root tests

## Auto Run Result

**Summary:** Implemented Story 2.2's random-maze generation: a pure `domain/maze_generation.py` (iterative randomized DFS-backtracker producing a perfect-maze spanning tree, exit placed at the BFS-farthest cell from entry -- deliberately superseding the legacy's random-frontier-pick/border-dead-end-exit convention) and `domain/maze_size_bounds.py` (the shared `MazeSizeBounds` value object plus its FR-4 3-50/3-35 defaults and a pure dimension validator); a thin `application/maze_size_bounds.py` reader resolving those bounds from `shared`-scope settings with per-field fallback; a new `GenerateRandomDialog` (`adapters/tkinter/player/`) with four live-validated fields (columns, rows, start column, start row); and wiring `ClassicMazeGallery`'s "Generate random" button (previously a documented no-op placeholder) through the dialog to the domain generator and the existing `navigate(ScreenId.PLAYER, maze)` hand-off Story 2.1's "Play" already established. A parallel code-review pass (Blind Hunter + Edge Case Hunter) then patched four findings (two medium: an inverted/non-positive settings-bound edge case that could soft-lock or crash generation; two low: cross-field validation masking, missing initial dialog focus), deferred three low-severity, not-reachable-today findings to `deferred-work.md`, and rejected two findings that were either already correct by inspection or would contradict the spec's own pinned function signatures.

**Files changed:**
- `src/labyrinthes/domain/maze_generation.py` -- new; `generate_random_maze` (iterative DFS backtracker + BFS-farthest-cell exit), `validate_start_position`
- `src/labyrinthes/domain/maze_size_bounds.py` -- new; `MazeSizeBounds`, `DEFAULT_MAZE_SIZE_BOUNDS` (3-50 cols/3-35 rows), `validate_dimensions`
- `src/labyrinthes/domain/__init__.py` -- exports the five new domain names
- `src/labyrinthes/application/maze_size_bounds.py` -- new; `read_maze_size_bounds`, per-field fallback plus the review-patched non-positive-value and inverted-pair guards
- `src/labyrinthes/adapters/tkinter/player/generate_random_dialog.py` -- new `GenerateRandomDialog`, including the review-patched independent per-field validation and initial-focus fix
- `src/labyrinthes/adapters/tkinter/player/classic_gallery.py` -- `_on_generate_random` now opens the dialog; new `_on_generation_confirmed` generates and navigates; `settings_repository` threaded into the constructor
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- `mount()` gains keyword-only `settings_repository`, threaded to `ClassicMazeGallery`
- `src/labyrinthes/app/composition_root.py` -- Player's `functools.partial` wiring gains `settings_repository`
- `_bmad-output/implementation-artifacts/deferred-work.md` -- three new entries (dialog dedup guard, float-truncation gap, missing bound ceiling)
- Tests: `tests/domain/test_maze_generation.py`, `tests/domain/test_maze_size_bounds.py`, `tests/application/test_maze_size_bounds_reader.py` (new; renamed from `test_maze_size_bounds.py` to avoid a same-basename pytest collection collision with the domain test file -- neither `tests/` subpackage has an `__init__.py`), `tests/adapters/tkinter/player/test_generate_random_dialog.py` (new), `tests/adapters/tkinter/player/conftest.py` (+`FakeSettingsRepository`), `tests/adapters/tkinter/player/test_classic_gallery.py` (replaced the no-op placeholder test, added dialog open/confirm coverage), `tests/adapters/tkinter/player/test_player_screen.py` (threaded `settings_repository=` through every `mount()` call)

**Review findings breakdown:** Two parallel reviewers (Blind Hunter, Edge Case Hunter) found and largely overlapped on the same core issues. 4 patched (2 medium: inverted/non-positive settings-derived size bounds that could permanently soft-lock or crash "Generate random" -- both reproduced directly with small repro scripts before fixing; 2 low: cross-field inline-validation masking, missing initial dialog focus), 3 deferred (all low, not reachable today -- no writer exists yet for the shared bound settings keys this story only reads), 2 rejected (an `__all__`-ordering false positive that already matches the codebase's established grouped-alphabetical convention; a message-routing architecture preference already protected by existing exact-text test assertions and that would contradict the spec's own pinned `list[str]` return-type signature). Full breakdown in the Review Triage Log above.

**Verification performed:** `ruff check .` clean, `ruff format --check .` clean, `pytest` -- 381 passed (373 before the review-patch pass, +8 new regression tests for the four code-level patches).

**Residual risk:** The three deferred findings are all real but require either a settings file no current writer produces (float/oversized bound values) or repeated manual re-triggering of a non-modal dialog (stacking) -- none reachable through a normal play session today. No other residual risks identified. As with Story 2.1, the classic-maze library and any `shared`-scope settings are empty in a fresh checkout (Epic 4's migration/Epic 3's Builder settings UI haven't landed), so the settings-fallback path is exercised by tests, not yet by a real run against a populated `shared` settings file -- expected, unblocks on later epics, not this story.
