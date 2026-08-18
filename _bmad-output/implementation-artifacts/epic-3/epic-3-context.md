# Epic 3 Context: Build and Test a Maze (Builder)

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Deliver the Builder end-to-end (UJ-1): create a new empty maze at chosen dimensions (shared 3–50 col / 3–35 row bounds) or reopen an in-progress Sketch, edit walls cell-by-cell or by rectangular zone, mark an entry and a border-cell exit, and save the result as an editable Sketch or a finished Maze playable from the Game — plus a live light/dark theme toggle and click-to-move cursor navigation. Completes the bidirectional Builder↔Player link (`Test in Player`, `Edit in Builder`), now possible that both screens exist: the build → test → edit loop with no forced trip through Home.

## Stories

- Story 3.1: New maze / open a sketch
- Story 3.2: Wall editing — break/restore
- Story 3.3: Zone editing — destroy/restore a rectangular zone
- Story 3.4: Entry and exit marking
- Story 3.5: Direct navigation — "Go to"
- Story 3.6: Sketch / Maze save
- Story 3.7: Builder theme toggle
- Story 3.8: Test in Player — launch the Game from the Builder
- Story 3.9: Edit in Builder — launch the Builder from the Game

## Requirements & Constraints

- Wall editing (FR-1): break or restore a wall between adjacent cells, either by clicking a wall segment in Break mode or by moving the cursor across it in Pass-through mode. Both affected cells' 0/1/2/3 encoding updates symmetrically, and the saved CSV encoding stays unchanged from the legacy format.
- Zone editing (FR-2): click-and-drag selects a rectangular zone destroyed or restored as one operation. The gesture is distinct from a single click, so a slightly imprecise single click never triggers it. Restoring a just-destroyed zone returns it exactly to its initial state; the maze's outer border stays closed after any zone operation.
- Entry/exit (FR-3): Set Entry marks any cell; Set Exit marks a border cell, showing a `ghost-marker` (dashed border, `?` glyph, non-interactive) until actually set — never a default/placeholder position. Redefining an existing entry/exit triggers a confirmation prompt, toggleable off in Settings.
- New maze / open sketch (FR-4): dimensions bounded 3–50 cols / 3–35 rows, validated live inline; the bounds are defined once as a shared-scope setting read identically by the Builder's and the Player's dialogs — never hardcoded UI constants (fixes the legacy "Duplicated size bounds" defect). The New Maze dialog is the entry state; nothing renders in the maze-frame until dimensions are confirmed. Open Sketch resumes editing at the saved state via `MazeRepository`.
- Save (FR-5): save as Sketch (incomplete, editable) or Maze (finished, playable). With entry set but exit not set, the Maze path is blocked with an inline message while Sketch save stays available. A saved Maze becomes selectable from the Player's classic gallery; a saved Sketch reopens from "Open a Sketch" and shows a "Draft" status. Duplicate names get explicit handling — no silent overwrite.
- Theme (FR-6): light/dark toggle reuses the shell-wide theme mechanism from Story 1.9 (no Builder-only implementation) and persists via the shared scope.
- Direct navigation (FR-7): clicking a cell (no zone-drag in progress) moves the editing cursor there.
- Test in Player (FR-8): unconditionally available from an active Builder session (fixes the legacy disabled button); hands the in-progress `Maze` to the Player gameplay screen in memory through `mount()`, bypassing Home — no serialization round-trip and no save required first.
- Edit in Builder (FR-19): offered in the Player only for mazes with a Builder-editable source (`classic` or `saved-random`, never an unsaved `generated` maze); must work even when the Game was launched standalone (fixes the legacy one-way-only link). Re-saving an edited `classic`/`saved-random` maze carries its `MazeId` forward unchanged.
- Accessibility floor (NFR6): every Builder action is keyboard-reachable and registers into the one canonical keybinding table (Story 1.10); entry/exit/wall states are distinguished by shape as well as color (broken walls render as structural gaps, never dashed).

## Technical Decisions

- Editing logic (wall/zone encoding updates, entry/exit placement rules) is pure domain/application work — `domain/` operations return new immutable `Maze` values (never in-place mutation); orchestration lives in an `application/` service (e.g. `BuilderService`); only rendering and input wiring live in `adapters/tkinter/builder/`, which never imports `adapters/storage/` directly.
- The Builder owns an adapter-local mutable session wrapper (cursor position, active tool, in-progress zone drag) around the immutable `Maze` value it references.
- `MazeRepository`/`SettingsRepository` are Epic 1's single shared implementations — this epic consumes them (save/load sketches and mazes, read shared bounds, persist theme), never reimplements them. `MazeRepository.save()` mints a `MazeId` only when a maze first becomes `classic`/`saved-random`; a re-save of a maze that already has one (the Edit-in-Builder flow) keeps the existing id.
- The Builder registers with the single router (Story 1.7) as `mount(parent, state: Maze | None) -> Frame`, `None` meaning the New Maze flow. `Test in Player` / `Edit in Builder` are the two state-carrying exceptions to Home-only routing, wired at the `app/` composition-root level — `adapters/tkinter/builder` and `adapters/tkinter/player` never import each other.
- Builder-specific widgets (maze canvas, wall-editing cursor, zone drag, markers) stay local to `adapters/tkinter/builder/`; generic widgets (`tool-btn`, `pill-btn`, `kbd-tag`, `hud-chip`, breadcrumb, Settings window, confirmation dialogs, theme toggle) come from `adapters/tkinter/common/`.

## UX & Interaction Patterns

- Builder edit screen (`mockups/key-builder-edit.html`): maze-frame centered, flanked by tool side bars, top bar with breadcrumb (Home segment always present/clickable) plus Settings/theme `icon-btn`s; exactly one primary `pill-btn` per screen ("New Maze", "Save"); HUD `hud-chip`s show grid size and a live "Walls broken" count (monospace `hud-stat`).
- Tools are mutually-exclusive `tool-btn`s grouped by heading (e.g. Break Wall vs Set Entry vs Set Exit); the active tool persists until another is chosen. Pass-through mode breaks walls as the cursor moves across them.
- The single-click vs click-and-drag wall gesture split is a hard interaction contract (FR-1 vs FR-2) — the two must never blur.
- New Maze, Save, and Settings are dedicated windows (not inline panels); dimension validation is live and inline ("Columns must be between 3 and 50."), non-modal, and persists until resolved.
- Voice and Tone stays plain and non-alarmist ("Exit not set").

## Cross-Story Dependencies

- Epic 1 must supply the domain model (1.1), `MazeRepository`/`SettingsRepository` (1.3–1.5, hardened 1.12), the `common/` toolkit and tokens (1.6), the router (1.7), the theme mechanism (1.9), and the canonical keybinding table (1.10) before this epic's storage-, rendering-, and shortcut-consuming stories can land.
- Epic 2's gameplay screen is required for 3.8 (Test in Player mounts it with a `Maze`) and 3.9 (Edit in Builder keys off the `classic`/`saved-random` kinds); these two stories are the reason the epic waits until both screens exist.
- Internal: 3.1 (a grid to edit) precedes 3.2 (wall editing) and 3.4 (entry/exit); 3.2 precedes 3.3 (zone editing operates on walls); 3.4 precedes 3.6 (Save-as-Maze requires entry+exit); 3.6's Maze save feeds Epic 2's classic gallery (2.1).
- Re-saving a maze while preserving its `MazeId` (3.6/3.9) is what keeps Epic 5's Personal Records tied to a stable identity across edits.