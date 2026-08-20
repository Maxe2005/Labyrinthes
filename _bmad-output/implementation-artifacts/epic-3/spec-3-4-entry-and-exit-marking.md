---
title: 'Story 3.4: Entry and exit marking'
type: 'feature'
created: '2026-08-19'
status: 'done'
review_loop_iteration: 1
baseline_commit: 'b62f0ca5f8e0153edfc3acb5d0bd5448f31a4400'
context: ['_bmad-output/implementation-artifacts/epic-3/epic-3-context.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Builder (stories 3.1–3.3) edits walls but cannot define the maze's start and goal. Entry/exit already exist as required `Position` fields on `Maze` (`domain/maze.py:36-37`) and are persisted in the CSV, yet nothing renders or edits them on the Builder canvas — Epic 3's FR-3 is unimplemented.

**Approach:** Add mutually-exclusive Set Entry / Set Exit tools that place markers on the canvas (entry on any cell, exit on a border cell only), with a live dashed-`?` ghost-marker preview while Set Exit is active; `BuilderSession` gains optional `entry`/`exit` positions and a new domain `is_border_cell` predicate guards exit placement; redefining an existing marker prompts for confirmation through the shared FR-17 mechanism, toggleable off in Settings.

## Boundaries & Constraints

**Always:**
- Marker placement is pure application work: `apply_set_entry`/`apply_set_exit` return new immutable `BuilderSession`s, rebuilding `Maze` via `dataclasses.replace(session.maze, entry=...)` / `(exit=...)` — the exact `apply_wall_toggle` pattern (`builder_session.py:95`); no `tkinter` in `domain/`/`application/`
- `BuilderSession.entry`/`.exit` are `Position | None`; `start_builder_session` seeds `entry=maze.entry`, `exit=None` (a fresh sketch's entry renders immediately, its exit starts unset)
- Exit placement is border-cell only: a non-border target is a no-op. `apply_set_exit` guards via the new domain `is_border_cell` and raises `DomainValidationError`; the adapter catches and swallows it (mirrors `_on_wall_clicked` at `screen.py:306`)
- Ghost-marker: rendered only while `BuilderTool.SET_EXIT` is active, at the cursor cell if it is a border cell — dashed outline + `?` glyph in `colors.ghost`, non-interactive; never a standing default/placeholder position for an unset exit
- Redefining an entry/exit at a *different* position triggers the shared `ConfirmDialog`, gated by a new BUILDER-scope bool setting (default `True`); clicking the cell already holding the marker is a no-op with no prompt
- Entry and exit never share a cell: placing one marker on the other's current cell is a silent no-op (start and goal stay distinct) — mirrors the click-own-marker no-op and the non-border no-op
- Markers are distinguished by shape as well as color (entry = filled circle, exit = filled diamond) — NFR6 accessibility floor
- New keybindings register in the canonical table, BUILDER scope: `set_entry` ("e"), `set_exit` ("x")
- CSV format unchanged — entry/exit are already the first two header lines

**Ask First:**
- Any new color token or glyph beyond the existing `colors.entry`/`colors.exit`/`colors.ghost`

**Never:**
- Do not make `Maze.entry`/`Maze.exit` optional — blast radius across `player_session`, `maze_generation`, CSV readers; the session owns unset-ness
- No drag gesture for markers (click only), no undo/history, no marker persistence beyond the maze's existing entry/exit fields (save/load semantics are Story 3.6)

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Set Entry active, click a cell | any cell | Cell becomes the entry; filled circle marker rendered there | N/A |
| Set Exit active, click a border cell | ghost visible at cursor | Cell becomes the exit; filled diamond marker replaces the ghost | N/A |
| Set Exit active, click an interior cell | target not a border cell | No-op; exit unchanged, no marker moved | `DomainValidationError` raised, adapter swallows (no visual feedback) |
| Redefine entry/exit on a different cell | marker already set elsewhere | ConfirmDialog first, then placement (default); immediate placement when the setting is off | setting read via `read_confirm_redefine_marker`, never raises |
| Click the cell already holding the marker | same position | No-op, no prompt | N/A |
| Set Exit active, cursor moves to an interior cell | tool active, cursor interior | Ghost hidden on that cell | N/A |
| Fresh sketch session | maze from `NewMazeDialog` | Entry rendered at `maze.entry`, exit unset (nothing rendered) | N/A |

</frozen-after-approval>

## Code Map

- `src/labyrinthes/domain/level_visibility.py` — add `is_border_cell(grid, position) -> bool` beside `is_border_wall` (L216); true when `row in (0, grid.height - 1)` or `col in (0, grid.width - 1)`
- `src/labyrinthes/application/builder_session.py` — `BuilderTool` (L64) += `SET_ENTRY = "set-entry"`, `SET_EXIT = "set-exit"`; `BuilderSession` (L73) += `entry: Position | None`, `exit: Position | None`; `start_builder_session` (L83) seeds `entry=maze.entry, exit=None`; new `apply_set_entry(session, position)` / `apply_set_exit(session, position)` mirroring `apply_wall_toggle` (L95); update `__all__` (L52)
- `src/labyrinthes/application/settings_keys.py` — add `CONFIRM_REDEFINE_MARKER = "confirm_redefine_marker"` (BUILDER-scoped)
- `src/labyrinthes/application/confirmation_settings.py` — add a `scope` parameter to `_read_bool` (L39); add `read_confirm_redefine_marker` (default `True`) / `write_confirm_redefine_marker` using `SettingsScope.BUILDER`
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` — add `Keybinding("set_entry", "Set Entry", "e", ScreenId.BUILDER)` and `Keybinding("set_exit", "Set Exit", "x", ScreenId.BUILDER)` beside the existing BUILDER entries (L100-103)
- `src/labyrinthes/adapters/tkinter/common/settings_window.py` — add one row to `_CONFIRMATION_TOGGLES` (L86-91) wiring the new reader/writer
- `src/labyrinthes/adapters/tkinter/builder/screen.py` — thread `settings_repository` into `_BuilderEditArea` (L162-168); two `ToolButton`s + `_activate_set_entry`/`_activate_set_exit` mirroring `_activate_break` (L288-302); `ConfirmDialog` gating for redefinition (mirror the `_maybe_confirm` guard pattern from `gameplay_screen.py:665`); `_BuilderMazeCanvas` marker rendering (entry filled oval / exit filled diamond from `colors.entry`/`colors.exit`; ghost dashed rect + `?` text in `colors.ghost`) and `refresh_markers(entry, exit, ghost_at)`; `_on_release` (L480) fires a same-cell `on_cell_clicked` when the press-captured tool is a marker tool; `_on_move` (L330) refreshes markers so the ghost tracks the cursor

**Marker geometry reference** — `src/labyrinthes/adapters/tkinter/player/maze_canvas.py`: `_draw_entry_marker` (L220-231, filled oval), `_draw_exit_marker` (L233-250, filled diamond), `_MARKER_SCALE = 0.6` (L52).

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/domain/level_visibility.py` -- add `is_border_cell`, reusing the grid's playable `height`/`width` (no new concept)
- [x] `src/labyrinthes/application/builder_session.py` -- extend `BuilderTool` and `BuilderSession`; seed in `start_builder_session`; add `apply_set_entry`/`apply_set_exit` with the border-cell guard
- [x] `src/labyrinthes/application/settings_keys.py` + `src/labyrinthes/application/confirmation_settings.py` -- BUILDER-scope "confirm before redefining entry/exit" setting (default `True`)
- [x] `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- `set_entry` ("e") / `set_exit` ("x") BUILDER entries
- [x] `src/labyrinthes/adapters/tkinter/common/settings_window.py` -- Confirmation toggle row for the new setting
- [x] `src/labyrinthes/adapters/tkinter/builder/screen.py` -- tool buttons + activation handlers, cell-click placement (same-cell release), marker/ghost rendering + `refresh_markers`, confirm gating, marker refresh on cursor move
- [x] `tests/domain/test_level_visibility.py` -- `is_border_cell`: corners, edges, interior, 3×3 min grid
- [x] `tests/application/test_builder_session.py` -- set entry/exit, border guard, immutability (original session untouched), seeding, cursor unchanged
- [x] `tests/adapters/tkinter/builder/test_builder_screen.py` -- tool activation, cell placement, ghost preview follows cursor, non-border no-op, redefine confirm on/off, "e"/"x" activation
- [x] `tests/application/test_confirmation_settings.py` + `tests/adapters/tkinter/common/test_keybindings.py` -- new setting default/round-trip + new keybinding entries

**Acceptance Criteria:**
- Given the Set Entry tool active, when a cell is clicked, then it becomes the entry, rendered with the marker component's distinct glyph
- Given the Set Exit tool active, when a border cell is clicked, then it becomes the exit; before it's set, a ghost-marker state is shown, never a default/placeholder position
- Given an entry or exit is already set, when the user redefines it, then a confirmation prompt appears, toggleable off in Settings

## Spec Change Log

- 2026-08-19 (review loop 1): human renegotiated frozen intent after review finding "entry and exit can be set on the same cell (start == goal)". Added the rule "entry and exit never share a cell — placing one on the other's cell is a silent no-op" to the Intent. Guards go in `_place_entry`/`_place_exit` (adapter no-op) and `apply_set_entry`/`apply_set_exit` (application `DomainValidationError`, adapter swallows). KEEP: no-op-without-prompt semantics match the click-own-marker row; markers stay visually distinct; the ghost is never drawn over a marker cell.

## Design Notes

- **Session owns "unset":** `Maze.entry`/`Maze.exit` stay required (player, generation, and CSV all depend on them); `BuilderSession` carries the authoritative optional positions and always keeps `session.maze` in sync via `dataclasses.replace`, so Story 3.6's save reads the right values.
- **Click vs drag:** marker placement reuses the press/release cell comparison (`screen.py:480`) — only a same-cell release places a marker, so a stray drag never misplaces one and the Story 3.3 gesture split stays intact.
- **Ghost as preview:** with Set Exit active, the ghost tracks the cursor across border cells (dashed `colors.ghost` outline + `?`), satisfying "shown until actually set" without ever resting on a placeholder cell — the .memlog's "fully absent" guarantee holds for the resting mid-edit state.
- **Reopened-sketch nuance:** `exit=None` seeding means a previously saved exit won't re-render until re-marked; intentionally out of scope — Story 3.6 owns save/load marker semantics.

## Verification

**Commands:**
- `ruff check .` -- passes
- `ruff format --check .` -- passes
- `pytest tests/domain/test_level_visibility.py tests/application/test_builder_session.py` -- passes
- `pytest tests/application/test_confirmation_settings.py tests/adapters/tkinter/common/test_keybindings.py` -- passes with the new setting and keybindings
- `pytest tests/adapters/tkinter/builder/test_builder_screen.py` -- passes (GUI; needs a display)

**Manual checks:**
- Set Entry active: click a cell — filled green circle appears; re-click elsewhere with confirm on — dialog first, then it moves
- Set Exit active: ghost (dashed outline + `?`) tracks the cursor on border cells only; clicking a border cell replaces it with the filled amber diamond; clicking an interior cell does nothing
- No tool active: no ghost anywhere, exit cell empty
- Settings → Confirmation shows the new toggle; turning it off makes redefinition instant
- 'e'/'x' activate the respective tools on the Builder screen only

## Suggested Review Order

**Entry/exit collision prevention** — the human-resolved intent that start and goal never share a cell:
- `src/labyrinthes/application/builder_session.py:122-139` — `apply_set_entry`/`apply_set_exit` guard against out-of-bounds and the other marker's cell, raising `DomainValidationError` (adapter swallows)
- `src/labyrinthes/application/confirmation_settings.py:39` — `_read_bool` gained `scope` parameter; `read/write_confirm_redefine_marker` default `True`, BUILDER-scoped
- `src/labyrinthes/adapters/tkinter/builder/screen.py:435-460` — `_place_entry` no-op when `self._session.exit == position`; `_place_exit` no-op when `self._session.entry == position`
- `src/labyrinthes/domain/level_visibility.py:216` — `is_border_cell` guards exit placement to border cells only

**Ghost preview behavior** — dashed `?` ghost only while Set Exit active, at cursor cell if border and holding no marker:
- `src/labyrinthes/adapters/tkinter/builder/screen.py:518-529` — `_sync_markers` excludes cursor cells that hold entry or exit from ghost rendering
- `src/labyrinthes/adapters/tkinter/builder/screen.py:767-793` — `_draw_ghost` scaled inset (`_GHOST_INSET_SCALE = 0.25`) and font size (`_GHOST_FONT_SCALE = 0.55`) via `self._ghost_font`; inset and glyph size derive from `_cell_size` so the preview stays inside the smallest cells

**Tool activation & keybindings** — Set Entry/Set Exit tools, mutual exclusivity, and confirmation gating:
- `src/labyrinthes/application/builder_session.py:64-81` — `BuilderTool` gains `SET_ENTRY = "set-entry"` / `SET_EXIT = "set-exit"`
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` — `Keybinding("set_entry", "Set Entry", "e", ScreenId.BUILDER)` / `Keybinding("set_exit", "Set Exit", "x", ScreenId.BUILDER)`
- `src/labyrinthes/adapters/tkinter/common/settings_window.py:86-91` — one row added to `_CONFIRMATION_TOGGLES` wiring `read_confirm_redefine_marker` (default True, BUILDER-scope)
- `src/labyrinthes/application/confirmation_settings.py` — `CONFIRM_REDEFINE_MARKER = "confirm_redefine_marker"`; `read_confirm_redefine_marker` / `write_confirm_redefine_marker`

**Test coverage** — new tests pinning the revised behavior:
- `tests/application/test_builder_session.py:123-184` — `test_apply_set_entry_rejects_an_out_of_bounds_cell`, `test_apply_set_entry_rejects_the_cell_already_holding_the_exit`, `test_apply_set_exit_rejects_the_cell_already_holding_the_entry`
- `tests/adapters/tkinter/builder/test_builder_screen.py:1033+` — `test_set_exit_ghost_preview_follows_the_cursor_along_the_border` (via `_on_move`), `test_set_exit_ghost_is_hidden_when_the_cursor_moves_to_an_interior_cell`, `test_set_exit_ghost_is_never_drawn_over_an_existing_marker`, `test_placing_the_exit_on_the_entry_cell_is_a_no_op`, `test_placing_the_entry_on_the_exit_cell_is_a_no_op`, `test_a_drag_under_a_marker_tool_never_places_a_marker`, `test_redefining_the_exit_at_a_different_cell_requires_confirmation`, `test_cancelling_the_exit_redefinition_dialog_leaves_the_marker_in_place`
- `tests/adapters/tkinter/common/test_settings_window.py:96+` — `test_toggling_the_redefine_marker_row_calls_its_writer`, `test_a_stored_value_is_reflected_in_the_rows_initial_state` (includes the new "Confirm before redefining an entry/exit" row)

EOF