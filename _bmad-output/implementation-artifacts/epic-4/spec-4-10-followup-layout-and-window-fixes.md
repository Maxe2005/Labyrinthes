---
title: 'Story 4.10 follow-up: visible grid, centered snug maze-frame, tighter margins, fixed window size'
type: 'bugfix'
created: '2026-09-03'
status: 'done'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-4/spec-4-10-screen-layout-blocks.md
baseline_commit: 30b6fa9685d0662623b99d97b2eed89d2b491b04
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Manual verification of story 4.10 found four defects: (1) the `Stage` grid lines use `colors.panel`, ~3-8 RGB units from `colors.window` — imperceptible on Tk's non-anti-aliased canvas; (2) the maze canvas stretches (`fill="both", expand=True`) to fill the entire `maze-frame`, but the drawn maze itself is a small fixed-pixel-size drawing anchored at the canvas's origin (0,0) — it floats top-left in a mostly-empty frame instead of being centered; (3) `edit_area.pack()`/`gameplay.pack()` add a large `SPACING["page-margin"]`/`SPACING["section-gap"]` (64px/40px) outer margin around the whole three-panel layout, reading as a big blank border outside the panels; (4) the window has no fixed size — it takes whatever size the current screen's content naturally requests, visibly jumping between Home (small) and Builder/Player (larger) on every navigation.

**Approach:** Switch the grid-line color to `colors.border`. Make the maze canvas report its true pixel size (`grid_width × cell_size`, `grid_height × cell_size`) as its own requested size instead of stretching, and center the (now snug) `maze-frame` within `Stage.content`'s leftover space via Tk's `pack(expand=True)` (no `fill`) idiom. Move the fit-to-space "available space" measurement from the canvas's own `<Configure>` to `Stage.content`'s, since the canvas no longer resizes with its parent. Shrink the outer `edit_area.pack()`/`gameplay.pack()` margins. Give the app window a fixed initial size (1280×800 default) read once at startup from a new `shared`-scope setting, with a "Window size" field pair in the Settings window's existing "Defaults" category (applies on next launch, same precedent as Story 4.9's logo-change timing).

## Boundaries & Constraints

**Always:**
- `Stage`'s gridlines use `colors.border`, not `colors.panel`
- `_apply_effective_cell_size()` (both `builder/maze_canvas.py` and `player/maze_canvas.py`) calls `self.configure(width=self._grid_width * new_size, height=self._grid_height * new_size)` after rescaling, so the canvas's own requested size always matches its drawn content exactly
- Builder's `maze-frame` (`edit_area.py::_build_canvas`) and Player's (`screen.py::_build_maze_frame`) pack with `expand=True` and no `fill` inside `Stage.content`, so they hug their canvas and center in the leftover space (Tk's standard "claim space, don't stretch, center" idiom)
- `fit_to_space()`'s available-width/height comes from a `<Configure>` binding on `Stage.content` (or `Stage` itself, adjusted for the inset margin) instead of the canvas's own `<Configure>` — subtract the HUD row's rendered height where the HUD sits above the maze-frame in the same column
- `edit_area.pack()` (`builder/screen.py`) and `gameplay.pack()` (`player/screen.py`) use a small fixed padding (e.g. `SPACING["lg"]`/`SPACING["xl"]`) instead of `SPACING["page-margin"]`/`SPACING["section-gap"]`
- New `shared`-scope settings `window_width`/`window_height` (keys in `settings_keys.py`), a small reader/writer module mirroring `theme_logo_settings.py`, default `1280`/`800`, clamped to `[800, screen_width]`×`[600, screen_height]`
- `composition_root.py::build_app()` reads these once before/at `root` creation and calls `root.geometry(f"{width}x{height}")` — the window never auto-resizes again on navigation (screens still fill whatever that fixed size is via the existing `fill="both", expand=True` chain)
- Settings window's existing "Defaults" category gets a "Window size" field pair (Width/Height), built with the same `_add_default_dimension_field()` helper already used for New Maze/Random Maze dimensions — changes apply on next launch, not live (same precedent as the Story 4.9 logo setting)
- Zoom (`+`/`-`, Ctrl+wheel) and all existing Story 4.8 fit-to-space behavior keep working exactly as before — only what "available space" is measured against changes, not the sizing algorithm itself

**Ask First:** None — every value/approach below was confirmed with the human.

**Never:**
- Change `_apply_effective_cell_size`'s `.scale("all", 0, 0, factor, factor)` rescaling math, or any marker/wall/cursor drawing coordinates — they stay origin-relative; only the canvas's own reported size changes
- Make window size live-apply from the open Settings window — next-launch is sufficient, per precedent
- Touch `domain/`/`application/` beyond the new tiny settings reader/writer module (same shape as existing ones)
- Change `ClassicMazeGallery`'s layout — unaffected by this correction

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Builder/Player screen renders | Maze loaded, default window size | Grid lines visible (`colors.border`) in the stage margin; maze-frame hugs the maze and sits centered in the stage; small, consistent outer margin around the whole panel layout | N/A |
| Window resized bigger | User drags window edge | Maze cell size grows (fit-to-space, capped at 40px/cell) and the frame re-centers at its new, still-snug size | N/A |
| App launches | No `window_width`/`window_height` setting stored | Window opens at 1280×800, centered on screen | Falls back to defaults, never raises |
| User sets an out-of-bounds window size in Settings | e.g. `50` or `99999` | Clamped to `[800, screen_width]`×`[600, screen_height]` on write, same inline-error pattern as existing dimension fields | Inline error, no crash |
| Navigating Home → Builder → Player → Home | Any state | Window size never changes across navigation | N/A |

</frozen-after-approval>

## Code Map

- `src/labyrinthes/adapters/tkinter/common/stage.py` -- `_redraw_lines` (gridline color): change `self._colors.panel` → `self._colors.border`.
- `src/labyrinthes/adapters/tkinter/builder/maze_canvas.py` -- `_apply_effective_cell_size` (~line 534): add `self.configure(width=..., height=...)`. `fit_to_space` (~line 500): caller changes, signature unchanged.
- `src/labyrinthes/adapters/tkinter/player/maze_canvas.py` -- same two methods (~lines 307, 342), mirrored change.
- `src/labyrinthes/adapters/tkinter/builder/edit_area.py` -- `_build_canvas` (~line 393): `maze_frame.pack(fill="both", expand=True)` → `pack(expand=True)`; canvas Configure binding (~line 420, `_on_canvas_configure`) moves to `self._stage.content`.
- `src/labyrinthes/adapters/tkinter/player/gameplay/screen.py` -- `_build_maze_frame` (~line 379: `pack(fill="both", expand=True, anchor="w", ...)` → `pack(expand=True, ...)`), `_on_canvas_configure` (~line 405) moves to `self._stage.content`.
- `src/labyrinthes/adapters/tkinter/builder/screen.py` -- `edit_area.pack(..., padx=SPACING["page-margin"], pady=SPACING["section-gap"])` (~line 128): shrink both.
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- `gameplay.pack(..., padx=SPACING["page-margin"], pady=SPACING["section-gap"])` (~line 183): shrink both.
- `src/labyrinthes/application/settings_keys.py` -- add `WINDOW_WIDTH`/`WINDOW_HEIGHT` keys.
- New `src/labyrinthes/application/window_settings.py` -- `read_window_size`/`write_window_width`/`write_window_height`, `shared` scope, mirrors `theme_logo_settings.py`'s shape.
- `src/labyrinthes/app/composition_root.py` -- `build_app()`: read window size before/at `root = tk.Tk()`, call `root.geometry(...)` once; remove/adjust `_center_on_screen`'s reliance on natural post-mount size if now redundant.
- `src/labyrinthes/adapters/tkinter/common/settings_window.py` -- `_build_defaults`: add a "Window size" field pair using the existing `_add_default_dimension_field` helper.

## Tasks & Acceptance

**Execution:**
- [ ] `common/stage.py` -- gridline color `colors.panel` → `colors.border`
- [ ] `builder/maze_canvas.py` + `player/maze_canvas.py` -- `_apply_effective_cell_size` configures the canvas's own width/height to match drawn content
- [ ] `builder/edit_area.py` -- `maze-frame` packs with `expand=True` (no `fill`); fit-to-space Configure binding moves to `Stage.content`
- [ ] `player/gameplay/screen.py` -- same `maze-frame`/Configure-binding change
- [ ] `builder/screen.py` + `player/screen.py` -- shrink the outer `edit_area`/`gameplay` pack padding
- [ ] `application/settings_keys.py` + new `application/window_settings.py` -- `window_width`/`window_height` shared-scope setting, default 1280×800, clamped
- [ ] `app/composition_root.py` -- read the setting once, fix the window's initial `geometry()`, no auto-resize across navigation
- [ ] `common/settings_window.py` -- "Window size" field pair in the Defaults category
- [ ] Tests -- cover the I/O matrix rows: gridline color, canvas self-sizing, centered packing (`expand=True`/no `fill`), window geometry set once, setting read/write + clamping
- [ ] Run `ruff check .`, `ruff format --check .`, `pytest` -- all green

**Acceptance Criteria:**
- Given the Builder or Player screen renders, when inspected, then gridlines use `colors.border` and the maze-frame is snug around the maze, centered in the stage
- Given the app launches with no stored window-size setting, when the root window is created, then it opens at 1280×800
- Given the window is resized larger, when the maze re-fits, then the frame stays snug and re-centers (no stretch-to-fill)
- Given the user navigates Home → Builder → Player → Home, when each screen mounts, then the window's size never changes
- Given an out-of-bounds window-size value is entered in Settings, when saved, then it's clamped, matching the existing dimension-field validation pattern

## Design Notes

Centering idiom (`pack(expand=True)`, no `fill`): the standard Tk pattern for "claim leftover space in a cavity, but keep the widget at its own natural size, centered within that cavity." Combined with the canvas now reporting its true pixel size via `.configure(width=, height=)`, this replaces the previous `fill="both", expand=True` stretch.

Fit-to-space now measures against `Stage.content` rather than the canvas, because the canvas's own `<Configure>` events would otherwise reflect *our own* `.configure()` calls, not the actual available room — a feedback loop, not a resize signal.

## Verification

**Commands:**
- `ruff check .` -- expected: no errors
- `ruff format --check .` -- expected: no reformatting needed
- `pytest -q` -- expected: all tests pass (GUI tests require DISPLAY)

**Manual checks (if no CLI):**
- Launch app: window opens at 1280×800, centered on screen
- Open Builder/Player: gridlines visible around a snug, centered maze-frame; small consistent outer margin, not a huge blank border
- Navigate Home → Builder → Player → Home: window size stays constant throughout
- Resize the window: maze re-fits and stays centered, snug
- Settings → Defaults: change window size, restart app, confirm new size takes effect; try an out-of-bounds value, confirm it's clamped with an inline error like the existing dimension fields
</frozen-after-approval>

## Suggested Review Order

**Why the grid was invisible, and the fix**

- Gridlines now draw in `colors.border` instead of `colors.panel` — the only real fix needed for visibility.
  [`stage.py:68`](../../../src/labyrinthes/adapters/tkinter/common/stage.py#L68)

**Centering the maze: canvas reports its true size, frame hugs and centers it**

- The canvas now tells Tk its real drawn size instead of relying on `fill` to stretch.
  [`maze_canvas.py:560`](../../../src/labyrinthes/adapters/tkinter/builder/maze_canvas.py#L560)
  [`maze_canvas.py:370`](../../../src/labyrinthes/adapters/tkinter/player/maze_canvas.py#L370)

- `maze-frame` now hugs and centers via `pack(expand=True)`, no `fill` — the standard Tk idiom for this.
  [`edit_area.py:403`](../../../src/labyrinthes/adapters/tkinter/builder/edit_area.py#L403)

- Fit-to-space now measures `Stage.content`'s own resize instead of the canvas's (which no longer stretches).
  [`edit_area.py:431`](../../../src/labyrinthes/adapters/tkinter/builder/edit_area.py#L431)

**Fixed, configurable window size**

- Read once, right after `Tk()` is created, before any screen mounts — the window never auto-resizes again.
  [`composition_root.py:137`](../../../src/labyrinthes/app/composition_root.py#L137)

- New Settings → Defaults field pair, reusing the existing dimension-field validation pattern.
  [`settings_window.py:497`](../../../src/labyrinthes/adapters/tkinter/common/settings_window.py#L497)

**Review-round patches (Configure-after-destroy guard, bool-as-int guard, clamp-mode UX)**

- Guards against a `<Configure>` firing on a container after its HUD child is torn down mid-navigation.
  [`edit_area.py:454`](../../../src/labyrinthes/adapters/tkinter/builder/edit_area.py#L454)

- `window_settings.py`'s corruption guard now rejects `bool`, which Python's `isinstance(_, int)` would otherwise accept.
  [`window_settings.py:78`](../../../src/labyrinthes/application/window_settings.py#L78)

**Peripherals**

- New coverage: window-size read/write/clamp, canvas self-sizing, real Width/Height field wiring.
  [`test_window_settings.py`](../../../tests/application/test_window_settings.py)
  [`test_settings_window.py`](../../../tests/adapters/tkinter/common/test_settings_window.py)
