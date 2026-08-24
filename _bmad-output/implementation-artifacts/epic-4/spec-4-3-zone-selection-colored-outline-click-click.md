---
baseline_commit: 9cf8c97
---
# Story 4.3: Zone selection — colored outline & click-click gesture

Status: done

## Story

As a maze author,
I want zone selection to show a colored outline and to accept a second gesture,
So that I can see what I'm about to destroy/restore and select with either a drag or two clicks.

## Acceptance Criteria

1. **Given** a zone tool (Destroy or Restore) active, **when** the user starts a selection, **then** a colored rectangle outline is drawn live from the anchor to the current cell, distinct per tool.

2. **Given** a click-and-drag, **when** released on another cell, **then** the dragged zone is applied (the existing gesture, Story 3.3).

3. **Given** a plain click on a cell (press + release, no drag), **when** a zone tool is active, **then** the click arms the anchor, the outline follows the mouse, and a second click on another cell commits the zone — a single click never applies a zone operation.

4. **Given** an armed anchor, **when** Escape is pressed, **then** the anchor is cancelled and no zone operation applies.

## Boundaries & Constraints

**Always:**
- AD-1 (Domain/UI decoupling): `domain/` imports nothing from `adapters/` or any UI framework — zone selection rendering lives in `adapters/tkinter/builder/`.
- AD-3 (Domain object shapes are pinned): `Grid`, `Cell`, `Position`, `Wall` are immutable value objects; `apply_zone_operation` returns a new `BuilderSession` with updated `maze.grid`.
- NFR4 (Language convention): English identifiers and comments throughout.
- NFR6 (Accessibility floor): Escape key cancels the armed anchor; the click-click gesture is fully keyboard-accessible.

**Ask First:**
- Whether the colored outline should use the design token colors or hardcoded values (preference: design tokens).
- Whether the click-click gesture should have a visual indicator for the armed state beyond the outline (e.g., cursor change).

**Never:**
- Modify `domain/zone_editing.py` — the domain logic is complete and correct.
- Add new keybindings to the canonical table for the click-click gesture (uses existing mouse events).
- Break the existing click-and-drag gesture — it must remain fully functional.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| HAPPY_PATH_DRAG | Destroy Zone active, drag from (0,0) to (2,2) | Zone destroyed, outline visible during drag | N/A |
| HAPPY_PATH_CLICK_CLICK | Destroy Zone active, click (0,0), move mouse, click (2,2) | Zone destroyed, outline visible between clicks | N/A |
| ESCAPE_CANCELS | Destroy Zone active, click (0,0) to arm, press Escape | Anchor cancelled, no zone operation, outline removed | N/A |
| SAME_CELL_CLICK | Destroy Zone active, click (1,1), release on (1,1) | No zone operation (same as Story 3.3) | N/A |
| TOOL_SWITCH_MID_GESTURE | Destroy Zone active, click (0,0) to arm, switch to Restore Zone, click (2,2) | Restore zone from (0,0) to (2,2) — tool at press time governs | N/A |
| WRONG_TOOL_CLICK | Break tool active, click (0,0) | No anchor armed, no outline | N/A |
| BORDER_CELLS | Destroy Zone active, click (0,0), click (0,3) on 4x3 grid | Zone applied, border walls skipped silently | N/A |

## Code Map

- `src/labyrinthes/adapters/tkinter/builder/screen.py` -- Main builder screen with `_BuilderEditArea` and `_BuilderMazeCanvas`; zone selection logic in `_on_click`, `_on_release`, `_on_zone_dragged`
- `src/labyrinthes/application/builder_session.py` -- `apply_zone_operation`, `BuilderTool.DESTROY_ZONE`/`RESTORE_ZONE`, `BuilderSession` (immutable session state)
- `src/labyrinthes/domain/zone_editing.py` -- `destroy_zone`, `restore_zone`, `_walls_in_zone` (pure domain logic, no changes needed)
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- Canonical keybinding table (Escape handling may need binding)
- `src/labyrinthes/adapters/tkinter/common/tokens.py` -- Design tokens for colored outline colors
- `tests/adapters/tkinter/builder/test_builder_screen.py` -- Existing zone editing tests (extend for new gesture)

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/adapters/tkinter/builder/screen.py` -- Add colored outline rendering in `_BuilderMazeCanvas`: track armed anchor state, draw live rectangle outline on mouse motion, clear on Escape or commit
- [x] `src/labyrinthes/adapters/tkinter/builder/screen.py` -- Modify `_on_click` and `_on_release` to support click-click gesture: arm anchor on first click (no drag), commit on second click
- [x] `src/labyrinthes/adapters/tkinter/builder/screen.py` -- Add Escape key binding to cancel armed anchor
- [x] `src/labyrinthes/adapters/tkinter/builder/screen.py` -- Update tooltips for Destroy Zone / Restore Zone to mention click-click gesture
- [x] `tests/adapters/tkinter/builder/test_builder_screen.py` -- Add tests for: colored outline during drag, click-click gesture arm/commit, Escape cancels anchor, tool switch mid-gesture

**Acceptance Criteria:**
- Given Destroy Zone active, when mouse moves after click, then live colored outline follows cursor
- Given Destroy Zone active, when click (no drag) then click another cell, then zone is destroyed
- Given armed anchor, when Escape pressed, then anchor cancelled and outline removed
- Given click-and-drag, when released on different cell, then zone applied (existing behavior preserved)
- Given same-cell click, when zone tool active, then no zone operation (existing behavior preserved)

## Spec Change Log

- **2026-08-24**: Implemented Story 4.3 (Zone selection — colored outline & click-click gesture)
  - Added live colored rectangle outline during zone selection (drag and click-click gesture)
  - Implemented click-click gesture: first click arms anchor, mouse motion shows outline, second click commits
  - Added Escape key binding to cancel armed anchor
  - Updated tooltips for Destroy Zone / Restore Zone tools
  - Used design token colors (accent for destroy, entry for restore)
  - All 7 new tests pass, all 889 existing tests pass
  - Lint and format checks pass

## Design Notes

The click-click gesture reuses the existing press-time tool capture pattern (`capture_tool` lambda). The armed anchor state is tracked in `_BuilderMazeCanvas` with `_drag_anchor` (already exists) and a new `_armed_anchor` flag. The live outline is drawn using `create_rectangle` with a distinct color per tool (destroy=red tint, restore=green tint from design tokens). Escape key is bound via `bind_shortcut` to a new `_cancel_armed_anchor` method.

## Verification

**Commands:**
- `ruff check src/labyrinthes/adapters/tkinter/builder/ tests/adapters/tkinter/builder/`
- `ruff format --check src/labyrinthes/adapters/tkinter/builder/ tests/adapters/tkinter/builder/`
- `pytest tests/adapters/tkinter/builder/test_builder_screen.py -v`

**Manual checks (if no CLI):**
- Open Builder, select Destroy Zone tool, click a cell, verify colored outline appears and follows mouse
- Click a second cell, verify zone is destroyed
- Press Escape after first click, verify anchor cancelled and outline removed
- Verify existing click-and-drag still works