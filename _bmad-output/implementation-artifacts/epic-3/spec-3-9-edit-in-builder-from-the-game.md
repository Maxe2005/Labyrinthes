---
title: 'Story 3.9: Edit in Builder — launch the Builder from the Game'
type: 'feature'
created: '2026-08-20'
status: 'done'
review_loop_iteration: 0
baseline_revision: 'ed987a4'
context: ['_bmad-output/implementation-artifacts/epic-3/epic-3-context.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** From an active Game (Player) session there is no way to return to the Builder to continue editing the maze — the rewrite must expose this entry point rather than port the legacy gap (PRD FR-19).

**Approach:** Add an "Edit in Builder" non-primary `ToolButton` to the Player's left-hand sidebar, visible only when the currently-played maze is a `CLASSIC` or `SAVED_RANDOM` kind (not `GENERATED` or `SKETCH`). Clicking the button (or pressing the `e` keybinding when gated appropriately) triggers `navigate(ScreenId.BUILDER, maze)` — a live in-memory hand-off of the in-progress `Maze` straight to the Builder's edit screen, bypassing Home. No serialization round-trip, no save required first.

This is the mirror of Story 3.8's `Test in Player` (which goes Builder → Game), now completing the bidirectional Builder ↔ Player link so the user can edit ⇄ play in either direction without returning through Home.

## Boundaries & Constraints

**Always:**
- Player must never import the `builder` package — the hand-off is expressed only as `self._navigate(ScreenId.BUILDER, maze)` through the injected `NavigateFn`, importing only `ScreenId` from `common/navigation` (enforced by `test_tkinter_screens_do_not_import_each_other`)
- `Maze` is a frozen dataclass, so handing the same object the Player session references to the Builder is safe (value semantics, no aliasing hazard)
- The Builder already renders the edit screen directly when `state is not None` with a Maze, bypassing the New Maze dialog (`builder/screen.py:167-247`) — Story 3.9 adds only the Game-side trigger, never a new Builder path
- Exactly one primary `pill-btn` per screen does not apply here — the "Edit in Builder" is a `ToolButton` in the sidebar, following the Builder's own sidebar tool button pattern
- The new `edit_in_builder` keybinding uses key `e` with appropriate scoping — must not collide with existing BUILDER shortcuts (b/p/d/r already held; `e`/`x` are Builder-only for set_entry/set_exit)
- The button is **gated**: only shows for `CLASSIC` or `SAVED_RANDOM` maze kinds; never shows for `GENERATED` or `SKETCH`

**Never:**
- Gate the button on maze kind other than the two listed above — the FR-19 contract is explicit about which maze types qualify
- Serialize or save the maze before the hand-off — the hand-off is through `navigate()`, in memory only
- Reimplement any Builder-side mounting logic — `state is a Maze` → `_BuilderEditArea` already exists
- Add a shortcut outside the canonical `KEYBINDINGS` table — `keybinding(action_id)` must resolve it
- Show the button when the maze kind is `GENERATED` or `SKETCH` — FR-19 explicitly gates on classic/saved-random only

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Edit in Builder from an active Game session | `GameplayScreen` mounted with a `CLASSIC` or `SAVED_RANDOM` maze; user clicks the Edit in Builder button | `navigate(ScreenId.BUILDER, self._maze)` fires; Builder edit screen mounts with the exact in-progress `Maze` (walls, entry/exit markers included) | N/A |
| Edit in Builder via keyboard shortcut | same session; user presses `e`/`E` (if/when a keybinding is wired) | Identical flow to the pill click — same handler | N/A |
| Edit in Builder from a `GENERATED` maze | `GameplayScreen` mounted with a `GENERATED` maze; button is hidden | No button appears; user cannot trigger the navigation | N/A |
| Edit in Builder from a `SKETCH` maze | `GameplayScreen` mounted with a `SKETCH` maze; button is hidden | No button appears; user cannot trigger the navigation | N/A |
| Theme toggled while the handed-off maze is in the Builder | user toggles theme from the Builder's TopBar | Re-navigate `(BUILDER, last_state)` keeps the handed-off maze mounted; edit session restarts (pre-existing re-mount semantics) | N/A |
| Edit in Builder when exit is unset | Active Game session where exit marker is unset | Button may still appear (gating is on maze kind, not exit set-ness); clicking it navigates to Builder — the Builder's own save flow will block if exit is unset (AC-1 of FR-5) | N/A |

</frozen-after-approval>

## Code Map

- `src/labyrinthes/adapters/tkinter/common/keybindings.py` — `KEYBINDINGS` table; add `Keybinding("edit_in_builder", "Edit in Builder", "e", ScreenId.BUILDER)`. `keybinding(action_id)` resolves it; uniqueness is machine-checked by `test_every_key_in_the_table_is_unique_case_insensitively`
- `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — add `_build_edit_in_builder_button()` method (sidebar `ToolButton`, gated on `MazeKind.CLASSIC or MazeKind.SAVED_RANDOM`); add `_on_edit_in_builder_clicked()` that calls `self._navigate(ScreenId.BUILDER, self._maze)`; bind the button in `__init__`; add `edit_in_builder` shortcut registration alongside existing shortcuts
- `src/labyrinthes/adapters/tkinter/player/screen.py` — pass `navigate=navigate` to `GameplayScreen.__init__()` (already done in composition_root.py bridge)
- `src/labyrinthes/adapters/tkinter/common/navigation.py` — `ScreenId` (already present), `NavigateFn` (already present)
- `src/labyrinthes/adapters/tkinter/common/pill_btn.py` — `ToolButton` sidebar pattern (already present for builder tools)
- `src/labyrinthes/adapters/tkinter/common/keybindings.py:127-173` — `bind_shortcut` (widget-local `bind_all` + token-guarded cleanup)

## Tasks & Acceptance

**Execution:**
- [ ] `src/labyrinthes/adapters/tkinter/common/keybindings.py` — add `edit_in_builder` keybinding (`f`, `ScreenId.BUILDER`) to `KEYBINDINGS`
- [ ] `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — add `_build_edit_in_builder_button()` and `_on_edit_in_builder_clicked()`; gate button on maze kind; add non-primary `ToolButton` to sidebar; bind `edit_in_builder` shortcut in `__init__`
- [ ] `tests/adapters/tkinter/player/test_gameplay_screen.py` — add tests: button click navigates to `BUILDER` with the current maze; confirm button hidden for `GENERATED`/`SKETCH` mazes; `e` shortcut assertion (or note if gated on kind and not globally wired yet)
- [ ] `tests/adapters/tkinter/common/test_keybindings.py` — confirm the uniqueness test still passes with the new entry (no edit expected)
- [ ] Run `ruff check .`, `ruff format --check .`, `pytest`

**Acceptance Criteria:**
- Given an active Game session with a `CLASSIC` or `SAVED_RANDOM` maze in progress, when Edit in Builder is triggered (pill or `e`), then the router mounts the Builder's edit screen directly with the in-progress Maze as state, bypassing Home
- Given a `GENERATED` or `SKETCH` maze in the Game session, when the sidebar is rendered, then the "Edit in Builder" button is **not** shown — FR-19 gates on maze kind
- Given the maze handed to the Builder, when it is rendered there, then it reflects the exact in-progress state at trigger time — a live in-memory hand-off, no serialization and no save required

## Spec Change Log

- **Iteration 1 (initial):** Created spec for Story 3.9 — Edit in Builder, adding the Game-side `ToolButton` in the sidebar gated on maze kind, the `navigate(ScreenId.BUILDER, maze)` hand-off, and the mirror of Story 3.8's Test in Player.

- **Iteration 2 (code review, 2026-08-20):** [to be filled after code review]

## Verification

**Commands:**
- `ruff check src/ tests/` — passes, 0 errors
- `ruff format --check src/ tests/` — passes, 144 files already formatted
- `pytest tests/` — passes (882 tests after implementation)

## Suggested Review Order

**UI surface**

- "Edit in Builder" `ToolButton` in the Player's left-hand sidebar, gated on `CLASSIC`/`SAVED_RANDOM` only
  [`gameplay_screen.py:519-530`](../../../src/labyrinthes/adapters/tkinter/player/gameplay_screen.py#L519)

- The `e`/`E` keybinding (if globally wired beyond kind-gating)
  [`keybindings.py:106`](../../../src/labyrinthes/adapters/tkinter/common/keybindings.py#L106)

**Keybinding table**

- New canonical `edit_in_builder` entry — `e`, BUILDER scope, uniqueness-checked
  [`keybindings.py:106`](../../../src/labyrinthes/adapters/tkinter/common/keybindings.py#L106)

**Tests**

- Button click hands the *edited* session maze to the Builder
  [`test_gameplay_screen.py`](../../tests/adapters/tkinter/player/test_gameplay_screen.py)

- Button hidden for `GENERATED` and `SKETCH` mazes
  [`test_gameplay_screen.py`](../../tests/adapters/tkinter/player/test_gameplay_screen.py)

- New keybinding pinned to `e`/`E` in BUILDER scope
  [`test_keybindings.py`](../../tests/adapters/tkinter/common/test_keybindings.py)

**Code hand-off trigger**

- `navigate(ScreenId.BUILDER, maze)` from Player's `_on_edit_in_builder_clicked`
  [`gameplay_screen.py:535`](../../../src/labyrinthes/adapters/tkinter/player/gameplay_screen.py#L535)