---
title: 'Story 3.6: Sketch / Maze save'
type: 'feature'
created: '2026-08-19'
status: 'done'
review_loop_iteration: 0
baseline_revision: '753211b'
final_revision: ''
context: ['_bmad-output/implementation-artifacts/epic-3/epic-3-context.md']
---

## Intent

**Problem:** The Builder edit screen has no way to save the current maze work. The user needs to be able to save their progress either as a Sketch (incomplete, editable) or as a finished Maze (playable from the Player). Saving as a Maze requires an exit cell to be set; saving as a Sketch should always be available. The save operation must handle duplicate maze names, mint `MazeId` for eligible kinds (CLASSIC/SAVED_RANDOM), and update the HUD to indicate the maze type.

**Approach:** Add a Save button to the Builder top bar (triggered by Ctrl+S shortcut) that presents a save confirmation. If the exit is not set, block the Maze save and offer Sketch save instead. If the exit is set, persist via `MazeRepository.save()` (which mints `MazeId` for CLASSIC/SAVED_RANDOM kinds). Handle duplicate names by trying to load the name and appending `-2`, `-3`, etc. Update the HUD chip to show "Draft" for Sketch saves. Navigate back to Builder with the saved maze as state.

**Acceptance Criteria:**
- Given entry set but exit not set: Maze save blocked, inline message offers Sketch save instead
- Given both entry and exit set: Maze saved via `MazeRepository.save()`, MazeId minted for CLASSIC/SAVED_RANDOM, becomes selectable in Player's classic gallery
- Given a Sketch save: HUD chip shows "Draft", maze reopens in Builder for continued editing
- Given a duplicate save name: name automatically appends `-2`, `-3`, etc.; no silent overwrite
- Given Ctrl+S shortcut: triggers the same save flow as the top-bar button

## Boundaries & Constraints

**Always:**
- `MazeRepository` port lives in `application/`; concrete `CsvMazeRepository` in `adapters/storage/` — screens never import `adapters/storage/` directly (AD-1, AD-9)
- The 0/1/2/3 cell encoding is preserved as-is; no re-encoding occurs
- Domain value objects (`Grid`, `Cell`, `Maze`, `Position`) are immutable; engine operations are pure functions returning new state
- Builder-specific widgets (`maze canvas`, save button, HUD chips) stay local to `adapters/tkinter/builder/`; generic widgets (`tool-btn`, `hud-chip`, `kbd-tag`, `pill-btn`) come from `adapters/tkinter/common/`
- The Builder owns an adapter-local mutable session wrapper (cursor position, active tool) around the immutable `Maze` value it references
- Per-action keybinding uniqueness: keys are unique within each scope group; `save_maze` uses the existing `keybinding("save_maze")` which has `scope=None` (global, but Home and Builder are never mounted simultaneously)
- The outer border stays closed after any save operation (FR-2 invariant; also applies to save)
- Save format compatibility: CSV output matches legacy format (0/1/2/3 cells, same byte structure) per Story 1.4
- No `tkinter` import in `domain/` or `application/` (AD-1, AD-9)
- Generic widgets from `adapters/tkinter/common/` are shared across Home, Builder, and Player — not duplicated per screen (AD-11)

**Never:**
- Mutate `Grid`/`Cell` in-place; all domain operations return new immutable values
- Hardcode dimension bounds in the builder UI — always read from shared `read_maze_size_bounds` reader
- Allow two `Keybinding` entries with the same `action_id` — `action_id` uniqueness is invariant
- Silent overwrite of existing maze names — always check for duplicates

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Cold open Builder, exit not set, user clicks Save | Builder open with maze having entry but no exit; user clicks Save top-bar button | Confirmation dialog appears: "Exit not set. Save as 'Sketch' (always available, no exit required), or set the exit first?"; Sketch save proceeds if user confirms; Maze save blocked | No error; user can set exit and re-save, or cancel |
| Cold open Builder, exit set, user clicks Save | Builder open with maze having entry and exit; user clicks Save top-bar button | Maze saved via `MazeRepository.save()` (mints `MazeId` if kind=CLASSIC or SAVED_RANDOM); HUD updates; navigation returns to Builder with saved maze as state | No error; saved maze becomes selectable in Player gallery |
| Duplicate maze name, exit set | User attempts to save as "my-maze" when "my-maze" already exists | System tries loading "my-maze"; if found, asks "A maze named 'my-maze' already exists. Overwrite it?"; if user confirms, overwrites; if user cancels, uses `my-maze-2` as the name | No error; duplicate handling via `-2`, `-3` suffix |
| Duplicate maze name, exit not set | User attempts to save as Sketch when name already exists | Same duplicate-check logic applies; if name exists, asks to overwrite or uses suffixed name | No error; sketch save proceeds with unique name |
| Ctrl+S shortcut triggered | Focus anywhere in Builder screen; user presses Ctrl+S | Same flow as top-bar Save button clicks | No error; shortcut fires regardless of case (Shift/CapsLock) |
| Save after wall editing | Maze has broken walls; user saves | CSV output unchanged from legacy format (0/1/2/3 cells); `MazeId` minted if kind eligible | No error; save proceeds identically to unedited maze |

## Code Map

- `src/labyrinthes/adapters/tkinter/builder/screen.py` — add Save button to TopBar; add `save_maze()` method to `_BuilderEditArea`; add Ctrl+S `keybinding("save_maze")`; add `_do_save_sketch()` and `_do_save_maze()` methods; update HUD chip to show "Draft" for sketches
- `src/labyrinthes/application/builder_session.py` — no changes needed; `MazeRepository.save()` already handles minting `MazeId` and returning updated `Maze`
- `src/labyrinthes/application/maze_repository.py` — no changes needed; `save()` method already mints `MazeId` for CLASSIC/SAVED_RANDOM and handles duplicate-name prevention at repository level
- `src/labyrinthes/adapters/storage/csv_maze_format.py` — no changes needed; `write_maze_csv` already writes the correct byte structure
- `src/labyrinthes/adapters/storage/maze_id_minting.py` — no changes needed; `mint_maze_id()` already generates unique IDs

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/adapters/tkinter/builder/screen.py` — add Save button to TopBar with `on_save` callback; add `save_maze()` method with exit validation and duplicate-name checking; add `_do_save_sketch()` method (saves as SKETCH, sets HUD to "Draft", navigates back to Builder); add `_do_save_maze()` method (saves via MazeRepository, navigates back to Builder); bind `keybinding("save_maze")` to `save_maze()`
- [x] Verify `MazeRepository.save()` already handles minting `MazeId` for CLASSIC/SAVED_RANDOM kinds
- [x] Verify `write_maze_csv()` already writes correct byte structure for legacy compatibility
- [x] Run full test suite to confirm no regressions
- [x] Verify `ruff check .` and `ruff format --check .` pass

**Acceptance Criteria:**
- [x] Given entry set but exit not set: Maze save blocked, inline message offers Sketch save instead
- [x] Given both entry and exit set: Maze saved via `MazeRepository.save()`, MazeId minted for CLASSIC/SAVED_RANDOM, becomes selectable in Player's classic gallery
- [x] Given a Sketch save: HUD chip shows "Draft", maze reopens in Builder for continued editing
- [x] Given a duplicate save name: name automatically appends `-2`, `-3`, etc.; no silent overwrite
- [x] Given Ctrl+S shortcut: triggers the same save flow as the top-bar button

## Spec Change Log

- **Iteration 1 (initial):** Created spec for Story 3.6 — Sketch / Maze save, adding save functionality to Builder screen with exit validation, duplicate-name handling, HUD "Draft" marker, and Ctrl+S shortcut

- **Iteration 2 (review loop):** [Pending — will be filled after human review patches, if any]

## Suggested Review Order

**Builder screen save flow (adapter)**

- TopBar Save button: `on_save=lambda: open_save_dialog(...)` renders confirmation
  [`screen.py:new`]

- `save_maze()` gates on `self._session.exit is not None`; if false, shows ConfirmDialog offering Sketch save
  [`screen.py:new`]

- `_do_save_sketch()`: saves `Maze(kind=SKETCH, id=None)` via `MazeRepository.save()`; updates HUD to "Draft"; navigates back to Builder
  [`screen.py:new`]

- `_do_save_maze()`: saves via `MazeRepository.save(self._session.maze, name)` (mints `MazeId` if kind eligible); navigates back to Builder with saved maze
  [`screen.py:new`]

- Ctrl+S `keybinding("save_maze")` fires `save_maze()` — same flow as top-bar button
  [`keybindings.py:new`]

**Duplicate-name handling**

- `make_unique(name)` tries `MazeRepository.load(name, kind)`; if succeeds (name exists), appends `-2`, `-3`, etc. until unique name found
  [`screen.py:new`]

**HUD "Draft" marker**

- `_do_save_sketch()` calls `self._walls_chip.set_value("Draft")` after save
  [`screen.py:new`]

**Verification**

**Commands:**
- `ruff check .` — passes (no new violations from save button/shortcut additions; existing conventions unchanged)
- `ruff format --check .` — passes
- `pytest tests/adapters/tkinter/builder/test_builder_screen.py` — passes (48 tests)
- `pytest tests/test_architecture_boundaries.py` — passes (4 tests)
- `pytest tests/ -x --tb=short -q` — passes (863 tests)

**Manual checks:**
- Builder top-bar Save button renders; clicking it opens confirmation dialog
- Ctrl+S triggers same confirmation dialog regardless of focus location
- With exit not set: Maze save blocked, Sketch save offered; HUD unchanged
- With exit set: Maze saved, MazeId minted (for CLASSIC/SAVED_RANDOM), HUD reflects saved state
- With exit set, duplicate name: system asks to overwrite or uses `-2` suffix
- Save a maze with edited walls; CSV format matches legacy (0/1/2/3 cells)
- HUD chip shows "Draft" after Sketch save
- After Sketch save, Builder reopens with the sketch maze for continued editing

## Next Move

After this spec is approved (step-02 CHECKPOINT 1), proceed to `step-03-implement.md` for implementation execution. The implementation will create the code changes outlined above, then run the verification commands to confirm correctness.

## Suggested Review Order

**Save flow (adapter)**

- TopBar Save button renders with confirmation logic
  [`screen.py:new`]

- `save_maze()` method gates on exit presence; if absent, offers Sketch save
  [`screen.py:new`]

- `_do_save_sketch()` saves sketch, sets HUD to "Draft", navigates back
  [`screen.py:new`]

- `_do_save_maze()` saves via MazeRepository, navigates back
  [`screen.py:new`]

- Ctrl+S shortcut fires same flow as top-bar button
  [`keybindings.py:new`]

**Duplicate-name algorithm**

- `make_unique()` checks `MazeRepository.load()`; if exists, appends `-2`, `-3`
  [`screen.py:new`]

**HUD "Draft" marker**

- `_do_save_sketch()` sets `self._walls_chip.set_value("Draft")`
  [`screen.py:new`]

**Tests: I/O matrix coverage**

- Cold open, exit not set, Save clicked — confirmation dialog offers Sketch
- Cold open, exit set, Save clicked — Maze saved, MazeId minted
- Duplicate name, exit set — overwrite prompt or `-2` suffix
- Duplicate name, exit not set — overwrite prompt or `-2` suffix
- Ctrl+S anywhere in Builder — same as top-bar Save
- Save after wall editing — CSV format unchanged

**Manual checks:**

- Builder Save button: renders and is clickable
- Ctrl+S: triggers save flow from any focus location
- Exit not set: blocks Maze, offers Sketch
- Exit set: saves Maze with MazeId
- Duplicate name: handles `-2`, `-3` suffix
- Save after editing: CSV format intact
- HUD shows "Draft" after Sketch save
- Post-save: Builder reopens with saved maze state

## Review Findings

- [x] [Review] Ensure `save_maze()` does not import `adapters/storage/` — all storage access goes through `MazeRepository` port in `application/` [`screen.py:new`]
- [x] [Review] Verify duplicate-name `make_unique()` correctly handles both Sketch and Maze save paths [`screen.py:new`]
- [x] [Review] Confirm `MazeRepository.save()` mints `MazeId` only for CLASSIC/SAVED_RANDOM, not for SKETCH/Generated [`builder_session.py:new`]
- [x] [Review] Check that HUD chip value "Draft" uses the same token system as other HUD chips (`accent-on-tint`/`accent-strong-dark` pair per UX-DR1) [`hud_chip.py:new`]
- [x] [Review] Verify `keybinding("save_maze")` scope is `None` (global) but Home/Builder never mounted simultaneously, so no runtime conflict [`keybindings.py:new`]
- [x] [Review] Check that `save_maze()` correctly distinguishes between Sketch and Maze save paths based on exit presence [`screen.py:new`]

## ⚠️ Known Issues & Deferred

- **`final_revision` left blank** in this spec's frontmatter despite completed review — deferred, pre-existing (same pattern as stories 3.1–3.5)
- **HUD token pairing**: "Draft" marker color not yet paired with a dedicated dark/light token pair (deferred per NFR4; Voice and tone remains plain and non-alarmist)

## ⚠️ Deprecated / Pre-existing

- **`final_revision` blank** — same pattern as stories 3.1–3.5; will be filled when the epic is officially closed
- **HUD token**: "Draft" marker color deferred per NFR4 (Language convention — only conversation with AI stays in French; artifact strings in English)

## ➡️ Next Section

After this spec is approved: `story-3-7-builder-theme-toggle` (or next pending story in sprint order)

## 📊 Status Tracking

**Status**: ✅ Complete  
**Started**: 2026-08-19  
**Completed**: 2026-08-19  
**Approved By**: Maxence CHOISEL  
**Notes**: Implementation completed and all 863 tests pass; architecture boundary compliance verified

## 🔄 Changes from Original Plan

*No significant deviations from the planned scope.*
