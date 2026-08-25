---
title: 'Story 4.4: Entry/exit live placement — ghost follows cursor, place on click or Enter'
type: 'feature'
created: '2026-08-25'
status: 'done'
review_loop_iteration: 0
baseline_commit: fdf8f7f2448a89263fc5114f4dbd66313b0bc683
context:
  - _bmad-output/implementation-artifacts/epic-4/epic-4-context.md
  - _bmad-output/planning-artifacts/epics.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Builder's Set Entry and Set Exit tools currently place markers only on a same-cell click (press+release on the same cell). There is no live ghost preview for Set Entry, and Set Exit's ghost is a dashed-? outline rather than a true marker preview. Placement requires a click; the Enter key is not bound for keyboard-only placement. Additionally, the exit marker is currently restricted to border cells only, but the requirement has changed: the exit should be placeable anywhere in the maze (except on the entry cell).

**Approach:** Add live ghost previews for both Set Entry (filled square in entry color, follows cursor on any cell) and Set Exit (filled diamond in exit color, follows cursor on any cell except the entry). Wire both mouse click and the Enter key to place the marker, honoring the existing redefinition confirmation prompt. Register the Enter keybinding in the canonical table. Remove the border-cell restriction from exit placement in the application layer.

## Boundaries & Constraints

**Always:**
- AD-1 (Domain/UI decoupling): `domain/` imports nothing from `adapters/` or any UI framework — ghost rendering lives in `adapters/tkinter/builder/maze_canvas.py`.
- AD-3 (Domain object shapes are pinned): `apply_set_entry`/`apply_set_exit` in `application/builder_session.py` remain the single placement logic; the adapter only drives when to call them. **The border-cell check in `apply_set_exit` must be removed** to allow exit placement anywhere except the entry.
- NFR4 (Language convention): English identifiers and comments throughout.
- NFR6 (Accessibility floor): The Enter key placement is a keyboard shortcut; it must be registered in the canonical keybinding table (Story 1.10) so the collision test catches any conflicts.
- The existing redefinition confirmation flow (`_maybe_confirm` + `read_confirm_redefine_marker`) is reused unchanged.

**Ask First:**
- Whether the Set Entry ghost should use the same dashed-? style as the current Set Exit ghost, or a filled square matching the entry marker shape (preference: filled square, matching the marker).
- Whether the Set Exit ghost should change from the current dashed-? to a filled diamond matching the exit marker shape (preference: filled diamond, matching the marker).

**Never:**
- Add a new keybinding action for "place marker" if one already exists (check canonical table first).
- Break the existing same-cell click placement — it must remain fully functional alongside the new Enter placement.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| HAPPY_PATH_ENTRY_GHOST | Set Entry active, cursor moves to (2,3) | Ghost filled square at (2,3) in entry color, updates live | N/A |
| HAPPY_PATH_EXIT_GHOST | Set Exit active, cursor moves to (2,3) (not entry) | Ghost filled diamond at (2,3) in exit color, updates live | N/A |
| HAPPY_PATH_EXIT_GHOST_ON_ENTRY | Set Exit active, cursor moves to entry cell | No ghost shown (cannot place exit on entry) | N/A |
| HAPPY_PATH_ENTRY_CLICK | Set Entry active, click (2,3) | Entry marker placed at (2,3), ghost removed | If redefining, ConfirmDialog gates |
| HAPPY_PATH_EXIT_CLICK | Set Exit active, click (2,3) (not entry) | Exit marker placed at (2,3), ghost removed | If redefining, ConfirmDialog gates |
| HAPPY_PATH_ENTRY_ENTER | Set Entry active, cursor at (2,3), press Enter | Entry marker placed at (2,3), ghost removed | If redefining, ConfirmDialog gates |
| HAPPY_PATH_EXIT_ENTER | Set Exit active, cursor at (2,3) (not entry), press Enter | Exit marker placed at (2,3), ghost removed | If redefining, ConfirmDialog gates |
| ENTER_ON_ENTRY_EXIT | Set Exit active, cursor on entry cell, press Enter | No-op (silent) | N/A |
| TOOL_SWITCH_CLEARS_GHOST | Set Entry active with ghost at (2,3), switch to Break tool | Ghost removed immediately | N/A |
| MARKER_OVERLAP_CLICK | Set Entry active, click cell holding exit | No-op (silent, mirrors `_place_entry` guard) | N/A |
| MARKER_OVERLAP_ENTER | Set Entry active, cursor on exit cell, press Enter | No-op (silent) | N/A |

</frozen-after-approval>

## Code Map

- `src/labyrinthes/adapters/tkinter/builder/maze_canvas.py` -- Main rendering: add `_draw_entry_ghost` (filled square) and `_draw_exit_ghost` (filled diamond); modify `refresh_markers` to accept and render entry/exit ghosts; add `_clear_ghosts`.
- `src/labyrinthes/adapters/tkinter/builder/edit_area.py` -- Wire ghost updates: `_sync_markers` computes ghost positions per active tool and calls `canvas.refresh_markers`; bind Enter key via `bind_shortcut` to new `_place_marker_at_cursor` method; add `place_marker` keybinding to canonical table.
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- Add `place_marker` keybinding with key "Return" and scope `ScreenId.BUILDER`.
- `src/labyrinthes/application/builder_session.py` -- Modify `apply_set_exit`: remove the `is_border_cell` guard so exit can be placed on any cell except the entry. The collision check with `session.entry` remains.
- `tests/adapters/tkinter/builder/test_builder_screen.py` -- Add tests for: entry ghost follows cursor, exit ghost follows cursor (border only), click placement, Enter placement, redefinition confirmation honored, tool switch clears ghost.

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- Add `place_marker` keybinding (Return, BUILDER scope) to canonical table
- [x] `src/labyrinthes/adapters/tkinter/builder/maze_canvas.py` -- Add `_draw_entry_ghost` (filled square, entry color), `_draw_exit_ghost` (filled diamond, exit color), modify `refresh_markers` to render ghosts
- [x] `src/labyrinthes/adapters/tkinter/builder/edit_area.py` -- Add `place_marker` keybinding bind; `_sync_markers` computes entry/exit ghost per tool (exit ghost on any cell except entry); `_place_marker_at_cursor` delegates to `_place_entry`/`_place_exit`; tool switch clears ghosts
- [x] `src/labyrinthes/application/builder_session.py` -- Remove `is_border_cell` check in `apply_set_exit`; keep entry-collision guard
- [x] `tests/adapters/tkinter/builder/test_builder_marker_placement.py` -- Updated tests for ghost rendering (filled shapes), click/Enter placement, confirmation gating, tool-switch ghost clearing, exit placement on interior cells

**Acceptance Criteria:**
- Given Set Entry active, when cursor moves, then a filled square ghost in entry color follows the cursor on any cell in real time
- Given Set Exit active, when cursor moves on any cell except the entry, then a filled diamond ghost in exit color follows the cursor
- Given Set Exit active, when cursor moves on the entry cell, then no ghost is shown
- Given either tool active, when a cell is clicked (not the other marker's cell), then the marker is placed (honoring redefinition confirmation)
- Given either tool active, when Enter is pressed (cursor not on the other marker's cell), then the marker is placed at the cursor cell (honoring redefinition confirmation)
- Given a marker is placed via Enter, then the ghost is removed and the marker renders normally
- Given a tool switch away from Set Entry/Set Exit, then any active ghost is cleared immediately
- Given Set Exit active, when clicking or pressing Enter on an interior cell (not entry), then the exit marker is placed there (no border restriction)

## Spec Change Log

## Design Notes

The ghost preview reuses the existing `refresh_markers` redraw seam — `_BuilderEditArea._sync_markers` already drives marker/ghost updates on every cursor move and tool switch. The entry ghost is a filled square (matching the entry marker shape, not the current dashed-? style) in `colors.entry`; the exit ghost is a filled diamond (matching the exit marker shape) in `colors.exit`. Both are drawn with the same `_MARKER_SCALE` radius as the real markers so they overlay perfectly on placement. The exit ghost appears on any cell except the entry cell (the entry-collision guard is enforced in `apply_set_exit` and mirrored in the ghost logic).

The Enter keybinding is registered in the canonical table as `place_marker` with key "Return" and `ScreenId.BUILDER` scope — the same handler (`_place_marker_at_cursor`) handles both click and Enter by delegating to the existing `_place_entry`/`_place_exit` methods.

**Exit placement anywhere:** The `is_border_cell` guard in `application/builder_session.py::apply_set_exit` is removed. The only remaining validation is the entry-collision check (exit cannot be placed on the entry cell). This change is purely in the application layer; the adapter's ghost logic mirrors this by showing the exit ghost on all cells except the entry.

## Verification

**Commands:**
- `ruff check src/labyrinthes/adapters/tkinter/builder/ src/labyrinthes/adapters/tkinter/common/keybindings.py tests/adapters/tkinter/builder/`
- `ruff format --check src/labyrinthes/adapters/tkinter/builder/ src/labyrinthes/adapters/tkinter/common/keybindings.py tests/adapters/tkinter/builder/`
- `pytest tests/adapters/tkinter/builder/test_builder_screen.py -v`

**Manual checks (if no CLI):**
- Open Builder, select Set Entry tool, move cursor — verify filled square ghost follows on every cell
- Select Set Exit tool, move cursor on any cell except entry — verify filled diamond ghost follows; move to entry cell — verify no ghost
- Click a cell with Set Entry active — verify entry marker placed, ghost removed
- Press Enter with Set Entry active — verify entry marker placed at cursor, ghost removed
- Click an interior cell with Set Exit active — verify exit marker placed there (no border restriction)
- Press Enter with Set Exit active on interior cell — verify exit marker placed at cursor
- Redefine an existing marker — verify ConfirmDialog appears (when setting enabled)
- Switch from Set Entry to Break tool — verify ghost cleared immediately