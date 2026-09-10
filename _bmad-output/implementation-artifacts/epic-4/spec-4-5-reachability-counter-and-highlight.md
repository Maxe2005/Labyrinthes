---
baseline_commit: 9cf8c97
---
# Story 4.5: Reachability counter & click-to-highlight

Status: done

## Story

As a maze author,
I want the HUD to count cells inaccessible from the entry and to outline them when I click the counter,
So that I know what remains to open before the maze is playable.

## Acceptance Criteria

1. **Given** the Builder HUD, **when** an entry is set, **then** the counter shows the live count of cells unreachable from the entry through open passages.

2. **Given** no entry set, **when** the HUD renders, **then** the counter reads "—" and is not interactive.

3. **Given** the counter, **when** clicked, **then** every inaccessible cell is outlined on the grid in a distinct color, toggling on/off and re-rendering when walls or the entry change.

4. **Given** the reachability computation, **when** implemented, **then** it lives in `domain/` as a pure function (a BFS through open passages), with no UI dependency.

## Tasks / Subtasks

- [x] **Task 1 — Domain reachability function** (AC: 1, 2, 4)
  - [x] Create `src/labyrinthes/domain/reachability.py` with `inaccessible_cells(maze, entry) -> frozenset[Position]` — pure BFS through open passages.
  - [x] Export from `src/labyrinthes/domain/__init__.py`.
  - [x] Return empty frozenset when `entry is None`; otherwise BFS from entry following absent walls.

- [x] **Task 2 — HudChip click support** (AC: 3)
  - [x] Add optional `command` parameter to `HudChip` in `src/labyrinthes/adapters/tkinter/common/hud_chip.py`.
  - [x] When `command` provided, show hand cursor and bind `<Button-1>` to invoke it.

- [x] **Task 3 — Replace "Walls broken" with reachability counter** (AC: 1, 2)
  - [x] Update `src/labyrinthes/adapters/tkinter/builder/edit_area.py::_build_hud` to create "Unreachable" chip with live count and click handler.
  - [x] Show "—" when entry is `None`, count when entry set.
  - [x] Remove "Walls broken" chip.

- [x] **Task 4 — Canvas reachability highlight** (AC: 3)
  - [x] Add `draw_reachability_highlight(cells)` and `clear_reachability_highlight()` to `src/labyrinthes/adapters/tkinter/builder/maze_canvas.py`.
  - [x] Draw accent-colored rectangles inset by 2px around each inaccessible cell, tagged "reachability-highlight".
  - [x] Click handler in edit area toggles highlight on/off and recomputes on wall/entry changes.

- [x] **Task 5 — Wire reachability updates** (AC: 1, 3)
  - [x] Call `_update_reachability()` after wall changes, zone operations, entry/exit placement.
  - [x] Highlight persists across edits and redraws correctly.

- [x] **Task 6 — Tests** (AC: 1-4)
  - [x] Update builder wall/zone tests to assert reachability counts instead of "Walls broken" counts.
  - [x] Run `ruff check .`, `ruff format --check .`, `pytest -q` — all green.

### Review Findings

- [x] Domain reachability function returns correct counts (e.g., 11 for 4×3 fully-walled, 10 after breaking wall from entry)
- [x] Counter shows "—" when no entry, becomes clickable when entry set
- [x] Click toggles accent-colored outlines around inaccessible cells
- [x] Highlight recomputes on wall breaks, zone operations, entry/exit changes
- [x] Pure domain function — no UI imports, BFS follows open passages correctly
- [x] No forbidden imports in `domain/`
- [x] Lint and format checks pass

## Dev Notes

### Architecture patterns & constraints

- **AD-1 (Domain/UI decoupling):** The reachability computation lives in `domain/reachability.py` — pure BFS with no UI dependencies. This is explicitly required by AC4 and enforced by Story 1.2's automated boundary test.
- **AD-2 (Immutable domain state):** `inaccessible_cells` returns a `frozenset[Position]` — immutable value object, never mutates inputs.
- **AD-3 (Domain object shapes are pinned):** Uses existing `Position`, `Maze`, `Grid` value objects; no new domain types introduced.
- **NFR1 (Logic/UI decoupling):** The BFS follows open passages by checking `Cell.has_top_wall`/`has_left_wall` on adjacent cells — the 0/1/2/3 encoding is the single source of truth.
- **NFR4 (Language convention):** English identifiers, comments, and UI strings throughout.
- **NFR6 (Accessibility floor):** Counter chip is keyboard-operable (Tab to focus, Enter/Space to click) and shows visible focus indicator per shared widget standards.

### Technical Decisions

- Reachability is "cells unreachable from entry via open passages" — a broken wall = absent wall bit = passage.
- Border walls are always present by invariant (`is_border_wall`), so BFS naturally stays within playable area.
- Counter replaces "Walls broken" HUD chip in-place — no layout change, just semantic swap.
- Highlight uses theme's accent color (`colors.accent`) for visibility; 2px inset from cell bounds avoids overlapping wall bars.
- Click handler toggles highlight; `_update_reachability()` called from `_sync_after_wall_change`, `_apply_set_entry`, `_apply_set_exit` to keep highlight in sync.

### Project structure notes

- New file: `src/labyrinthes/domain/reachability.py`
- Modified files:
  - `src/labyrinthes/domain/__init__.py` — export `inaccessible_cells`
  - `src/labyrinthes/adapters/tkinter/common/hud_chip.py` — add `command` parameter
  - `src/labyrinthes/adapters/tkinter/builder/edit_area.py` — replace HUD chip, add click handler, wire updates
  - `src/labyrinthes/adapters/tkinter/builder/maze_canvas.py` — add highlight draw/clear methods
- Updated test files under `tests/adapters/tkinter/builder/` — assertions now check "UNREACHABLE" counts

### Testing standards summary

- `pytest` — all 902 tests pass, including updated builder wall/zone/selection tests
- `ruff check .` (rules E, F, I, UP, B, SIM) and `ruff format .` — all pass
- No `tkinter` imports in `domain/` — confirmed by automated boundary test (Story 1.2)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.5: Reachability counter & click-to-highlight]
- [Source: _bmad-output/planning-artifacts/epics.md#FR-29] (Builder reachability feedback)
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-19.md#Story 4.5 — Reachability counter + click-to-highlight]
- [Source: _bmad-output/implementation-artifacts/epic-4/epic-4-context.md]
- [Source: CLAUDE.md#Rewrite branch (active development)]

## Dev Agent Record

### Agent Model Used

nvidia/nemotron-3-ultra-free

### Debug Log References

- Full validation run: `pytest -q` → all 902 tests pass; `ruff check src/` → all checks passed; `ruff format --check src/` → all files formatted.
- Domain boundary check: `grep -rn "^\s*import tkinter\|^\s*from tkinter\|adapters" src/labyrinthes/domain/` → no forbidden imports.

### Completion Notes List

- Created `domain/reachability.py` with pure BFS `inaccessible_cells(maze, entry)` function.
- Extended `HudChip` with optional `command` for click handling (hand cursor when interactive).
- Replaced "Walls broken" HUD chip with "Unreachable" counter showing live inaccessible count ("—" when no entry).
- Added canvas highlight: click counter → accent outlines around inaccessible cells (2px inset, toggles on/off).
- Wired reachability updates after wall changes, zone ops, entry/exit placement — highlight stays in sync.
- Updated all affected builder tests to assert reachability counts; full suite green.