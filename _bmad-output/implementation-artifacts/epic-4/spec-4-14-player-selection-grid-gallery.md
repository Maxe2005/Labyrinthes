---
title: 'Story 4.14: Player selection screen — grid gallery split into Classic / Creations / Random'
type: 'feature'
created: '2026-09-10'
status: 'done'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-4/epic-4-context.md
baseline_commit: ad6fc4b1aec68470da0044db2716dec91f9fb2fd
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Player's maze-selection screen (`ClassicMazeGallery`) is still a one-item-at-a-time pager (Previous/Next/Restart/jump-to-number) over a flat classic-then-saved-random list — a Story 2.1 descope made only because no wall-rendering component existed yet to draw thumbnails from. That blocker is gone (`maze_canvas.py` since Epic 3), `MazeKind.CREATION` now exists (Story 4.11) but is browsable nowhere in Player, and the locked mockup (`key-player-selection.html`) has always specified a 4-column card grid.

**Approach:** Rebuild the widget (renamed `MazeSelectionGallery`) as one scrollable card grid with three independently-populated, labeled sections — Classic, Creations, Random (`SAVED_RANDOM`) — each card showing a small wall/entry/exit thumbnail reused from `MazeCanvas`'s own drawing routines, name, and dimensions. "Generate random" stays a separate action below the grid, unchanged. Clicking/activating a card loads and navigates exactly like the old "Play" button did. Previous/Next/Restart/jump and their Story 2.10 confirm-gating (`confirm_switch_maze`/`confirm_invalid_input`) have no equivalent in a grid — they're deleted, not ported; the two now-orphaned settings are left in place (deferred cleanup) rather than removed here.

## Boundaries & Constraints

**Always:**
- `MazeSelectionGallery` (renamed from `ClassicMazeGallery`, `player/maze_selection_gallery.py`) replaces the pager wholesale — no Previous/Next/Restart/jump-to-number UI survives.
- Three sections, each via `build_group_heading` (Story 4.10) + a card row, populated independently from `maze_repository.list_names(MazeKind.CLASSIC / CREATION / SAVED_RANDOM)`; an empty section shows its own inline empty-state message, sibling sections unaffected.
- Every listed maze is loaded (`maze_repository.load(name, kind)`) and rendered as a `MazeCard` (thumbnail + name + `W×H`) inside a new shared `common/scrollable_frame.py::ScrollableFrame`. Every card is `takefocus=True`, follows `IconButton`'s existing focus-ring recipe (`<Return>`/`<space>` activation, `<FocusIn>`/`<FocusOut>` ring toggle via `RESTING_RING_THICKNESS`/`FOCUS_RING_THICKNESS`), and `ScrollableFrame` auto-scrolls a focused card into view on `<FocusIn>`.
- Clicking or activating a card calls `navigate(ScreenId.PLAYER, maze)` — the same commit path `_on_play` used; never gated behind a confirm dialog (mirrors spec-2-10's own "committing is not switching mazes" precedent).
- "Generate random" keeps its exact existing wiring (`GenerateRandomDialog`, shortcut "N", `_on_generation_confirmed`), placed below the three sections, never a fourth section card.
- `player/screen.py`'s `_KIND_LABELS` gains `MazeKind.CREATION: "Creation"` (its absence would `KeyError` the breadcrumb the first time a Creation card is opened).
- `player/screen.py`'s `gallery.pack()` margin shrinks from `SPACING["page-margin"]`/`["section-gap"]` to `SPACING["lg"]`/`["xl"]`, matching the Story 4.10 follow-up's gameplay/edit-area margin (closes a named deferred-work item).
- Thumbnail wall/entry/exit drawing reuses `MazeCanvas`'s own routines, extracted to `player/maze_wall_rendering.py` (`draw_walls`/`draw_entry_marker`/`draw_exit_marker`, parametrized by `cell_size`/`wall_width`); `MazeCanvas.__init__` is refactored to call them, not left duplicated.

**Ask First:** None — the sprint-change-proposal (2026-08-25) and epics.md's Story 4.14 ACs fully determine scope. The thumbnail-rendering approach was flagged there as "a story-level decision" and is resolved above (reuse via extraction, not a simplified re-draw).

**Never:** Never touch `confirmation_settings.py`/`settings_keys.py`/`settings_window.py` — `confirm_switch_maze`/`confirm_invalid_input` become unread by this story but are left defined (append one `deferred-work.md` entry instead of deleting shipped settings surface). Never touch Builder's own `_BuilderMazeCanvas` (`builder/maze_canvas.py`) — unaffected. Never add a "best time" to card-meta — Epic 6's `RecordsRepository` doesn't exist yet; cards show dimensions only. Never change `GameplayScreen`'s or `GenerateRandomDialog`'s own behavior — only what constructs/wires the dialog moves.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| All three sections populated | classic + creation + saved-random mazes exist | Grid renders 3 labeled sections, each listing its own cards | N/A |
| One section empty | e.g. no Creations saved yet | That section alone shows its inline empty-state message; the other two render normally | N/A |
| Every section empty | fresh install, empty repository | Each of the 3 sections shows its own empty message; "Generate random" zone still renders | N/A |
| Card activated by mouse | click a Creation card | `navigate(ScreenId.PLAYER, maze)` with that maze | N/A |
| Card activated by keyboard | Tab to a card, press `<Return>` or `<space>` | Same navigate as a click | N/A |
| Focus moves off-screen | Tab past the currently visible scrolled region | `ScrollableFrame` scrolls the newly focused card into view | N/A |

</frozen-after-approval>

## Code Map

- `src/labyrinthes/adapters/tkinter/player/classic_gallery.py` -- rename to `maze_selection_gallery.py`; `ClassicMazeGallery` -> `MazeSelectionGallery`; delete `_on_previous/_on_next/_on_restart/_on_jump/_maybe_confirm/_apply_*`, the `ConfirmDialog`/`confirm_*` imports, and the `<KeyPress-n>` local guards; keep `_on_generate_random`/`_on_generation_confirmed` verbatim
- `src/labyrinthes/adapters/tkinter/player/maze_card.py` -- new `MazeCard(tk.Frame)`: thumbnail canvas + name + `W×H` labels, `IconButton`-pattern focus ring, click/Enter/Space -> caller-supplied callback
- `src/labyrinthes/adapters/tkinter/player/maze_wall_rendering.py` -- new; `draw_walls(canvas, maze, cell_size, colors, wall_width=2)`, `draw_entry_marker(...)`, `draw_exit_marker(...)` extracted verbatim from `maze_canvas.py:130-144,228-259`
- `src/labyrinthes/adapters/tkinter/player/maze_canvas.py:130-259` -- `_draw_walls`/`_draw_entry_marker`/`_draw_exit_marker` become thin delegations to the extracted functions; `_draw_wall_bar`/`redraw_structure`/`_draw_contour`/ball drawing stay local (structural-visibility/gameplay-only, not thumbnail concerns)
- `src/labyrinthes/adapters/tkinter/common/scrollable_frame.py` -- new `ScrollableFrame(tk.Frame)`: `Canvas`+inner `Frame`(`.content`)+`Scrollbar`, `scrollregion` kept in sync via `<Configure>`, mouse-wheel bound (`<MouseWheel>` + `<Button-4>/<Button-5>`), `scroll_into_view(widget)` method
- `src/labyrinthes/adapters/tkinter/common/group_heading.py::build_group_heading` -- reused verbatim for each of the 3 section headings
- `src/labyrinthes/adapters/tkinter/common/icon_btn.py:26-94` -- focus-ring recipe (`takefocus`, `RESTING_RING_THICKNESS`/`FOCUS_RING_THICKNESS`, `<FocusIn>`/`<FocusOut>`, `<Return>`/`<space>`) to mirror in `MazeCard`
- `src/labyrinthes/adapters/tkinter/player/screen.py:59-64` -- `_KIND_LABELS`, add `MazeKind.CREATION: "Creation"`
- `src/labyrinthes/adapters/tkinter/player/screen.py:50,147-159` -- import/instantiate `MazeSelectionGallery`; `gallery.pack()` padding `SPACING["page-margin"]`/`["section-gap"]` -> `SPACING["lg"]`/`["xl"]`
- `src/labyrinthes/adapters/tkinter/common/tokens.py` -- `SPACING`, `TYPOGRAPHY`, `colors_for`, `RESTING_RING_THICKNESS`/`FOCUS_RING_THICKNESS` (existing, reused)
- `tests/adapters/tkinter/player/test_classic_gallery.py` -- rename to `test_maze_selection_gallery.py`; drop pager/confirm-gating tests, add section/empty-state/card-activation/keyboard-focus tests
- `tests/adapters/tkinter/player/test_player_screen.py` -- update gallery import/class name; add a `MazeKind.CREATION` case to the parametrized breadcrumb-label test
- `tests/adapters/tkinter/conftest.py` -- add a `creation_maze(width, height)` helper mirroring `classic_maze`/`saved_random_maze`
- `_bmad-output/implementation-artifacts/deferred-work.md` -- append: `confirm_switch_maze`/`confirm_invalid_input` are now unread anywhere (their only caller, the old pager, is gone); worth a follow-up removing them from `confirmation_settings.py`/`settings_keys.py`/`settings_window.py` and the tests that exercise them via `tests/adapters/tkinter/home/test_home_screen.py`, `tests/adapters/tkinter/builder/test_builder_screen.py`, `tests/adapters/tkinter/common/test_settings_window.py`, `tests/application/test_confirmation_settings.py`

## Tasks & Acceptance

**Execution:**
- [x] `player/maze_wall_rendering.py` -- extract `draw_walls`/`draw_entry_marker`/`draw_exit_marker` from `maze_canvas.py` -- reuse precondition for thumbnails
- [x] `player/maze_canvas.py` -- delegate its three drawing methods to the extracted functions -- AC (reuse), no behavior change
- [x] `player/maze_card.py` -- new `MazeCard` widget (thumbnail + name + dimensions, focus ring, click/Enter/Space) -- AC 3, 5
- [x] `common/scrollable_frame.py` -- new `ScrollableFrame` (Canvas+Frame+Scrollbar+`scroll_into_view`) -- AC 1, 5
- [x] `player/maze_selection_gallery.py` -- rebuild `MazeSelectionGallery`: 3 sections + per-section empty-state + `ScrollableFrame` + unchanged generate-random zone -- AC 1, 2, 3, 4
- [x] `player/screen.py` -- `_KIND_LABELS[MazeKind.CREATION]`, renamed gallery import, shrunk `gallery.pack()` margin -- prerequisite + deferred-work cleanup
- [x] `tests/adapters/tkinter/conftest.py` -- add `creation_maze()` -- test data for the Creations section
- [x] `tests/adapters/tkinter/player/test_maze_selection_gallery.py` -- section rendering, per-section empty-state, card click/Enter/Space navigation, scroll-into-view on focus -- AC 1-5
- [x] `tests/adapters/tkinter/player/test_player_screen.py` -- `MazeKind.CREATION` breadcrumb case, updated gallery references -- AC (prerequisite)
- [x] `deferred-work.md` -- append the orphaned-settings entry
- [x] Run `ruff check .`, `ruff format --check .`, `pytest -q` -- all green

**Acceptance Criteria:**
- Given the Player's maze-selection screen, when it renders, then it shows a scrollable card grid with three labeled sections — Classic, Creations, Random — per `key-player-selection.html`'s `gallery-grid`/`maze-card` pattern.
- Given a section with no mazes, when rendered, then that section alone shows an inline empty-state message; the other populated sections are unaffected.
- Given a maze card, when clicked or activated via keyboard, then the router mounts the gameplay screen with that `Maze` as state (same commit behavior as today's pager's "Play").
- Given the "Generate random" entry point, when rendered, then it stays a clearly separate action, not a fourth section card.
- Given the accessibility floor (NFR6), when the grid is keyboard-navigated, then every card is reachable and operable via Tab + Enter/Space, with a visible focus indicator (including auto-scroll into view).

## Design Notes

Thumbnail sizing mirrors `maze_canvas.py::_cell_size`'s clamp shape but at card scale: a small fixed pixel budget (suggested `_THUMBNAIL_SPAN = 120`, `clamp(min(120 // w, 120 // h), 2, 10)`) with `wall_width=1` (2px reads as chunky at this scale) — exact constants are the implementer's call, not locked, since they're purely visual.

`ScrollableFrame` is this codebase's first scrollable container; Tk has no native one — the standard idiom is a `Canvas` + inner `Frame` attached via `create_window()` (the same mechanism `common/stage.py` already uses for its own embedded content frame) + a `Scrollbar` wired to `yscrollcommand`, with `scrollregion` recomputed on the inner frame's `<Configure>`. `scroll_into_view(widget)` matters because Tk's default Tab traversal moves keyboard focus without scrolling anything — without it, Tabbing to a card below the fold would satisfy "reachable" but silently fail "visible focus indicator" (NFR6).

Eager-loading every listed maze at construction (one `maze_repository.load()` per card, not lazily per browsed position like the old pager) is a deliberate, necessary change — a grid must render every visible thumbnail at once. This widens the reach of the pre-existing, already-deferred "unguarded `load()` raises `MazeNotFoundError` if a listed file was deleted after listing" gap (still not fixed here, same codebase-wide posture).

## Verification

**Commands:**
- `ruff check .` -- expected: no errors
- `ruff format --check .` -- expected: no reformatting needed
- `pytest -q` -- expected: all tests pass, including the new gallery/card/scroll tests and the updated breadcrumb test

**Manual checks (if no CLI):**
- Launch the Player: with classics, creations, and saved-random mazes present, all three sections render with thumbnails; clicking a card opens gameplay.
- Empty a category (e.g. delete all Creations on disk) and relaunch: only that section shows its empty message, the others are unaffected.
- Tab through the grid with the mouse untouched: focus ring is visible on each card in turn, including cards below the initial scroll position, and Enter/Space opens the focused card.

## Suggested Review Order

**Sectioned card grid (the rebuild's core)**

- Entry point: constructs the 3 independently-populated sections, eager-loads every listed maze, builds the (unchanged) generate-random zone.
  [`maze_selection_gallery.py:101`](../../../src/labyrinthes/adapters/tkinter/player/maze_selection_gallery.py#L101)

- Per-section build: `list_names(kind)` → load → `MazeCard`, plus the independent inline empty-state per section.
  [`maze_selection_gallery.py:127`](../../../src/labyrinthes/adapters/tkinter/player/maze_selection_gallery.py#L127)

- Focus-driven auto-scroll wiring: each card's `<FocusIn>` calls back into the gallery to keep it visible (NFR6).
  [`maze_selection_gallery.py:176`](../../../src/labyrinthes/adapters/tkinter/player/maze_selection_gallery.py#L176)

**Card widget + reused thumbnail rendering**

- `MazeCard`: thumbnail + name + dimensions, `IconButton`-pattern focus ring, click/Enter/Space activation.
  [`maze_card.py:61`](../../../src/labyrinthes/adapters/tkinter/player/maze_card.py#L61)

- Review-fix: marker radius floored so entry/exit stay shape-distinguishable at the thumbnail's smallest cell size.
  [`maze_card.py:106`](../../../src/labyrinthes/adapters/tkinter/player/maze_card.py#L106)

- Extracted, reused (not duplicated) by both `MazeCard` and `MazeCanvas`; `min_radius` is this story's review-added floor.
  [`maze_wall_rendering.py:75`](../../../src/labyrinthes/adapters/tkinter/player/maze_wall_rendering.py#L75)

- `MazeCanvas` now delegates its own drawing to the extracted functions — confirms the extraction changed no gameplay behavior.
  [`maze_canvas.py:130`](../../../src/labyrinthes/adapters/tkinter/player/maze_canvas.py#L130)

**New shared primitive: `ScrollableFrame`**

- This codebase's first scrollable container — `Canvas`+`Frame`+`Scrollbar`, the `create_window()` idiom `stage.py` established.
  [`scrollable_frame.py:39`](../../../src/labyrinthes/adapters/tkinter/common/scrollable_frame.py#L39)

- The geometry math behind NFR6's "visible focus indicator": brings a Tab-focused card back inside the viewport.
  [`scrollable_frame.py:114`](../../../src/labyrinthes/adapters/tkinter/common/scrollable_frame.py#L114)

- Review-fix: recursive wheel binding so scrolling works with the pointer over a card, not just the bare canvas margin.
  [`scrollable_frame.py:69`](../../../src/labyrinthes/adapters/tkinter/common/scrollable_frame.py#L69)

**Wiring into the Player screen**

- Prerequisite fix: `_KIND_LABELS` gains `CREATION`, or opening a Creation card would `KeyError` the breadcrumb.
  [`screen.py:60`](../../../src/labyrinthes/adapters/tkinter/player/screen.py#L60)

- Renamed-gallery mount plus the shrunk outer margin that closes the Story 4.10-follow-up deferred-work item.
  [`screen.py:150`](../../../src/labyrinthes/adapters/tkinter/player/screen.py#L150)

**Peripherals: tests, deleted pager, deferred-work log**

- Real (non-stubbed) `scroll_into_view` geometry tests — the review-fix that closes the "spy defeats the test" gap.
  [`test_scrollable_frame.py:57`](../../../tests/adapters/tkinter/common/test_scrollable_frame.py#L57)

- Section rendering, per-section empty-state, card activation, and the wheel-binding regression test.
  [`test_maze_selection_gallery.py:46`](../../../tests/adapters/tkinter/player/test_maze_selection_gallery.py#L46)

- Deleted outright: the pager this story replaces, along with its now-superseded jump-entry guard.
  [`classic_gallery.py` (deleted)](../../../src/labyrinthes/adapters/tkinter/player/classic_gallery.py)

- New deferred-work entries from this story's own review (orphaned confirm settings, widened eager-load blast radius, and others).
  [`deferred-work.md:368`](../../../_bmad-output/implementation-artifacts/deferred-work.md#L368)
