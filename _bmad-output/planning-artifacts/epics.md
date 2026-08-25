---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/prd.md
  - _bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/ux-designs/ux-Labyrinthes-2026-08-04/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-Labyrinthes-2026-08-04/EXPERIENCE.md
---

# Labyrinthes - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Labyrinthes, decomposing the requirements from the PRD (`prd-Labyrinthes-2026-08-04`), the finalized UX design contract (`ux-Labyrinthes-2026-08-04`), and the Architecture Spine (`architecture-Labyrinthes-2026-08-04`) into implementable stories for the `rewrite` branch.

## Requirements Inventory

### Functional Requirements

FR-1: Wall editing — the user can break or restore a wall between two adjacent cells (Break mode, or by moving the cursor in Pass-through mode). Breaking a wall updates the 0/1/2/3 encoding of both affected cells symmetrically; the save format stays unchanged from the legacy format (FR-20).

FR-2: Zone editing — the user can select a rectangular zone of cells and destroy (remove walls) or restore (place walls) it in a single operation. The operation is symmetric (restoring a zone just destroyed returns it to its initial state); the maze's outer border stays closed after the operation.

FR-3: Entry and exit — the user can mark a cell as the entry and a border cell as the exit, with a confirmation prompt if an existing entry/exit is being redefined (toggleable off per FR-17).

FR-4: New maze / open a sketch — the user can create a new empty maze by specifying its dimensions (3–50 columns, 3–35 rows), or reopen an existing Sketch to keep editing it. The bounds are defined once, in settings, and read by both the Builder and the Game — not duplicated as hardcoded UI constants (fixes the legacy "Duplicated size bounds" defect).

FR-5: Sketch / Maze save — the user can save their work either as a Sketch (incomplete, editable) or as a Maze (finished, playable from the Game), with duplicate-name handling. Out of scope: an automated migration tool for existing Sketches/Mazes on disk — covered by FR-23.

FR-6: Builder theme — the user can toggle the editor's color theme (light/dark).

FR-7: Direct navigation — the user can click a cell to move the editing cursor there ("Go to").

FR-8: Launch the Game from the Builder — the user can open the Game from the Builder without leaving their editing session. This is the `Test in Player` action (FR-26) — the rewrite must expose this entry point as a live, enabled control, unlike the legacy app's disabled button.

FR-9: Classic maze selection — the user can browse classic mazes (previous / next / restart) or jump directly to a given number.

FR-10: Random maze generation — the user can generate a procedural maze by configuring its dimensions (same 3–50 column / 3–35 row bounds as FR-4) and starting position, with input validation.

FR-11: Random maze saving — the user can save a generated random maze, and later find it again in the selector alongside classic mazes; a saved random maze appears in the selection list after the application restarts (in the legacy app this writes a file nothing else ever reads back — explicitly fixed here).

FR-12: Levels — the user can choose a Level (1 through 4, plus "Max") that controls progressive grid visibility during solving, derived from how the 0/1/2/3-encoded grid is partitioned. See the addendum's "Level detail" section for the exact per-Level visibility mechanics.

FR-13: Difficulty — the user can choose a Difficulty (1 through 3, unlockable from Level 2 onward) that adjusts the partition size or reveal thresholds used by Levels. The reveal-threshold calculation follows a single, consistent formula, applied identically regardless of which Level is active (fixes the legacy inconsistency between Level 2 and Level 4).

FR-14: HARD mode — the user can enable a mode where the ball becomes invisible during movement, with a visual state indicator (light) whose color follows the user's configured setting. Changing the indicator's color in settings updates its state-toggling behavior without breaking it (fixes a hardcoded value in the legacy app). First activation triggers the same explainer popup as any other tier (FR-28).

FR-15: Movement modes — the user can choose between Smooth movement (direction can be redirected mid-move) and Discrete movement (cell by cell), with a configurable speed.

FR-16: Timer — the user can time their maze solve, with an optional configurable time limit and a message on timeout. (Present but never wired up in the legacy app — picked back up and finished here.)

FR-17: Confirmation prompts — the user can enable/disable, per action (switching mazes, restarting, Level change, invalid input, entry/exit redefinition, ...), a confirmation prompt before that action applies.

FR-18: Appearance — the user can toggle the Game's color theme and pick a logo from a list.

FR-19: Launch the Builder from the Game — the user can open the Builder from the Game when it was launched standalone (not only when the Game was itself opened from the Builder). This is the `Edit in Builder` action (FR-26), gated to mazes with a Builder-editable source (a classic or a saved random maze — not an unsaved procedurally-generated maze).

FR-20: Maze data format — the system reads and writes mazes (classic, sketch, saved random) in the existing CSV-based format: the first two lines for entry/exit, then — for classic/saved-random mazes only — a `MazeId` header line, then the grid encoded as 0/1/2/3. Existing maze data remains readable without conversion loss (subject to FR-23). The Builder and the Game share the same read/write logic for this format, including the `MazeId` line: minted once, when a maze is first saved as classic or saved-random, and carried forward unchanged on every subsequent re-save.

FR-21: Settings persistence — the system persists each application's (Builder, Game) default settings between sessions. Running the Builder and the Game at the same time and changing settings in one does not silently overwrite the other's settings on close (fixes a legacy defect).

FR-22: Keyboard shortcuts — every keyboard shortcut maps to exactly one action, and the label/tooltip shown to the user accurately describes the real shortcut. (Fixes the legacy collision where `r` triggers "Restart" while its tooltip claims "Settings".)

FR-23: Legacy data migration to English — the system provides a one-time conversion script — not a dual-layout compatibility shim — that converts existing on-disk legacy data (folder names, save file naming, CSV headers, e.g. `entité,nom,valeur`) to the new English-named layout, without altering the maze content itself. Every maze and settings file present under the legacy layout is reachable, unchanged in content, under the new layout after the script runs; the 0/1/2/3 cell-encoding values are copied as-is; the script renames/moves files in place (no side-by-side copy, no built-in rollback). The script also mints and writes FR-20's `MazeId` header line for every legacy classic and saved-random maze it converts, reusing the same shared writer routine as a fresh save.

FR-24 *(deferred, P2)*: Water Chase mode — the player can face a maze where water falls from above and naturally flows downward, progressively filling the maze; several difficulty tiers define an underwater breath reserve (cells or time) beyond which the player fails.

FR-25 *(deferred, P2)*: Exploration mode — the player can move through several mazes chained together on a 2D map, with collectible items (e.g. keys) scattered across the different mazes, and optional narration accompanying progress toward the end.

FR-26: Home screen navigation hub — the user opens the app to a Home screen that routes to the Builder and to the Game. Home is the sole general router between the Builder and the Game — no persistent switcher between them exists elsewhere. Two contextual exceptions bypass Home for a tight build/test loop: `Test in Player` (FR-8, available unconditionally from an active Builder session) and `Edit in Builder` (FR-19, gated to mazes with a Builder-editable source). Every other transition between the Builder and the Game passes back through Home. Every screen carries a persistent, clickable breadcrumb path back to Home (and to any intermediate level). Settings is reachable from a top-bar icon present on every screen (Home, Builder, Game alike) — not routed through Home specifically.

FR-27: Personal Records (local best-times) — on winning a maze that has a stable identity (a classic maze or a saved random maze — not an unsaved procedurally-generated maze), the system records, locally, the player's fastest completion time for that specific maze **at the Level and Difficulty the run used**. Home's Personal Records zone displays these records, most-recently-set-or-broken first. A record is scoped to the (maze, Level, Difficulty) combination — never compared across combinations. Home's Personal Records zone groups a maze's records into a single, expandable entry (flat if only one combo; collapsed behind its most-recently-set-or-broken combo if several, expanding to list every combo — the `record-group` UX pattern). A new completion time replaces the stored record for that combination only if it is faster than the existing one. Before any maze has been won, the zone shows an inviting empty-state message rather than a fabricated score. Records are local-only this milestone: no server sync, no shared/community leaderboard — though the underlying data model doesn't preclude a later extension.

FR-28: First-activation explainer for Level, Difficulty, and HARD-mode tiers — the first time the user activates a given Level, Difficulty, or HARD-mode tier, an explainer popup describes what that tier changes; an ⓘ affordance next to the corresponding control reopens the same explainer on demand at any time. Every tier gets this treatment — Level, Difficulty, and HARD mode (FR-14) alike. Auto-show-on-first-activation is configurable off in Settings; the on-demand ⓘ affordance keeps working regardless of that setting. The explainer's wording stays plain and non-alarmist, consistent with the product's voice and tone (see UX spec).

FR-29 *(added by the 2026-08-19 course correction)*: Builder reachability feedback — the Builder HUD shows the count of cells inaccessible from the entry; clicking the counter outlines those cells on the grid. Before an entry is set, the counter reads "—" and is not interactive. Replaces the "Walls broken" HUD stat.

FR-30 *(added by the 2026-08-19 course correction)*: Configurable defaults — the default dimensions proposed by the Builder's New Maze dialog and the Player's Generate Random dialog, and the Builder's default tool when a session opens, are user-configurable settings (dimensions bounded by the shared 3–50 / 3–35 bounds).

FR-31 *(added by the 2026-08-19 course correction)*: Window management — the app window opens centered on screen, is freely resizable, the maze canvas zooms (Ctrl+wheel, `+`/`-`) and adapts to the available space, and F11 toggles fullscreen. The Settings window opens centered, is resizable, and supports fullscreen.

FR-32 *(added by the 2026-08-19 course correction)*: Top-bar brand mark — every screen's top bar shows the brand logo (per the user's logo setting) before the app name.

FR-33 *(added by the 2026-08-19 course correction)*: Play again — after solving a generated random maze, the win banner's continue action generates a new random maze with the same dimensions and entry position, immediately.

FR-34 *(added by the 2026-08-19 course correction)*: Layout grouping — the Builder's and Player's controls and displays are grouped into labeled blocks on the sides and top, clearly separated from the maze frame.

FR-35 *(added by the 2026-08-25 course correction)*: Classic vs. Creation maze — a Classic maze is a hand-built maze present at first install, authored by the project's developer as shipped game content; it is never produced by a player's own Builder save. A Creation is a finished maze (entry and exit set) a player builds and saves via the Builder — built with the same tool as a Classic maze, but distinct in provenance and never shipped as game content. A Creation is `MazeId`-eligible and Personal-Record-eligible on the same terms as Classic and Saved-random (FR-20, FR-27).

FR-36 *(added by the 2026-08-25 course correction)*: Screen shortcuts never leak into a focused text field — no keyboard shortcut registered for the active screen fires while a text-entry field inside an open dialog holds keyboard focus; enforced once, at the shortcut-dispatch mechanism, not by individually blocking each colliding letter per dialog.

FR-37 *(added by the 2026-08-25 course correction)*: Maze name in the breadcrumb — whenever a screen has a specific maze loaded, its breadcrumb gains one additional trailing segment carrying that maze's own saved name, appended after the existing kind-derived segment (e.g. "Home / Player / Classic / 10x10edf") — the kind segment is never replaced or removed.

FR-38 *(added by the 2026-08-25 course correction)*: Grid gallery, split by category — the Player's maze-selection screen presents Classic, Creation, and Random (saved) mazes as three separate, clearly labeled sections in one scrollable card grid, per the locked mockup, replacing the single-item pager.

### NonFunctional Requirements

NFR1: Logic/UI decoupling — the maze engine (grid, 0/1/2/3 encoding, generation, Level/Difficulty rules) depends on no UI library. This is a PRD requirement, not just good practice — it's what makes a future web/mobile interface possible.

NFR2: Data contract stability — the 0/1/2/3 cell encoding and the maze CSV format are a public contract between the Builder and the Game; any evolution must stay backward-compatible with existing data once migrated (FR-23). The `MazeId` header line (FR-20) is the one deliberate, additive exception in this milestone, and is not itself a precedent for further changes without the same explicit sign-off.

NFR3: Quality and tests — every ported feature is covered by automated tests (`pytest`) and passes linting (`ruff`), already in place on the `rewrite` branch.

NFR4: Language convention — code identifiers, comments, UI strings, on-disk data (folder names, file naming, CSV headers), and documentation are all in English from the `rewrite` branch onward. Only the author's live conversation with an AI assistant stays in French — that does not extend to any artifact the project produces.

NFR5: Readable git workflow — history reflects an incremental, feature-by-feature port, with commits/PRs that stay understandable in hindsight (an explicit project success criterion).

NFR6: Accessibility floor — every action is reachable via a keyboard shortcut — no mouse-only affordance anywhere in Home, the Builder, or the Game; every focusable control shows a visible focus indicator; text/background contrast meets WCAG AA; entry/exit/wall states are distinguished by shape as well as color, never color alone. Screen-reader support is explicitly out of scope this milestone (a known Tkinter renderer limitation).

### Additional Requirements

- **Fixed package layout (hexagonal / ports & adapters):** all code lands under `src/labyrinthes/{domain/, application/, adapters/tkinter/{common/,home/,builder/,player/}, adapters/storage/, app/}` per the layer the Architecture Spine assigns it — not wherever's convenient for a given story (AD-1 through AD-11).
- **One-way dependency direction, structurally enforced:** `domain/` and `application/` import nothing from `adapters/` or any UI framework; `app/` → `adapters/` → `application/` → `domain/`; `adapters/tkinter/` never imports `adapters/storage/` directly — storage access always goes through an `application/` service (AD-1).
- **Domain state is immutable:** `Grid`, `Cell`, `Maze`, `Position`, `Level`, `Difficulty`, `Duration`, `MazeId` and other domain value objects are immutable (frozen dataclasses or equivalent); engine operations are pure functions that take a state and return a new state (AD-2, AD-3).
- **Domain object shapes are pinned, not left implicit:** `Grid` is `[row][col]`, 0-origin; `Cell` decodes wall booleans as computed properties over its digit, never a separate drift-prone representation; `Position` is one shared `(row, col)` type for entry/exit/ball/cursor alike; `Maze` = `Grid` + entry/exit `Position` + a kind tag (`classic`/`sketch`/`saved-random`/`generated`) + `id: MazeId | None`; `Level`/`Difficulty`/`Duration` are single shared types, not independently invented per feature (AD-3).
- **Automated import-boundary test:** a pytest test scans `domain/` and `application/` for forbidden imports (`tkinter`, `adapters`), and flags `adapters/tkinter/` importing `adapters/storage/` directly, the three screen packages (`home/`, `builder/`, `player/`) importing one another, and `adapters/tkinter/common/` importing any of them — this must exist early enough to catch violations in the same features it's meant to guard (AD-9).
- **Single-implementation persistence ports:** exactly one `MazeRepository` (AD-5), one `SettingsRepository` scoped `builder`/`game`/`shared` (AD-7), and one `RecordsRepository` (AD-12) implementation each live under `adapters/storage/` — no per-screen duplicate read/write logic. `SettingsRepository` is `get(scope, key)`/`set(scope, key, value)`, written immediately — never a load-everything/dump-everything cycle (fixes the legacy clobbering bug).
- **Single composition root, screen router:** exactly one shell under `app/` owns the single `Tk()` root and a screen router; Home, Builder, and Player are the three screens registered with it (keyed by a stable enum, not a bare string), each implementing `mount(parent, state: Maze | None) -> Frame`; they never import each other directly — all top-level navigation goes through the router (AD-10).
- **Sequencing constraint:** a "define the port interfaces" story (`MazeRepository`/`SettingsRepository` method signatures) must land strictly before the Builder-, Game-, and Home-side storage-consuming stories are started in parallel, so none start from divergent assumptions (Architecture Spine, Deferred section).
- **Migration script shares the repositories' constants and writers:** FR-23's one-time script imports the same new-layout path/naming constants module the repositories use, and reuses `MazeRepository`'s own `MazeId`-line writer rather than a bespoke serializer, when backfilling `MazeId` for legacy classic/saved-random mazes (AD-6, AD-8).
- **Records business logic lives in `application/`:** `RecordsService` owns the "is this a new best" comparison and the "most-recently-set-or-broken first" ordering — never duplicated into `adapters/storage/` or `adapters/tkinter/`; the Player screen calls `RecordsService.record_completion(...)` on a win; Home reads through `RecordsService`, never `adapters/storage/` directly (AD-12).
- **Shared Tkinter toolkit:** generic, app-agnostic widgets (button/tooltip factories, the settings-panel widget, theme toggling, confirmation-prompt dialogs, the shared breadcrumb widget) live in `adapters/tkinter/common/`, imported by `home/`, `builder/`, `player/` — not duplicated per screen (AD-11).
- **Toolchain already adopted, must stay green:** Python ≥3.12, ruff ≥0.6 (rules E, F, I, UP, B, SIM), pytest ≥8.0, hatchling build backend — already configured in `pyproject.toml` on the `rewrite` branch; no story should need to re-establish this.
- **Explicitly out of scope for this epics/stories pass** (per the Architecture Spine's Deferred section — should not spawn stories now): final web/mobile stack choice; FR-24/FR-25 detailed design; exact on-disk file formats for settings/maze-repository/records (JSON/TOML/CSV, `MazeId` generation scheme); packaging/distribution (e.g. a frozen executable); a hosted CI/CD pipeline.

### UX Design Requirements

UX-DR1: Implement the Blueprint design token system as a shared, reusable style module — paired light/dark color tokens, the two typography stacks (system UI + monospace `hud-stat`/`kbd`), the spacing scale, and the radii scale — consumed by every Tkinter screen (not hardcoded per-widget), including the two dedicated AA-contrast-fix tokens (`accent-on-tint` for light-mode active-tool text, `accent-strong-dark` for dark-mode primary-button fills).

UX-DR2: Build the shared `adapters/tkinter/common/` widget library per `DESIGN.md → Components`: `tool-btn` (with mutually-exclusive active-tool-group behavior), `hud-chip` (with the live/accent variant for the running Time chip), `icon-btn`, `pill-btn` (with at-most-one-primary-per-screen rule), `kbd-tag` + separate hover tooltip (shortcut always printed, tooltip never restates it), the top-bar breadcrumb/brand-mark, `settings-window`, the first-activation explainer popup, and the inline error/empty-state message pattern.

UX-DR3: Implement `maze-frame` + `wall-bar` rendering with the corrected broken-wall treatment: a broken wall renders as a structural gap (nothing drawn at that segment) — never a dashed or patterned bar. This overrides the rejected treatment still visible in `mockups/direction-blueprint.html`.

UX-DR4: Implement `marker` (entry/exit, filled with a distinct glyph — circle for entry, flag/arrow for exit) and `ghost-marker` (unset-exit state: dashed border, `?` glyph, non-interactive) components, satisfying the "shape as well as color" accessibility rule.

UX-DR5: Implement the `ball` component (Player) — radial-gradient fill, accent-hue halo, drop shadow at rest — and its "not rendered at all" state during HARD-mode movement.

UX-DR6: Implement the top-bar breadcrumb navigation pattern (e.g. "Home / Player / Classic Maze 4") on every screen, replacing the rejected persistent Builder/Player `.switch` toggle; the Home segment is always present and clickable; each earlier crumb jumps there directly; each screen feeds its own dynamic sub-state label to the shared breadcrumb widget.

UX-DR7: Implement the HARD-mode fog overlay + status light: a translucent scrim (`colors.bg`/`colors.bg-dark` at 0.85 opacity, no animation) shown only while the ball is moving, with load-bearing z-order — above the corridor/ball plane, below wall-bars and markers, so structure stays crisp and only the ball is obscured — plus a 10px status light reflecting ready/moving state, colored from the user's configurable HARD-mode setting (fixing the legacy hardcoded-color bug so both ready and moving states stay consistent with the setting).

UX-DR8: Implement the `record-group` component (Home, Personal Records zone): one row per maze with a stored record; flat with no chevron for a single (Level, Difficulty) combo; collapsed-by-default with a chevron toggle and a most-recently-set-or-broken headline for 2+ combos; expands to an indented combo list ordered canonically by Level then Difficulty ascending (not by recency); the toggle is a real focusable control activated by click or Enter/Space.

UX-DR9: Implement the win banner (inline, non-blocking, appears around the maze-frame on solve, offers a "continue" action) and the inline timeout-failure message (non-modal, restart/continue stay reachable from the same message) — both using the plain, non-alarmist Voice and Tone wording (e.g. "Solved in 00:42.", "Time's up — the exit wasn't reached.").

UX-DR10: Apply the Accessibility Floor across Home, Builder, and Player: full keyboard operability for every action (including the `record-group` toggle), a visible focus indicator on every focusable control at an AA-equivalent contrast, and WCAG AA text/background contrast per the locked token pairs (including the two AA-fix tokens from UX-DR1).

UX-DR11: Implement the light/dark theme toggle wired to the complete paired token set (not a partial subset), consistent across Home, Builder, Player, and the Settings window — including the deliberately-inverted wall/corridor brightness relationship between modes (never derived by mechanically inverting the light-mode hex values).

UX-DR12: Implement the Builder's New Maze dialog and Save dialog, and the Settings window, as dedicated windows (not inline panels) per the spine-only IA rows in `EXPERIENCE.md`, each with live inline validation (dimensions) against the shared bounds from FR-4/FR-10 where applicable.

### FR Coverage Map

FR-1: Epic 3 - Wall editing (Builder)
FR-2: Epic 3 - Zone editing (Builder)
FR-3: Epic 3 - Entry/exit marking (Builder)
FR-4: Epic 3 - New maze / open sketch, shared size bounds (Builder)
FR-5: Epic 3 - Sketch / Maze save (Builder)
FR-6: Epic 3 - Builder theme toggle
FR-7: Epic 3 - Direct navigation ("Go to")
FR-8: Epic 3 - Test in Player (Builder → Game, wired once Epic 2's Player exists)
FR-9: Epic 2 - Classic maze selection (Game)
FR-10: Epic 2 - Random maze generation (Game)
FR-11: Epic 2 - Random maze saving (Game)
FR-12: Epic 2 - Levels (Game)
FR-13: Epic 2 - Difficulty (Game)
FR-14: Epic 2 - HARD mode (Game)
FR-15: Epic 2 - Movement modes (Game)
FR-16: Epic 2 - Timer (Game)
FR-17: Epic 2 - Confirmation prompts (Game)
FR-18: Epic 2 - Appearance (Game)
FR-19: Epic 3 - Edit in Builder (Game → Builder, wired once Builder exists)
FR-20: Epic 1 - Maze data format, single shared MazeRepository
FR-21: Epic 1 - Settings persistence, single shared SettingsRepository
FR-22: Epic 1 (Story 1.10) - Canonical keybinding table + automated collision/label-consistency check; every later epic's actions register into this same table
FR-23: Epic 5 - Legacy data migration to English, MazeId backfill
FR-24: Epic 7 (deferred, P2) - Water Chase mode
FR-25: Epic 7 (deferred, P2) - Exploration mode
FR-26: Epic 1 - Home screen navigation hub, breadcrumb, Settings top-bar affordance
FR-27: Epic 6 - Personal Records (local best-times)
FR-28: Epic 6 - First-activation explainers (Level/Difficulty/HARD)
FR-29: Epic 4 - Builder reachability counter (replaces "Walls broken")
FR-30: Epic 4 - Configurable defaults (Builder tool, new-maze & random dimensions)
FR-31: Epic 4 - Window management (centered, resizable, zoom, fullscreen)
FR-32: Epic 4 - Top-bar brand mark (logo before the app name)
FR-33: Epic 4 - Play again (win banner regenerates a random maze)
FR-34: Epic 4 - Layout grouping (labeled blocks separated from the maze)
FR-35: Epic 4 (Story 4.11) - Classic vs. Creation maze kind
FR-36: Epic 4 (Story 4.12) - Screen shortcuts never leak into a focused text field
FR-37: Epic 4 (Story 4.13) - Maze name in the breadcrumb
FR-38: Epic 4 (Story 4.14) - Grid gallery, split by category (Classic / Creations / Random)

**Epic 4 amendments:** Epic 4's stories also refine the acceptance criteria of FR-1 (wall-tool semantics, cursor glyph), FR-2 (zone gestures), FR-3 (marker shapes, live placement), FR-4 (default dimensions), FR-10 (random defaults, play-again), FR-18 (top-bar logo) delivered by Epics 1-3 — those FR rows stay owned by their original epic, with the refinements tracked in Epic 4's stories. The 2026-08-25 course correction (Stories 4.11-4.14, FR-35 through FR-38) further amends FR-5/FR-9/FR-11/FR-20/FR-27 (Classic vs. Creation), FR-22 (keybinding dispatch), and FR-26 (breadcrumb) — see `sprint-change-proposal-2026-08-25.md`.

**NFRs — cross-cutting, apply to every epic (not owned by a single one):**
NFR1 (Logic/UI decoupling), NFR4 (Language convention), NFR5 (Readable git workflow) apply to all epics' stories. NFR2 (Data contract stability) and NFR3 (Quality and tests, including the AD-9 import-boundary test) are established structurally in Epic 1 and must hold for every epic thereafter. NFR6 (Accessibility floor) gets its explicit anchor in Epic 1 (Story 1.10, shared-widget focus/contrast/keyboard operability) but every epic's screen-specific stories (e.g. Epic 2/3's marker and wall-bar shape-vs-color distinction) must uphold it too.

## Epic List

### Epic 1: Foundation & Navigation Shell
Establishes the single composition root and screen router, a functional Home hub (breadcrumb navigation, Settings top-bar access), the immutable domain engine (Grid/Cell/Maze/Position/Level/Difficulty/Duration), the single shared `MazeRepository` and `SettingsRepository` implementations, the shared Tkinter `common/` toolkit (design tokens, `tool-btn`/`hud-chip`/`icon-btn`/`pill-btn`/`kbd-tag`, breadcrumb, Settings window), and the automated domain/UI boundary test (AD-9). Delivers a working, themable Home that already routes to (initially minimal) Builder and Player screens — replacing the legacy `big_boss`/two-separate-apps pattern from the first epic.
**FRs covered:** FR-20, FR-21, FR-22, FR-26

### Epic 2: Play a Maze (Game / Player)
Classic maze selection (browse/jump), random maze generation and saving, Levels, Difficulty, HARD mode, Smooth/Discrete movement, timer, per-action confirmation prompts, and appearance (theme + logo). Delivers UJ-2's core play loop end-to-end (short of Personal Records, added in Epic 6).
**FRs covered:** FR-9, FR-10, FR-11, FR-12, FR-13, FR-14, FR-15, FR-16, FR-17, FR-18

### Epic 3: Build and Test a Maze (Builder)
Wall and zone editing, entry/exit marking, new maze / sketch creation with shared size bounds, Sketch/Maze saving, Builder theme, direct cell navigation — plus the complete bidirectional Builder↔Player link (`Test in Player`, `Edit in Builder`), only completable now that both screens exist. Delivers UJ-1 end-to-end, including the build → test → edit loop with no forced trip through Home.
**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8, FR-19

### Epic 4: Review Corrections — Builder & Player Polish, Windowing, Configurable Defaults
Corrects delivered Builder/Player/shell behavior per the 2026-08-19 course correction: distinct marker/cursor glyphs, reworked Break vs Pass-through semantics, visible zone selection with a second gesture, live entry/exit placement, a reachability counter replacing "Walls broken", configurable defaults (Builder tool, new-maze and random dimensions), a play-again win-banner action, shell windowing (centered, resizable, zoom, fullscreen), a top-bar brand logo, and grouped screen layouts. Amends acceptance criteria of Epics 1-3 (FR-1/2/3/4/10/18) and adds FR-29 through FR-34. The 2026-08-25 course correction extends the epic further: a Classic-vs-Creation maze-kind distinction, a keybinding-dispatch fix so screen shortcuts never leak into a focused text field, the maze's own name added to the breadcrumb, and a Classic/Creations/Random sectioned grid gallery. Adds FR-35 through FR-38.
**FRs covered:** FR-29, FR-30, FR-31, FR-32, FR-33, FR-34, FR-35, FR-36, FR-37, FR-38

### Epic 5: Legacy Data Migration to English
A one-time conversion script that renames the legacy French-named folders/files/CSV headers to the new English-named layout without altering maze content, and backfills the `MazeId` header line on every legacy classic and saved-random maze. Makes the author's existing maze library usable under the rewritten app, and eligible for Personal Records from day one of Epic 6.
**FRs covered:** FR-23

### Epic 6: Home Enrichment — Personal Records & First-Activation Explainers
The `RecordsRepository`/`RecordsService`, the Personal Records zone on Home (`record-group`, flat/collapsed/expanded), and first-activation explainer popups for Level/Difficulty/HARD-mode tiers with an on-demand ⓘ affordance. Completes UJ-2 (the run now updates a Personal Record) and completes Home's information architecture.
**FRs covered:** FR-27, FR-28

### Epic 7: (Deferred, P2) New Play Modes — Water Chase & Exploration
Water Chase (rising-water hazard) and Exploration (chained mazes, collectibles, narration) — explicitly low priority per the PRD, to be tackled only after full legacy parity (Epics 1-6). No detailed design or stories are produced in this pass; kept as a placeholder so FR-24/FR-25 stay tracked.
**FRs covered:** FR-24, FR-25

## Epic 1: Foundation & Navigation Shell

Establishes the single composition root and screen router, a functional Home hub (breadcrumb navigation, Settings top-bar access), the immutable domain engine (Grid/Cell/Maze/Position/Level/Difficulty/Duration), the single shared `MazeRepository` and `SettingsRepository` implementations, the shared Tkinter `common/` toolkit, and the automated domain/UI boundary test (AD-9). Delivers a working, themable Home that already routes to (initially minimal) Builder and Player screens.

**FRs covered:** FR-20, FR-21, FR-22, FR-26

### Story 1.1: Domain model foundation

As a developer (the project's author),
I want a pinned, immutable domain model for mazes and gameplay concepts (Grid, Cell, Position, Maze, Level, Difficulty, Duration, MazeId),
So that every later feature builds on one shared, drift-free shape rather than each screen inventing its own.

**Acceptance Criteria:**

**Given** the `domain/` package
**When** Grid/Cell/Position/Level/Difficulty/Duration/Maze/MazeId are defined
**Then** they are immutable value objects with no mutating methods
**And** Cell's wall booleans are computed properties derived from its `"0"`-`"3"` digit, never a separately stored representation

**Given** a Maze value
**When** it is constructed
**Then** it carries a kind tag (`classic`/`sketch`/`saved-random`/`generated`) and an `id: MazeId | None` consistent with the id-eligibility rule (non-`None` only for `classic`/`saved-random`)

**Given** the `domain/` package
**When** its imports are inspected
**Then** it imports nothing from `adapters/` or any UI framework

### Story 1.2: Automated domain/UI boundary test

As the project's author,
I want an automated test that fails the build if domain/application code imports Tkinter or a storage adapter, or if adapters/tkinter screens import each other laterally,
So that the architecture boundary can't erode silently the way it did under the legacy `big_boss` pattern.

**Acceptance Criteria:**

**Given** the test suite
**When** it scans `domain/` and `application/` source
**Then** it fails if any forbidden import (`tkinter`, `adapters`) is found

**Given** `adapters/tkinter/home`, `adapters/tkinter/builder`, `adapters/tkinter/player`
**When** any one imports another directly
**Then** the test fails

**Given** `adapters/tkinter/common/`
**When** it imports `home/`, `builder/`, or `player/`
**Then** the test fails

**Given** the current codebase (before feature code exists)
**When** the test runs
**Then** it passes, establishing the gate ahead of the code it will guard

### Story 1.3: Persistence port interfaces — MazeRepository & SettingsRepository

As a developer,
I want MazeRepository's and SettingsRepository's method signatures defined in `application/` before any storage-consuming feature work starts,
So that the Builder-, Game-, and Home-side stories that follow don't start from divergent assumptions.

**Acceptance Criteria:**

**Given** `application/`
**When** `MazeRepository` is defined
**Then** it exposes saving/loading a Maze and looking one up by `MazeId` (not only by path)

**Given** `application/`
**When** `SettingsRepository` is defined
**Then** it exposes `get(scope, key)` / `set(scope, key, value)` for the `builder`/`game`/`shared` scopes

**Given** the set of `shared`-scope key names (e.g. FR-4's size bounds)
**When** declared
**Then** they live in one module the shell imports, not duplicated per consumer

**And** this story lands before any story that implements or consumes a concrete repository

### Story 1.4: Concrete MazeRepository — single shared CSV read/write implementation

As the maze author,
I want the app to read and write mazes in the existing CSV-based format (entry/exit, optional MazeId, 0/1/2/3 grid),
So that the Builder and the Game share exactly one read/write implementation with no format divergence.

**Acceptance Criteria:**

**Given** a maze CSV in the new-layout format
**When** `MazeRepository.load()` reads it
**Then** entry/exit, the `MazeId` (if present), and the grid decode correctly into a `Maze` value

**Given** a `Maze` being saved as `classic` or `saved-random` for the first time
**When** `MazeRepository.save()` writes it
**Then** a `MazeId` is minted once, via the shared minting function, and written as the header line immediately after entry/exit and before the grid rows

**Given** a `Maze` that already carries a `MazeId`
**When** it is re-saved
**Then** the existing id is carried forward unchanged, never re-minted

**Given** a `sketch` or `generated` maze
**When** it is saved
**Then** no `MazeId` line is written

### Story 1.5: Concrete SettingsRepository — scoped persistence

As the project's author,
I want Builder and Game settings persisted immediately per scope,
So that running both apps at once and changing a setting in one never silently overwrites the other's settings on close.

**Acceptance Criteria:**

**Given** a `builder`-scoped setting change
**When** `set()` is called
**Then** it is written immediately, without touching `game`- or `shared`-scoped values

**Given** the `shared` scope (e.g. FR-4's size bounds)
**When** read from Builder and from Game in the same session
**Then** both observe the identical value

**Given** the implementation
**When** inspected
**Then** get/set operate per key, never via a load-everything/dump-everything cycle

### Story 1.6: Design token system & shared Tkinter widget primitives

As the project's author,
I want the Blueprint design tokens (colors, typography, spacing, radii) and the core widget primitives (tool-btn, hud-chip, icon-btn, pill-btn, kbd-tag + tooltip) implemented once in `adapters/tkinter/common/`,
So that Home, Builder, and Player render consistently without duplicated widget code.

**Acceptance Criteria:**

**Given** the token module
**When** light/dark values are requested
**Then** every paired token (including `accent-on-tint`, `accent-strong-dark`) resolves correctly per theme

**Given** `tool-btn`
**When** one member of a mutually-exclusive group is activated
**Then** only that member shows the active-state styling

**Given** `kbd-tag`
**When** rendered on a control
**Then** the shortcut is always visibly printed (never hover-only) and a separate hover tooltip describes the action's effect

**Given** `adapters/tkinter/common/`
**When** its imports are inspected
**Then** it imports nothing from `home/`, `builder/`, or `player/` (enforced by Story 1.2's test)

### Story 1.7: Single composition root & screen router

As the project's author,
I want one `Tk()` root and one screen router that Home, Builder, and Player register with via a shared `mount(parent, state)` interface,
So that navigating between them is a router call, not three independently-launchable apps cross-importing each other.

**Acceptance Criteria:**

**Given** the shell starts
**When** it launches
**Then** exactly one `Tk()` root exists and Home is the initial screen

**Given** a screen enum member and a `Maze | None` state
**When** the router swaps screens
**Then** the target screen's `mount(parent, state)` is called and the previous screen is torn down/hidden

**Given** Home, Builder, and Player
**When** their imports are inspected
**Then** none imports another directly — all navigation goes through `app/`'s router

### Story 1.8: Home — breadcrumb navigation & Settings access

As a user,
I want Home to show a persistent breadcrumb back to itself from any screen, and a Settings icon reachable from every screen's top bar,
So that I'm never more than one click from the router, regardless of how deep I've navigated.

**Acceptance Criteria:**

**Given** any screen
**When** it renders
**Then** a breadcrumb reflecting the actual navigation depth (e.g. "Home / Player / Classic Maze 4") is shown, with the Home segment always present and clickable

**Given** an earlier breadcrumb segment
**When** clicked
**Then** the router navigates directly to that level

**Given** the top-bar Settings icon
**When** clicked from Home, Builder, or Player
**Then** the settings-window opens as its own window (not routed through Home), and the underlying screen stays mounted behind it

**Given** Home at cold start
**When** the app launches
**Then** Home shows navigation entry points to Builder and Player (even while those screens are still minimal placeholders at this point in the port)

### Story 1.9: Light/dark theme toggle, wired end-to-end

As a user,
I want a single theme toggle whose effect is consistent across Home, Builder, Player, and Settings,
So that switching modes never leaves part of the UI on the wrong palette.

**Acceptance Criteria:**

**Given** the theme is toggled
**When** any mounted screen re-renders
**Then** every token-driven surface switches to its paired dark/light value

**Given** dark mode
**When** wall/corridor colors are checked
**Then** they use the dedicated dark-mode values, never a mechanical inversion of the light-mode hex

**Given** the theme setting
**When** the app restarts
**Then** the previously chosen theme persists, via the shared-scope `SettingsRepository` (Story 1.5)

### Story 1.10: Accessibility floor & keyboard shortcut consistency

As a user,
I want every focusable control in the shared toolkit to be keyboard-operable with a visible, AA-contrast focus indicator, and every keyboard shortcut to map to exactly one action,
So that no action in Home, Builder, or Player is mouse-only, and no shortcut label is ever stale.

**Acceptance Criteria:**

**Given** any `common/` widget (tool-btn, hud-chip, icon-btn, pill-btn, settings rows)
**When** tabbed to
**Then** it shows a visible focus indicator meeting the same AA contrast bar as body text

**Given** any actionable control
**When** operated via keyboard only (Tab + Enter/Space, or its printed `kbd-tag` shortcut)
**Then** it performs the same action as a mouse click

**Given** the locked light/dark token pairs
**When** checked against WCAG AA text/background contrast
**Then** the two dedicated AA-fix tokens (`accent-on-tint`, `accent-strong-dark`) are applied exactly where specified (active-tool-button text, primary-button fill in dark mode)

**Given** the app's one canonical keybinding table
**When** any two registered actions are checked
**Then** each keyboard shortcut maps to exactly one action — collisions are caught by an automated test, not discovered at runtime

**Given** a control's printed `kbd-tag`
**When** compared to the actual shortcut registered for that action in the canonical table
**Then** they match exactly, so no label/tooltip can go stale (fixes the legacy `r` = "Settings"-label-but-"Restart"-behavior collision)

### Story 1.11: Settings dialog survives screen navigation

_Added by the Epic 1 retrospective (2026-08-09) — closes a gap independently deferred three times (Stories 1.8, 1.9, 1.10) without ever being fixed._

As a user,
I want the Settings dialog to never disappear as an accidental side effect of navigating away from the screen it was opened on,
So that closing Settings is always something I chose, not something that happened to me.

**Acceptance Criteria:**

**Given** `SettingsWindow` is open over any screen (Home, Builder, or Player)
**When** a navigation is triggered (a breadcrumb click, the theme toggle, or a keyboard shortcut that calls `Router.navigate()`)
**Then** `SettingsWindow`'s lifecycle is no longer an accidental side effect of the previous screen's frame being torn down — its fate (staying open or closing) is a deliberate, explicit outcome, not an incidental consequence of Tk parent/child destruction

**Given** the chosen deliberate behavior
**When** `Router.navigate()` is invoked while `SettingsWindow` is open
**Then** an automated test asserts the resulting `SettingsWindow` state matches that documented behavior exactly

**Given** the fix
**When** exercised from Home, Builder, and Player
**Then** all three screens exhibit identical behavior — no per-screen divergence

### Story 1.12: Persistence hardening — atomic writes & typed errors

_Added by the Epic 1 retrospective (2026-08-09) — closes gaps deferred in Stories 1.4/1.5 and escalated by Story 1.9, where `ThemeController` became the first unconditional, every-launch consumer of `SettingsRepository.get()`._

As the project's author,
I want maze and settings writes to be crash-safe, and malformed persisted data to raise a typed error instead of crashing the app,
So that an interrupted write or a corrupted file never destroys existing data or takes down the app at startup.

**Acceptance Criteria:**

**Given** a `Maze` or a setting being written
**When** the write is interrupted (process crash or kill) partway through
**Then** the previously saved file is never left corrupted or truncated — both `write_maze_csv` and `write_setting_value` write via a temp-file-plus-rename, never in-place truncation

**Given** a maze CSV file that is truncated, malformed, or has a non-numeric header
**When** `MazeRepository.load()` / `read_maze_csv` reads it
**Then** a typed `LabyrinthesError` subclass is raised, never a raw `IndexError`/`ValueError`

**Given** a settings file that is malformed, corrupted, or removed/replaced between the existence check and the read (a TOCTOU race)
**When** `SettingsRepository.get()` / `JsonSettingsRepository.get()` / `read_setting_value` reads it
**Then** a typed `LabyrinthesError` subclass is raised, never a raw `json.JSONDecodeError`/`FileNotFoundError`

**Given** `ThemeController._load_theme()` (Story 1.9), which reads settings unconditionally on every app launch
**When** the persisted `shared/theme` file is corrupted
**Then** the app no longer crashes at startup — it falls back to the default theme, the same way it already handles an unrecognized-but-well-formed value

## Epic 2: Play a Maze (Game / Player)

Classic maze selection, random maze generation and saving, Levels, Difficulty, HARD mode, movement modes, timer, per-action confirmation prompts, and appearance. Delivers UJ-2's core play loop end-to-end (short of Personal Records, added in Epic 6).

**FRs covered:** FR-9, FR-10, FR-11, FR-12, FR-13, FR-14, FR-15, FR-16, FR-17, FR-18

### Story 2.1: Player maze-selection screen — classic maze browsing

As a player,
I want to browse classic mazes (previous / next / restart) or jump to a specific number,
So that I can pick which maze to play before entering gameplay.

**Acceptance Criteria:**

**Given** the classic maze library, loaded via `MazeRepository`
**When** the selection screen opens
**Then** the first classic maze is shown with previous/next/restart controls and a jump-to-number field

**Given** the previous/next controls
**When** used at the first/last maze
**Then** navigation stays within bounds (no crash, no out-of-range index)

**Given** no classic mazes exist yet
**When** the screen opens
**Then** an inline empty-state message is shown with a way to generate a random maze instead

**Given** a classic maze is picked
**When** confirmed
**Then** the router mounts the gameplay screen with that Maze as state

### Story 2.2: Random maze generation with validation

As a player,
I want to generate a procedural maze by configuring its dimensions and starting position,
So that I can play beyond the classic library.

**Acceptance Criteria:**

**Given** the random-maze dialog
**When** columns/rows are entered outside the shared 3–50 / 3–35 bounds
**Then** inline validation blocks generation with a message (e.g. "Columns must be between 3 and 50.")

**Given** valid dimensions and a starting position
**When** generation is requested
**Then** a solvable maze is produced, entry at the given position, exit at the cell farthest from it

**Given** a freshly generated maze
**When** produced
**Then** its kind is `generated` (not `saved-random`), with no `MazeId`

**Given** a generated maze
**When** the player proceeds to play it
**Then** the router mounts the gameplay screen with it as state

### Story 2.3: Random maze saving, reappears after restart

As a player,
I want to save a generated random maze,
So that I can find and replay it later alongside classic mazes.

**Acceptance Criteria:**

**Given** a `generated` maze in play
**When** the player chooses to save it
**Then** `MazeRepository.save()` writes it and the returned Maze now carries kind `saved-random` and a freshly minted `MazeId`

**Given** a previously saved random maze
**When** the app is restarted and the selection screen opens
**Then** it appears in the selector alongside classic mazes

**Given** a save-name collision
**When** saving
**Then** duplicate-name handling applies, consistent with the Builder's save behavior (FR-5)

### Story 2.4: Gameplay screen foundation — rendering, HUD, baseline movement, win detection

As a player,
I want the gameplay screen to render the maze, entry/exit markers, and the ball, show a live HUD, respond to arrow-key movement, and detect when I reach the exit,
So that I can play a maze end to end.

**Acceptance Criteria:**

**Given** a Maze mounted into the gameplay screen
**When** it renders
**Then** walls draw as solid bars with broken walls as gaps (never dashed), entry/exit render with distinct glyphs, and the ball starts at rest on the entry cell

**Given** the HUD
**When** the screen is active
**Then** Level/Difficulty/Time/Pos chips are shown, each updating on its own trigger

**Given** arrow-key input
**When** pressed
**Then** the ball moves one cell at a time, respecting wall collisions (this story's baseline movement)

**Given** the ball reaches the exit cell
**When** that happens
**Then** a win banner appears inline around the maze-frame, non-blocking, with a continue action, and the run is marked solved

### Story 2.5: Movement modes — Smooth vs Discrete, configurable speed

As a player,
I want to choose between Smooth movement (redirectable mid-move) and Discrete movement (cell by cell), with a configurable speed,
So that I can play in the style I prefer.

**Acceptance Criteria:**

**Given** Discrete mode
**When** an arrow key is pressed
**Then** the ball moves exactly one cell per press (as established in Story 2.4)

**Given** Smooth mode
**When** an arrow key is held or pressed
**Then** the ball moves continuously and can be redirected mid-move without stopping at a cell boundary

**Given** the configurable speed setting
**When** changed
**Then** both modes' underlying tick/animation rate reflects it identically

**Given** the mode is switched mid-session
**When** the next input arrives
**Then** the new mode's behavior applies immediately

### Story 2.6: Levels — progressive visibility (1–4, Max)

As a player,
I want to choose a Level that controls how much of the grid is visible while I solve,
So that I can play at my preferred challenge tier.

**Acceptance Criteria:**

**Given** Level 1
**When** active
**Then** the full grid is visible at all times

**Given** Level 2
**When** active
**Then** the maze is split into rectangular partitions; each visited partition stays shown until a reveal threshold is crossed, then hides again

**Given** Level 3
**When** active
**Then** only one partition is visible at a time

**Given** Level 4
**When** active
**Then** walls stay invisible until collision, hiding again past a discovered-wall threshold

**Given** Level Max
**When** active
**Then** all walls are permanently invisible

### Story 2.7: Difficulty — unified threshold formula

As a player,
I want a Difficulty setting (1–3, unlockable from Level 2 onward) that adjusts the partition size/reveal thresholds Levels use,
So that the challenge scales consistently regardless of which Level I'm on.

**Acceptance Criteria:**

**Given** Level 1 is selected
**When** the Difficulty control is checked
**Then** it is disabled, per the unlockable-from-Level-2 rule

**Given** Level 2 or higher
**When** Difficulty 1/2/3 is selected
**Then** the reveal-threshold calculation applies a single shared formula, used identically by Level 2's and Level 4's mechanics (fixing the legacy inconsistency)

**Given** a Difficulty change mid-session
**When** applied
**Then** the active Level's visibility recalculates using the new threshold immediately

### Story 2.8: HARD mode — invisible ball, fog overlay, status light

As a player,
I want to enable HARD mode, where the ball is invisible while moving and a status light shows ready/moving state in a color I configure,
So that I can play a more demanding hidden-position challenge.

**Acceptance Criteria:**

**Given** HARD mode is active
**When** the ball is moving
**Then** it is not rendered, and a translucent fog scrim covers the maze-frame above the corridor/ball plane but below wall-bars/markers

**Given** the ball comes to rest
**When** movement stops
**Then** the fog overlay disappears instantly (no fade) and the ball renders normally

**Given** the status light
**When** ready vs. moving
**Then** its color follows the user's configured HARD-mode color setting consistently in both states

**Given** the user changes the color setting
**When** HARD mode is next used
**Then** both ready and moving states use the new color without the return-to-ready toggle breaking

### Story 2.9: Timer — optional time limit, timeout message

As a player,
I want to time my solve, optionally against a configurable limit,
So that I can challenge myself and get clear feedback if I run out of time.

**Acceptance Criteria:**

**Given** a run in progress
**When** the gameplay screen is active
**Then** the Time HUD chip updates continuously

**Given** no time limit configured
**When** the player solves the maze
**Then** the elapsed time is shown in the win banner (e.g. "Solved in 00:42.")

**Given** a time limit configured
**When** the limit is reached before the exit is found
**Then** an inline, non-modal failure message appears ("Time's up — the exit wasn't reached."), the run stops, and restart/continue options remain reachable from that message

**Given** the timer
**When** started
**Then** it uses the same `Duration` type used elsewhere in the domain (Story 1.1)

### Story 2.10: Confirmation prompts per action

As a player,
I want to enable/disable, per action, a confirmation prompt before it applies,
So that I don't get interrupted by dialogs I don't want, while keeping guardrails for actions I do.

**Acceptance Criteria:**

**Given** switching mazes, restarting, changing Level, or invalid input
**When** the corresponding confirmation setting is on
**Then** a confirm prompt appears before the action applies

**Given** the same actions
**When** the corresponding setting is off
**Then** the action applies immediately, with no prompt

**Given** each action's confirmation setting
**When** changed in Settings
**Then** it persists via the game-scoped `SettingsRepository` and takes effect without an app restart

### Story 2.11: Appearance — theme + logo

As a player,
I want to toggle the Game's color theme and pick a logo from a list,
So that I can personalize the play experience.

**Acceptance Criteria:**

**Given** the Game's theme toggle
**When** switched
**Then** it uses the same shell-wide theme mechanism established in Story 1.9, not a separate Game-only implementation

**Given** the logo picker
**When** a logo is selected from the list
**Then** it persists via the game-scoped `SettingsRepository` and is shown wherever the Game displays its logo

**Given** no logo yet selected
**When** the Game is first run
**Then** a sensible default logo is shown

## Epic 3: Build and Test a Maze (Builder)

Wall and zone editing, entry/exit marking, new maze / sketch creation with shared size bounds, Sketch/Maze saving, Builder theme, direct cell navigation — plus the complete bidirectional Builder↔Player link (`Test in Player`, `Edit in Builder`), only completable now that both screens exist. Delivers UJ-1 end-to-end, including the build → test → edit loop with no forced trip through Home.

**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8, FR-19

### Story 3.1: New maze / open a sketch

As a maze author,
I want to create a new empty maze by specifying its dimensions, or reopen an existing Sketch,
So that I can start or resume construction work.

**Acceptance Criteria:**

**Given** the New Maze dialog
**When** columns/rows are entered outside the shared 3–50 / 3–35 bounds
**Then** inline validation blocks creation with a message

**Given** valid dimensions
**When** confirmed
**Then** an empty grid opens in the maze-frame — nothing rendered until dimensions are confirmed

**Given** the "Open a Sketch" path
**When** a sketch is selected
**Then** the Builder loads it via `MazeRepository` and resumes editing at its saved state

**Given** the same shared bounds source used by Player's random-maze dialog (Story 2.2)
**When** both dialogs are compared
**Then** they read identical values, never independently duplicated

### Story 3.2: Wall editing — break/restore

As a maze author,
I want to break or restore a wall between two adjacent cells, either in Break mode or by moving the cursor in Pass-through mode,
So that I can trace a path through the maze.

**Acceptance Criteria:**

**Given** a single click on a wall-bar segment
**When** Break mode is active
**Then** that wall breaks/restores and both affected cells' 0/1/2/3 encoding update symmetrically

**Given** Pass-through mode
**When** the cursor moves across a wall
**Then** the wall breaks as the cursor crosses it

**Given** the HUD
**When** a wall changes
**Then** the "walls broken" count updates live

**Given** the save format
**When** a maze with edited walls is saved
**Then** the CSV encoding stays unchanged from the legacy format (Story 1.4's `MazeRepository`)

### Story 3.3: Zone editing — destroy/restore a rectangular zone

As a maze author,
I want to select a rectangular zone and destroy (remove walls) or restore (place walls) it in one operation,
So that I can quickly clear or rebuild larger areas.

**Acceptance Criteria:**

**Given** a click-and-drag across multiple wall segments
**When** released
**Then** the dragged rectangular zone is destroyed or restored as a single operation — a distinct gesture from a single click, never triggered by a slightly-imprecise one

**Given** a zone just destroyed
**When** immediately restored
**Then** it returns exactly to its initial state

**Given** any zone operation
**When** it completes
**Then** the maze's outer border stays closed

### Story 3.4: Entry and exit marking

As a maze author,
I want to mark a cell as the entry and a border cell as the exit,
So that the maze has a defined start and goal.

**Acceptance Criteria:**

**Given** the Set Entry tool active
**When** a cell is clicked
**Then** it becomes the entry, rendered with the `marker` component's distinct glyph

**Given** the Set Exit tool active
**When** a border cell is clicked
**Then** it becomes the exit; before it's set, a `ghost-marker` state is shown, never a default/placeholder position

**Given** an entry or exit is already set
**When** the user redefines it
**Then** a confirmation prompt appears, toggleable off in Settings

### Story 3.5: Direct navigation — "Go to"

As a maze author,
I want to click a cell to move the editing cursor there,
So that I can jump around the grid without stepping cell by cell.

**Acceptance Criteria:**

**Given** the maze-frame
**When** a cell is clicked with no zone-drag in progress
**Then** the editing cursor moves directly to that cell

**Given** the cursor at a new position
**When** rendered
**Then** its position is reflected without needing further input

### Story 3.6: Sketch / Maze save

As a maze author,
I want to save my work either as a Sketch (incomplete, editable) or as a Maze (finished, playable),
So that I can pause construction or publish a finished maze.

**Acceptance Criteria:**

**Given** entry set but exit not set
**When** the author tries to save as a finished Maze
**Then** that path is blocked with an inline message, while Sketch save remains available

**Given** both entry and exit set
**When** saved as a Maze
**Then** it becomes selectable from the Player's classic gallery (Story 2.1) once persisted

**Given** a Sketch save
**When** the status HUD chip is checked
**Then** it reads "Draft"; reopenable from the New Maze dialog's "Open a Sketch" path

**Given** a duplicate save name
**When** saving either kind
**Then** duplicate-name handling applies — no silent overwrite

### Story 3.7: Builder theme toggle

As a maze author,
I want to toggle the editor's color theme,
So that I can work in my preferred light/dark mode.

**Acceptance Criteria:**

**Given** the Builder's theme toggle
**When** switched
**Then** it uses the same shell-wide mechanism established in Story 1.9

**Given** the theme
**When** the app restarts
**Then** the previously chosen theme persists

### Story 3.8: Test in Player — launch the Game from the Builder

As a maze author,
I want to open the Game from the Builder without leaving my editing session,
So that I can immediately confirm a maze is solvable.

**Acceptance Criteria:**

**Given** an active Builder session with a maze in progress
**When** Test in Player is triggered
**Then** the router mounts the Player's gameplay screen directly with the in-progress Maze as state, bypassing Home

**Given** this action
**When** invoked
**Then** it is unconditionally available from an active Builder session, not gated to any maze kind (unlike FR-19's mirror)

**Given** the maze handed to the Player screen
**When** it is rendered there
**Then** it reflects the exact in-progress state at the moment Test in Player was triggered — a live in-memory hand-off through `mount()`, no serialization round-trip and no save required first

### Story 3.9: Edit in Builder — launch the Builder from the Game

As a player,
I want to open the Builder from the Game on the maze I'm currently playing,
So that I can jump straight into editing it.

**Acceptance Criteria:**

**Given** a maze in the Player with a Builder-editable source (`classic` or `saved-random`)
**When** Edit in Builder is triggered
**Then** the router mounts the Builder screen directly with that Maze as state, bypassing Home

**Given** a maze with no Builder-editable source (an unsaved `generated` maze)
**When** the Player screen is checked
**Then** Edit in Builder is not offered at all

**Given** the Game was launched standalone, not via Test in Player
**When** Edit in Builder is used
**Then** it still works — fixing the legacy one-way-only link

## Epic 4: Review Corrections — Builder & Player Polish, Windowing, Configurable Defaults

Delivers the 2026-08-19 course correction: distinct marker/cursor glyphs, reworked Break vs Pass-through semantics, visible zone selection with a second gesture, live entry/exit placement, a reachability counter replacing "Walls broken", configurable defaults (Builder tool, new-maze and random dimensions), a play-again win-banner action, shell windowing (centered, resizable, zoom, fullscreen), a top-bar brand logo, and grouped screen layouts. Amends acceptance criteria delivered by Epics 1-3 (FR-1/2/3/4/10/18) and adds FR-29 through FR-34. Also delivers the 2026-08-25 course correction (Stories 4.11-4.14): a Classic-vs-Creation maze-kind distinction, a keybinding-dispatch fix so screen shortcuts never leak into a focused text field, the maze's own name added to the breadcrumb, and a Classic/Creations/Random sectioned grid gallery. Adds FR-35 through FR-38.

**FRs covered:** FR-29, FR-30, FR-31, FR-32, FR-33, FR-34, FR-35, FR-36, FR-37, FR-38

### Story 4.1: Builder cursor & marker glyphs

As a maze author and a player,
I want the Builder's selected cell to render as a round like the Player's ball, and the entry marker to render as a square everywhere,
So that entry, exit, and the player/builder are never confused by shape alone.

**Acceptance Criteria:**

**Given** the Builder edit screen
**When** a cell is selected
**Then** the cursor renders as a filled circle (the Player-ball glyph), never a blue rectangle outline

**Given** the entry marker (in both the Builder and the Player)
**When** rendered
**Then** it renders as a filled square, distinct from the round player/builder and the diamond exit marker

**Given** the exit marker
**When** rendered
**Then** it keeps the filled diamond glyph

### Story 4.2: Wall-tool semantics — Break vs Pass-through + Space toggle

As a maze author,
I want Break to break walls as I move through them and Pass-through to let me traverse walls freely without altering them, toggling the two with Space,
So that breaking a wall is a deliberate act while traversal is free.

**Acceptance Criteria:**

**Given** Break mode
**When** the cursor moves across a wall
**Then** the wall breaks and the cursor moves (the former Pass-through behavior)

**Given** Break mode
**When** a wall segment is clicked
**Then** it toggles as before (Story 3.2)

**Given** Pass-through mode
**When** the cursor moves across a wall
**Then** the cursor moves and no wall is modified — walls have no effect on the builder

**Given** either mode
**When** the cursor would leave the grid
**Then** movement stops at the grid bounds and the outer border stays closed

**Given** the Space shortcut
**When** pressed
**Then** the tool toggles between Break and Pass-through, registered in the canonical keybinding table

### Story 4.3: Zone selection — colored outline & click-click gesture

As a maze author,
I want zone selection to show a colored outline and to accept a second gesture,
So that I can see what I'm about to destroy/restore and select with either a drag or two clicks.

**Acceptance Criteria:**

**Given** a zone tool (Destroy or Restore) active
**When** the user starts a selection
**Then** a colored rectangle outline is drawn live from the anchor to the current cell, distinct per tool

**Given** a click-and-drag
**When** released on another cell
**Then** the dragged zone is applied (the existing gesture, Story 3.3)

**Given** a plain click on a cell (press + release, no drag)
**When** a zone tool is active
**Then** the click arms the anchor, the outline follows the mouse, and a second click on another cell commits the zone — a single click never applies a zone operation

**Given** an armed anchor
**When** Escape is pressed
**Then** the anchor is cancelled and no zone operation applies

### Story 4.4: Entry/exit live placement — ghost follows cursor, place on click or Enter

As a maze author,
I want the entry/exit icon to follow my cursor in real time and be placed on a click or the Enter key,
So that I can aim precisely before placing and place without the mouse.

**Acceptance Criteria:**

**Given** the Set Entry tool active
**When** the cursor moves
**Then** a ghost square (entry color) follows the cursor on any cell in real time, never resting on a placeholder position

**Given** the Set Exit tool active
**When** the cursor moves
**Then** the ghost diamond follows the cursor on border cells only (existing behavior, Story 3.4)

**Given** either tool active
**When** a cell is clicked or Enter is pressed on the cursor cell
**Then** the marker is placed (ghost for Set Entry, `ghost-marker` pre-placement for Set Exit) and the existing redefinition confirmation prompt is honored

**Given** the Enter shortcut
**When** registered
**Then** it lives in the canonical keybinding table as a Builder-scoped action

### Story 4.5: Reachability counter & click-to-highlight

As a maze author,
I want the HUD to count cells inaccessible from the entry and to outline them when I click the counter,
So that I know what remains to open before the maze is playable.

**Acceptance Criteria:**

**Given** the Builder HUD
**When** an entry is set
**Then** the counter shows the live count of cells unreachable from the entry through open passages

**Given** no entry set
**When** the HUD renders
**Then** the counter reads "—" and is not interactive

**Given** the counter
**When** clicked
**Then** every inaccessible cell is outlined on the grid in a distinct color, toggling on/off and re-rendering when walls or the entry change

**Given** the reachability computation
**When** implemented
**Then** it lives in `domain/` as a pure function (a BFS through open passages), with no UI dependency

### Story 4.6: Configurable defaults — Builder tool, new-maze & random dimensions

As the project's author,
I want the default Builder tool, the default new-maze dimensions, and the default random-maze dimensions to be configurable in Settings,
So that the dialogs and session start match my habits without editing values each time.

**Acceptance Criteria:**

**Given** the Settings window
**When** opened
**Then** a Defaults section offers the default Builder tool and the default dimensions (new-maze and random), each persisting via the scoped `SettingsRepository`

**Given** the Builder New Maze dialog
**When** opened
**Then** its dimension fields default to the configured values, clamped within the shared 3–50 / 3–35 bounds, falling back to the bounds' minimum when unset

**Given** the Player Generate Random dialog
**When** opened
**Then** its dimension fields default to the configured values, with the same clamping and fallback

**Given** a Builder session starting
**When** it opens
**Then** the configured default tool is active (fallback: Break), read in the adapter and passed into the session service — the application layer gains no settings dependency

### Story 4.7: Player — Continue regenerates a random maze with the same params

As a player,
I want the win banner of a generated random maze to offer regenerating another random maze with the same dimensions and entry,
So that I can keep playing the same setup without retyping parameters.

**Acceptance Criteria:**

**Given** a solved `generated` maze
**When** the win banner's continue action is triggered
**Then** a new random maze is generated immediately with the same width, height, and entry position, and mounted in play — no dialog, no re-save

**Given** a solved `classic` or `saved-random` maze
**When** the win banner's continue action is triggered
**Then** the existing Continue behavior is unchanged

**Given** the continue action on a `generated` maze
**When** rendered
**Then** it is labelled distinctly (e.g. "New random maze"), not "Continue"

### Story 4.8: Shell windowing — centered, resizable, zoom, fullscreen

As a user,
I want the app window to open centered, resize freely, zoom the maze, and go fullscreen, with the Settings window behaving the same way,
So that I can work in the window arrangement I prefer.

**Acceptance Criteria:**

**Given** the shell starts
**When** the root window opens
**Then** it is centered on screen and resizable in both directions

**Given** a screen with a maze canvas (Builder, Player)
**When** the window is resized
**Then** the canvas re-renders to fit the available space

**Given** Ctrl+wheel (or `+`/`-`)
**When** used over a maze canvas
**Then** the cell size zooms in/out and the canvas re-renders

**Given** the F11 shortcut
**When** pressed
**Then** the window toggles fullscreen, registered in the canonical keybinding table

**Given** the Settings window
**When** opened
**Then** it is centered, resizable, and supports F11 fullscreen, and is never silently closed by a navigation frame teardown

### Story 4.9: Top-bar brand logo follows the logo setting

As a user,
I want the top bar to show the brand logo before the app name, matching my chosen logo setting,
So that the app has an identifiable brand mark.

**Acceptance Criteria:**

**Given** any screen's top bar
**When** it renders
**Then** the logo image for the current logo setting is shown top-left before the "Labyrinthes" name

**Given** the logo setting (Story 2.11)
**When** changed and the screen re-mounts
**Then** the top bar shows the newly chosen logo

**Given** the logo rendering
**When** implemented
**Then** it reuses the shared logo loader in `application/` and never couples `common/` to a screen's asset folder

### Story 4.10: Screen layout — labeled blocks separated from the maze

As a user,
I want the Builder's and Player's controls and displays grouped into labeled blocks on the sides and top, clearly separated from the maze,
So that the UI reads as tidy panels around a focused grid.

**Acceptance Criteria:**

**Given** the Builder edit screen
**When** it renders
**Then** tools are grouped under labeled headings in side blocks (e.g. Tools, Markers), the HUD sits on top, and the maze renders inside its own bordered maze-frame separated from the side blocks

**Given** the Player screens
**When** they render
**Then** the existing labeled groups are tidied into consistent blocks clearly separated from the maze frame

**Given** the group headings
**When** rendered
**Then** they use the shared typography tokens, with consistent spacing across Builder and Player

### Story 4.11: Classic vs. Creation maze kind

_Added by the 2026-08-25 course correction — see `sprint-change-proposal-2026-08-25.md`._

As a maze author,
I want a maze I save as finished from the Builder to be tagged `Creation`, never `Classic`,
So that "Classic" stays reserved for the mazes the project's developer ships with the game, matching the legacy app's own `Labyrinthes_classiques/` vs `Labyrinthes_creation/` split.

**Acceptance Criteria:**

**Given** the Builder's "Save as Maze" (finished) flow
**When** confirmed
**Then** the resulting `Maze` carries `MazeKind.CREATION`, never `MazeKind.CLASSIC`

**Given** `MazeKind.CREATION`
**When** a `Maze` of that kind is saved
**Then** `MazeRepository` mints a `MazeId` exactly as it does for `CLASSIC`/`SAVED_RANDOM` (Story 1.4's minting rule extended)

**Given** the Records eligibility check (Story 6.1's `RecordsService.record_completion`, once implemented)
**When** a `CREATION` maze is won
**Then** a record is written, on the same terms as `CLASSIC`/`SAVED_RANDOM`

**Given** existing `CLASSIC`-folder local saves made under the pre-correction behavior
**When** this story lands
**Then** they are not silently reinterpreted — no automatic reclassification is in scope here (Epic 5/migration territory if ever needed for real shipped data)

### Story 4.12: Screen shortcuts never fire while a text-entry dialog is focused

_Added by the 2026-08-25 course correction — see `sprint-change-proposal-2026-08-25.md`._

As a maze author,
I want to type any character into a maze-name field without a screen-wide keyboard shortcut firing instead,
So that saving a maze named e.g. "destroy" or "break" doesn't accidentally trigger the Destroy Zone or Break tool.

**Acceptance Criteria:**

**Given** any screen-scoped keyboard shortcut registered via `bind_shortcut()`
**When** the current Tk focus widget is a text-entry field (`tk.Entry`/`tk.Text`) inside an open dialog
**Then** the shortcut's callback does not fire and the keystroke reaches the entry field normally

**Given** `_SaveNameDialog`'s and `SaveMazeDialog`'s per-letter `<KeyPress-s/S/t/T>` `"break"` guards
**When** this story lands
**Then** they are deleted — the general dispatch guard supersedes them, so no dialog needs its own allowlist

**Given** `NewMazeDialog`'s and `GenerateRandomDialog`'s numeric entry fields
**When** checked against this same guard
**Then** they are covered too, even though no prior collision was reported for them (defense-in-depth, not a per-field patch)

**Given** the canonical keybinding table's collision test (Story 1.10)
**When** this story lands
**Then** it still passes unchanged — this is a dispatch-time fix, not a table change

### Story 4.13: Breadcrumb shows the maze's own name

_Added by the 2026-08-25 course correction — see `sprint-change-proposal-2026-08-25.md`._

As a user,
I want the breadcrumb to show the specific maze's own saved name, in addition to its kind,
So that I always know exactly which maze I'm in, not just what category it belongs to.

**Acceptance Criteria:**

**Given** the Builder with a maze loaded (new, opened sketch, or Test-in-Player round-trip)
**When** the top bar renders
**Then** a new trailing segment carrying that maze's saved name is appended after "Builder" (or an in-progress/unsaved indicator, for a maze with no name yet) — "Builder" itself is untouched

**Given** the Player with a maze mounted (classic, creation, saved-random, or generated)
**When** the top bar renders
**Then** a new trailing segment carrying that maze's saved name is appended *after* the existing kind-derived segment (e.g. "Home / Player / Classic / 10x10edf") — the kind segment is never replaced or removed; an unsaved `generated` maze simply gets no name segment appended (it has none)

**Given** the current `Maze` domain value
**When** inspected
**Then** it has no `name` field (name is a storage-layer/filename concept) — this story resolves how the name is threaded from `MazeRepository`/the save flow through to the screen's breadcrumb without adding a UI concern to `domain/`

### Story 4.14: Player selection screen — grid gallery split into Classic / Creations / Random

_Added by the 2026-08-25 course correction — see `sprint-change-proposal-2026-08-25.md`. Depends on Story 4.11 (needs the `Creation` kind to populate its section)._

As a player,
I want the maze-selection screen to show a scrollable card grid split into Classic, Creations, and Random sections,
So that I can browse my library the way the locked UX mockup always intended, now that maze-frame rendering exists to draw the cards from.

**Acceptance Criteria:**

**Given** the Player's maze-selection screen
**When** it renders
**Then** it shows a scrollable card grid with three labeled sections — Classic, Creations, Random — per `key-player-selection.html`'s `gallery-grid`/`maze-card` pattern

**Given** a section with no mazes
**When** rendered
**Then** that section alone shows an inline empty-state message (e.g. Creations before the player has saved one) — the other populated sections stay unaffected

**Given** a maze card
**When** clicked or activated via keyboard
**Then** the router mounts the gameplay screen with that Maze as state (same commit behavior as today's pager)

**Given** the "Generate random" entry point
**When** rendered
**Then** it stays a clearly separate action, not a fourth section card (existing behavior, FR-10)

**Given** the accessibility floor (NFR6)
**When** the grid is keyboard-navigated
**Then** every card is reachable and operable via Tab + Enter/Space, with a visible focus indicator

## Epic 5: Legacy Data Migration to English

A one-time conversion script that renames the legacy French-named folders/files/CSV headers to the new English-named layout without altering maze content, and backfills the `MazeId` header line on every legacy classic and saved-random maze. Makes the author's existing maze library usable under the rewritten app, and eligible for Personal Records from day one of Epic 6.

**FRs covered:** FR-23

### Story 5.1: Migration script — folder & file renaming

As the project's author,
I want a one-time script that renames the legacy French-named data folders and files to the new English-named layout,
So that my existing maze library becomes usable under the rewritten app.

**Acceptance Criteria:**

**Given** the legacy folders (`Labyrinthes_classiques/`, `Labyrinthes_creation/`, `Labyrinthes_croquis/`, `Labyrinthes_aléatoires_enregistrés/`)
**When** the script runs
**Then** each is renamed/moved to its new English-named equivalent, using the same path constants `MazeRepository` uses (Story 1.4)

**Given** the maze CSV content (entry/exit lines + grid)
**When** files are moved
**Then** their content — including the 0/1/2/3 grid values — is copied byte-for-byte unchanged (this story only renames/relocates; it does not touch file content)

**Given** the per-folder `#_Doc_index.csv` files
**When** migrated
**Then** they're renamed/rewritten consistently so the index still lists the moved files correctly

**Given** the script completes
**When** the legacy folders are checked
**Then** the French-named layout no longer exists on disk — no side-by-side copy, no built-in rollback beyond whatever backup the author took beforehand

### Story 5.2: Migration script — settings CSV header renaming

As the project's author,
I want the legacy settings file's `entité,nom,valeur` header and `builder`/`parcoureur` entity tags renamed to the new English-named layout,
So that Settings persistence (Epic 1) reads a consistent, English-named file from day one.

**Acceptance Criteria:**

**Given** `Autres/Parametres_defaut.csv`
**When** the script runs
**Then** its header and entity-tag values are renamed to their new English equivalents without altering the stored setting values themselves

**Given** the renamed settings file
**When** `SettingsRepository` (Story 1.5) reads it
**Then** every existing default setting value is present, unchanged, under its new key

### Story 5.3: Migration script — MazeId backfill

As the project's author,
I want the migration script to mint and write a `MazeId` for every legacy classic and saved-random maze it converts,
So that my existing maze library is eligible for Personal Records from day one.

**Acceptance Criteria:**

**Given** a migrated classic or saved-random maze with no `MazeId`
**When** the script processes it
**Then** it mints one via `MazeRepository`'s shared minting/writer routine (Story 1.4), not a bespoke migration-script serializer, and inserts it immediately after the entry/exit header lines, before the grid rows

**Given** a migrated sketch
**When** processed
**Then** no `MazeId` line is added

**Given** the migration completes
**When** any migrated classic/saved-random maze is reloaded via `MazeRepository`
**Then** it carries a non-`None` `id`

## Epic 6: Home Enrichment — Personal Records & First-Activation Explainers

The `RecordsRepository`/`RecordsService`, the Personal Records zone on Home (`record-group`, flat/collapsed/expanded), and first-activation explainer popups for Level/Difficulty/HARD-mode tiers with an on-demand ⓘ affordance. Completes UJ-2 (the run now updates a Personal Record) and completes Home's information architecture.

**FRs covered:** FR-27, FR-28

### Story 6.1: RecordsRepository & RecordsService

As a developer,
I want a single `RecordsRepository` (storage) and a `RecordsService` (application) implementing the "is this a new best" comparison and the "most-recently-set-or-broken first" ordering,
So that Home and Player never invent divergent comparison logic.

**Acceptance Criteria:**

**Given** `application/`
**When** `RecordsRepository` is defined
**Then** its port stays minimal and mechanical: `get_best(maze_id, level, difficulty) -> Record | None`, `list_all() -> list[Record]` (unsorted), `set_best(record)` (raw write) — no "record and decide" method on the port itself

**Given** `RecordsService.record_completion(maze, level, difficulty, time)`
**When** called
**Then** it checks `maze.kind` is `classic` or `saved-random` before touching the repository, and only overwrites the stored record if the new time is faster

**Given** `RecordsService`'s read path for display
**When** called
**Then** results come back ordered most-recently-set-or-broken first

**Given** `Record`
**When** defined
**Then** it is an immutable value object (`maze_id`, `level`, `difficulty`, `time`, `set_at`) living in `application/`, not `domain/`

### Story 6.2: Player records a completion on win

As a player,
I want my fastest completion time recorded automatically when I win a classic or saved-random maze, at the Level and Difficulty I used,
So that my Personal Records reflect real runs without extra steps.

**Acceptance Criteria:**

**Given** a win (Story 2.4's win detection) on a classic or saved-random maze
**When** it happens
**Then** `RecordsService.record_completion(maze, level, difficulty, elapsed_time)` is called with `maze.id` passed straight through, no separate null check

**Given** a win on an unsaved `generated` maze
**When** it happens
**Then** no record is written — `RecordsRepository` is never reached

**Given** a record already exists for that (maze, Level, Difficulty) combination
**When** the new time is slower
**Then** the stored record is left unchanged

**Given** a record already exists
**When** the new time is faster
**Then** it replaces the stored one

### Story 6.3: Home — Personal Records zone with record-group

As a player,
I want Home to show my Personal Records grouped per maze, with an inviting empty state before I've won anything,
So that I can see my progress at a glance.

**Acceptance Criteria:**

**Given** no records exist yet
**When** Home renders
**Then** the Personal Records zone shows an inviting inline empty-state message, no fabricated scores

**Given** a maze with exactly one (Level, Difficulty) record
**When** rendered
**Then** its `record-group` row is flat, no chevron

**Given** a maze with 2+ combo records
**When** rendered
**Then** the row is collapsed by default: chevron, maze name, and the most-recently-set-or-broken combo as headline — never a cross-combo "fastest" figure

**Given** a collapsed multi-combo row
**When** its chevron/header is clicked or activated via Enter/Space
**Then** it expands to an indented combo list ordered canonically by Level then Difficulty ascending

**Given** the Personal Records zone as a whole
**When** multiple mazes have records
**Then** rows are ordered most-recently-set-or-broken first

### Story 6.4: First-activation explainer — Level and Difficulty tiers

As a player,
I want an explainer popup the first time I activate a given Level or Difficulty tier, with an ⓘ affordance to reopen it on demand,
So that I understand what each tier changes without hunting for documentation.

**Acceptance Criteria:**

**Given** a Level or Difficulty tier the player has never activated before
**When** it's activated
**Then** an explainer popup describing that tier's effect appears automatically, anchored near the control

**Given** the ⓘ affordance next to the Level/Difficulty control
**When** clicked at any time
**Then** the same explainer reopens, regardless of the auto-show setting

**Given** the "auto-show on first activation" setting turned off in Settings
**When** a never-before-seen tier is activated
**Then** no popup auto-shows, but the ⓘ affordance still works

**Given** the explainer's wording
**When** read
**Then** it stays plain and non-alarmist, consistent with the product's Voice and Tone

### Story 6.5: First-activation explainer — HARD mode tier

As a player,
I want the same first-activation explainer treatment for HARD mode as for Level/Difficulty tiers,
So that every tier gets a consistent, non-alarmist introduction.

**Acceptance Criteria:**

**Given** HARD mode has never been activated before
**When** it's activated
**Then** the explainer popup fires automatically (subject to the same auto-show setting as Story 6.4), describing the ball-invisible-during-movement effect factually, not as a warning

**Given** the ⓘ affordance next to the HARD-mode control
**When** clicked
**Then** the same explainer reopens on demand

**Given** the "seen" state for each tier (Level, Difficulty, HARD mode)
**When** persisted
**Then** it survives app restarts, via the game-scoped `SettingsRepository`

## Epic 7: (Deferred, P2) New Play Modes — Water Chase & Exploration

Water Chase (rising-water hazard) and Exploration (chained mazes, collectibles, narration) — explicitly low priority per the PRD, to be tackled only after full legacy parity (Epics 1-6). Per the PRD's own framing (§4.6, §8), design detail remains to be refined when the time comes; this epic intentionally carries no stories yet. It is kept as a placeholder so FR-24/FR-25 stay tracked in the coverage map rather than silently dropped, and should be revisited with a fresh epics/stories pass once Epics 1-6 have shipped and the concrete design questions the PRD leaves open (breath-reserve mechanic, exploration map structure, narration format) have been settled.

**FRs covered:** FR-24, FR-25
