# Epic 2 Context: Play a Maze (Game / Player)

<!-- Generated from planning artifacts. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Deliver the Game/Player's core play loop end-to-end: browsing and picking a maze (classic library or freshly generated random), and playing it with configurable Levels, Difficulty, HARD mode, movement style, timer, confirmation prompts, and appearance — matching and fixing the legacy player's mature-but-buggy feature set. This is UJ-2's spine (short of Personal Records, which lands in Epic 5) and the first fully playable slice of the rewrite.

## Stories

- Story 2.1: Player maze-selection screen — classic maze browsing
- Story 2.2: Random maze generation with validation
- Story 2.3: Random maze saving, reappears after restart
- Story 2.4: Gameplay screen foundation — rendering, HUD, baseline movement, win detection
- Story 2.5: Movement modes — Smooth vs Discrete, configurable speed
- Story 2.6: Levels — progressive visibility (1–4, Max)
- Story 2.7: Difficulty — unified threshold formula
- Story 2.8: HARD mode — invisible ball, fog overlay, status light
- Story 2.9: Timer — optional time limit, timeout message
- Story 2.10: Confirmation prompts per action
- Story 2.11: Appearance — theme + logo

## Requirements & Constraints

- Maze-selection is a distinct screen from gameplay: it opens first when Player is entered from Home, shows a classic-maze gallery (previous/next/restart/jump-to-number) plus a generate-random entry point; only after a maze is picked does gameplay mount. An empty classic library shows an inline empty-state message with a way to generate a random maze instead of a dead-end blank gallery.
- Random maze generation: dimensions (3–50 columns, 3–35 rows, same shared bounds as the Builder's New Maze dialog — read from one settings-backed source, never hardcoded per screen) plus a starting position, with live inline validation. Generation produces a solvable maze (DFS/backtracking-style, as in the legacy implementation) with the exit placed at the cell farthest from the entry. A freshly generated maze has kind `generated` (no `MazeId`) until explicitly saved; saving transitions it to kind `saved-random` with a freshly minted `MazeId`, and it must then reappear in the selector after an app restart (the legacy version wrote this file but nothing ever read it back — that dead end must not be reproduced). Save-name collisions get the same duplicate-name handling as the Builder's save flow.
- Gameplay screen: renders the maze-frame (walls as solid bars, a broken wall as a structural gap — never dashed/patterned), entry/exit markers with distinct glyphs, and the ball at rest on entry. A live HUD shows Level/Difficulty/Time/Pos chips, each updating on its own trigger. Arrow-key movement respects wall collisions. Reaching the exit shows an inline, non-blocking win banner around the maze-frame with a continue action ("Solved in 00:42." wording) and marks the run solved.
- Movement modes: Discrete (one cell per key press, the Story 2.4 baseline) and Smooth (continuous movement, redirectable mid-move without stopping at a cell boundary), both driven by one configurable speed setting whose change is reflected identically in both modes' tick/animation rate. Switching modes mid-session applies immediately to the next input.
- Levels (1–4, Max) control progressive grid visibility, all derived from the same 0/1/2/3-encoded grid (no separate abstraction layer):
  - Level 1: full grid always visible.
  - Level 2: maze split into rectangular partitions; a visited partition stays shown until a reveal threshold (depends on Difficulty) is crossed, then hides again.
  - Level 3: only one partition visible at a time.
  - Level 4: walls invisible until collision; past a threshold of discovered walls, they hide again.
  - Level Max: all walls permanently invisible.
- Difficulty (1–3) is unlockable only from Level 2 onward (disabled at Level 1) and adjusts the partition size / reveal thresholds Levels use. It must apply **one single shared reveal-threshold formula**, used identically by Level 2 and Level 4 — the legacy code used two different formulas for a similar concept (`count > round(cols*rows/(difficulty+1))` for Level 2 vs. fixed `/2, /5, /10` division for Level 4); this inconsistency must not be reproduced. A mid-session Difficulty change recalculates the active Level's visibility immediately.
- HARD mode: the ball is not rendered while moving; a translucent fog scrim (opacity per design tokens, no animation — instant show/hide tied to the moving state) covers the maze-frame, ordered above the corridor/ball plane but below wall-bars/markers so structure stays crisp. A small status light shows ready-vs-moving state, colored from the user's configurable HARD-mode color setting; changing that color must not break the ready↔moving toggle (the legacy bug hardcoded the "ready" color while only "moving" was configurable, breaking the toggle silently — must not be reproduced).
- Timer: the Time HUD chip updates continuously during a run, using the shared `Duration` type (Story 1.1) — the same type `Record.time` (Epic 5) will use. An optional configurable time limit, when reached before the exit is found, shows a non-modal inline failure message ("Time's up — the exit wasn't reached.") with restart/continue still reachable; with no limit configured, elapsed time appears in the win banner. (The legacy `Chrono` class was fully implemented but never wired up — this epic finishes wiring it.)
- Confirmation prompts are per-action, toggleable in Settings, and take effect without an app restart: switching mazes, restarting, changing Level, and invalid input all have their own on/off setting; when on, a confirm prompt gates the action; when off, the action applies immediately. Settings persist via the game-scoped `SettingsRepository`.
- Appearance: theme toggle reuses the shell-wide theme mechanism from Story 1.9 (no separate Game-only implementation); a logo picker persists the chosen logo via the game-scoped `SettingsRepository` and is shown wherever the Game displays its logo, with a sensible default before any logo is chosen.
- Keyboard shortcuts introduced in this epic register into the one canonical keybinding table (Story 1.10/FR-22) — no ad hoc per-widget bindings, and printed `kbd-tag` labels must match the actual registered shortcut.
- Accessibility floor (NFR6) applies to every Player control: keyboard-operable, visible AA-contrast focus indicators, and entry/exit/wall states distinguished by shape as well as color.

## Technical Decisions

- Layering: gameplay/selection logic composing generation, movement, Level/Difficulty visibility rules, and win detection belongs in `domain/` (pure, no UI) and `application/` (orchestration, e.g. a `PlayerService`); only rendering/HUD/input-wiring lives in `adapters/tkinter/player/`. `adapters/tkinter/player/` never imports `adapters/storage/` directly — maze/settings access goes through `application/` services (`MazeRepository`, `SettingsRepository`).
- Domain types are pinned and immutable (frozen dataclasses / equivalent), operations are pure functions returning new state: `Grid` (`[row][col]`, 0-origin), `Cell` (wall booleans as computed properties over its `"0"`–`"3"` digit, never a separate stored representation), `Position` (one shared type for entry/exit/ball/cursor alike), `Maze` (`Grid` + entry/exit `Position` + kind tag `classic`/`sketch`/`saved-random`/`generated` + `id: MazeId | None`), `Level`, `Difficulty`, `Duration` (shared, e.g. whole-millisecond count — also used later by `Record.time`).
- `Maze.kind` transitions: `generated` → `saved-random` happens by producing a *new* `Maze` value on save (never an in-place mutation), at which point a `MazeId` is minted once via the shared minting function shared with `MazeRepository`'s save path — an already-`classic`/`saved-random` `Maze` being re-saved carries its existing id forward unchanged.
- Player screen registers with the single composition root's router (Story 1.7) via `mount(parent, state: Maze | None) -> Frame`; the router models only Home/Builder/Player at the top level — Player's own maze-selection → gameplay transition is sub-navigation the Player screen manages internally, feeding its own dynamic breadcrumb label (e.g. "Classic Maze 4") to the shared breadcrumb widget rather than the router modeling that depth.
- All Player-specific reusable widgets (maze canvas, ball, wall-bar rendering) stay local to `adapters/tkinter/player/`; generic widgets (`hud-chip`, `tool-btn`, `pill-btn`, `kbd-tag`, breadcrumb, settings window, confirmation dialogs) come from the already-built `adapters/tkinter/common/` toolkit (Story 1.6) — not reimplemented per screen.
- `MazeRepository`/`SettingsRepository` are the single shared implementations from Epic 1 (Stories 1.3–1.5, hardened in 1.12) — Epic 2 stories are consumers, not reimplementors. Settings this epic writes/reads are `game`-scoped (movement speed, per-action confirmation toggles, HARD-mode color, theme, logo, time-limit) or `shared`-scoped (the FR-4/FR-10 size bounds, already declared once for both Builder and Game to read).
- Records (`RecordsService.record_completion(...)` on win) are explicitly Epic 5's concern, not this epic's — Story 2.4's win detection stops at marking the run solved and showing the win banner.

## UX & Interaction Patterns

- Maze-selection screen (`mockups/key-player-selection.html`): classic-maze gallery with previous/next/jump-to-number controls plus a generate-random entry point; empty state shown inline when no classics exist yet.
- Gameplay screen (`mockups/key-player-gameplay.html`, light/dark/HARD-mode states): HUD chips for Level/Difficulty/Time/Pos using the `hud-chip` component (the running Time chip uses the live/accent variant — the one HUD chip allowed to visually signal "live"); `maze-frame` + `wall-bar` rendering with broken walls as structural gaps, never dashed; `marker` (filled, distinct glyph: circle for entry, flag/arrow for exit) and `ghost-marker` (unset state) for shape-plus-color accessibility; the `ball` component (radial-gradient fill, accent-hue halo, drop shadow) which is not rendered at all during HARD-mode movement.
- HARD-mode fog overlay: translucent scrim at `colors.bg`/`colors.bg-dark` 0.85 opacity, no animation, load-bearing z-order (above corridor/ball plane, below wall-bars/markers); a 10px `rounded-full` status light near the HUD reflects ready/moving state in the user's configured color.
- Win banner: `rounded.lg`, `accent-bg`/`accent` styling, appears inline above/around the maze-frame on solve (never a modal takeover), plain non-alarmist wording ("Solved in 00:42."). Timeout failure message is likewise inline/non-modal ("Time's up — the exit wasn't reached."), with restart/continue still reachable from it.
- Top-bar breadcrumb (shared widget, e.g. "Home / Player / Classic Maze 4") appears on both the selection and gameplay screens, Home segment always present/clickable; Settings reachable from the same top-bar icon on every screen, opening as its own window without unmounting Player underneath.
- First-activation explainer popups for Level/Difficulty/HARD-mode tiers are introduced by Epic 5 (Stories 5.4/5.5) — Epic 2 stories should leave the ⓘ-affordance anchor points for those controls in a state that doesn't block that later wiring, but implementing the explainers themselves is out of this epic's scope.

## Cross-Story Dependencies

- Story 1.3 (port interfaces) must precede all of this epic's storage-consuming stories (2.1, 2.3); Stories 1.4/1.5 (concrete `MazeRepository`/`SettingsRepository`) and 1.12 (persistence hardening) must be in place before those same stories can be implemented against real storage.
- Story 1.7 (composition root & router) and 1.6 (shared `common/` widget toolkit) must exist before the Player screen can register with the router or render HUD/tool widgets.
- Story 1.9 (theme toggle) is a direct dependency of Story 2.11 (Appearance reuses the same mechanism, not a Game-only reimplementation).
- Story 1.10 (canonical keybinding table) is a dependency for every story introducing a new shortcut (movement keys, restart, jump-to, etc.).
- Story 2.4 (gameplay foundation: rendering, HUD, baseline movement, win detection) is a prerequisite for 2.5 (movement modes build on its baseline), 2.6/2.7 (Level/Difficulty visibility render into the same maze-frame), 2.8 (HARD mode's fog/ball-hide behavior), and 2.9 (timer ties into the same HUD/win-banner surface).
- Story 2.2 (random generation) is a prerequisite for 2.3 (saving a generated maze).
- Story 2.1's classic-gallery selection and 2.2/2.3's random-maze path both feed the same gameplay screen (2.4) via the router's `mount(parent, state)` — both must hand off a `Maze` value in the same shape.
- This epic's `Maze` kind/`MazeId` handling depends on Story 1.1's domain model and interacts with Epic 3's Builder (FR-8 `Test in Player` bypasses this epic's selection screen entirely; FR-19 `Edit in Builder` depends on this epic's `saved-random`/`classic` kind distinction) and Epic 5 (Personal Records reads the same `Maze.kind`/`MazeId`/`Level`/`Difficulty`/`Duration` types this epic establishes usage of, and Story 2.4's win detection is exactly where Epic 5's `RecordsService.record_completion(...)` call will be added).
