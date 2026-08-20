---
title: 'Story 3.8: Test in Player — launch the Game from the Builder'
type: 'feature'
created: '2026-08-20'
status: 'done'
review_loop_iteration: 0
baseline_revision: 'ed987a4'
context: ['_bmad-output/implementation-artifacts/epic-3/epic-3-context.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** From an active Builder session there is no way to immediately confirm a maze is solvable — the legacy app's corresponding button exists but is disabled, and the rewrite must expose this entry point rather than port the disabled code (PRD FR-8).

**Approach:** Add a `Test in Player` non-primary `PillButton` to the Builder's HUD row plus a `test_in_player` keybinding (`T`, BUILDER scope), both triggering `navigate(ScreenId.PLAYER, session.maze)` — a live in-memory hand-off of the in-progress `Maze` straight to the Player's gameplay screen, bypassing Home. No serialization round-trip, no save required first, and the button is unconditionally available from any active Builder session (not gated to maze kind, unlike FR-19's mirror).

## Boundaries & Constraints

**Always:**
- Builder must never import the `player` package — the hand-off is expressed only as `self._navigate(ScreenId.PLAYER, maze)` through the injected `NavigateFn`, importing only `ScreenId` from `common/navigation` (enforced by `test_tkinter_screens_do_not_import_each_other`)
- `Maze` is a frozen dataclass, so handing the same object the Builder session references to the Player is safe (value semantics, no aliasing hazard)
- The Player already renders the gameplay screen directly when `mount()` receives `state is not None`, bypassing the gallery with no repository read (`player/screen.py:119-151`; proven by `test_state_not_none_never_reads_the_maze_repository`) — Story 3.8 adds only the Builder-side trigger, never a new Player path
- Exactly one primary `pill-btn` per screen: the Test in Player pill must be the default (non-primary) variant; Save keeps `primary=True`
- The new `test_in_player` keybinding uses key `t` with `scope=ScreenId.BUILDER` — free of collisions in the table (BUILDER scope currently holds b/p/d/r/e/x)
- `bind_shortcut` is bound in `_BuilderEditArea.__init__`, mirroring the existing `save_maze` binding

**Ask First:** none anticipated.

**Never:**
- Gate the button on maze kind or on a saved state — it is unconditionally available from any active Builder session (FR-8 vs FR-19)
- Serialize or save the maze before the hand-off — the hand-off is through `mount()`, in memory only
- Reimplement any Player-side mounting logic — `state is not None` → `GameplayScreen` already exists
- Add a shortcut outside the canonical `KEYBINDINGS` table — `keybinding(action_id)` must resolve it

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Test in Player from an active edit session | `_BuilderEditArea` mounted with a maze; user clicks the Test in Player pill | `navigate(ScreenId.PLAYER, self._session.maze)` fires; Player gameplay screen mounts with the exact in-progress `Maze` (broken walls, entry/exit markers included) | N/A |
| Test in Player via keyboard | same session; user presses `t`/`T` | Identical flow to the pill click — same handler | N/A |
| Builder in the New-Maze entry state | `state is None`, `NewMazeDialog` showing | No Test in Player button exists — it lives only in `_BuilderEditArea` (the active-session branch) | N/A |
| Theme toggled while the handed-off maze is in the Player | user toggles theme from the Player's TopBar | Re-navigate `(PLAYER, last_state)` keeps the handed-off maze mounted; gameplay run restarts (pre-existing re-mount semantics, same as a standalone run) | N/A |

</frozen-after-approval>

## Code Map

- `src/labyrinthes/adapters/tkinter/common/keybindings.py` — `KEYBINDINGS` table (`:88-106`); add `Keybinding("test_in_player", "Test in Player", "t", ScreenId.BUILDER)`. `keybinding(action_id)` (`:111`) resolves it; uniqueness is machine-checked by `test_every_key_in_the_table_is_unique_case_insensitively` (`tests/adapters/tkinter/common/test_keybindings.py:19-30`)
- `src/labyrinthes/adapters/tkinter/builder/screen.py` — `_BuilderEditArea.__init__` (`:235-275`) already stores `self._navigate` (`:249`) and `self._session` (`:252`); add `bind_shortcut(self, keybinding("test_in_player"), self._test_in_player)` beside the `save_maze` binding (`:275`). `_build_hud` (`:363-406`) packs the primary Save pill `side="right"` (`:398-406`); add the non-primary Test in Player pill next to it (`shortcut=keybinding("test_in_player").display`). New `_test_in_player()` method: `self._navigate(ScreenId.PLAYER, self._session.maze)`
- `src/labyrinthes/adapters/tkinter/player/screen.py` — read-only reference: `state is not None` → `GameplayScreen` directly (`:119-151`); do not modify
- `src/labyrinthes/adapters/tkinter/common/pill_btn.py` — `PillButton` default (non-primary) variant; constructor signature (`:29-38`)
- `src/labyrinthes/adapters/tkinter/common/navigation.py` — `ScreenId` (`:25-30`), `NavigateFn` (`:37`)
- `src/labyrinthes/adapters/tkinter/common/keybindings.py:127-173` — `bind_shortcut` (widget-local `bind_all` + token-guarded cleanup)

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/adapters/tkinter/common/keybindings.py` — add `test_in_player` keybinding (`t`, `ScreenId.BUILDER`) to `KEYBINDINGS`
- [x] `src/labyrinthes/adapters/tkinter/builder/screen.py` — add `_test_in_player()` (navigate to `ScreenId.PLAYER` with `self._session.maze`); add a non-primary Test in Player `PillButton` to the HUD row beside Save; bind the `test_in_player` shortcut in `_BuilderEditArea.__init__`
- [x] `tests/adapters/tkinter/builder/test_builder_screen.py` — add tests: pill click navigates to `PLAYER` with the session maze; `t` shortcut fires the same handler; assert the passed maze is the exact in-progress object (`calls[0] == (ScreenId.PLAYER, edit_area._session.maze)` pattern from `test_builder_screen.py:1860-1898`)
- [x] `tests/adapters/tkinter/common/test_keybindings.py` — confirm the uniqueness test still passes with the new entry (no edit expected)
- [x] Run `ruff check .`, `ruff format --check .`, `pytest`

**Acceptance Criteria:**
- Given an active Builder session with a maze in progress, when Test in Player is triggered (pill or `t`), then the router mounts the Player's gameplay screen directly with the in-progress Maze as state, bypassing Home
- Given any active Builder session, when Test in Player is invoked, then it is unconditionally available — not gated to any maze kind
- Given the maze handed to the Player, when it is rendered there, then it reflects the exact in-progress state at trigger time — a live in-memory hand-off, no serialization and no save required

## Spec Change Log

- **Iteration 1 (initial):** Created spec for Story 3.8 — Test in Player, adding the Builder-side pill + `t` shortcut and the `navigate(ScreenId.PLAYER, session.maze)` hand-off, reusing the Player's existing state-mount path.

- **Iteration 2 (code review, 2026-08-20):** A 3-layer adversarial review (Blind Hunter, Edge Case Hunter, Verification Gap) found seven patch-level issues, all fixed in the `fix(...)` patch commit: (1) typing `t` into the `_SaveNameDialog` name field fired the new `test_in_player` `bind_all` shortcut and navigated away mid-save — now guarded by consuming `t`/`T` in the name entry, mirroring the existing `s`/`S` guard; (2) the "shortcut" test called `_test_in_player()` directly, so the `bind_shortcut` registration was never asserted — added `bind_all(...) != ""` assertions for the active-edit and New-Maze entry states; (3) the "not gated to maze kind" AC was only exercised with a `SKETCH` maze — added a `CLASSIC`-kind pill/navigation test; (4) the "exact in-progress object" assertion was trivially satisfied — the pill-click test now breaks an interior wall first and asserts the handed-off maze reflects the edit; (5) no `test_keybindings.py` pin for the new entry — added one (`t`, `ScreenId.BUILDER`, `T`); (6) the Builder module docstring inventory did not mention the new pill/shortcut — updated; (7) an inaccurate "mirrors the 'b'/'d'/'r' tests" comment — corrected. Full suite: 881 tests pass, `ruff check`/`ruff format --check` clean.

## Verification

**Commands:**
- `ruff check src/ tests/` — passes, 0 errors
- `ruff format --check src/ tests/` — passes, 144 files already formatted
- `pytest tests/adapters/tkinter/builder/test_builder_screen.py tests/adapters/tkinter/common/test_keybindings.py tests/test_architecture_boundaries.py` — passes (88 tests, incl. the 4 new Test-in-Player tests)
- `pytest tests/app/test_composition_root.py` — passes (10 tests, incl. the new handed-off-maze theme-toggle test)
- `pytest tests/` — passes (881 tests after the review patch round; 877 at initial implementation)

## Suggested Review Order

**Hand-off trigger (entry point)**

- Live in-memory hand-off of the in-progress maze straight to the Player gameplay screen
  [`screen.py:641`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L641)

- `bind_all` wiring for the BUILDER-scoped `t` shortcut beside the Save binding
  [`screen.py:282`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L282)

**UI surface**

- Non-primary Test in Player pill beside the primary Save pill in the HUD row
  [`screen.py:417`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L417)

- The `t`/`T` key-consumption guard in the Save-name entry, so typing a name can't fire the shortcut mid-save
  [`screen.py:810`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L810)

- Docstring inventory updated to enumerate the new pill and shortcut
  [`screen.py:27`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L27)

**Keybinding table**

- New canonical `test_in_player` entry — `t`, BUILDER scope, uniqueness-checked
  [`keybindings.py:106`](../../../src/labyrinthes/adapters/tkinter/common/keybindings.py#L106)

**Tests**

- Pill click hands the *edited* session maze to the Player (wall broken first)
  [`test_builder_screen.py:1818`](../../../tests/adapters/tkinter/builder/test_builder_screen.py#L1818)

- Unconditional availability proven for a non-SKETCH (CLASSIC) maze
  [`test_builder_screen.py:1859`](../../../tests/adapters/tkinter/builder/test_builder_screen.py#L1859)

- Shortcut registration asserted active and inert-in-entry-state
  [`test_builder_screen.py:1891`](../../../tests/adapters/tkinter/builder/test_builder_screen.py#L1891)

- New keybinding pinned to `t`/`T` in BUILDER scope
  [`test_keybindings.py:191`](../../../tests/adapters/tkinter/common/test_keybindings.py#L191)

- Theme toggle re-mounts the Player keeping the handed-off maze
  [`test_composition_root.py:83`](../../../tests/app/test_composition_root.py#L83)
