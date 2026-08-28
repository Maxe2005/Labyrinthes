---
title: 'Screen layout — labeled blocks separated from the maze'
type: 'feature'
created: '2026-08-28'
status: 'draft'
review_loop_iteration: 0
context:
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/ux-designs/ux-Labyrinthes-2026-08-04/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-Labyrinthes-2026-08-04/EXPERIENCE.md
  - _bmad-output/implementation-artifacts/epic-4/epic-4-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Builder and Player screens currently render tools and controls as unstructured lists without visual grouping. The maze canvas is not visually separated from the side panels, making the UI feel cluttered and lacking clear hierarchy.

**Approach:** Introduce labeled block containers for both screens using shared design tokens. Builder tools will be grouped under "Tools" and "Markers" headings. Player's existing groups (Movement, Mode, Levels, Difficulty, Logo) will be tidied into consistent blocks. The maze canvas in both screens will render inside a bordered `maze-frame` clearly separated from side blocks, using the spacing scale and typography tokens consistently.

## Boundaries & Constraints

**Always:**
- Use paired light/dark design tokens from `adapters/tkinter/common/tokens.py` for all colors
- Use `SPACING` scale from tokens for all padding/margins
- Group headings use `{typography.label}` token; consistent across Builder and Player
- Maze canvas wrapped in a bordered frame with `{rounded.xl}` radius and `{colors.border}` color
- Builder: "Tools" group contains Break, Pass-through, Destroy Zone, Restore Zone; "Markers" group contains Set Entry, Set Exit
- Player: tidy existing sidebar groups into labeled blocks with consistent spacing
- No domain changes — purely adapter/UI refactoring
- `adapters/tkinter/common/` never imports `builder/` or `player/` (AD-9)
- Screens never import each other (AD-9)

**Ask First:**
- Whether to extract a shared group-heading helper into `common/` (optional, low risk)

**Never:**
- Hardcode colors, spacing, or radii values
- Add UI concerns to `domain/` or `application/`
- Couple `common/` to screen-specific asset folders

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Builder edit screen renders | Maze loaded, tools sidebar visible | Left sidebar shows "Tools" heading, then 4 tool buttons; "Markers" heading, then 2 marker buttons; HUD row above maze-frame; maze in bordered frame separated from sidebar | N/A |
| Player gameplay screen renders | Maze mounted, gameplay active | Left sidebar shows labeled blocks for Movement, Mode, Levels, Difficulty, Logo with consistent headings; HUD row above maze-frame; maze in bordered frame | N/A |
| Player selection screen renders | Browsing classic mazes | Gallery in bordered frame, no sidebar groups (selection is the main content) | N/A |
| Theme toggle | Light → Dark or Dark → Light | All block backgrounds, borders, headings, and maze-frame update to new theme tokens without restart | N/A |
| Window resize | User drags window edge | Blocks and maze-frame reflow with consistent spacing, no overlap or clipping | N/A |

</frozen-after-approval>

## Code Map

- `src/labyrinthes/adapters/tkinter/builder/edit_area.py` -- Main Builder edit area layout (sidebar + HUD + canvas). Lines 177-182: `center` frame packs HUD then canvas. Lines 203-302: `_build_tool_sidebar` creates unlabeled tool buttons. Lines 303-348: `_build_hud` creates HUD chips and Save pill.
- `src/labyrinthes/adapters/tkinter/builder/maze_canvas.py` -- `_BuilderMazeCanvas` renders maze. Used by `edit_area.py` line 182.
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- Player screen mount. Lines 146-159: gallery view; lines 160-188: gameplay view with `GameplayScreen`.
- `src/labyrinthes/adapters/tkinter/player/gameplay/screen.py` -- `GameplayScreen` layout. Lines 350-450 (approx): sidebar (`_Sidebar`) and canvas layout.
- `src/labyrinthes/adapters/tkinter/player/gameplay/sidebar.py` -- `_Sidebar` with Movement/Mode/Levels/Difficulty/Logo groups. Currently renders buttons without labeled block headings.
- `src/labyrinthes/adapters/tkinter/common/tokens.py` -- `SPACING`, `colors_for`, `ColorTokens`, `TypographyTokens`, `Theme` — all design tokens.
- `src/labyrinthes/adapters/tkinter/common/top_bar.py` -- `TopBar` with breadcrumb/logo; already uses tokens.
- `src/labyrinthes/adapters/tkinter/common/settings_window.py` -- Reference for bordered frame pattern (if any).

## Tasks & Acceptance

**Execution:**
- [ ] `src/labyrinthes/adapters/tkinter/builder/edit_area.py` -- Refactor `_build_tool_sidebar` to wrap tool buttons in labeled "Tools" and "Markers" group blocks using `TypographyTokens.label` for headings and `SPACING` for consistent gaps
- [ ] `src/labyrinthes/adapters/tkinter/builder/edit_area.py` -- Wrap canvas in a bordered `maze-frame` frame (background `colors.window`, border `colors.border`, radius `rounded.xl`) separated from sidebar by `SPACING["lg"]`
- [ ] `src/labyrinthes/adapters/tkinter/builder/edit_area.py` -- Ensure HUD row sits above maze-frame inside the center column with `SPACING["section-gap"]` below
- [ ] `src/labyrinthes/adapters/tkinter/player/gameplay/sidebar.py` -- Add group heading labels ("Movement", "Mode", "Levels", "Difficulty", "Logo") using `TypographyTokens.label` above each button group with consistent `SPACING`
- [ ] `src/labyrinthes/adapters/tkinter/player/gameplay/screen.py` -- Wrap `MazeCanvas` in bordered `maze-frame` matching Builder's styling; ensure sidebar and maze-frame are separated by `SPACING["lg"]`
- [ ] `src/labyrinthes/adapters/tkinter/player/screen.py` -- Wrap `ClassicMazeGallery` in bordered frame when in selection mode (optional, per UX-DR9 gallery mockup)
- [ ] `src/labyrinthes/adapters/tkinter/common/tokens.py` -- Verify `TypographyTokens.label` exists and is used; if missing, add it (minimal change)

**Acceptance Criteria:**
- Given the Builder edit screen with a maze loaded, when it renders, then tools are grouped under a "Tools" heading and markers under a "Markers" heading, both using the shared label typography token, with consistent spacing between groups and buttons
- Given the Builder edit screen, when it renders, then the maze renders inside a bordered `maze-frame` (rounded XL, border color token) clearly separated from the left sidebar
- Given the Player gameplay screen, when it renders, then the sidebar groups (Movement, Mode, Levels, Difficulty, Logo) each have a visible heading label using the shared typography token, with consistent spacing
- Given the Player gameplay screen, when it renders, then the maze canvas is inside a bordered `maze-frame` matching the Builder's frame styling, separated from the sidebar
- Given a theme toggle, when switching light/dark, then all block backgrounds, borders, headings, and maze-frame update correctly without restart
- Given window resize, when dragging the window edge, then layout reflows with consistent spacing, no clipping

## Spec Change Log

## Design Notes

The UX spec (`DESIGN.md` → Components → Layout blocks) specifies:
- Side bars with group headings in `{typography.label}`
- Maze in bordered `maze-frame` (`{rounded.xl}`, `{colors.border}`)
- Consistent spacing via `{spacing}` scale

Builder groups: "Tools" (Break, Pass-through, Destroy Zone, Restore Zone) and "Markers" (Set Entry, Set Exit).
Player groups: existing "Movement", "Mode", "Levels", "Difficulty", "Logo" — just add headings and tidy spacing.

No new widgets needed — only composition changes using existing `tk.Frame` containers and token-driven styling.

## Verification

**Commands:**
- `ruff check .` -- expected: no errors
- `ruff format --check .` -- expected: no formatting changes needed
- `pytest` -- expected: all tests pass (GUI tests require DISPLAY)

**Manual checks (if no CLI):**
- Launch app (`python -m labyrinthes.app`), open Builder with a maze: verify "Tools" and "Markers" headings visible, maze in bordered frame
- Open Player, start gameplay: verify sidebar group headings visible, maze in bordered frame matching Builder
- Toggle theme (top-bar icon): verify all blocks and frames update colors
- Resize window: verify layout reflows correctly