---
title: 'Story 3.2: Wall editing — break/restore'
type: 'feature'
created: '2026-08-18'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'b2db51f6a1142a23c30be7a1643c77a1d402b4dc'
context: ['_bmad-output/implementation-artifacts/epic-3/epic-3-context.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The app has no way for the user to break or restore a wall between adjacent cells. The Builder end-to-end (Epic 3) requires wall editing functionality — both single-click Break mode and Pass-through mode (cursor movement across a wall breaks it) — plus a live HUD "walls broken" count and save format compatibility with the legacy CSV format (Story 1.4's `MazeRepository`). Additionally, the user chose two operational decisions: (a) the Builder should host `NewMazeDialog` as its entry state when `state=None`, and Home's "New Maze" button must re-route to `ScreenId.BUILDER` rather than `ScreenId.PLAYER`; (b) keyboard shortcuts must be unique per page/screen, allowing `b` to serve both `open_builder` (Home) and `break_wall` (Builder), which requires extending the `Keybinding` dataclass with a `scope` field and updating the uniqueness test to group by scope.

**Approach:** Add pure domain functions for wall break/restore in `domain/wall_editing.py`; create an application service `application/builder_session.py` with `BuilderSession` orchestration and `BuilderTool` enum; rewrite the Builder edit screen in `builder/screen.py` with maze canvas, tool side bar (Break Wall + Pass-through mutually exclusive tool-btns), HUD chips (grid size + Walls broken live), and `NewMazeDialog` as entry state; re-route Home's New Maze button to navigate to `ScreenId.BUILDER`; extend `Keybinding` with a `scope: ScreenId | None` field and add per-scope uniqueness to the keybinding test; add new keybindings `break_wall` ("b", BUILDER) and `pass_through` ("p", BUILDER).

## Boundaries & Constraints

**Always:**
- Domain value objects (`Grid`, `Cell`, `Maze`, `Position`, `Wall`) are immutable; engine operations are pure functions returning new state
- The 0/1/2/3 cell encoding is preserved as-is; no re-encoding occurs
- `MazeRepository.save()/load()` reads/writes CSV byte-for-byte compatible with the legacy format (NFR2/AD-6)
- No `tkinter` import in `domain/` or `application/` (AD-1, AD-9)
- Builder-specific widgets (`maze canvas`, wall-editing cursor, tools) stay local to `adapters/tkinter/builder/`; generic widgets (`tool-btn`, `hud-chip`, `kbd-tag`, `pill-btn`) come from `adapters/tkinter/common/`
- The Builder owns an adapter-local mutable session wrapper (cursor position, active tool) around the immutable `Maze` value it references
- Per-screen keybinding uniqueness: keys are unique within each `Scope` group; entries with `scope=None` form one group, entries with explicit `ScreenId` scopes form separate groups
- The maze's outer border stays closed after any wall operation (FR-2 invariant; also applies to single wall editing)
- `break_wall` / `restore_wall` raise `DomainValidationError` when attempted on a border `Wall`

**Ask First:**
- Adding the `scope` field to `Keybinding` and changing the uniqueness test — human approval required if test changes ripple into other story execution
- Any new token or color usage in the builder screen

**Never:**
- Mutate `Grid`/`Cell` in-place; all domain operations return new immutable values
- Hardcode dimension bounds in the builder UI — always read from shared `read_maze_size_bounds` reader
- Break the outer border invariant — `break_wall`/`restore_wall` refuse border walls
- Allow two `Keybinding` entries with the same `action_id` — `action_id` uniqueness is invariant

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Cold open Builder with `state=None` | `mount(parent, None, navigate, theme, toggle, settings_repo=...)` | Builder chrome renders; `NewMazeDialog` opens as entry state; maze-frame empty until confirm | No error; dialog destroyed on cancel, frame stays empty |
| Valid dimensions confirmed in New Maze dialog | Dialog `on_confirm` with columns=20, rows=15 | `Maze(grid=Grid.filled(20, 15), entry=Position(0,0), exit=Position(14, 19), kind=MazeKind.SKETCH, id=None)`; maze-frame renders for editing; HUD shows "Walls broken: 0" | No error; user remains on Builder edit screen |
| Break mode: click wall-bar segment | Break mode active; segment under cursor toggles (breaks if present, restores if absent) | Both affected cells' 0/1/2/3 encoding update; wall segment visually removed/added; HUD "walls broken" count changes by ±1 | No error; clicking border wall raises `DomainValidationError` (no-op, ignored by adapter) |
| Pass-through mode: cursor moves across wall | Pass-through tool active; arrow key moves cursor into a wall cell | Wall between current and target cell breaks; cursor moves into target; HUD count increments | Border wall: cursor stays; no count change; wall not broken |
| HUD updates after wall change | Any wall break/restore occurs | `HudChip` value updates live (accent background when live); count reflects current broken walls | No special handling; chip `set_value()` called from screen |
| Save maze with edited walls | User clicks Save; maze has broken walls | CSV output encoding unchanged from legacy format (0/1/2/3 cell values); `MazeId` not minted (kind=SKETCH, id=None) | No error; save proceeds identically to unedited maze |
| Keybinding 'b' on Home screen | Home mounted; `bind_shortcut(frame, keybinding("open_builder"), ...)` | `open_builder` fires; navigates to `ScreenId.BUILDER` with `state=None` | No error; standard navigation flow |
| Keybinding 'b' on Builder screen | Builder mounted; `bind_shortcut` with `keybinding("break_wall")` | `break_wall` fires; toggles wall segment in Break mode or breaks wall in Pass-through mode | No conflict with Home's 'b' — different scope |
| Keybinding 'p' on Builder screen | Builder mounted; `bind_shortcut` with `keybinding("pass_through")` | Pass-through mode toggles on; cursor movement breaks walls | No conflict with Home's 'p' (open_player) — different scope |
| Arrow key movement in Builder | `move_up`/`move_down`/`move_left`/`move_right` keys | Cursor moves one cell in respective direction; in Pass-through mode, crossing a wall breaks it | Border: cursor stays; no wall broken |

## Code Map

- `src/labyrinthes/domain/wall_editing.py` — pure functions: `break_wall(grid, wall) -> Grid`, `restore_wall(grid, wall) -> Grid`, `toggle_wall(grid, wall) -> Grid`, `count_broken_walls(grid) -> int`, `wall_between(position, direction) -> Wall`
- `src/labyrinthes/application/builder_session.py` — `BuilderSession` frozen dataclass (`maze`, `cursor`, `tool`), `BuilderTool` enum (`BREAK`, `PASS_THROUGH`), `start_builder_session(maze)`, `set_tool(session, tool)`, `apply_wall_toggle(session, wall)`, `move_cursor(session, direction)`, `broken_wall_count(session)`
- `src/labyrinthes/adapters/tkinter/builder/screen.py` — full Builder edit screen: top bar with breadcrumb Home/Builder + settings/theme icons; left tool side bar with `ToolButtonGroup` holding `Break Wall` (B) and `Pass-through` (P) mutually exclusive `ToolButton`s; center column with `HudChip` for grid size and live `HudChip` for "Walls broken"; maze canvas rendering walls (raw `Wall` coordinates, gaps for broken segments); editing cursor highlight; `NewMazeDialog` as entry state when `state=None`
- `src/labyrinthes/adapters/tkinter/home/screen.py` — re-route `go_to_new_maze()`: `on_confirm=lambda maze: navigate(ScreenId.BUILDER, maze)` instead of `ScreenId.PLAYER`; update docstring and test expectation
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` — `Keybinding` dataclass gains `scope: ScreenId | None = None` field; `KEYBINDINGS` tuple updated with `scope` on new entries `break_wall` (BUILDER) and `pass_through` (BUILDER); existing entries retain default `scope=None`
- `tests/adapters/tkinter/common/test_keybindings.py` — `test_every_key_in_the_table_is_unique_case_insensitively` updated to group keys by `kb.scope` and assert uniqueness within each scope group; other key tests unchanged
- `tests/adapters/tkinter/home/test_home_screen.py` — `test_new_maze_dialog_confirm_navigates_to_player_with_the_new_sketch` updated to assert `screen_id is ScreenId.BUILDER` and navigate call includes the new `Maze`; home-screen test for New Maze button expectation updated

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/domain/wall_editing.py` — add `break_wall`, `restore_wall`, `toggle_wall`, `count_broken_walls`, `wall_between` pure functions using `_blocked_wall` mapping conventions and `Cell.has_top_wall`/`has_left_wall` bit operations; border wall refusal via `is_border_wall`
- [x] `src/labyrinthes/application/builder_session.py` — add `BuilderTool` enum, `BuilderSession` frozen dataclass, `start_builder_session`, `set_tool`, `apply_wall_toggle` (Break mode: toggle; Pass-through: break wall then move), `move_cursor` (move cursor; in Pass-through break wall crossed), `broken_wall_count` (delegate to `count_broken_walls(grid)`)
- [x] `src/labyrinthes/adapters/tkinter/builder/screen.py` — rewrite `mount()`: top bar with breadcrumb + settings/theme icons; left side bar with `ToolButtonGroup`/`Break Wall` + `Pass-through`; center column with `HudChip` grid size + live `HudChip` Walls broken + `MazeCanvas`-derived builder canvas; `NewMazeDialog` entry when `state=None`; on confirm, render maze-frame; on cancel, clear maze-frame
- [x] `src/labyrinthes/adapters/tkinter/home/screen.py` — change `go_to_new_maze()` `on_confirm` to `navigate(ScreenId.BUILDER, maze)`; update docstring; update test `test_new_maze_dialog_confirm_navigates_to_player_with_the_new_sketch` to expect `ScreenId.BUILDER`
- [x] `src/labyrinthes/adapters/tkinter/common/keybindings.py` — add `scope: ScreenId | None = None` to `Keybinding`; add `KEYBINDINGS` entries `Keybinding("break_wall", "Break Wall", "b", ScreenId.BUILDER)` and `Keybinding("pass_through", "Pass-through", "p", ScreenId.BUILDER)`; import `ScreenId` from `navigation`; update `test_every_key_in_the_table_is_unique_case_insensitively` test body
- [x] `tests/adapters/tkinter/common/test_keybindings.py` — modify `test_every_key_in_the_table_is_unique_case_insensitively` to group `KEYBINDINGS` entries by `kb.scope` and assert `len(keys) == len(set(keys))` within each scope group; other test bodies unchanged
- [x] `tests/adapters/tkinter/home/test_home_screen.py` — update `test_new_maze_dialog_confirm_navigates_to_player_with_the_new_sketch` to assert `screen_id is ScreenId.BUILDER` and `calls == [(ScreenId.BUILDER, maze)]`; update any test that checks New Maze navigation target

**Acceptance Criteria:**
- [x] AC1: Given a single click on a wall-bar segment, when Break mode is active, then that wall breaks/restores and both affected cells' 0/1/2/3 encoding update symmetrically
- [x] AC2: Given Pass-through mode, when the cursor moves across a wall, then the wall breaks as the cursor crosses it
- [x] AC3: Given the HUD, when a wall changes, then the "walls broken" count updates live
- [x] AC4: Given the save format, when a maze with edited walls is saved, then the CSV encoding stays unchanged from the legacy format (Story 1.4's `MazeRepository`)
- [x] Bonus: Keybinding 'b' functions on both Home (open_builder) and Builder (break_wall) screens without runtime conflict, thanks to per-page scope uniqueness
- [x] Bonus: Keybinding 'p' (Pass-through) on Builder, separate from Home's 'p' (open_player), thanks to per-page scope uniqueness

## Spec Change Log

</frozen-after-approval>

## Design Notes

- **Wall encoding**: `break_wall(grid, wall)` clears the `side` bit (top/left) of `grid.cell_at(Position(wall.row, wall.col))`; `restore_wall` sets it. This mirrors the legacy `conbinaisons` lookup: for right/left moves the target cell's left wall (bit 2) is cleared/set; for up/down moves the target cell's top wall (bit 1) is cleared/set. The `_blocked_wall(position, direction)` mapping from `level_visibility.py` provides the exact `Wall(row, col, side)` for a given move — reused by `wall_between`.
- **Border walls**: `is_border_wall(grid, Wall(row, col, side))` returns `True` when `row == 0 or row == grid.height` (for side "top") or `col == 0 or col == grid.width` (for side "left"). `break_wall`/`restore_wall` raise `DomainValidationError` for border walls; the adapter hit-tests never select border segments for clicking.
- **Pass-through mode**: When the cursor moves in `direction` and `attempt_move` would be blocked by a non-border wall, the wall breaks first (`break_wall`), then the cursor moves into the target cell. If the target is a border wall, the move is a no-op and the wall is not broken. This is composed from `wall_between` + `break_wall` + `attempt_move` semantics.
- **Symmetric encoding update**: "Both affected cells' encoding update symmetrically" means the wall segment is single-encoded (per the AD-6/public contract): only one cell's digit changes, but the passage opens/closes consistently for both adjacent cells because walls are never double-encoded. The FR-1 wording reflects the behavioral symmetry, not that both cells' digits change.
- **Keybinding scope**: `Keybinding.scope` is `ScreenId | None`. The uniqueness test `test_every_key_in_the_table_is_unique_case_insensitively` groups entries by `kb.scope` and checks per-group uniqueness. The `None`-group contains all existing entries (Home + Player keys, all distinct). The `BUILDER`-group contains `break_wall` ('b') and `pass_through` ('p'). Since Home and Builder are never mounted simultaneously, runtime bindings never conflict even though 'b' and 'p' appear in different scope groups. This satisfies the user's request for per-page uniqueness without global key collision.
- **Builder entry state**: `mount(parent, state=None, ...)` renders the Builder chrome (top bar, side bars, HUD) and immediately opens `NewMazeDialog` as the entry state. The maze-frame is empty until the user confirms dimensions. On confirm, the maze-frame renders with the new `Maze`; on cancel, the maze-frame area is cleared (showing no maze yet). `mount(parent, state=Maze, ...)` renders the edit screen directly with the given maze already loaded.
- **HUD "walls broken" count**: `count_broken_walls(grid)` = number of interior (non-border) wall segments whose bit is currently clear, relative to a fully-filled grid baseline. Since every new sketch starts as `Grid.filled` (all walls present), the count starts at 0 and increments/decrements with each break/restore. The `HudChip` with `live=True` uses `accent_bg` background and `accent` text color per `hud_chip.py` convention.
- **Save format compatibility**: Domain functions operate on the preserved 0/1/2/3 cell encoding. `CsvMazeRepository.save()` writes cells byte-for-byte as before; broken walls only change the affected cell's digit, which the CSV reader interprets identically. No re-encoding or format migration occurs.

## Verification

**Commands:**
- `ruff check .` — passes (no new violations from keybinding scope field addition; existing conventions unchanged)
- `ruff format --check .` — passes
- `pytest tests/adapters/tkinter/common/test_keybindings.py` — passes (including updated `test_every_key_in_the_table_is_unique_case_insensitively` per-scope grouping)
- `pytest tests/adapters/tkinter/common/test_keybindings.py::test_every_action_id_in_the_table_is_unique` — passes (no duplicate action_ids)
- `pytest tests/adapters/tkinter/home/test_home_screen.py::test_new_maze_dialog_confirm_navigates_to_player_with_the_new_sketch` — passes (now expects `ScreenId.BUILDER`)
- `pytest tests/adapters/tkinter/builder/test_builder_screen.py` — passes

**Manual checks:**
- Builder edit screen renders with top bar, tool side bar (Break Wall + Pass-through mutually exclusive), maze canvas with wall gaps, HUD chips (grid size + Walls broken live)
- Break mode: clicking a wall segment toggles it (breaks if present, restores if absent); border segments ignored
- Pass-through mode: arrow-key cursor movement across a wall breaks the wall; cursor moves into the target cell; border walls stop the cursor without breaking
- HUD "Walls broken" chip updates its value after each break/restore operation
- Home New Maze button navigates to `ScreenId.BUILDER` with the new `Maze`; Old `test expecting PLAYER` updated
- Keybinding 'b' registered and fires on both Home and Builder frames without runtime collision
- Keybinding 'p' registered and fires on Builder frame only; Home's 'p' (open_player) unaffected
- Save a maze with edited walls; CSV output matches legacy format (0/1/2/3 cells, same byte structure)

## Next Move

After this spec is approved (step-02 CHECKPOINT 1), proceed to `step-03-implement.md` for implementation execution. The implementation will create the domain, application, adapter, and test changes outlined above, then run the verification commands to confirm correctness.

## Suggested Review Order

**Wall bit encoding (domain)**

- Single shared mutator: sets/clears one wall bit, refuses border walls — every break/restore/toggle routes through this.
  [`wall_editing.py:43`](../../../src/labyrinthes/domain/wall_editing.py#L43)

- Bug fixed during implementation: excludes the padding row/column's dead bits from the "broken" count.
  [`wall_editing.py:102`](../../../src/labyrinthes/domain/wall_editing.py#L102)

**Session orchestration (application)**

- Pass-through's core composition: break the blocking wall, then move the cursor into it.
  [`builder_session.py:94`](../../../src/labyrinthes/application/builder_session.py#L94)

- Break mode's pure toggle, used only by the adapter's click handler.
  [`builder_session.py:81`](../../../src/labyrinthes/application/builder_session.py#L81)

**Builder screen wiring (adapter)**

- Entry point: dispatches `state=None` to the New Maze dialog, `state=Maze` to the edit UI.
  [`screen.py:95`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L95)

- Break-mode-only click gate — Pass-through never toggles a wall via click.
  [`screen.py:254`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L254)

- Cursor move plus the identity check that triggers HUD/canvas resync after a wall breaks.
  [`screen.py:266`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L266)

- Hit-test: nearest canvas item within a click halo, mapped back to its `Wall`.
  [`screen.py:383`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L383)

- Permanent-item recolor strategy: every wall position is drawn once, gaps stay clickable to restore.
  [`screen.py:342`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L342)

**Keybinding scoping**

- New `scope` field: keys are unique per screen group, not globally — lets 'b'/'p' serve two screens.
  [`keybindings.py:75`](../../../src/labyrinthes/adapters/tkinter/common/keybindings.py#L75)

**Home re-route**

- New Maze now hands the fresh sketch to the Builder instead of the Player.
  [`home/screen.py:108`](../../../src/labyrinthes/adapters/tkinter/home/screen.py#L108)

**Peripherals**

- Break/Pass-through behavioral coverage for AC1/AC2.
  [`test_builder_screen.py:309`](../../../tests/adapters/tkinter/builder/test_builder_screen.py#L309)

- Per-scope keybinding uniqueness, replacing the old global-uniqueness assertion.
  [`test_keybindings.py:18`](../../../tests/adapters/tkinter/common/test_keybindings.py#L18)