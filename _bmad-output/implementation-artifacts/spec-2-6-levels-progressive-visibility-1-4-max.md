---
title: 'Story 2.6: Levels — progressive visibility (1–4, Max)'
type: 'feature'
created: '2026-08-13'
status: 'done'
baseline_commit: '01c043a'
review_loop_iteration: 1
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-2-context.md']
baseline_revision: '01c043a'
---

# Story 2.6: Levels — progressive visibility (1–4, Max)

Status: done

## Story

As a player,
I want to choose a Level (1 through 4, plus Max) that controls how much of the grid is visible while I solve,
so that I can play at my preferred challenge tier.

## Acceptance Criteria

1. **Given** Level 1 active, **when** the maze renders, **then** the full grid is visible at all times (the Story 2.4 baseline).
2. **Given** Level 2 active, **when** the maze renders, **then** it is split into rectangular partitions; each partition the ball has entered **stays shown**, and when the number of visited partitions crosses the reveal threshold, all partitions hide again and accumulation restarts from the current one.
3. **Given** Level 3 active, **when** the maze renders, **then** only the partition the ball is currently inside is visible at a time.
4. **Given** Level 4 active, **when** the maze renders, **then** walls stay invisible until the ball collides with one (which reveals that one wall); when the number of discovered walls crosses the discovered-wall threshold, all discovered walls hide again.
5. **Given** Level Max active, **when** the maze renders, **then** all interior walls are permanently invisible (the outer contour alone remains, per the legacy navigation aid — see Design Notes).
6. **Given** a Level selector on the gameplay screen, **when** the player changes Level, **then** it cycles ONE→TWO→THREE→FOUR→MAX (wrapping), the HUD Level chip updates immediately, and the maze re-renders under the new Level's visibility rules without restarting the run.
7. **Given** a Level change mid-session, **when** applied, **then** the ball's position, elapsed time, movement mode and speed are preserved; only the visibility state resets fresh (partitioned/visited/discovered from the ball's current cell).
8. **Given** a blocked move at Level 4 (at-rest keypress or a Smooth boundary stop), **when** the move is rejected, **then** the collided interior wall becomes visible (and, past the threshold, all discovered walls hide again). Border walls are never "discovered" — the contour already shows them.
9. **Given** a solved run, **when** the Level control is used, **then** it follows the same no-op-after-solve convention as the movement controls (Story 2.5) — no position/time change.

## Intent Contract

### Problem

Story 2.4's `GameplayScreen` renders the whole maze once (`MazeCanvas._draw_walls` draws every wall from the grid) and never redraws structure; Story 2.5 added movement modes/speed but no visibility rules. The product requires five progressive-visibility Levels (FR-12), all derived from the same 0/1/2/3 grid (no separate abstraction layer): Level 1 = everything visible, Level 2 = visited rectangular partitions stay shown until a reveal threshold, Level 3 = one partition at a time, Level 4 = walls revealed only on collision up to a discovered-wall threshold, Level Max = all walls permanently invisible.

### Approach

Build a pure, immutable **Level visibility engine** in `domain/` (`domain/level_visibility.py`): a frozen `LevelVisibility` state (level, difficulty, partition layout, visited-partition set, current partition, discovered-wall set, contour flag) advanced by pure functions as the ball moves or collides. Thread the Level into the run by adding `level`, `difficulty`, and `visibility` fields to `PlayerSession` (`application/player_session.py`), hooking the two movement seams — a blocked move (Level-4 wall discovery) and a leg commit (partition tracking) — and adding a `set_level` function. The screen (Story 2.5's sidebar pattern) gains a "Levels" group (`−`/value/`+`, Tab-operable, no global shortcut), syncs the HUD Level chip, and triggers a structural redraw whenever the session's visibility object changes identity. `MazeCanvas` grows a `redraw_structure(visibility)` that deletes only `"wall"`-tagged items and redraws exactly the walls the domain says are visible (plus the Level 2/3/4 outer contour), leaving entry/exit markers and the ball untouched.

The Level is **session-scoped, not persisted** — each new maze mount starts at `Level.ONE` (matches the legacy `Niveaux.numero` starting at 1 and the epic context's explicit game-scoped settings list, which excludes Level). Difficulty is parameterized with a `Difficulty.ONE` default; **Story 2.7 wires the Difficulty control** and the Level-1-disable gating (see Design Notes for the exact 2.6/2.7 seam).

## Boundaries & Constraints

**Always:** `adapters/tkinter/player/` never imports `adapters/storage/` directly (AD-9). Level/Difficulty visibility rules live in `domain/` as pure functions over frozen state — no Tk, no wall-clock reads, no repository access (NFR1, AD-1..AD-3). `player_session.py` stays a pure orchestration module: the screen applies `set_level` and reads the visibility object back; it never mutates visibility itself. Settings are not touched at all — no new `SettingsRepository` keys, no `settings_keys.py` change (Level is session state, not a persisted preference; the epic context's game-scoped list has no Level entry). The `GameplayScreen` `.after()` loops and toplevel focus guard from Stories 2.4/2.5 stay intact — the new Level buttons share the same guard. No new global keyboard shortcut (the `−`/`+` ToolButtons are Tab+Enter/Space-operable per NFR6, matching Story 2.5's Ball-speed precedent; `m` is already taken by the movement-mode toggle).

**Block If:** Nothing here needs human input — the 2.6/2.7 split (Difficulty control deferred), the Max-contour behavior, the threshold formula placeholder, the Level-cycle wrap, the sidebar placement, and the collision-discovery hooks are all documented decisions below.

**Never:** No Difficulty control (that is Story 2.7 — including its Level-1-disable gating and its final unified threshold formula). No HARD-mode fog/status light (2.8), no timer/timeout (2.9), no confirmation prompts on Level change (2.10), no first-activation explainers (Epic 5 — but leave the Level control's location/state in a shape that won't block later ⓘ-anchor wiring). No change to `composition_root.py`, `screen.py`, `settings_keys.py`, or `keybindings.py`. No new persisted setting. No change to `PlayerSession`'s existing `mode`/`speed`/leg fields or to `attempt_move`/`Duration`. No redraw on every animation sub-step — structure redraws only when the visibility object actually changes (partition entered, threshold reset, wall discovered, contour toggle, Level change).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Initial render, Level 1 (default) | Maze mounted, `level=ONE`, fresh session | Full grid visible — identical to the Story 2.4 baseline; HUD Level chip shows `1` | No error |
| Initial render, Level 2 | `set_level(TWO)` at mount (or mid-session) | Maze partitioned; the partition containing the ball's cell is shown (pre-visited at init); the outer contour is drawn | No error |
| Ball enters a new partition, Level 2 | Leg commits onto a cell in an unvisited partition | New partition is added to the visited set and becomes visible (accumulates — previous visited partitions stay shown) | No error |
| Visited count crosses the reveal threshold, Level 2 | `n_visited > threshold` at partition entry | Visited set clears, then re-adds only the current partition — all previously shown partitions hide again | No error |
| Ball moves within an already-visited partition, Level 2 | No partition-boundary crossing | No visibility change — no redraw, no state churn | No error |
| Ball enters any partition, Level 3 | Leg commits onto a cell in a different partition | Only the current partition is visible; the previous one hides immediately | No error |
| Ball at rest, blocked move, Level 4 | `request_move` returns unchanged (target == position), interior wall | The collided interior wall is added to `discovered_walls` and rendered; session's visibility object identity changes → redraw | No error |
| Ball at rest, blocked move against the border, Level 4 | Blocked move whose wall is a border segment | No discovery — the contour already shows it; no state change | No error |
| Discovered count crosses the discovered-wall threshold, Level 4 | `len(discovered) > threshold` after a discovery | `discovered_walls` clears (all hidden again), then re-adds the just-collided wall | No error |
| Smooth boundary stop, Level 4 | `_resolve_smooth_next` stops (pending + straight blocked) | The blocked boundary wall is discovered (same idempotent `note_collision`) | No error |
| Level Max | `set_level(MAX)` | No interior walls rendered; contour shown at session start and re-shown on each blocked move, hidden again on the next successful move (legacy `contours_visibles` semantics) | No error |
| Level change mid-leg | `set_level` while a leg is in flight | The in-flight leg's geometry is untouched (mirrors Story 2.5's mid-leg mode switch); visibility resets fresh for the current ball cell; next commit re-applies | No error |
| Level change after solve | `set_level` with `solved=True` | No-op — returns the session unchanged (Story 2.5 convention) | No error |
| Win reached | Leg commits onto `maze.exit` | Unchanged Story 2.4/2.5 win path (visibility may redraw first; banner wins) | No error |
| Input while focus is in another toplevel | `−`/`+` clicked or activated while `SaveMazeDialog` has focus | No-op — Level unchanged behind the dialog (shared toplevel focus guard) | No error |
| Screen destroyed mid-session | `.after()` jobs pending, Level buttons present | Existing tick/animation cancellation + `bind_shortcut` cleanup on `<Destroy>` unchanged | No error |

## Code Map

- `src/labyrinthes/domain/level_visibility.py` — **NEW**, pure domain engine (no Tk, no repository):
  - `Wall` — a frozen value object `(row: int, col: int, side: Literal["top", "left"])` identifying one wall segment in **raw grid coordinates** (same space `MazeCanvas._draw_walls` draws in today: `row`/`col` range `0..grid.height`/`0..grid.width`, where the top wall of raw cell `(row,col)` is a horizontal segment and the left wall a vertical one). `Wall` exists iff `grid.cell_at(Position(row, col)).has_top_wall` / `.has_left_wall`.
  - `Partition` — a frozen value object `(top_left: Position, bottom_right: Position)` with `bottom_right` **exclusive**, in **playable** coordinates (`0..grid.width` / `0..grid.height`).
  - `LevelVisibility` — a frozen dataclass carrying: `level: Level`, `difficulty: Difficulty`, `partition_size: tuple[int, int]` (cols, rows), `partitions: tuple[Partition, ...]`, `visited: frozenset[int]` (row-major partition indices entered), `current_partition: int`, `discovered_walls: frozenset[Wall]`, `contour_shown: bool` (Level-Max navigation aid only), `total_interior_walls: int` (Level-4 threshold base).
  - `partition_size_for_difficulty(width, height, difficulty) -> tuple[int, int]` — faithful port of legacy `init_taille_partition_par_difficultées` operating on **playable** `grid.width`/`grid.height`: `D1 → petit_cote//2`, `D2 → grand_cote//4`, `D3 → grand_cote//8` (grand_cote = max(width,height), petit_cote = min), clamped to a minimum of **2** on each axis.
  - `partition_grid(width, height, partition_cols, partition_rows) -> tuple[Partition, ...]` — faithful port of legacy `decoupage_du_lab` (its remainder-edge `x_modif`/`y_modif` adjustments included), operating on playable dimensions; returns a flat row-major tuple.
  - `reveal_threshold(axis_counts: tuple[int, int], difficulty) -> int` — `round(axis_cols * axis_rows / (difficulty + 1))`, the **single shared** threshold formula applied to both Level 2's partition count and Level 4's discovered-wall count (deliberately reusing the legacy Level-2 formula for both, so FR-13's inconsistency is not reproduced even before Story 2.7; this function is the one seam Story 2.7 finalizes).
  - `is_border_wall(grid, wall) -> bool` — `True` for a top wall at raw `row == 0` or `row == grid.height`, or a left wall at raw `col == 0` or `col == grid.width`.
  - `total_interior_walls(grid) -> int` — count of all non-border wall segments.
  - `initial_level_visibility(maze, level, difficulty, position) -> LevelVisibility` — builds the state: partitions per difficulty, `current_partition` = the partition containing `position`, `visited` = `{current}` (Level 2/3 start showing the ball's partition), `discovered_walls` = empty, `contour_shown = True` (Max), `total_interior_walls` computed for Level 4.
  - `advance_visibility(visibility, maze, position) -> LevelVisibility` — pure, called when the ball reaches `position` (leg commit): Level 2 → add the newly-entered partition to `visited` and, if `len(visited) > reveal_threshold(...)`, clear then re-add only the current one; Level 3 → set `current_partition` to the partition containing `position` (single visible partition); Level Max → `contour_shown = False` (legacy hides the contour once the ball moves); no-op for Levels 1/4.
  - `note_collision(visibility, maze, position, direction) -> LevelVisibility` — pure, called on a blocked move: if `level is FOUR` and the blocked segment (mapped from `position`+`direction`, see below) is an interior wall not already discovered, add it; if `len(discovered) > reveal_threshold(...)`, clear then re-add the just-collided wall; if `level is MAX`, set `contour_shown = True` (legacy re-reveals the contour on collision); idempotent — an already-discovered or border wall is a no-op.
  - `visible_walls(visibility, grid) -> frozenset[Wall]` — the exact wall segments to render: ONE → all wall segments; TWO/THREE → all segments whose `(row, col)` cell lies inside a visible partition; FOUR → `discovered_walls`; MAX → empty set.
  - `show_contour(visibility) -> bool` — `True` for Levels TWO/THREE/FOUR always; for MAX, `contour_shown`; `False` for ONE (its border walls are drawn as ordinary walls).
  - Blocked-move → `Wall` mapping (used by `note_collision`'s caller): blocked **up** from `(r,c)` → `Wall(r, c, "top")`; **down** → `Wall(r+1, c, "top")`; **left** → `Wall(r, c, "left")`; **right** → `Wall(r, c+1, "left")`.
- `src/labyrinthes/domain/__init__.py` — **UPDATE**; export the new public types/functions (follow the existing re-export style).
- `src/labyrinthes/application/player_session.py` — **UPDATE**:
  - `PlayerSession` gains `level: Level`, `difficulty: Difficulty`, `visibility: LevelVisibility`. `start_session(maze)` initializes `level=Level.ONE`, `difficulty=Difficulty.ONE`, `visibility=initial_level_visibility(maze, Level.ONE, Difficulty.ONE, maze.entry)`.
  - `request_move(session, direction)` — in the at-rest blocked branch (`attempt_move == position`), apply `note_collision(session.visibility, session.maze.grid, session.position, direction)` to the returned session (Level-4 discovery / Max contour toggle). All other branches unchanged.
  - `_resolve_smooth_next(session)` — in the stop branch (both pending and straight blocked), apply `note_collision` for the blocked `heading` before returning the stopped session.
  - `advance_step(session)` — on leg commit (both Discrete and Smooth), apply `advance_visibility(session.visibility, session.maze, position)` to the committed session. On solve, apply it too (the win position's partition is legitimately entered) — or skip; either is fine as long as the win path is unaffected.
  - `set_level(session, level) -> PlayerSession` — **NEW**: no-op once solved; otherwise returns `replace(session, level=level, visibility=initial_level_visibility(session.maze, level, session.difficulty, session.position))` — visibility resets fresh at the ball's current cell, everything else (position/elapsed/mode/speed/in-flight leg) preserved.
  - Update `__all__`.
- `src/labyrinthes/adapters/tkinter/player/maze_canvas.py` — **UPDATE**:
  - `redraw_structure(visibility: LevelVisibility)` — **NEW**: `delete("wall")`, then draw exactly `visible_walls(visibility, self._maze.grid)` (same line-drawing as `_draw_walls`), then draw the outer contour when `show_contour(visibility)` (a rectangle outline around the playable area, with the exit-side segment left open — mirrors legacy `trace_contours_lab`). Entry marker, exit marker, and ball items are untouched (different tags).
  - Keep `_draw_walls` as the Level-1/full-draw path (or fold it into `redraw_structure` — either way, Level-1 rendering must stay byte-identical to today).
  - No change to `set_ball_offset`/`set_ball_position` or the marker drawing.
- `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — **UPDATE**:
  - Replace the placeholder `_PLACEHOLDER_LEVEL = "1"` with a real Level chip fed from the session (`HudChip.set_value` on change). Add `_LEVEL_LABELS = {ONE: "1", TWO: "2", THREE: "3", FOUR: "4", MAX: "Max"}`.
  - Add a "Levels" group to the left sidebar (Story 2.5's "Movement" group already sets the pattern): a `−` `ToolButton`, a monospace value label (`TYPOGRAPHY.hud-stat`, the same font the HUD uses for numeric data), and a `+` `ToolButton`. `−`/`+` step through the `Level` enum with wraparound (`MAX + 1 → ONE`, `ONE - 1 → MAX`) — matching legacy `plus`/`moins` wrap. No global shortcut (Tab-operable, per `ToolButton`'s existing `<Return>`/`<space>` bindings). The controls call `session_set_level`, then sync the HUD chip and redraw.
  - After every `session_request_move` / `session_advance_step` / `session_set_level` call, detect a visibility change via object identity (`self._session.visibility is not previous_visibility`) and call `self._maze_canvas.redraw_structure(self._session.visibility)` — never a full rebuild, never a per-sub-step redraw.
  - The new controls reuse the shared toplevel focus guard (extracted in Story 2.5).
- `tests/domain/test_level_visibility.py` — **NEW**: partition sizing per difficulty (incl. the min-2 clamp and an 8×6 example: D1 → 3×3 partitions, 3×2 = 6 partitions), `partition_grid` coverage of a no-remainder and a remainder case, Level-1 all-visible, Level-2 accumulate-then-reset across the threshold (assert the reset point for a known `threshold`), Level-3 one-at-a-time, Level-4 discovery (blocked move maps to the right `Wall`; border-wall discovery is a no-op; threshold reset), Max (no interior walls; contour toggle on collision then hidden on move), `is_border_wall`, `total_interior_walls`, `visible_walls`/`show_contour` per level.
- `tests/application/test_player_session.py` — **UPDATE**: `start_session` defaults (`level=ONE`, `difficulty=ONE`, entry partition pre-visited); `set_level` resets visibility at the current position, preserves position/elapsed/mode/speed, no-op once solved; blocked at-rest `request_move` at Level 4 records the wall (identity change) and stays a no-op at Levels 1–3; `advance_step` updates partition tracking on commit; Smooth boundary-stop discovery.
- `tests/adapters/tkinter/player/test_maze_canvas.py` — **UPDATE**: `redraw_structure` renders exactly the visible walls per level, draws/omits the contour per `show_contour`, leaves entry/exit/ball items untouched.
- `tests/adapters/tkinter/player/test_gameplay_screen.py` — **UPDATE**: Level group renders at `Level.ONE`; `−`/`+` cycle the session level and HUD chip (wrap both directions); a Level change redraws the canvas (assert the wall set changed) without restarting the run (position/elapsed/mode/speed preserved); Level 2's partition redraw on entry and threshold reset (drive the animation loop with the existing `_settle()` helper); focus guard applies to the Level controls; no-op after solve.

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/domain/level_visibility.py` — add `Wall`, `Partition`, `LevelVisibility`, partition/visibility pure functions — no Tk, no repository
- [x] `src/labyrinthes/domain/__init__.py` — export the new public API
- [x] `tests/domain/test_level_visibility.py` — unit coverage of every Level behavior + threshold math
- [x] `src/labyrinthes/application/player_session.py` — add `level`/`difficulty`/`visibility` fields, discovery + partition-tracking hooks, `set_level`
- [x] `tests/application/test_player_session.py` — extend for the new fields/hooks/set_level
- [x] `src/labyrinthes/adapters/tkinter/player/maze_canvas.py` — add `redraw_structure` + contour; keep Level-1 rendering identical
- [x] `tests/adapters/tkinter/player/test_maze_canvas.py` — test `redraw_structure`
- [x] `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — "Levels" sidebar group, live HUD Level chip, identity-diff redraw, focus guard
- [x] `tests/adapters/tkinter/player/test_gameplay_screen.py` — Level-group/mid-session-change/redraw/no-op rows

**Acceptance Criteria:**
- [x] Given Level 1 active → full grid always visible
- [x] Given Level 2 active → rectangular partitions; visited partitions stay shown until the reveal threshold is crossed, then hide again
- [x] Given Level 3 active → only one partition visible at a time
- [x] Given Level 4 active → walls invisible until collision; past a discovered-wall threshold they hide again
- [x] Given Level Max active → all walls permanently invisible

### Review Findings

- [x] [Review][Patch] Screen-level Level-2 threshold-reset redraw test missing [tests/adapters/tkinter/player/test_gameplay_screen.py] — spec test plan (line 113) promises "Level 2's partition redraw on entry and threshold reset"; only partition-entry is covered (`test_level_two_partition_advance_redraws_the_structure`). The reset-on-threshold branch (level_visibility.py:293-294) is implemented but only exercised at domain level. Also gaps the I/O matrix rows for Level 3 and Level-4 Smooth-boundary-stop at screen level. — fixed: added `test_level_two_threshold_reset_hides_all_partitions_but_the_current`, `test_level_three_redraws_only_the_current_partition`, `test_level_four_smooth_boundary_stop_redraws_the_discovered_wall`
- [x] [Review][Patch] `set_level` mid-leg in-flight-leg preservation untested [tests/application/test_player_session.py] — I/O matrix row "Level change mid-leg" ("the in-flight leg's geometry is untouched") has no test; all `set_level`/`_cycle_level` tests run at rest, so a regression dropping `moving_direction`/`leg_target`/`step` on a mid-motion level change would freeze the ball with no test failing. Mirror `test_set_mode_replaces_the_mode_without_touching_an_in_flight_leg`. — fixed: added `test_set_level_preserves_an_in_flight_leg`
- [x] [Review][Patch] `set_level` preservation of elapsed/mode/speed unasserted [tests/application/test_player_session.py:446] — spec test plan (line 111) requires "preserves position/elapsed/mode/speed, no-op once solved"; the test asserts only position/solved/level/visibility. Behavior is correct (`set_level` uses `replace`, keeping elapsed/mode/speed); assertions needed. — fixed: added `test_set_level_preserves_elapsed_mode_and_speed`
- [x] [Review][Patch] Contour exit-reopen bars tested only for the bottom edge [tests/adapters/tkinter/player/test_maze_canvas.py:298] — the top/left/right reopen branches (maze_canvas.py:155-182) are implemented but untested; a regression reopening the wrong side for a top/left/right-exiting maze would visually wall the exit off while `len(contour) > 0` assertions still pass. Parametrize over all four edges plus a corner. — fixed: added `test_redraw_structure_reopens_every_exit_edge_with_corridor_bars`
- [x] [Review][Patch] Level-2 `current_partition` goes stale on re-entry into a visited partition [src/labyrinthes/domain/level_visibility.py:287] — `advance_visibility` Level-TWO re-entry branch returns `visibility` unchanged, leaving `current_partition` behind the ball. Benign today (Level-2 rendering reads `visited`, not `current_partition`) but violates the field's documented meaning ("the ball's current partition"); a latent trap for any future consumer. — fixed: re-entry now `replace(visibility, current_partition=current)` unless already the current partition (no-op preserved); tests `test_level_two_reentering_a_visited_partition_updates_current_partition` + `test_level_two_staying_within_the_current_partition_is_a_no_op`
- [x] [Review][Patch] `Wall`/`Partition` lack runtime validation [src/labyrinthes/domain/level_visibility.py:62,72] — `side: Literal["top","left"]` is type-hint only; a `side="bottom"` typo silently renders nothing, defeats `is_border_wall`, and inflates `total_interior_walls`, unlike the defensive `__post_init__` used elsewhere in `domain/`. Add a `__post_init__` guard. — fixed: `__post_init__` on `Wall` (side) and `Partition` (non-degenerate rectangle); tests `test_wall_rejects_an_invalid_side`/`test_partition_rejects_a_degenerate_rectangle`
- [x] [Review][Defer] Level-4 reveal threshold is degenerate at real maze sizes [src/labyrinthes/domain/level_visibility.py:324] — `round(total_interior_walls/(d+1))` at D1 means ~half of a 10×10 grid's ~180 interior walls must be discovered before AC-4's "hide again" fires; in practice walls accumulate until solve. Spec-pinned placeholder formula, explicitly the Story-2.7 seam — deferred, pre-existing
- [x] [Review][Defer] `reveal_threshold` uses Python's banker's `round()` vs legacy half-up `arrondi` [src/labyrinthes/domain/level_visibility.py:194] — `round(0.5)==0`, `round(2.5)==2`; for a maze with 1 interior wall at D1 the threshold is 0, so every discovery immediately resets to just that wall (equivalent rendering, but diverges from legacy semantics at fractional boundaries). Spec-pinned `round(...)`; Story-2.7 finalizes the function — deferred, pre-existing
- [x] [Review][Defer] `redraw_structure` recreates walls above markers/ball in canvas z-order [src/labyrinthes/adapters/tkinter/player/maze_canvas.py:131] — deleted-and-recreated `"wall"`/`"contour"` items stack above the constructor-drawn markers/ball (constructor order was walls → markers → ball). No geometric overlap today (ball radius ≪ cell half), so visually benign; latent if wall/marker sizing ever changes — deferred, pre-existing
- [x] [Review][Defer] Wall-decoding walkers duplicated across four sites [src/labyrinthes/domain/level_visibility.py] — `_all_walls`, `total_interior_walls`, `visible_walls`, and `MazeCanvas._draw_walls` each walk the grid decoding walls with subtly different semantics; drift risk. A single "walls of this grid" primitive would remove it — deferred, pre-existing

## Spec Change Log

- 2026-08-13 — Created spec from epics.md Story 2.6 ACs (lines 600-628), epic-2-context.md (Levels/Difficulty mechanics + game-scoped settings list), PRD FR-12/FR-13 + addendum "Level detail", legacy `Labyrinthes_copy.py` (`decoupage_du_lab`, `creation_partitions_lab`, `Position_joueur_sur_back_lab_partition`, `trace_grille`/`trace_contours_lab`, `fleches`/`test_nb_murs_niv_4`, `Niveaux`), Story 2.5's spec/review learnings, and the current `rewrite` codebase.
- 2026-08-13 — Implemented Story 2.6 on `story-2-6-levels-progressive-visibility-1-4-max` (baseline `01c043a`). Full suite green (577 passed); `ruff check` clean on the touched files (6 pre-existing E501/F401 issues fixed), `ruff format` clean. Story status moved `in-progress` -> `review` for code review.
- 2026-08-13 — Code review complete (Blind Hunter, Verification Gap, Acceptance Auditor; Edge Case Hunter returned empty and was marked failed). 6 patch findings fixed, 4 deferred (written to `deferred-work.md`), 10 dismissed. Full suite now 593 passed; `ruff check`/`ruff format` clean on `src`+`tests`. Story status moved `review` -> `done`.

## Review Triage Log

_No review yet — this story is fresh (`ready-for-dev`)._
_Implementation complete — status moved `in-progress` -> `review` for code review._

## Design Notes

**The 2.6/2.7 seam — Difficulty stays out of this story.** Level 2/3's partition sizing and both Level 2 and Level 4's thresholds are *parameterized by* `Difficulty` in the engine (`partition_size_for_difficulty`, `reveal_threshold`, session `difficulty` field defaulting to `Difficulty.ONE`), but the Difficulty **control, its Level-1-disable gating, and the final shared-formula decision are Story 2.7's.** `reveal_threshold` already applies ONE formula to both Level 2 and Level 4 (`round(counts/(d+1))`) so FR-13's legacy inconsistency (Level 2's `/(d+1)` vs Level 4's `/2,/5,/10`) is not reproduced even now — 2.7 just needs the control to drive the parameter and can revise the single function if the final formula differs. **Do not** add per-level duplicate threshold code; there is exactly one threshold function.

**Faithful port vs. the AC's wording — Level 2 accumulates.** The addendum and AC say "each visited partition stays shown until a reveal threshold is crossed, then hides again." The legacy code *as written* only ever rendered the current partition (`self.Partitions_lab = [self.back_lab_partition_grille[y][x]]`), which contradicts its own addendum description. The AC/PRD wording is authoritative: visited partitions accumulate and stay shown; on `n_visited > threshold` all hide and accumulation restarts from the current one. Port the *documented* behavior, not the legacy rendering shortcut.

**Level Max's outer contour is the legacy navigation aid, not an interior wall.** The AC's "all walls permanently invisible" refers to interior walls. Legacy still draws the playable-area contour rectangle at Level Max: visible at start, re-shown briefly on each collision, hidden again on the next move (`contours_visibles`). Reproduce that via the `contour_shown` flag toggled by `note_collision` (set `True`) and `advance_visibility` (set `False`). Levels 2/3/4 draw the contour permanently (`trace_contours_lab`), with the exit-side segment left open so the exit reads as a passage; Level 1 draws its border as ordinary walls and draws no separate contour.

**Level cycles as one ordinal, Max included.** Legacy modeled Max as a separate toggle layered on levels 1–4 (`Niveaux.niveau_max`). The rewrite's `Level` enum already pins `MAX = 5` ordered above `FOUR` (Story 1.1). Make the selector a single wrap-around ordinal (`−` and `+`), so MAX is reachable in one `+` from FOUR and wraps back to ONE — simpler than a toggle and consistent with AD-3's pinned ordinal. (The `m` shortcut legacy used for Max is already taken by Story 2.5's movement-mode toggle; the Level buttons are Tab-operable instead.)

**Coordinate translation — playable vs raw grid.** `MazeCanvas._draw_walls` draws in **raw** grid indices (`0..grid.height` × `0..grid.width`, the extra padding row/column), and `Wall(row, col, side)` uses those same raw coordinates so rendering needs no translation. Partitions live in **playable** coordinates (`0..grid.width` × `0..grid.height`) so `partition_grid` is a direct port of legacy `decoupage_du_lab` on the playable dimensions (legacy used the raw +1 array and then compensated with `-1`s; the rewrite's `Grid.width`/`height` are already playable — do **not** reintroduce `-1` compensation, per `grid.py`'s docstring). The blocked-move→`Wall` mapping in the Code Map produces raw coordinates directly.

**Wall discovery is interior-only.** A blocked move against the maze border maps to a border `Wall` — that must be a no-op for `discovered_walls` (the contour already shows the border). `is_border_wall` gates discovery. This matches legacy's `condition_2 = self.x < self.grille.x-2` exclusion.

**Level-4 discovery hooks (faithful with one deliberate widening).** Legacy discovered a wall only on a *keypress-time* collision (`fleches`); a Smooth boundary stop revealed nothing. This story deliberately widens that to "any blocked move" — at-rest keypress **and** Smooth boundary stop — so "walls stay invisible until collision" holds everywhere the ball actually hits something. `note_collision` is idempotent (already-discovered walls don't re-trigger the threshold).

**Redraw discipline — identity diff, never per-sub-step.** `LevelVisibility` is frozen, so a visibility *change* is exactly an object-identity change. The screen compares `session.visibility is not previous` after each session call and redraws structure only then (entered a partition, threshold reset, discovered a wall, contour toggle, Level change). This keeps the animation hot loop cheap and avoids re-rendering on every sub-step.

**Level change is non-destructive to the run.** `set_level` resets visibility fresh at the ball's *current* cell (not `maze.entry`) and preserves position/elapsed/mode/speed and the in-flight leg (Story 2.5's mid-leg-switch precedent). The run is not restarted, the elapsed timer is not reset. The visited/discovered state always starts fresh for the new Level.

**Placement of the control.** The finalized mockup's gameplay sidebar shows only Session/Movement/Shortcuts/Mode groups and puts Level/Difficulty values in the HUD chips; the *change* control's placement is this story's call. The left sidebar "Levels" group (`−` value `+`) mirrors the legacy `<-`/`Niveau`/`->` triad, keeps the controls on the gameplay surface (where FR-28's explainer will later anchor), and reuses Story 2.5's sidebar pattern. The HUD Level chip and the sidebar value label stay in sync via `HudChip.set_value`.

**No persistence.** The epic context's game-scoped settings list (movement speed, confirmation toggles, HARD-mode color, theme, logo, time-limit) does **not** include Level, and the legacy `Niveaux.numero` was session state. The Level therefore is session-scoped: `start_session` defaults it to `Level.ONE`, and a fresh mount (re-navigate) starts over. Do not add a `game`-scoped `LEVEL` key.

## Previous Story Intelligence

- **Story 2.5 (movement modes)** established the exact patterns this story extends: `PlayerSession` is an immutable `@dataclass(frozen=True)` with free functions over it (`request_move`/`advance_step`/`set_mode`/`set_speed`), settings applied by the *screen* at mount, a left-hand sidebar of `ToolButton`s with the shared toplevel focus guard, win detection at leg completion, `.after()` jobs cancelled on `<Destroy>`/solve, and tests driven by a `_settle()` helper that advances the animation loop. Reuse `session_set_*` naming for `set_level`.
- **Story 2.4** defined `MazeCanvas`'s one-shot wall/marker/ball drawing and `HudChip` (`set_value`). The Level chip replaces 2.4's `_PLACEHOLDER_LEVEL`; the Difficulty chip keeps 2.4's `_PLACEHOLDER_DIFFICULTY = "—"` until 2.7.
- **Regression watchlist from 2.5:** all `GameplayScreen(...)` call sites in `test_gameplay_screen.py` already pass `settings_repository=` (2.5 made it required); adding the Level group must not disturb those. The focus-dependent GUI tests flagged in `AGENTS.md` remain flaky in a full run but pass in isolation — re-run a single failing GUI test alone before assuming a regression.

## Git Intelligence

- Working branch: `epic-2-play-a-maze-game-player` (the epic-2 accumulation branch). **Never commit directly to it** — create `story-2-6-levels-progressive-visibility-1-4-max` from it, merge story → epic via `git merge --no-ff` when done; epic → `rewrite` only via PR once the whole epic is done.
- Recent commits show the per-story rhythm to mirror: `feat(player): ...` (feature) → `refactor(player): ...` / `test(player): ...` (cleanup/tests) → `docs(planning): record Story 2.x review, mark done, log deferred work` → `Merge story-2-x-... into epic-2-... (story 2.x)`. Conventional Commits in English, story number in the subject (`(story 2.6)`).
- `uv.lock` is currently an untracked file in the working tree — leave it alone (do not stage/commit).

## Latest Technical Information

No new external dependencies: the stack is pinned in `pyproject.toml` (Python ≥3.12, tkinter, pytest ≥8.0, ruff ≥0.6, hatchling). Everything here uses stdlib (`enum`, `dataclasses`, `frozenset`) and the existing `domain/` types — no web research was needed, and no version/API changes affect this story.

## Verification

**Commands:**
- `ruff check .` — expected: no new lint violations (line-length 100, rules `E, F, I, UP, B, SIM`; no comments unless asked)
- `ruff format --check .` — expected: no formatting diffs
- `pytest` — expected: full suite green, including the new `test_level_visibility.py` and all updated test files

**Regression watchlist:** the `GameplayScreen` construction sites and `_settle()`-driven movement/win tests in `test_gameplay_screen.py`; `player_session.py`'s `request_move`/`advance_step` no-op-after-solve guards (the new hooks must stay no-ops once solved); `MazeCanvas` Level-1 rendering must stay visually identical; the AD-9 import-boundary test must still pass (domain/application import no Tk, `adapters/tkinter/player` imports no `adapters/storage/`).

## Project Structure Notes

- All Level/Difficulty visibility logic lands under `src/labyrinthes/domain/` (pure) and `src/labyrinthes/application/` (session orchestration); only rendering/input in `adapters/tkinter/player/`. No new screen, no new port, no new settings key, no composition-root change.
- Naming is English throughout (NFR4); maze data (`0/1/2/3`) untouched; the `Level`/`Difficulty` types already exist and stay as-is (Stories 1.1).
- No `tkinter`/`adapters` import may appear in `domain/level_visibility.py` or `player_session.py` (AD-1, AD-9).

## References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 2.6 ACs (lines 600-628); FR-12/FR-13 (lines 140-146); FR-28 anchor note (line 79)]
- [Source: `_bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/addendum.md` — "Level detail" (lines 28-34), incl. the Level 2 vs Level 4 formula inconsistency]
- [Source: `_bmad-output/implementation-artifacts/epic-2-context.md` — Levels mechanics (lines 29-35), game-scoped settings list (line 50), technical decisions (lines 45-51)]
- [Source: `Labyrinthes_copy.py` (legacy, read-only) — `decoupage_du_lab` (680-719), `creation_partitions_lab` (721-745), `init_taille_partition_par_difficultées` (747-770), `Position_joueur_sur_back_lab_partition` (772-806), `trace_grille`/`trace_contours_lab` (469-497), `fleches` collision/discovery (1120-1173), `test_nb_murs_niv_4` (965-979), `Niveaux` (1969-2070)]
- [Source: `src/labyrinthes/domain/grid.py` (padding row/col, playable width/height), `domain/cell.py` (wall bits), `domain/level.py`/`domain/difficulty.py` (ordinals), `application/player_session.py` (session shape), `adapters/tkinter/player/gameplay_screen.py` + `maze_canvas.py` (current rendering/sidebar), `tests/adapters/tkinter/player/conftest.py` (fakes)]
- [Source: Story 2.5 spec `_bmad-output/implementation-artifacts/spec-2-5-movement-modes-smooth-vs-discrete-configurable-speed.md` — sidebar/focus-guard/session patterns to extend]

## Dev Agent Record

### Agent Model Used

opencode/deepseek-v4-flash-free

### Debug Log References

- Implementation dev session 2026-08-13 (`opencode`, model `opencode/deepseek-v4-flash-free`): implemented domain engine, session hooks, canvas redraw, screen Level group, and all tests; fixed a row/col swap in `partition_grid` (legacy `(x,y)=(col,row)` translation), an inverted Level-Max `advance_visibility`/`note_collision` contour toggle, and test assertions for the row-major partition layout.

### Completion Notes List

- Created spec from epics.md Story 2.6 ACs, epic-2-context.md, PRD FR-12/FR-13 + addendum "Level detail", legacy `Labyrinthes_copy.py` Level mechanics, Story 2.5's spec/review learnings, and the current `rewrite` codebase.
- Implemented `domain/level_visibility.py` (Wall, Partition, LevelVisibility, `partition_size_for_difficulty`, `partition_grid`, `reveal_threshold`, `is_border_wall`, `total_interior_walls`, `initial_level_visibility`, `advance_visibility`, `note_collision`, `visible_walls`, `show_contour`) — pure, frozen, no Tk. Exported via `domain/__init__.py`.
- Extended `PlayerSession` with `level`/`difficulty`/`visibility`; `request_move` blocked branch and `_resolve_smooth_next` stop branch apply `note_collision`; `advance_step` commit applies `advance_visibility`; added `set_level` (fresh visibility at current cell, preserves run, no-op when solved). Idempotence via object identity (unchanged state returns the same object) preserves the `result is session` no-op convention.
- Added `MazeCanvas.redraw_structure(visibility)` + `_draw_wall_bar`/`_draw_contour` (Level-1 rendering unchanged); Level-2/3/4 contour mirrors legacy `trace_contours_lab` with the exit-side segment left open.
- Wired the real Level chip + "Levels" sidebar group (`−`/value/`+`, wraparound cycle) in `GameplayScreen` with identity-diff visibility redraws; toplevel focus guard shared with the Story 2.5 controls.
- Full suite: 577 passed (23 domain level-visibility, 27 player-session, 21 maze-canvas, 48 gameplay-screen). `ruff check` + `ruff format` clean on the touched files. Story status moved `in-progress` -> `review`.

### File List

- This spec: `_bmad-output/implementation-artifacts/spec-2-6-levels-progressive-visibility-1-4-max.md`
- Story-2.6 backlog entry in `_bmad-output/implementation-artifacts/sprint-status.yaml` (2-6: backlog -> in-progress -> review)
- `src/labyrinthes/domain/level_visibility.py` — NEW, pure Level-visibility engine
- `src/labyrinthes/domain/__init__.py` — export new public API
- `src/labyrinthes/application/player_session.py` — level/difficulty/visibility fields, collision-discovery + partition-tracking hooks, `set_level`
- `src/labyrinthes/adapters/tkinter/player/maze_canvas.py` — `redraw_structure`, `_draw_wall_bar`, `_draw_contour`
- `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — real Level chip, "Levels" sidebar group, identity-diff redraw
- `tests/domain/test_level_visibility.py` — NEW, domain coverage of every Level + threshold math
- `tests/application/test_player_session.py` — extended for the new fields/hooks/set_level
- `tests/adapters/tkinter/player/test_maze_canvas.py` — `redraw_structure` coverage
- `tests/adapters/tkinter/player/test_gameplay_screen.py` — Level-group/mid-session-change/redraw/no-op coverage
