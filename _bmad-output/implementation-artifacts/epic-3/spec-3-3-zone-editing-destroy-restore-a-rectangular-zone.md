---
title: 'Story 3.3: Zone editing — destroy/restore a rectangular zone'
type: 'feature'
created: '2026-08-18'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'a93dae5c0f1cceb81c4dd57b2615938d49982d15'
context: ['_bmad-output/implementation-artifacts/epic-3/epic-3-context.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Builder can only break/restore one wall at a time (Story 3.2); there is no way to clear or rebuild a larger rectangular area in a single operation, which the Builder end-to-end (Epic 3, FR-2) requires.

**Approach:** Add pure domain functions `destroy_zone`/`restore_zone` in a new `domain/zone_editing.py`, batching `wall_editing.break_wall`/`restore_wall` over every interior wall spanned by two corner cells; extend `BuilderSession`/`BuilderTool` with `DESTROY_ZONE`/`RESTORE_ZONE` and an `apply_zone_operation` dispatcher; wire click-and-drag detection (press/release cell comparison, no new pixel-threshold constant) into the Builder canvas, plus two new mutually-exclusive tool buttons and `d`/`r` keybindings.

## Boundaries & Constraints

**Always:**
- `destroy_zone`/`restore_zone` are pure, return new immutable `Grid` values (never mutate in place), matching `wall_editing.py`'s pattern
- Border walls inside a zone's span are always silently skipped, never raised — the closed-border invariant wins for batch operations without aborting the whole zone on a span touching the grid edge (unlike single-wall `break_wall`/`restore_wall`, which raise for a directly-targeted border wall)
- The click-vs-drag split is decided purely by comparing the press cell to the release cell (both cell-quantized via `_pixel_to_cell`) — a release on the same cell as the press is never a zone operation, with no separate pixel-distance threshold
- `BuilderTool` gains `DESTROY_ZONE`/`RESTORE_ZONE`; exactly one tool is active at a time (same single-`tool`-field session design as Story 3.2), and all four tool buttons (Break Wall, Pass-through, Destroy Zone, Restore Zone) share one `ToolButtonGroup`
- No `tkinter` import in `domain/`/`application/` (AD-1, AD-9); zone rendering/input wiring stays local to `adapters/tkinter/builder/`

**Ask First:**
- Any new token or color usage for the zone tool buttons or drag interaction

**Never:**
- No live rubber-band/preview rectangle drawn while dragging — out of scope; the operation applies atomically only on release
- `destroy_zone`/`restore_zone` never raise `DomainValidationError` for a border wall inside their span — only the single-wall functions they wrap do that

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Destroy Zone active, drag across cells | Press at cell (1,1), release at cell (2,3) | Every interior wall in the rectangle spanning those two cells breaks in one operation; HUD "Walls broken" updates once | N/A |
| Restore Zone active, drag over a just-destroyed zone | Same corner cells as the prior destroy | Every interior wall in that rectangle is set back to present; grid matches its pre-destroy state exactly (AC2) | N/A |
| Zone tool active, press and release on the same cell | Start cell == end cell (no drag) | No zone operation applied; grid unchanged | Ignored — not a distinct gesture from a single click |
| Zone tool active, dragged rectangle touches the grid's outer edge | Span includes row 0 / col 0 / last row / last col | Border walls within the span are skipped; only interior walls inside the rectangle change; outer contour stays closed (AC3) | Border walls silently excluded, never raised |
| Break mode active, click-and-drag on a wall segment | Press/release with `tool=BREAK` | Story 3.2's single-click wall toggle only; the drag itself is ignored since zone dispatch gates on `DESTROY_ZONE`/`RESTORE_ZONE` | N/A |

</frozen-after-approval>

## Code Map

- `src/labyrinthes/domain/zone_editing.py` (new) — `destroy_zone(grid, corner_a, corner_b) -> Grid`, `restore_zone(grid, corner_a, corner_b) -> Grid`; private `_walls_in_zone(grid, corner_a, corner_b)` generator normalizes the two corners (order-independent) and yields every `Wall` in the span, skipping border ones via `level_visibility.is_border_wall`
- `src/labyrinthes/application/builder_session.py` — `BuilderTool` gains `DESTROY_ZONE = "destroy-zone"`, `RESTORE_ZONE = "restore-zone"`; new `apply_zone_operation(session, corner_a, corner_b) -> BuilderSession` dispatches to `destroy_zone`/`restore_zone` per `session.tool`, cursor unchanged (mirrors `apply_wall_toggle` at [`builder_session.py:81`](../../../src/labyrinthes/application/builder_session.py#L81))
- `src/labyrinthes/adapters/tkinter/builder/screen.py` — `_BuilderMazeCanvas`: add `_pixel_to_cell(x, y) -> Position` (clamped to grid bounds, stored `_grid_width`/`_grid_height` at init); `_on_click` (bound to `<Button-1>`, [`screen.py:383`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L383)) also records `_drag_anchor`; new `<ButtonRelease-1>` → `_on_release` fires `on_zone_dragged(anchor, end)` only when `end != anchor`. `_BuilderEditArea`: two new `ToolButton`s in the existing `group` ([`screen.py:185`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L185)); `_activate_destroy_zone`/`_activate_restore_zone`; `_on_zone_dragged` gates on `session.tool` being a zone tool, calls `apply_zone_operation` + `_sync_after_wall_change` ([`screen.py:273`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L273)); two new `bind_shortcut` registrations
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` — add `Keybinding("destroy_zone", "Destroy Zone", "d", ScreenId.BUILDER)` and `Keybinding("restore_zone", "Restore Zone", "r", ScreenId.BUILDER)` to `KEYBINDINGS` ([`keybindings.py:81`](../../../src/labyrinthes/adapters/tkinter/common/keybindings.py#L81))
- `tests/domain/test_zone_editing.py` (new) — mirrors `test_wall_editing.py`'s style
- `tests/adapters/tkinter/builder/test_builder_screen.py` — add a drag helper alongside `_click_wall` ([`test_builder_screen.py:46`](../../../tests/adapters/tkinter/builder/test_builder_screen.py#L46))

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/domain/zone_editing.py` — add `destroy_zone`, `restore_zone`, `_walls_in_zone`, reusing `wall_editing.break_wall`/`restore_wall` per non-border wall rather than duplicating the bit-twiddle
- [x] `src/labyrinthes/application/builder_session.py` — extend `BuilderTool`; add `apply_zone_operation` (patched post-review to take `tool` as an explicit argument rather than reading `session.tool`, closing a mid-drag tool-switch bug — see Suggested Review Order)
- [x] `src/labyrinthes/adapters/tkinter/common/keybindings.py` — add `destroy_zone` ("d") / `restore_zone` ("r") entries, `scope=ScreenId.BUILDER`
- [x] `src/labyrinthes/adapters/tkinter/builder/screen.py` — `_pixel_to_cell`, drag-anchor tracking, `<ButtonRelease-1>` binding, two new `ToolButton`s + activation handlers + `_on_zone_dragged` + keybinding registrations (patched post-review to capture the active tool at press time and clear drag state on release)
- [x] `tests/domain/test_zone_editing.py` — cover destroy/restore over a rectangle, border-skip at grid edges, destroy-then-restore round trip (AC2), corner-order independence, single-row/single-column spans
- [x] `tests/adapters/tkinter/builder/test_builder_screen.py` — cover: drag destroys/restores a zone in one operation (AC1), same-cell press/release is a no-op, Break-mode drag doesn't trigger a zone op, `d`/`r` keybinding activation, mid-drag tool-switch regressions, stray-release safety
- [x] `tests/application/test_builder_session.py` (new) — direct unit coverage for `apply_zone_operation`'s three branches, cursor stability, non-mutation

**Acceptance Criteria:**
- [x] AC1: Given Destroy Zone or Restore Zone active, when a click-and-drag across multiple wall segments is released, then the dragged rectangular zone is destroyed/restored as one operation — never triggered by a same-cell (non-dragging) click
- [x] AC2: Given a zone just destroyed, when the same rectangle is immediately restored, then every interior wall in it returns exactly to its initial (present) state
- [x] AC3: Given any zone operation, when it completes, then the maze's outer border stays closed

## Spec Change Log

## Design Notes

- **Wall span**: for corners normalized to `(r0, c0)`–`(r1, c1)` (inclusive, row0/col0 ≤ row1/col1), "top" walls run `row in [r0, r1+1]`, `col in [c0, c1]`; "left" walls run `row in [r0, r1]`, `col in [c0, c1+1]` — the same indexing convention `count_broken_walls` already uses, just bounded to the span instead of the whole grid.
- **Skip vs. raise**: `_walls_in_zone` checks `is_border_wall` and skips rather than calling `break_wall`/`restore_wall` (which would raise) so a zone touching the grid's edge — the common case — still processes every interior wall in one pass instead of aborting.
- **Round trip**: `destroy_zone` then `restore_zone` on the identical corners sets every wall in the span back to present, which is exactly a fresh sketch's baseline (`Grid.filled`) — satisfying AC2 without tracking any drag history.

## Verification

**Commands:**
- `ruff check .` — passes
- `ruff format --check .` — passes
- `pytest tests/domain/test_zone_editing.py` — passes
- `pytest tests/adapters/tkinter/builder/test_builder_screen.py` — passes
- `pytest tests/adapters/tkinter/common/test_keybindings.py` — passes with the two new BUILDER-scope entries

**Manual checks:**
- Destroy Zone: drag across several cells, release — all interior walls in the rectangle break in one visible update
- Restore Zone: drag the same rectangle just destroyed — walls return to present, matching the original fully-walled state
- Pressing and releasing on the same cell while a zone tool is active does nothing
- Dragging a zone that touches the grid's outer edge leaves the border closed
- Keybindings 'd'/'r' activate the respective tool on the Builder screen only

## Next Move

After this spec is approved (step-02 CHECKPOINT 1), proceed to `step-03-implement.md` for implementation execution.

## Suggested Review Order

**Zone span math (domain)**

- Entry point: normalizes the two drag corners and yields every non-border wall in the span.
  [`zone_editing.py:30`](../../../src/labyrinthes/domain/zone_editing.py#L30)

- Batches the single-wall mutator per wall in the span rather than duplicating the bit-twiddle.
  [`zone_editing.py:56`](../../../src/labyrinthes/domain/zone_editing.py#L56)

- Mirror operation restoring the identical span — the round trip AC2 depends on.
  [`zone_editing.py:67`](../../../src/labyrinthes/domain/zone_editing.py#L67)

**Mid-drag tool-switch fix (application)**

- Dispatch now takes `tool` as an explicit argument instead of trusting a live `session.tool` re-read at release time — closes the review-found bug where switching tools mid-drag could compound a press-time wall toggle with a release-time zone op under a different tool.
  [`builder_session.py:108`](../../../src/labyrinthes/application/builder_session.py#L108)

**Drag detection and tool capture (adapter)**

- Press: quantizes the click to a cell and snapshots the active tool for the whole gesture, not just the click itself.
  [`screen.py:465`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L465)

- Release: consumes and clears both the anchor and the captured tool so a stray release can't replay a stale drag; fires only on a genuine cell-to-cell move.
  [`screen.py:480`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L480)

- Screen-level gate: dispatches on the press-time-captured tool, never a live session read.
  [`screen.py:318`](../../../src/labyrinthes/adapters/tkinter/builder/screen.py#L318)

**Keybinding registration**

- New `d`/`r` BUILDER-scoped shortcuts, mirroring `break_wall`/`pass_through`'s existing entries.
  [`keybindings.py:102`](../../../src/labyrinthes/adapters/tkinter/common/keybindings.py#L102)

**Peripherals**

- Single-row/single-column span coverage added for `_walls_in_zone`'s asymmetric range math.
  [`test_zone_editing.py:135`](../../../tests/domain/test_zone_editing.py#L135)

- Drag-simulation helper reused across every adapter-level zone test.
  [`test_builder_screen.py:69`](../../../tests/adapters/tkinter/builder/test_builder_screen.py#L69)

- Regression coverage pinning the mid-drag tool-switch fix, both directions.
  [`test_builder_screen.py:762`](../../../tests/adapters/tkinter/builder/test_builder_screen.py#L762)

- Direct unit coverage for `apply_zone_operation`'s three branches, previously untested at this layer.
  [`test_builder_session.py:30`](../../../tests/application/test_builder_session.py#L30)
