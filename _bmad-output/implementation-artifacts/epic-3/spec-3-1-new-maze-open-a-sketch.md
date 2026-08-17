---
title: 'Story 3.1: New maze / Open a sketch (New Maze scope; Open Sketch deferred, see Spec Change Log)'
type: 'feature'
created: '2026-08-09'
status: 'done'
review_loop_iteration: 1
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-3/epic-3-context.md']
baseline_revision: '753211b'
final_revision: ''
---

## Intent

**Problem:** The app has no way for the user to create a new empty maze from scratch. The Home screen only provides entries to open an existing Builder or Player session — there is no "New Maze" functionality. ("Open a sketch" was originally bundled into this same story's title/problem statement, but this spec's actual Boundaries/Code Map/I-O Matrix/Tasks below only ever covered "New Maze" — a single independently-shippable goal per the workflow's SCOPE STANDARD. That mismatch was caught by this story's own review loop; "Open Sketch" is now tracked as separate future work, see `deferred-work.md`.)

**Approach:** Add a "New Maze" entry point to the Home screen that opens a dialog allowing the user to specify maze dimensions (columns/rows). After valid dimensions are confirmed, create a new `Maze` with `kind=MazeKind.SKETCH`, `id=None`, and a filled grid using `Grid.filled(columns, rows)`, then navigate to the Player screen with that new sketch. Use the shared `MazeSizeBounds` from settings (FR-4: "The bounds are defined once, in settings, and read by both the Builder and the Game — not duplicated as hardcoded UI constants"). The dialog reuses the shared `read_maze_size_bounds` reader and validates against the 3–50 columns / 3–35 rows bounds. After creation, the user can edit the sketch in the Player, save it, etc.

## Boundaries & Constraints

**Always:**
- `Grid.filled(columns, rows)` produces a closed-border grid with padding row/column, real cells initialized to `"3"` (fully walled), matching the legacy format for lossless CSV round-trips (NFR2/AD-6)
- The dialog is a `tk.Toplevel` parented to the calling widget, not the app's persistent container — nothing is worth surviving a navigate-away, unlike `SettingsWindow`
- The 0/1/2/3 cell encoding is preserved as-is; no re-encoding occurs
- Domain value objects (`Grid`, `Cell`, `Maze`, `Position`, `MazeKind`) are immutable; engine operations are pure functions returning new state
- `MazeKind.SKETCH` has `id=None` eligibility; only `CLASSIC`/`SAVED_RANDOM` elidible kinds receive a `MazeId` on save
- The shared `read_maze_size_bounds(settings)` reader falls back field-by-field to `DEFAULT_MAZE_SIZE_BOUNDS = MazeSizeBounds(3, 50, 3, 35)` on `SettingNotFoundError`/`SettingCorruptError`/`ValueError`/`TypeError`
- Never write to settings from the dialog — only read-with-fallback

**Never:**
- Do not implement a dual-layout compatibility shim for legacy data — FR-23 covers the one-time migration script
- Do not hardcode dimension bounds in the dialog — always read from the shared settings-backed reader
- Do not add a disabled/greyed-out state to the Generate/Create button — use the "leave errors visible, no state change" pattern chosen
- Do not reproduce the legacy "negative offset" exit convention — sketches have no exit convention beyond the grid itself

## Code Map

- `src/labyrinthes/adapters/tkinter/common/new_maze_dialog.py` -- new; `NewMazeDialog(tk.Toplevel)` -- 2-field form (columns, rows), live validation against shared bounds, Create/Cancel
- `src/labyrinthes/adapters/tkinter/home/screen.py` -- add `go_to_new_maze()` that opens `NewMazeDialog`; on confirm, navigate to `ScreenId.PLAYER` with the new `Maze`; add "New Maze" `PillButton` and keyboard shortcut `C`; wire `bind_shortcut` for the `C` key
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- add `Keybinding("open_new_maze", "New Maze", "c")` to canonical keybinding table
- `src/labyrinthes/adapters/tkinter/common/__init__.py` -- export `NewMazeDialog`, `OnConfirmFn`
- `tests/adapters/tkinter/home/test_home_screen.py` -- update test to expect "New Maze" button

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Cold open | Dialog opens with default bounds from settings | Fields pre-filled with valid values (`min_columns`/`min_rows`), no inline errors | No error expected |
| Columns below min | Columns field set to `2` (min 3) | Inline "Columns must be between 3 and 50." shown; Create click does not navigate | No exception, no state change |
| Columns above max | Columns field set to `99` (max 50) | Inline "Columns must be between 3 and 50." shown; Create click does not navigate | No exception |
| Rows below min | Rows field set to `2` (min 3) | Inline "Rows must be between 3 and 35." shown; Create click does not navigate | No exception |
| Rows above max | Rows field set to `99` (max 35) | Inline "Rows must be between 3 and 35." shown; Create click does not navigate | No exception |
| Non-numeric field | Any field set to `"abc"` | Inline "Enter a whole number." for that field; Create click does not navigate | No exception |
| All fields valid | Columns=20, Rows=15 | `Maze(grid=Grid.filled(20, 15), entry=Position(0,0), exit=Position(14, 19), kind=MazeKind.SKETCH, id=None)`; navigate to `ScreenId.PLAYER` with that maze | No error expected |
| Cancel / Escape | Dialog open, Cancel clicked (or `<Escape>`) | Dialog destroyed, navigate never called | No error expected |
| All fields valid, navigate | After create, user is in Player screen browsing the new sketch | Player gallery shows the new sketch; can be played, saved, etc. | No error expected |

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/adapters/tkinter/common/new_maze_dialog.py` -- add `NewMazeDialog` -- the 2-field form, live validation, Create/Cancel
- [x] `src/labyrinthes/adapters/tkinter/home/screen.py` -- add `go_to_new_maze()` + "New Maze" PillButton + `C` shortcut; wire `bind_shortcut`
- [x] `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- add `Keybinding("open_new_maze", "New Maze", "c")`
- [x] `src/labyrinthes/adapters/tkinter/common/__init__.py` -- export `NewMazeDialog`, `OnConfirmFn`
- [x] `tests/adapters/tkinter/home/test_home_screen.py` -- update test to expect "New Maze" button
- [x] Verify `Grid.filled(columns, rows)` produces correct closed-border grid
- [x] Verify `MazeKind.SKETCH` with `id=None` is properly handled by `CsvMazeRepository.save/load`
- [x] Run full test suite to confirm no regressions

## Acceptance Criteria

- [x] User can open "New Maze" from Home screen
- [x] Dialog validates columns (3–50) and rows (3–35) using shared settings bounds
- [x] Invalid inputs show per-field inline errors, Create does not navigate
- [x] Valid dimensions create a sketch maze and navigate to Player screen
- [x] Keyboard shortcut `C` opens the dialog
- [x] Code follows all conventions: English identifiers, domain/UI decoupling, English UI strings, 0/1/2/3 cell encoding preserved

## Spec Change Log

- **Iteration 1 (review loop, bad_spec):** Triggering finding (from three parallel review layers — Blind Hunter, Edge Case Hunter, Verification Gap): this spec's title and Problem statement claimed both "New Maze" and "Open Sketch" as this story's deliverable, but its own Boundaries/Code Map/I-O Matrix/Tasks/Acceptance Criteria were entirely and consistently scoped to "New Maze" only. Separately, a prior work session (commit `39a9aa1`, before this review loop) had committed `src/labyrinthes/adapters/tkinter/common/open_sketch_dialog.py` — a whole `OpenSketchDialog` component, exported from `common/__init__.py` — trying to satisfy the title's "Open Sketch" half, but it was never wired into any screen (`home/screen.py`'s `mount()` doesn't even accept a `maze_repository` port, which the dialog requires) and had zero tests. Reviewers also found it internally buggy: `_compute_errors` had a duplicated, dead `hasattr(self, "_no_sketch_label")` guard that made its "No sketches available." message unreachable and left the Confirm button wrongly enabled with an empty selection; no `trace_add` on the sketch-selection `StringVar` meant Confirm never re-validated after the user picked a different sketch post-failure; a bare `except Exception as e` leaked raw exception text into the UI; and it used `ttk.Button`+disabled-state gating instead of this story's established `PillButton`+"leave errors visible, no state change" pattern.
  - **What was amended:** Retitled and reworded the Problem statement to scope this spec to "New Maze" only, matching what its Boundaries/Code Map/I-O Matrix/Tasks/AC already, correctly specified — per the workflow's own SCOPE STANDARD, "New Maze" and "Open Sketch" are two independently shippable deliverables and should never have shared one spec. "Open Sketch" is deferred to `deferred-work.md` as its own future story, carrying forward the concrete bug list above so whoever picks it up doesn't repeat them.
  - **Known-bad state avoided:** Re-deriving code from the now-corrected spec must NOT reintroduce `open_sketch_dialog.py`/its `common/__init__.py` export — that component is out of this story's scope entirely; it was reverted.
  - **KEEP instructions** (verified correct by review, must survive re-derivation unchanged): `src/labyrinthes/adapters/tkinter/common/new_maze_dialog.py` (`NewMazeDialog`, mirroring `GenerateRandomDialog`'s per-field `tk.Entry` + inline-error-label + `PillButton` Cancel/Create + no-disabled-state + `<KeyRelease>`/`<Return>`/`<Escape>` pattern, bounds via `read_maze_size_bounds`, `validate_dimensions` for per-field messages) and `tests/adapters/tkinter/common/test_new_maze_dialog.py` (16 tests covering the full I/O matrix); `home/screen.py`'s `go_to_new_maze()` + "New Maze" `PillButton` + `C` shortcut wiring; `keybindings.py`'s `Keybinding("open_new_maze", "New Maze", "c")`; `common/__init__.py`'s `NewMazeDialog`/`OnConfirmFn` exports; and the "New Maze" additions to `tests/adapters/tkinter/home/test_home_screen.py`. All of the above passed `ruff check`/`ruff format --check` clean and the full test suite with no regressions (the one pre-existing `test_open_settings_from_home_reflects_a_stored_confirmation_value` failure and the ~110 pre-existing Player-screen `TypeError` failures both reproduce identically on baseline `753211b`, unrelated to this story). Also keep: neither dialog should gain `transient()`/`grab_set()` — non-modal is this codebase's deliberate, documented dialog convention (see `confirm_dialog.py`'s module docstring), not a gap.
- **Iteration 2 (review loop, patch):** A second review round against the re-derived diff (same three parallel layers) found the re-derived code still deviated from this spec's own Boundaries text: `home/screen.py`'s `go_to_new_maze()` constructed `NewMazeDialog(parent, ...)` (the app's persistent container), contradicting both this spec's "parented to the calling widget, not the app's persistent container" bullet and `new_maze_dialog.py`'s own (correct) module docstring. Patched in place, no further spec amendment needed: `go_to_new_maze()` now constructs `NewMazeDialog(frame, ...)`; the Home docstring paragraph and the home-screen test (renamed to `test_new_maze_button_click_opens_a_dialog_parented_to_the_calling_screen_frame`) were updated to match. Also added missing test coverage for the `<Return>`-to-submit binding on both dialog fields (`test_return_on_every_field_is_bound_to_trigger_create`), mirroring `test_generate_random_dialog.py`'s existing convention. Re-verified clean (`ruff`/full suite, no new regressions). Remaining round-2 findings (dialog dedup guard, stale-bounds-on-reopen, uncaught `on_confirm` exception, paste-doesn't-revalidate, 1x1-degenerate-maze-via-corrupt-settings) were pre-existing/systemic patterns already shared with sibling dialogs — logged in `deferred-work.md` rather than patched here.
## Suggested Review Order

**Dialog: dimensions form, validation, maze construction**

- Entry point — the dialog's own shape and lifetime contract (Cancel/Create, bounds source, no disabled-state gate).
  [`new_maze_dialog.py:50`](../../../src/labyrinthes/adapters/tkinter/common/new_maze_dialog.py#L50)

- Per-field validation, routed by matching `validate_dimensions`' message text to each field.
  [`new_maze_dialog.py:145`](../../../src/labyrinthes/adapters/tkinter/common/new_maze_dialog.py#L145)

- Confirm path: re-validates, then builds the `MazeKind.SKETCH`/`id=None` `Maze` via `Grid.filled(...)`.
  [`new_maze_dialog.py:179`](../../../src/labyrinthes/adapters/tkinter/common/new_maze_dialog.py#L179)

**Home screen wiring**

- `go_to_new_maze()` opens the dialog parented to `frame` (the calling screen, not the persistent container) — fixed in review iteration 2.
  [`screen.py:101`](../../../src/labyrinthes/adapters/tkinter/home/screen.py#L101)

- "New Maze" `PillButton` + `C` keyboard shortcut, wired from the same `Keybinding` entry as the printed kbd-tag.
  [`screen.py:130`](../../../src/labyrinthes/adapters/tkinter/home/screen.py#L130)

- Canonical keybinding table entry backing the shortcut/label pair above.
  [`keybindings.py:76`](../../../src/labyrinthes/adapters/tkinter/common/keybindings.py#L76)

- `NewMazeDialog`/`OnConfirmFn` re-exported from the `common` package barrel.
  [`__init__.py:29`](../../../src/labyrinthes/adapters/tkinter/common/__init__.py#L29)

**Tests: I/O matrix coverage**

- Dialog behavior suite — cold open, bounds violations, non-numeric input, no-disabled-state proof, valid creation, cancel/escape, `<Return>` binding.
  [`test_new_maze_dialog.py:42`](../../../tests/adapters/tkinter/common/test_new_maze_dialog.py#L42)

- Home-screen suite — kbd-tag match, shortcut registration, dialog parented to `frame`, confirm navigates to Player with the new sketch.
  [`test_home_screen.py:291`](../../../tests/adapters/tkinter/home/test_home_screen.py#L291)
