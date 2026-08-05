---
title: Labyrinthes — Modular Rewrite
status: final
created: 2026-08-04
updated: 2026-08-05
---

# PRD: Labyrinthes — Modular Rewrite

## 0. Document Purpose

This PRD scopes the rewrite of the Labyrinthes project on the `rewrite` branch: what must be ported from the two legacy monoliths (`Creer_labyrinthes.py`, `Labyrinthes_copy.py`), what should be improved or fixed along the way, and what is deliberately deferred. `[ASSUMPTION: no external input beyond the legacy code and CLAUDE.md was provided — this PRD relies solely on those sources plus the conversation with the author; see §9]` It is the reference for downstream phases (architecture, epics/stories, incremental development). The Glossary (§3) fixes the vocabulary; Features (§4) list functional requirements numbered globally (FR-1 through FR-28) so downstream artifacts (architecture, stories) can reference them stably. The detailed feature inventory extracted from the legacy code and the full list of known defects live in `addendum.md`.

**Update note (2026-08-05):** FR-26 through FR-28 were added after the UX phase (`ux-Labyrinthes-2026-08-04`) finalized a Home screen — a navigation hub with a Personal Records module — that this PRD had not captured. The Architecture phase hit the same gap, amended its navigation model around it, and explicitly deferred extending the architecture for Personal Records until this PRD update landed; see `_bmad-output/planning-artifacts/architecture/architecture-Labyrinthes-2026-08-04/.memlog.md`. The same pass also added an Accessibility NFR (§6), two Glossary entries (§3: Home, Personal Record), and amended UJ-1/UJ-2 (§2.2) to route through Home. That same PRD update left the Personal Records display-grouping question open (former §8.5); a follow-up UX pass on `ux-Labyrinthes-2026-08-04` (updated 2026-08-05) resolved it with a per-maze, expandable `record-group` pattern, folded back into FR-27 below and closing the Open Question. The migration-approach question (former §8, item 4) is also now resolved: FR-23 commits to a one-time, in-place conversion script, folded back into FR-23 below. Separately, while extending its own spine to cover FR-27's Personal Records, the Architecture phase added a Maze ID header line to the maze CSV format (an additive, Max-approved exception to the "never re-encoded" contract) — folded back into FR-20, FR-23, and §6 here so the PRD's data-contract description doesn't diverge from the now-closed architecture spine.

**Language note:** this PRD, and every project artifact from the `rewrite` branch onward (code, identifiers, comments, UI strings, on-disk data, documentation), is written in English — see §6. Only the author's live conversation with the assistant stays in French; that choice does not extend to anything the project produces.

## 1. Vision

Labyrinthes is a game where maze design and maze solving are two faces of the same product: a strong identity built on an original cell-encoding scheme (0/1/2/3), which powers both a construction editor and a play mode with levels, difficulty settings, and a timer.

The project started as self-taught, unevenly-skilled code, and is becoming a clean, modular, tested codebase — laying the groundwork now (strict logic/UI separation) for a future release beyond desktop (web, mobile).

**Explicit anti-goal:** from the legacy project, only its *features* and its *cell-encoding scheme* deserve to survive. The implementation, the class breakdown, and the "big_boss" pattern described in `CLAUDE.md` are learning-era hacking — not to be reproduced or imitated in the rewrite.

## 2. Target User

### 2.1 Jobs To Be Done

- As the project's author, I want to add a new feature without touching three different files or untangling a `big_boss` reference graph.
- As a player (myself today, potentially a wider audience later), I want to build mazes and solve them, with gameplay mechanics that genuinely exploit the 0/1/2/3 cell-encoding scheme.
- As a future maintainer of a publishable version, I want the game engine to assume nothing about the interface (Tkinter today, possibly something else tomorrow).

### 2.2 Key User Journeys

*Lightweight journeys — solo project, a single user role for now.*

- **UJ-1. Build a maze.** From Home, the author opens the Builder, creates a new maze at the desired dimensions, breaks walls to trace a path, places an entry and an exit, then saves either as a Sketch (work in progress) or as a finished Maze — reusable from the Game. Realizes FR-1 through FR-5, FR-26.
- **UJ-2. Play a classic maze.** From Home, the player opens the Game, picks a classic maze (or generates a random one), selects a Level and a Difficulty, then navigates the ball to the exit; the run ends with a success screen offering to continue and, for a classic or saved-random maze, updates the player's Personal Record for it on Home. Realizes FR-9, FR-10, FR-12, FR-13, FR-15, FR-26, FR-27, FR-28.
- **UJ-3. (deferred) Outrun the rising water.** The player enables the Water Chase mode: water falls and progressively flows through the maze while the player searches for the exit, their breath reserve limiting how long they can stay submerged. Realizes FR-24.

## 3. Glossary

- **Grid** — the 2D structure of cells that makes up a maze.
- **Cell** — a grid square, encoded as a `"0"`/`"1"`/`"2"`/`"3"` string, where bit 1 marks a top wall and bit 2 a left wall (a cell's bottom/right walls are its neighbor's top/left walls). This is the project's core invention and must be preserved as-is — digits, not language-dependent.
- **Wall** — a boundary between two cells, broken or restored through Builder editing.
- **Entry / Exit** — the two cells marking a maze's starting point and goal.
- **Ball** — the entity the player controls in the Game.
- **Classic maze** — a hand-built maze created via the Builder and shipped with the game.
- **Random maze** — a maze procedurally generated by the Game.
- **Sketch** — an incomplete maze save, still editable in the Builder.
- **Level** — a progressive-visibility setting during solving (1 through 4, plus "Max"), derived from how the encoded grid is partitioned.
- **Difficulty** — a setting (1 through 3) that adjusts the thresholds/sizes used by Levels.
- **HARD mode** — a play mode where the ball is rendered invisible during movement.
- **Builder** — the maze editing/construction application.
- **Game** (or Player) — the maze solving/navigation application.
- **Home** — the app's entry screen and sole general router between the Builder and the Game; also hosts Settings access and the Personal Records zone.
- **Personal Record** — the player's fastest recorded completion time for a given classic or saved-random maze at a specific Level and Difficulty, stored locally and shown on Home.

## 4. Features

### 4.1 Construction (Builder)

**Description:** tools to edit a maze cell by cell or by zone, with saving to two formats (editable Sketch, playable Maze). Realizes UJ-1.

#### FR-1: Wall editing
The user can break or restore a wall between two adjacent cells, either in "Break" mode or by moving the cursor in "Pass-through" mode.
**Consequences (testable):**
- Breaking a wall updates the 0/1/2/3 encoding of both affected cells symmetrically.
- The save format stays unchanged from the legacy format (see FR-20).

#### FR-2: Zone editing
The user can select a rectangular zone of cells and destroy it (walls removed) or restore it (walls placed) in a single operation.
**Consequences (testable):**
- The operation is symmetric: restoring a zone just destroyed returns it to its initial state.
- The maze's outer border stays closed after the operation.

#### FR-3: Entry and exit
The user can mark a cell as the entry and a border cell as the exit, with a confirmation prompt if an existing entry/exit is being redefined.

#### FR-4: New maze / open a sketch
The user can create a new empty maze by specifying its dimensions (columns/rows, bounded to 3–50 columns and 3–35 rows), or reopen an existing Sketch to keep editing it.
**Consequences (testable):**
- The bounds are defined once, in settings, and read by both the Builder and the Game — not duplicated as hardcoded UI constants (fixes the legacy defect described in the addendum's "Duplicated size bounds").

#### FR-5: Sketch / Maze save
The user can save their work either as a Sketch (incomplete, editable) or as a Maze (finished, playable from the Game), with duplicate-name handling.
**Out of Scope:** an automated migration tool for existing Sketches/Mazes on disk is not part of this FR — that's covered separately by FR-23.

#### FR-6: Builder theme
The user can toggle the editor's color theme (light/dark).

#### FR-7: Direct navigation
The user can click a cell to move the editing cursor there ("Go to").

#### FR-8: Launch the Game from the Builder
The user can open the Game from the Builder without leaving their editing session.
**Notes:** in the legacy app the corresponding button exists but is disabled — the rewrite must expose this entry point, not just port the disabled code. Per FR-26, this is the `Test in Player` action — one of the two contextual routes between Builder and Game that bypass Home.

### 4.2 Navigation — Home

**Description:** the single entry point and general router between the Builder and the Game, plus the Personal Records module. `[NOTE: this section did not exist in the original PRD — added 2026-08-05 to reconcile with the finalized UX (`ux-Labyrinthes-2026-08-04`), which fixed Home as the app's sole router and introduced Personal Records; the Architecture phase hit the same gap and deferred it here, see §0's update note.]` Realizes UJ-1, UJ-2.

#### FR-26: Home screen navigation hub
The user opens the app to a Home screen that routes to the Builder and to the Game. Home is the sole general router between the Builder and the Game — no persistent switcher between them exists elsewhere.
**Consequences (testable):**
- Two contextual exceptions bypass Home for a tight build/test loop: `Test in Player` (open the Game directly on the maze currently open in the Builder — FR-8), available unconditionally from an active Builder session, and `Edit in Builder` (open the Builder directly on the maze currently loaded in the Game — FR-19), gated to mazes with a Builder-editable source (a classic or a saved random maze; not an unsaved procedurally-generated maze, which has no Builder file to open).
- Every other transition between the Builder and the Game passes back through Home.
- Every screen carries a persistent, clickable path back to Home (and to any intermediate level), so a user is never more than one click from the router regardless of how deep they've navigated.
- Settings is reachable from a top-bar icon present on every screen (Home, Builder, Game alike) — it is not routed through Home specifically.
**Notes:** FR-8 and FR-19 stay valid as the description of these two named exceptions; this FR is what makes them exceptions rather than a general standalone link between two independently-launchable apps.

#### FR-27: Personal Records (local best-times)
On winning a maze that has a stable identity (a classic maze or a saved random maze — not an unsaved procedurally-generated maze), the system records, locally, the player's fastest completion time for that specific maze **at the Level and Difficulty the run used**, and Home's Personal Records zone displays these records, most-recently-set-or-broken first.
**Consequences (testable):**
- A record is scoped to the (maze, Level, Difficulty) combination — a Level 1 run and a Level 4 run on the same maze are different records, never compared against each other, since Level/Difficulty change how much of the grid is visible during the solve (FR-12, FR-13).
- Home's Personal Records zone groups a maze's records into a single, expandable entry rather than one row per (maze, Level, Difficulty) combination: a maze with only one recorded combo renders flat; a maze with several renders collapsed behind its most-recently-set-or-broken combo, expanding to list every combo it holds a record for. See the UX spec's `record-group` pattern for the interaction detail.
- A new completion time replaces the stored record for that (maze, Level, Difficulty) combination only if it is faster than the existing one.
- Before any maze has been won, the Personal Records zone shows an inviting empty-state message rather than a fabricated score.
- Records are local-only this milestone: no server sync, no shared/community leaderboard (see §5).
- The underlying data model doesn't preclude a later extension to a community maze library or shared leaderboards, but that extension is explicitly out of scope now.
**Notes:** the display-grouping question this FR originally left open (Open Question §8.5) is resolved — see the consequence above and `ux-Labyrinthes-2026-08-04` (updated 2026-08-05).

### 4.3 Game — Selection and progression

**Description:** the player's path through the available mazes. Realizes UJ-2.

#### FR-9: Classic maze selection
The user can browse classic mazes (previous / next / restart) or jump directly to a given number.

#### FR-10: Random maze generation
The user can generate a procedural maze by configuring its dimensions (same 3–50 column / 3–35 row bounds as FR-4) and starting position, with input validation.

#### FR-11: Random maze saving
The user can save a generated random maze, and later find it again in the selector alongside classic mazes.
**Consequences (testable):**
- A saved random maze appears in the selection list after the application restarts.
*(In the legacy app this writes a file nothing else ever reads back — explicitly fixed here, see addendum.)*

#### FR-12: Levels
The user can choose a Level (1 through 4, plus "Max") that controls progressive grid visibility during solving, derived from how the 0/1/2/3-encoded grid is partitioned. See the addendum's "Level detail" section for the exact per-Level visibility mechanics (partition reveal/hide rules).

#### FR-13: Difficulty
The user can choose a Difficulty (1 through 3, unlockable from Level 2 onward) that adjusts the partition size or reveal thresholds used by Levels.
**Consequences (testable):**
- The reveal-threshold calculation follows a single, consistent formula, applied identically regardless of which Level is active (fixes a legacy inconsistency between Level 2 and Level 4, see addendum).

#### FR-28: First-activation explainer for Level, Difficulty, and HARD-mode tiers
The first time the user activates a given Level, Difficulty, or HARD-mode tier, an explainer popup describes what that tier changes; an ⓘ affordance next to the corresponding control reopens the same explainer on demand at any time.
**Consequences (testable):**
- Every tier gets this treatment — Level, Difficulty, and HARD mode (FR-14) alike.
- Auto-show-on-first-activation is configurable off in Settings; the on-demand ⓘ affordance keeps working regardless of that setting.
- The explainer's wording stays plain and non-alarmist (e.g. describing HARD mode's effect factually rather than as a warning), consistent with the product's voice and tone as specified in the UX spec.

#### FR-16: Timer
The user can time their maze solve, with an optional configurable time limit and a message on timeout.
*(Present but never wired up in the legacy app — picked back up and finished here.)*

#### FR-17: Confirmation prompts
The user can enable/disable, per action (switching mazes, restarting, Level change, invalid input...), a confirmation prompt before that action applies.

### 4.4 Game — Modes and presentation

#### FR-14: HARD mode
The user can enable a mode where the ball becomes invisible during movement, with a visual state indicator (light) whose color follows the user's configured setting.
**Consequences (testable):**
- Changing the indicator's color in settings updates its state-toggling behavior without breaking it (fixes a hardcoded value in the legacy app, see addendum).
- First activation triggers the same explainer popup as any other tier (FR-28).

#### FR-15: Movement modes
The user can choose between Smooth movement (direction can be redirected mid-move) and Discrete movement (cell by cell), with a configurable speed.

#### FR-18: Appearance
The user can toggle the Game's color theme and pick a logo from a list.

#### FR-19: Launch the Builder from the Game
The user can open the Builder from the Game when it was launched standalone (not only when the Game was itself opened from the Builder).
**Notes:** in the legacy app this link only works one way — explicitly fixed here. Per FR-26, this is the `Edit in Builder` action, gated to mazes with a Builder-editable source (a classic or a saved random maze).

### 4.5 Cross-cutting — Data and integration

#### FR-20: Maze data format
The system reads and writes mazes (classic, sketch, saved random) in the existing CSV-based format: the first two lines for entry/exit, then the grid encoded as 0/1/2/3. Classic and saved-random mazes additionally carry a stable Maze ID as a third header line, positioned right after the entry/exit lines and before the grid rows — sketches and freshly-generated-but-unsaved random mazes carry no such line, since they have no stable identity to key (FR-27).
**Consequences (testable):**
- Existing maze data remains readable without conversion loss (subject to the folder/header renaming and Maze ID backfill covered by FR-23).
- The Builder and the Game share the same read/write logic for this format (no divergence between the two applications) — including the Maze ID line: it is minted once, when a maze is first saved as classic or saved-random, and carried forward unchanged on every subsequent re-save (e.g. editing and re-saving a classic maze never mints a new one).
- This is the one addition to the format the "never re-encoded" contract (§6) tolerates: existing fields keep their exact meaning and position, and the Maze ID line is purely additive.

**Notes:** the Maze ID is what FR-27's Personal Records key a record on, instead of the maze's filename — so a record survives the maze file being renamed.

#### FR-21: Settings persistence
The system persists each application's (Builder, Game) default settings between sessions.
**Consequences (testable):**
- Running the Builder and the Game at the same time and changing settings in one does not silently overwrite the other's settings on close (fixes a legacy defect, see addendum).

#### FR-22: Keyboard shortcuts
Every keyboard shortcut maps to exactly one action, and the label/tooltip shown to the user accurately describes the real shortcut.
*(Fixes a legacy collision where `r` triggers "Restart" while its tooltip claims "Settings".)*

#### FR-23: Legacy data migration to English
The system provides a one-time conversion script — not a dual-layout compatibility shim — that converts existing on-disk legacy data — folder names, save file naming, and CSV headers (e.g. the `entité,nom,valeur` settings file) — to the new English-named layout, without altering the maze content itself (cell encoding, entry/exit, saved settings values).
**Consequences (testable):**
- Every maze and settings file present under the legacy French-named layout is reachable, unchanged in content, under the new English-named layout after the script runs.
- The 0/1/2/3 cell-encoding values are copied as-is — migration touches naming, not the encoding.
- The script renames/moves legacy files and folders in place: once it completes, the French-named layout no longer exists on disk — there is no side-by-side copy and no built-in rollback beyond whatever backup (e.g. a git commit or manual copy) the author takes before running it.
- The script also mints and writes FR-20's Maze ID header line for every legacy classic and saved-random maze it converts — legacy files predate that concept, so this is the one point where migration adds a line rather than only renaming, and it's what makes every pre-existing maze eligible for a Personal Record (FR-27) from day one.
**Notes:** resolves Open Questions §8's former migration-approach item — see the addendum's "Legacy-to-English data migration" section for the concrete path/header inventory the script must cover.

### 4.6 Game — New modes (deferred, P2)

**Description:** two new play modes, low priority — to be tackled after the existing features (§4.1-4.5) are fully ported. `[ASSUMPTION: design detail remains to be refined when the time comes; this PRD only captures intent, and more feature ideas are expected to surface while rewriting — see §9]`

#### FR-24: Water Chase mode
The player can face a maze where water falls from above and naturally flows downward, progressively filling the maze. Several difficulty tiers define an underwater breath reserve (in number of cells or in time) beyond which the player fails.

#### FR-25: Exploration mode
The player can move through several mazes chained together on a 2D map, with collectible items (e.g. keys) scattered across the different mazes, and optional narration accompanying progress toward the end of the exploration.

## 5. Explicit Non-Goals

- The rewrite does not reproduce the legacy architecture (the "big_boss" pattern, a single "Entité supérieure" class that owns everything) — only user-facing behavior and the data format are ported.
- This milestone does not settle the final stack choice for a future web/mobile target — it only requires the engine be ready to accommodate one (§6, architecture NFR).
- No user accounts, multiplayer, or online features in this milestone — Personal Records (FR-27) stay local-only; any future community maze library or shared leaderboards are out of scope beyond that.
- No monetization considered at this stage.

## 6. Cross-Cutting Constraints (NFRs)

- **Logic/UI decoupling:** the maze engine (grid, 0/1/2/3 encoding, generation, Level/Difficulty rules) depends on no UI library. This is a PRD requirement, not just a good practice — it's what makes a future web/mobile interface possible.
- **Data contract stability:** the 0/1/2/3 cell encoding and the maze CSV format are a public contract between the Builder and the Game; any evolution must stay backward-compatible with existing data once migrated (FR-23). The Maze ID header line (FR-20) is the one deliberate exception in this milestone — an additive field, not a re-encoding of any existing one — and is not itself a precedent for further changes without the same explicit sign-off.
- **Quality and tests:** every ported feature is covered by automated tests (`pytest`) and passes linting (`ruff`), already in place on the `rewrite` branch.
- **Language convention:** code identifiers, comments, UI strings, on-disk data (folder names, file naming, CSV headers), and documentation are all in English from the `rewrite` branch onward. This supersedes the legacy project's French-only convention (`CLAUDE.md` updated accordingly). Only the author's live conversation with an AI assistant stays in French — that does not extend to any artifact the project produces.
- **Readable git workflow:** history reflects an incremental, feature-by-feature port, with commits/PRs that stay understandable in hindsight (an explicit project success criterion, §7).
- **Accessibility floor:** every action is reachable via a keyboard shortcut — no mouse-only affordance anywhere in Home, the Builder, or the Game; every focusable control shows a visible focus indicator; text/background contrast meets WCAG AA; entry/exit/wall states are distinguished by shape as well as color, never color alone. Screen-reader support is explicitly out of scope this milestone — a known limitation of the current Tkinter renderer, to be revisited as a first-class requirement if/when a non-Tkinter interface is adopted (the logic/UI decoupling NFR above is what keeps that door open).

## 7. Success Metrics

**Primary**
- **SM-1**: All P0/P1 FRs (§4.1-4.5) are ported and covered by automated tests, on a modular codebase (no class re-creates the legacy "big_boss" role). Validates FR-1 through FR-23, FR-26 through FR-28.

**Counter-metric (do not optimize)**
- **SM-C1**: Porting speed must not come at the cost of code readability or test coverage — a feature shipped without a test, or with a confusing git history, does not count as ported. Counterbalances SM-1.

## 8. Open Questions

1. Final stack/platform choice for a possible web/mobile release — undecided; this PRD only requires that the architecture not preclude it (§6).
2. Exact porting order between Construction and Game (and between features within each domain) — to be settled at Sprint Planning, not in this PRD.
3. Detailed design of the Water Chase and Exploration modes (FR-24, FR-25) — to be fleshed out when the time comes; only the intent is captured here.

## 9. Assumptions Index

- §0 / overall framing — [ASSUMPTION] no external input beyond the legacy code and `CLAUDE.md` was provided; this PRD relies solely on those sources plus the conversation with the author.
- §4.6 — [ASSUMPTION] this PRD stays a living document: the author expects more feature ideas to surface while rewriting, to be captured via an Update pass rather than anticipated here. FR-26 through FR-28 (§0, §4.2, §4.3) are exactly this kind of pass, triggered by the finalized UX surfacing a Home screen and Personal Records the original PRD hadn't captured.
