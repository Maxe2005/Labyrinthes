---
title: 'Story 4.8: Shell windowing — centered, resizable, zoom, fullscreen'
type: 'feature'
created: '2026-08-26'
status: 'done'
review_loop_iteration: 0
context: []
baseline_commit: 63025b12389cc3db81c3b688e15bc31d99e01f96
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The root window opens at Tk's default size/position (no centering), maze canvases in Builder/Player are sized once at construction and never react to resize, there is no zoom, and F11 fullscreen doesn't exist anywhere — none of this matches FR-31.

**Approach:** Wire centering + resizable + F11 fullscreen on the single `Tk()` root in `composition_root.py`; make both maze canvases recompute cell size and redraw on `<Configure>` (fit-to-space) and on Ctrl+wheel/`+`/`-` (zoom offset on top of fit, still clamped 16–40px); add the same centered/resizable/F11 behavior to `SettingsWindow`, with its own F11 toggling itself rather than the root.

## Boundaries & Constraints

**Always:** Root window is centered on screen at startup and resizable in both directions. Maze canvas cell size stays clamped to the existing 16–40px range (`_MIN_CELL_SIZE`/`_MAX_CELL_SIZE`) in both Builder and Player. F11 fullscreen is registered in the canonical `KEYBINDINGS` table (Story 1.10) and keeps `test_keybindings.py`'s collision/uniqueness tests green. `SettingsWindow` stays a non-modal `Toplevel` that survives `Router.navigate()` teardown (Story 1.11 fix — do not regress; there's already a passing regression test, `tests/app/test_composition_root.py::test_settings_window_opened_on_home_survives_a_real_navigate_to_builder`). Zoom/fit logic is adapter-only (`maze_canvas.py`, `edit_area.py`, `gameplay/screen.py`) — no `domain/`/`application/` changes; cell size never crosses that boundary (AD-1).

**Ask First:** None — the one open design question (F11 scoping while `SettingsWindow` has focus) is resolved below under Design Notes, not left for the implementer to renegotiate.

**Never:** Never change wall/grid domain types, `Position`/`Grid`/`Maze` shapes, or any persistence format. Never add a new settings key to persist zoom/window geometry across sessions — this story is in-session behavior only. Never change `Router.navigate()`'s new-before-old teardown ordering (already correct, tested).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Window shrunk very small | Builder/Player canvas mounted, window dragged small | Cell size clamps at `_MIN_CELL_SIZE` (16px); canvas keeps rendering | N/A |
| Zoom at bound | Ctrl+wheel/`+`/`-` pressed while cell size already at 16 or 40 | No-op — stays clamped, no crash | N/A |
| F11 while Settings focused | `SettingsWindow` open and focused, F11 pressed | Only the Settings `Toplevel` toggles fullscreen; root's fullscreen state is untouched | N/A |
| Resize on a screen with no canvas | Home or classic-gallery screen mounted, window resized | No error — only screens owning a maze canvas react to `<Configure>` | N/A |

</frozen-after-approval>

## Code Map

- `src/labyrinthes/app/composition_root.py` -- `Tk()` at line 113, `App` dataclass 64-69, `main()` 183-187. Add centering (`update_idletasks()` + `winfo_screenwidth/height` + `.geometry()`), `.resizable(True, True)`, F11 `bind_shortcut(root, ...)` (AD-10: owns the root).
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- `KEYBINDINGS` table 88-110, `bind_shortcut()` 131-177 (self-unregisters on `<Destroy>`; multi-char-keysym guard at 161 already handles `"F11"` like `"Up"`). Add `toggle_fullscreen` (`F11`, `scope=None`) + zoom entries (`+`/`-`) scoped `ScreenId.BUILDER`/`ScreenId.PLAYER`.
- `tests/adapters/tkinter/common/test_keybindings.py` -- collision/uniqueness tests (14, 19) must stay green.
- `src/labyrinthes/adapters/tkinter/common/settings_window.py` -- `__init__` 121-168, no geometry/resizable/fullscreen today. Add centering + `.resizable(True, True)` + local `self.bind("<F11>", ...)` (see Design Notes).
- `src/labyrinthes/adapters/tkinter/builder/maze_canvas.py` / `player/maze_canvas.py` -- `_cell_size()` helper, cell size computed once in `__init__`, fixed `width=`/`height=` at construction. Add a public recompute-and-redraw method (same shape in both files).
- `src/labyrinthes/adapters/tkinter/builder/edit_area.py` -- `_build_canvas()` 344-358; canvas already packed `fill="both", expand=True`. Wire `<Configure>` + zoom keybindings here.
- `src/labyrinthes/adapters/tkinter/player/gameplay/screen.py` -- `_build_maze_frame()` 337-350; `_maze_frame` (344) and canvas `.pack()` (350) currently non-expanding — switch both to `fill="both", expand=True`. Wire `<Configure>` + zoom keybindings here.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- `epic-2-retro-item-1-router-cascade` (16-21) is already fixed and test-covered; flip to `status: done`.
- `tests/conftest.py` / `tests/adapters/tkinter/common/conftest.py` -- `tk_root` fixture (`Tk()` + `withdraw()`) to reuse for new tests.

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/app/composition_root.py` -- center root on startup, `.resizable(True, True)`, bind F11 globally to toggle root fullscreen -- AC 1, 4
- [x] `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- add `toggle_fullscreen` (F11, scope=None) and zoom entries (`+`/`-`, scoped per-screen) -- AC 3, 4
- [x] `builder/maze_canvas.py` + `player/maze_canvas.py` -- add a recompute-cell-size-and-redraw method combining fit-to-space and zoom offset, clamped 16–40px -- AC 2, 3
- [x] `builder/edit_area.py` -- bind `<Configure>` and Ctrl+wheel/`+`/`-` to the new recompute method -- AC 2, 3
- [x] `player/gameplay/screen.py` -- same `<Configure>` + zoom wiring; fix `_maze_frame`/canvas pack options to `fill="both", expand=True` -- AC 2, 3
- [x] `src/labyrinthes/adapters/tkinter/common/settings_window.py` -- center, `.resizable(True, True)`, local F11 override that returns `"break"` -- AC 5
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- flip `epic-2-retro-item-1-router-cascade` to `status: done` -- housekeeping
- [x] Tests -- centering, resizable flag, canvas resize-fit, zoom clamp, F11 toggle (root and Settings independently); confirm Settings-survives-navigate stays green -- AC 1-5
- [x] Run `ruff check .`, `ruff format --check .`, `pytest -q` -- all green

**Acceptance Criteria:**
- Given the shell starts, when the root window opens, then it is centered on screen and resizable in both directions.
- Given a screen with a maze canvas (Builder, Player), when the window is resized, then the canvas re-renders to fit the available space.
- Given Ctrl+wheel (or `+`/`-`) used over a maze canvas, then the cell size zooms in/out (clamped 16–40px) and the canvas re-renders.
- Given the F11 shortcut is pressed, then the window toggles fullscreen, and the shortcut is registered in the canonical keybinding table.
- Given the Settings window is opened, then it is centered, resizable, supports its own F11 fullscreen, and is never silently closed by a navigation frame teardown.

## Spec Change Log

## Design Notes

F11 scoping: one canonical `Keybinding("toggle_fullscreen", "Toggle Fullscreen", "F11", scope=None)`, bound once at root via `bind_shortcut(root, kb, toggle_root_fullscreen)`. `bind_all` is interpreter-wide, so it'd also fire while `SettingsWindow` (a separate `Toplevel`) has focus — give it its own local `self.bind("<F11>", toggle_settings_fullscreen)`; Tk dispatches a widget's own bindtag before `"all"`, so returning `"break"` there stops the global toggle too. Track fullscreen per-window as a bool flag (no Tk getter) and re-apply via `.attributes("-fullscreen", new_state)`.

Zoom/fit: each canvas keeps `self._fit_cell_size` (recomputed on every `<Configure>` via the existing `_cell_size()` clamp) and `self._zoom_offset` (int, default 0, ±2px per wheel notch or `+`/`-`). Effective size = `clamp(fit + offset, _MIN_CELL_SIZE, _MAX_CELL_SIZE)`. Resize doesn't reset the user's zoom offset — only the fit baseline moves.

## Verification

**Commands:**
- `ruff check .` -- expected: no errors
- `ruff format --check .` -- expected: no reformatting needed
- `pytest -q` -- expected: all tests pass, including new geometry/zoom/fullscreen tests and the existing `test_settings_window_opened_on_home_survives_a_real_navigate_to_builder`

**Manual checks (if no CLI):**
- Launch the app locally: root window appears centered, drag-resize works, F11 fullscreens/unfullscreens, Ctrl+wheel over a maze canvas zooms it, opening Settings and pressing F11 there fullscreens only the Settings window.

## Suggested Review Order

**Root window: center, resize, F11**

- Entry point — centers the root at startup on position only (`+x+y`), so a later screen can still grow the window instead of staying pinned to Home's size.
  [`composition_root.py:65`](../../../src/labyrinthes/app/composition_root.py#L65)

- Wires centering + `.resizable(True, True)` + a global F11 toggle right after Home mounts, inside the existing `build_app()` try block.
  [`composition_root.py:202`](../../../src/labyrinthes/app/composition_root.py#L202)

- The new canonical keybinding entries: `toggle_fullscreen` (scope=None, global) and the four per-screen zoom shortcuts on the real `plus`/`minus` keysyms.
  [`keybindings.py:119`](../../../src/labyrinthes/adapters/tkinter/common/keybindings.py#L119)

**Settings window: same treatment, scoped to itself**

- `_center_on_screen()` mirrors the root's version (position-only); `_toggle_fullscreen()` returns `"break"` so its local F11 binding pre-empts the root's global one.
  [`settings_window.py:174`](../../../src/labyrinthes/adapters/tkinter/common/settings_window.py#L174)

**Maze canvas zoom/fit: the shared mechanic (duplicated in Builder + Player)**

- `fit_to_space()` recomputes the resize-driven baseline and re-clamps any stale `_zoom_offset` to it, so a big shrink after zooming stays responsive.
  [`builder/maze_canvas.py:500`](../../../src/labyrinthes/adapters/tkinter/builder/maze_canvas.py#L500)

- `_apply_effective_cell_size()` rescales every drawn item with a single `.scale("all", ...)` call rather than tracking per-item redraw state.
  [`builder/maze_canvas.py:534`](../../../src/labyrinthes/adapters/tkinter/builder/maze_canvas.py#L534)

- Identical fit/zoom mechanic on the Player canvas.
  [`player/maze_canvas.py:307`](../../../src/labyrinthes/adapters/tkinter/player/maze_canvas.py#L307)

**Canvas wiring: `<Configure>` + Ctrl+wheel, per screen**

- `<Configure>` bound on the canvas itself (not its parent frame) plus the three wheel-event conventions (X11 buttons, Windows/macOS delta) routed to one zoom handler.
  [`builder/edit_area.py:396`](../../../src/labyrinthes/adapters/tkinter/builder/edit_area.py#L396)

- `_wheel_zoom_delta()` tells X11/Windows/macOS wheel events apart and now no-ops on a literal zero delta.
  [`builder/edit_area.py:130`](../../../src/labyrinthes/adapters/tkinter/builder/edit_area.py#L130)

- Same `<Configure>`/wheel wiring on the Player gameplay screen, plus the `_maze_frame`/canvas pack-option fix (`fill="both", expand=True`) that makes resize actually reach the canvas.
  [`gameplay/screen.py:376`](../../../src/labyrinthes/adapters/tkinter/player/gameplay/screen.py#L376)

**Tests: peripherals**

- Root centering/resizable/F11 unit tests, plus the real two-binding F11 integration test proving Settings' `"break"` actually stops the root's global toggle.
  [`test_composition_root.py:256`](../../../tests/app/test_composition_root.py#L256)

- Settings window's own centering/resizable/F11 tests.
  [`test_settings_window.py:53`](../../../tests/adapters/tkinter/common/test_settings_window.py#L53)

- Canonical keybinding table additions and the multi-char-keysym/collision regression tests.
  [`test_keybindings.py:224`](../../../tests/adapters/tkinter/common/test_keybindings.py#L224)

- Zoom/fit unit tests per canvas, including the stale-offset-after-shrink regression.
  [`test_maze_canvas.py:427`](../../../tests/adapters/tkinter/player/test_maze_canvas.py#L427)
