---
baseline_commit: 9cf8c97
---
# Story 4.2: Wall-tool semantics — Break vs Pass-through + Space toggle

Status: done

## Story

As a maze author,
I want Break mode to break walls as the cursor moves across them (the former Pass-through behavior) and toggle on click, and Pass-through mode to move through walls freely without modifying them,
So that the tool names match their behavior and the space key toggles between them.

## Acceptance Criteria

1. **Given** Break mode is active, **when** the cursor moves into a cell across an interior wall, **then** that wall is broken and the cursor enters the target cell.

2. **Given** Break mode is active, **when** the user clicks an interior wall segment, **then** that wall is toggled (broken if present, restored if absent) and the cursor does not move.

3. **Given** Pass-through mode is active, **when** the cursor moves into a cell across an interior wall, **then** the wall is ignored and the cursor enters the target cell without breaking anything.

4. **Given** Pass-through mode is active, **when** the cursor attempts to cross a border wall, **then** the cursor stays in place (closed-border invariant).

5. **Given** either mode, **when** the user presses `Space`, **then** the mode toggles between Break and Pass-through.

6. **Given** the Builder screen, **when** rendered, **then** the tooltips for Break and Pass-through reflect the new semantics.

## Tasks / Subtasks

- [x] **Task 1 — Swap wall-breaking behavior in `move_cursor`** (AC: 1, 3)
  - [x] Modify `src/labyrinthes/application/builder_session.py::move_cursor` so BREAK mode breaks walls on movement (current PASS_THROUGH behavior) and PASS_THROUGH mode moves freely without breaking walls (new behavior).

- [x] **Task 2 — Add Space toggle keybinding** (AC: 5)
  - [x] Add `toggle_break_pass_through` keybinding with key "space" and scope `ScreenId.BUILDER` to `src/labyrinthes/adapters/tkinter/common/keybindings.py`.

- [x] **Task 3 — Wire Space toggle in Builder screen** (AC: 5)
  - [x] Add `_toggle_break_pass_through` method in `src/labyrinthes/adapters/tkinter/builder/screen.py` that switches between BREAK and PASS_THROUGH tools.
  - [x] Register the keybinding in `_BuilderEditArea.__init__`.

- [x] **Task 4 — Update tooltips** (AC: 6)
  - [x] Update Break tool tooltip to "Moving the cursor across a wall breaks it"
  - [x] Update Pass-through tool tooltip to "Moving the cursor crosses walls freely"

- [x] **Task 5 — Tests** (AC: 1-6)
  - [x] Update tests in `tests/adapters/tkinter/builder/test_builder_screen.py` for the new move_cursor semantics.
  - [x] Run `ruff check .`, `ruff format --check .`, `pytest -q` — all green.

### Review Findings

- [x] Break mode breaks walls on cursor movement
- [x] Pass-through mode moves freely without breaking walls
- [x] Space key toggles between Break and Pass-through
- [x] Tooltips reflect correct semantics
- [x] Closed-border invariant holds in both modes
- [x] No forbidden imports in `domain/`
- [x] Lint and format checks pass

## Dev Notes

### Architecture patterns & constraints

- **AD-1 (Domain/UI decoupling):** `domain/` imports nothing from `adapters/` or any UI framework — wall-breaking logic lives in `application/builder_session.py`, not `domain/`. The `domain.wall_editing.break_wall` function is used by the application layer.
- **AD-3 (Domain object shapes are pinned):** `move_cursor` returns a new `BuilderSession` with updated `cursor` and possibly `maze.grid` — no mutation.
- **NFR4 (Language convention):** English identifiers and comments throughout.
- **NFR6 (Accessibility floor):** The Space toggle is a keyboard shortcut; it must be registered in the canonical keybinding table (Story 1.10) so the collision test catches any conflicts.

### Technical Decisions (from epic-4-context.md)

- Wall-tool semantics change lives in `application/builder_session.py::move_cursor` (pure logic); no data-model change, wall encoding `0/1/2/3` untouched.
- Keybindings added to the one canonical table (Story 1.10): `toggle_break_pass_through` (Space) — the collision/label-consistency test must stay green.
- `space` toggles the two tools, registered in the canonical keybinding table.

### Project structure notes

- Modified files:
  - `src/labyrinthes/application/builder_session.py` — `move_cursor` logic swap
  - `src/labyrinthes/adapters/tkinter/common/keybindings.py` — add `toggle_break_pass_through` keybinding
  - `src/labyrinthes/adapters/tkinter/builder/screen.py` — wire Space toggle, update tooltips
- No `domain/` changes
- Updated test files under `tests/adapters/tkinter/builder/`

### Testing standards summary

- `pytest`, tests verifying `move_cursor` behavior for both tools and Space toggle wiring
- `ruff check .` (rules E, F, I, UP, B, SIM) and `ruff format .` must both pass
- No `tkinter` imports in `domain/` or its tests — confirmed by automated boundary test (Story 1.2)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.2: Wall-tool semantics — Break vs Pass-through + Space toggle]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4 amendments] (FR-1 refinements tracked in Epic 4's stories)
- [Source: _bmad-output/implementation-artifacts/epic-4/epic-4-context.md#Technical Decisions]
- [Source: CLAUDE.md#Rewrite branch (active development)]

## Dev Agent Record

### Agent Model Used

nvidia/nemotron-3-ultra-free

### Debug Log References

- Full validation run: `pytest -q` → all 882 tests pass; `ruff check src/ tests/` → all checks passed; `ruff format --check src/ tests/` → all files formatted.

### Completion Notes List

- Swapped Break and Pass-through movement semantics in `move_cursor`: Break now breaks walls on cursor movement (former Pass-through behavior), Pass-through now moves freely without breaking walls (former Break behavior).
- Added `toggle_break_pass_through` keybinding (Space) to canonical keybinding table with `ScreenId.BUILDER` scope.
- Wired Space toggle in Builder screen via `_toggle_break_pass_through` method.
- Updated tooltips to reflect new semantics.
- Updated existing tests to match new behavior.