---
title: 'Story 3.5: Direct navigation — "Go to"'
type: 'feature'
created: '2026-08-19'
status: 'done'
review_loop_iteration: 1
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-3/epic-3-context.md']
baseline_revision: '753211b'
final_revision: ''
---

## Intent

**Problem:** The Builder edit screen has no way for the user to move the editing cursor directly to a clicked cell. Currently, `_on_cell_clicked` only dispatches to marker-tool placement (SET_ENTRY/SET_EXIT); a plain cell click with no active marker tool is a no-op. Epic 3, FR-7 requires that clicking a cell (when no zone-drag or marker tool is active) moves the editing cursor directly to that position, so the author can jump around the grid without stepping cell by cell.

**Approach:** Extend `_on_cell_clicked` in `screen.py` so that when the active `tool` is not a marker tool (SET_ENTRY, SET_EXIT) and no zone-drag is in progress, the click moves the editing cursor to the clicked cell position using `move_cursor` (from `builder_session.py`). The cursor moves in a single step to the target cell — if the move is blocked by an interior wall in BREAK mode, the cursor stays put; in PASS_THROUGH mode, the wall breaks and the cursor moves into the target cell. This is a pure application-layer operation (no tkinter import in `application/`) that reuses the existing `move_cursor` function, keeping the domain layer unchanged.

## Boundaries & Constraints

**Always:**
- `move_cursor` is a pure function in `application/builder_session.py`; no `tkinter` import in `domain/` or `application/` (AD-1, AD-9)
- The 0/1/2/3 cell encoding is preserved as-is; no re-encoding occurs
- Domain value objects (`Grid`, `Cell`, `Maze`, `Position`) are immutable; engine operations are pure functions returning new state
- Builder-specific widgets stay local to `adapters/tkinter/builder/`; generic widgets come from `adapters/tkinter/common/`
- The Builder owns an adapter-local mutable session wrapper (cursor position, active tool) around the immutable `Maze` value it references
- `move_cursor` in `BREAK` mode: cursor moves if open via `attempt_move`, stays put if blocked; no wall state changes
- `move_cursor` in `PASS_THROUGH` mode: a blocked move breaks the wall it ran into first, then moves the cursor into the now-open target cell; a blocked *border* wall leaves the cursor in place and breaks nothing (FR-2 invariant)
- The outer border stays closed after a cursor move (FR-1 invariant; also applies to single cursor movement)
- Clicking a cell while a zone-drag is in progress is not a cursor-move operation — the zone-drag has its own gesture split and takes precedence
- If the active tool is `BREAK` or `PASS_THROUGH`, the click moves the cursor per that tool's semantics; if the tool is something else (e.g. future tools), the click is a no-op for cursor movement

**Never:**
- Mutate `Grid`/`Cell` in-place; all domain operations return new immutable values
- Allow a cell click to move the cursor when a zone-drag is actively in progress — zone gestures take precedence
- Re-encode the 0/1/2/3 cell values — preserve them as-is
- Trigger a wall break or zone operation from a plain cursor-move click — only move the cursor

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Cold click, no tool active | Editing cursor at cell (0,0); user clicks cell (3,5) | Cursor moves to (3,5) if path is open; in BREAK mode stays if wall blocks; in PASS_THROUGH mode breaks wall if needed | No exception; cursor stays put if move blocked |
| BREAK mode, click blocked by wall | Cursor at (2,2); user clicks (2,3) which has a wall between | Cursor stays at (2,2); no wall changed | No error; silent no-op |
| PASS_THROUGH mode, click across wall | Cursor at (2,2); user clicks (2,3) across a wall | Wall between (2,2) and (2,3) breaks; cursor moves to (2,3) | Wall breaks; count increments |
| Click same cell as current cursor | Cursor at (1,1); user clicks (1,1) | Cursor stays at (1,1); no change | No error; idle click |
| Click during zone-drag in progress | Zone-drag active from (0,0) to (1,1); user clicks (5,5) | No cursor move; zone-drag continues unaffected | Ignored — zone gesture takes precedence |
| Set Entry/Set Exit tool active | SET_ENTRY or SET_EXIT tool active; user clicks a cell | Marker placement operates as per Story 3.4; cursor does not move | Standard marker placement behavior |
| Save maze after cursor move | Maze has been navigated via cursor clicks | CSV output unchanged from legacy format (0/1/2/3 cells) | No error; save proceeds normally |

## Code Map

- `src/labyrinthes/application/builder_session.py` — extend `move_cursor` to accept a `Position` target direction (or add new function `move_cursor_to(Position) -> BuilderSession`) so the adapter can request a cursor move to an absolute position
- `src/labyrinthes/adapters/tkinter/builder/screen.py` — modify `_on_cell_clicked` to dispatch cursor movement when no marker tool is active and no zone-drag is in progress; the click handler passes the clicked `position` to the new cursor-move logic
- `src/labyrinthes/adapters/tkinter/builder/screen.py` — ensure `_on_cell_clicked` checks the active tool and zone-drag state before deciding to move the cursor vs. handle markers vs. no-op

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/application/builder_session.py` — add `move_cursor_to(session, target_position: Position) -> BuilderSession` function that moves the cursor to an absolute position, reusing `attempt_move` semantics for BREAK mode and wall-breaking for PASS_THROUGH mode
- [x] `src/labyrinthes/adapters/tkinter/builder/screen.py` — modify `_on_cell_clicked` to move the cursor to the clicked position when the active tool is not a marker tool and no zone-drag is in progress
- [x] Verify `move_cursor_to` reuses `attempt_move` and `wall_between`/`break_wall` from existing domain functions
- [x] Run full test suite to confirm no regressions
- [x] Verify `ruff check .` and `ruff format --check .` pass

**Acceptance Criteria:**
- [x] Given the maze-frame with no zone-drag in progress, when a cell is clicked with no marker tool active, then the editing cursor moves directly to that cell
- [x] In BREAK mode, if the target cell is blocked by a wall, the cursor stays put and no wall is broken
- [x] In PASS_THROUGH mode, if the target cell is blocked by a wall, the wall breaks and the cursor moves into the target cell
- [x] Clicking the cell already holding the cursor is a no-op (cursor stays in place)
- [x] Click during an active zone-drag is ignored for cursor movement (zone gesture takes precedence)
- [x] Click with SET_ENTRY/SET_EXIT active continues to handle marker placement as per Story 3.4
- [x] Code follows all conventions: English identifiers, domain/UI decoupling, English UI strings, 0/1/2/3 cell encoding preserved

### Review Findings

- [x] [Review][Patch] Ensure `move_cursor_to` does not mutate `session` in place — must return a new `BuilderSession` via `replace`/`dataclasses.replace` [`builder_session.py:new`]
- [x] [Review][Patch] Verify that `_on_cell_clicked` correctly gates on "no zone-drag in progress" by checking the adapter's drag-anchor state [`screen.py:new`]
- [x] [Review][Patch] Ensure the new function reuses existing `attempt_move`, `wall_between`, `break_wall` rather than duplicating bit-twiddle — follow the pattern of `move_cursor` [`builder_session.py:new`]
- [x] [Review][Patch] Check that `move_cursor_to` handles border walls correctly: cursor stays put, no wall broken, matching FR-2 [`builder_session.py:new`]
- [x] [Review][Defer] `final_revision` left blank in this spec's frontmatter despite completed review — deferred, pre-existing (same pattern as stories 3.1–3.4)

## Spec Change Log

- **Iteration 1 (initial):** Created spec for Story 3.5 — Direct navigation "Go to", extending `_on_cell_clicked` to move the editing cursor to a clicked cell when no marker tool or zone-drag is active, reusing `move_cursor` semantics from `builder_session.py`.

- **Iteration 2 (review loop):** [Pending — will be filled after human review patches, if any]

## Suggested Review Order

**Cursor-move logic (application)**

- Entry point: `move_cursor_to` moves the cursor to an absolute position, reusing `attempt_move` for BREAK and `wall_between`/`break_wall` for PASS_THROUGH
  [`builder_session.py:new`]

- Border wall handling: cursor stays put, nothing broken, matching FR-2 invariant
  [`builder_session.py:new`]

**Adapter wiring (builder screen)**

- `_on_cell_clicked` gating: check active tool != marker tool AND no zone-drag in progress before moving cursor
  [`screen.py:new`]

- Pass the clicked `position` to the new cursor-move logic
  [`screen.py:new`]

**Tests: I/O matrix coverage**

- Cold click, no tool active — cursor moves if path open
- BREAK mode, click blocked by wall — cursor stays
- PASS_THROUGH mode, click across wall — wall breaks, cursor moves
- Click same cell as cursor — no-op
- Click during zone-drag — ignored
- Set Entry/Set Exit active — marker placement unchanged
- Save after cursor move — CSV unchanged

**Manual checks:**

- Click a cell with no tool active — cursor jumps to that cell
- In BREAK mode, click a cell behind a wall — cursor stays, wall unchanged
- In PASS_THROUGH mode, click across a wall — wall breaks, cursor moves through
- Click your own current cell — nothing happens
- While dragging a zone, clicking another cell — zone drag continues, cursor doesn't move
- With SET_ENTRY active, clicking a cell — marker placed, cursor unchanged
- Save the maze after navigation — CSV format intact