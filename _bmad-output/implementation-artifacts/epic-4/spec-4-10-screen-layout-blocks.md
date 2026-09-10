---
title: 'Story 4.10: Screen layout — labeled blocks separated from the maze'
type: 'feature'
created: '2026-09-03'
status: 'done'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-4/epic-4-context.md
baseline_commit: aeb3e52a0321c89fa49c7d56c436c0476acbc08d
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Builder's tool sidebar is one unlabeled, flat 6-button stack with no bordered canvas frame; Player's sidebar has 4 heading labels using the wrong typography token/color; neither screen matches the locked mockups' two-panel-flanking-a-centered-stage layout, which the implementation has drifted from over several stories.

**Approach:** Reorganize existing controls only (no new functionality — see Never) into two labeled side panels flanking a centered "stage" column (HUD + bordered `maze-frame`) with a light grid-line background, on both Builder's edit screen and Player's gameplay screen. Introduce two shared `common/` helpers: a group-heading builder and a grid-background stage container.

## Boundaries & Constraints

**Always:**
- Add `build_group_heading(parent, text, colors) -> tk.Label` to `common/` (`TYPOGRAPHY.label.to_tk_font()`, `text.upper()`, `foreground=colors.ghost`) — used by every group heading below
- Add a `common/stage.py` grid-background container (`tk.Canvas`-based, since Tk has no CSS-gradient equivalent): draws light horizontal/vertical lines in `colors.panel` at a fixed ~22px spacing, redrawn on `<Configure>`, hosting the HUD + `maze-frame` centered as a column — used by both screens
- **Builder left panel**: "Walls" (Break Wall, Pass-through), "Zones" (Destroy Zone, Restore Zone), "Markers" (Set Entry, Set Exit) — 3 labeled pairs, same order as today
- **Builder right panel**: "Actions" — Save, Test in Player, moved out of the HUD row into this panel
- **Builder HUD**: keeps only its existing chips (Grid, Walls broken, Draft status) — no buttons remain in it
- Builder canvas wrapped in a bordered `maze-frame` (`highlightthickness=1, highlightbackground=colors.border, highlightcolor=colors.border, background=colors.window`) — same recipe as Player's existing one
- **Player left panel**: "Mode" (HARD toggle), "Levels", "Difficulty", conditional "Edit in Builder" — same content/behavior, relocated and restyled
- **Player right panel**: "Movement" (mode toggle + speed cycle) + the existing conditional Save button (`_save_zone`, `GENERATED` mazes only) — relocated here
- All group headings use `build_group_heading`; theme toggle updates every new color without restart

**Ask First:** None — all placements below were confirmed with the human during spec planning.

**Never:**
- Add Undo, Resize, "Clear all", or a New-Maze/Export panel to the Builder — net-new functionality, deferred (`deferred-work.md`)
- Add Pause, Sound, Legend, or an in-gameplay Classic/Random toggle to the Player — net-new functionality, deferred (`deferred-work.md`)
- Touch `domain/` or `application/` — purely an `adapters/tkinter` layout change; every button's existing command/behavior is unchanged, only its container moves
- Attempt pixel-exact mockup fidelity (border-radius, CSS gradients, letter-spacing) — Tk has no equivalent; approximate per the existing `highlightthickness` border and canvas-drawn grid-line conventions
- Wrap `ClassicMazeGallery` (Player's selection screen) in a `maze-frame`/stage — no maze canvas there, out of scope

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Builder edit screen renders | Maze loaded | Left panel: Walls/Zones/Markers groups; right panel: Actions (Save, Test in Player); HUD chips only, above a bordered `maze-frame` on a grid-background stage | N/A |
| Player gameplay screen renders | Maze mounted | Left panel: Mode/Levels/Difficulty(/Edit in Builder); right panel: Movement(/Save); existing HUD + `maze-frame` on a grid-background stage | N/A |
| Player has an unsaved random maze | `maze.kind is GENERATED` | Save button renders in the right panel under Movement, same conditional behavior as today | N/A |
| Theme toggle | Light → Dark or Dark → Light | All panels, headings, stage grid lines, and both maze-frames re-render with the new theme's colors | N/A |

</frozen-after-approval>

## Code Map

- `src/labyrinthes/adapters/tkinter/builder/edit_area.py` -- `_build_tool_sidebar` (203–301): replace with left-panel build (Walls/Zones/Markers). `_build_hud` (303–363): drop the two `PillButton`s (Save, Test in Player), keep chips only. `_build_canvas` (365–392): wrap canvas in bordered `maze-frame`. Constructor (177–182): recompose as left panel / stage (HUD+maze-frame, grid-bg) / right panel (Actions: Save+Test in Player, currently built in `_build_hud`).
- `src/labyrinthes/adapters/tkinter/player/gameplay/screen.py` -- HUD build (302–310), sidebar build (312–331), `_build_maze_frame` (362–390), `_save_zone` init (335–337) and `_build_save_zone` (404–423, moves the conditional Save `PillButton`): recompose into left panel / stage (HUD+maze-frame, grid-bg) / right panel (Movement+Save).
- `src/labyrinthes/adapters/tkinter/player/gameplay/sidebar.py` -- `_Sidebar` (28–170): split into left-panel content (Mode/Levels/Difficulty/Edit-in-Builder, headings at 83–89/102–108/128–134) and right-panel content (Movement, heading at 56–62).
- `src/labyrinthes/adapters/tkinter/common/tokens.py` -- `TYPOGRAPHY.label` (line 187), `ColorTokens.ghost`/`.panel`/`.border`/`.window`, `SPACING` (195–207) — reuse as-is.
- New: `src/labyrinthes/adapters/tkinter/common/group_heading.py` -- `build_group_heading(parent, text, colors)`.
- New: `src/labyrinthes/adapters/tkinter/common/stage.py` -- grid-background centered stage container, reused by both screens.

## Tasks & Acceptance

**Execution:**
- [x] `common/group_heading.py` -- add `build_group_heading(parent, text, colors)` -- shared heading style
- [x] `common/stage.py` -- add grid-background `tk.Canvas` stage container hosting centered content, redrawn on `<Configure>` -- shared by both screens
- [x] `builder/edit_area.py` -- rebuild left panel (Walls/Zones/Markers), right panel (Actions: Save+Test in Player), simplify HUD to chips-only, mount canvas inside the new stage's `maze-frame`
- [x] `player/gameplay/sidebar.py` + `player/gameplay/screen.py` -- split sidebar into left panel (Mode/Levels/Difficulty/Edit-in-Builder) and right panel (Movement + relocated `_save_zone`), mount HUD+`maze-frame` inside the new stage
- [x] Tests -- update `tests/adapters/tkinter/builder/test_builder_screen.py` and `tests/adapters/tkinter/player/gameplay/test_screen.py` (and any other test relying on old widget layout/parentage) for the new panel structure; add coverage for group-heading text/font/color and stage grid-line rendering
- [x] Run `ruff check .`, `ruff format --check .`, `pytest` -- all green

**Acceptance Criteria:**
- Given the Builder edit screen with a maze loaded, when it renders, then the left panel shows Walls/Zones/Markers groups and the right panel shows an Actions group with Save and Test in Player
- Given the Builder edit screen, when it renders, then the maze sits inside a bordered `maze-frame` on a grid-background stage, and the HUD row shows only chips
- Given the Player gameplay screen, when it renders, then the left panel shows Mode/Levels/Difficulty(/Edit in Builder) and the right panel shows Movement (and Save when the maze is unsaved-random)
- Given a theme toggle, when switching light/dark, then all panels, headings, the stage grid, and both maze-frames update colors without restart

## Spec Change Log

## Design Notes

`common/stage.py`'s embedding pattern (grid lines behind regular child widgets, which `pack`/`grid` can't layer):
```python
class Stage(tk.Canvas):
    def __init__(self, parent, *, colors):
        super().__init__(parent, background=colors.window, highlightthickness=0)
        self.bind("<Configure>", self._redraw)

    def _redraw(self, event):
        self.delete("gridline")
        # draw horizontal/vertical lines at ~22px spacing in colors.panel,
        # tagged "gridline"; re-center embedded content via create_window
```
`build_group_heading` mirrors the existing `settings_window.py` category-nav precedent and `HudChip`'s `.upper()` pattern (Tk fakes CSS `text-transform` in Python since it has no native support).

Both screens' panel split is a pure recomposition: every existing button/callback keeps its exact command wiring, only its parent container and heading style change.

## Verification

**Commands:**
- `ruff check .` -- expected: no errors
- `ruff format --check .` -- expected: no reformatting needed
- `pytest -q` -- expected: all tests pass (GUI tests require DISPLAY)

**Manual checks (if no CLI):**
- Launch app, open Builder with a maze: verify left/right panels, Actions group, grid-background stage, bordered maze-frame
- Open Player, start gameplay: verify left/right panels, Movement+Save on the right
- Start Player with a freshly generated (unsaved) random maze: verify Save button appears in the right panel
- Toggle theme: verify all panels/headings/stage/maze-frames update colors

## Suggested Review Order

**The grid-background fix (start here)**

- `content` used to fill the whole canvas, permanently hiding every gridline underneath it — this insets it so the grid backdrop is actually visible.
  [`stage.py:53`](../../../src/labyrinthes/adapters/tkinter/common/stage.py#L53)

- Proof the fix holds: content's window is smaller than the canvas and at least one gridline sits outside it.
  [`test_stage.py:36`](../../../tests/adapters/tkinter/common/test_stage.py#L36)

**Builder: three-column composition**

- Entry point — left panel, right panel, then the centered `Stage` wired together.
  [`edit_area.py:184`](../../../src/labyrinthes/adapters/tkinter/builder/edit_area.py#L184)

- Walls/Zones/Markers groups replace the old flat, unlabeled tool stack.
  [`edit_area.py:211`](../../../src/labyrinthes/adapters/tkinter/builder/edit_area.py#L211)

- Save + Test in Player move out of the HUD into their own Actions panel.
  [`edit_area.py:323`](../../../src/labyrinthes/adapters/tkinter/builder/edit_area.py#L323)

- The maze canvas now sits inside a bordered `maze-frame`, previously unbordered.
  [`edit_area.py:393`](../../../src/labyrinthes/adapters/tkinter/builder/edit_area.py#L393)

**Player: sidebar split into two panels**

- `_LeftPanel`/`_RightPanel` replace the single `_Sidebar`, each flanking the `Stage` independently.
  [`sidebar.py:40`](../../../src/labyrinthes/adapters/tkinter/player/gameplay/sidebar.py#L40)

- `_RightPanel` also owns the conditional Save button's zone, relocated from below the maze.
  [`sidebar.py:157`](../../../src/labyrinthes/adapters/tkinter/player/gameplay/sidebar.py#L157)

- Construction wiring: left panel, right panel (with the relocated save zone), then the `Stage`.
  [`screen.py:306`](../../../src/labyrinthes/adapters/tkinter/player/gameplay/screen.py#L306)

**Shared helpers extracted for reuse across both screens**

- `build_group_heading` — the one place every group's label styling now lives.
  [`group_heading.py:23`](../../../src/labyrinthes/adapters/tkinter/common/group_heading.py#L23)

- `build_maze_frame` — the bordered-frame recipe, previously duplicated, now shared.
  [`maze_frame.py:23`](../../../src/labyrinthes/adapters/tkinter/common/maze_frame.py#L23)

**Peripherals**

- New screen-level layout assertions (headings, panel sides, HUD chips-only).
  [`test_builder_layout.py`](../../../tests/adapters/tkinter/builder/test_builder_layout.py)
  [`test_layout.py`](../../../tests/adapters/tkinter/player/gameplay/test_layout.py)

- Mechanical updates: `find_all(frame, tk.Canvas)` → `find_all(frame, _BuilderMazeCanvas)` (now ambiguous since `Stage` is also a canvas), `_sidebar` → `_left_panel`/`_right_panel`.
  [`test_builder_wall_editing.py:70`](../../../tests/adapters/tkinter/builder/test_builder_wall_editing.py#L70)
  [`test_hard_mode.py:34`](../../../tests/adapters/tkinter/player/gameplay/test_hard_mode.py#L34)
</frozen-after-approval>
