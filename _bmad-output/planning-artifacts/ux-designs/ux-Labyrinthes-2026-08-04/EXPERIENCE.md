---
name: Labyrinthes
status: final
sources:
  - _bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/prd.md
updated: 2026-08-05
---

# Labyrinthes — Experience Spine

## Foundation

Desktop, single-user, two cooperating surfaces (Builder and Player) sharing one visual identity and one navigation shell. Today's platform is Tkinter, but per the PRD's explicit non-goal (§5, §6), this milestone does not lock the final stack for a possible future web/mobile release — the engine is UI-agnostic and the interface layer is expected to be replaceable. This spine's Information Architecture is therefore written surface-first, not widget-first: it describes screens and navigation relationships that must hold regardless of whether the eventual renderer is Tkinter, a web frontend, or something else. `DESIGN.md` is the visual identity source (Blueprint direction, paired light/dark tokens); this file is the behavioral and structural spine. There is no pre-existing UI system to inherit from — Labyrinthes is a custom-built interface, and `DESIGN.md.Components` are original, not deltas on a component library.

## Information Architecture

| Surface | Reached from | Purpose | Visual reference |
|---|---|---|---|
| Home | App launch (cold start) | Navigation hub: routes to Builder and Player, Settings access, Personal Records zone | [`mockups/key-home.html`](mockups/key-home.html) |
| Builder — edit screen | Home → Builder, or New Maze / Open Sketch from within Builder | Cell-by-cell and zone maze editing | [`mockups/key-builder-edit.html`](mockups/key-builder-edit.html) |
| Builder — New Maze dialog | Builder edit screen (`New Maze`) | Choose dimensions (3–50 cols / 3–35 rows) for a new empty maze, or reopen a Sketch | spine-only (Component/State Patterns tables) |
| Builder — Save dialog | Builder edit screen (`Save`) | Save as Sketch (incomplete) or Maze (finished), with duplicate-name handling | spine-only (Component/State Patterns tables) |
| Player — maze-selection screen | Home → Player | Classic maze gallery (previous/next/jump-to-number) + generate-random entry point, separate from gameplay | [`mockups/key-player-selection.html`](mockups/key-player-selection.html) |
| Player — gameplay screen | Maze-selection screen (pick a classic or generate random) | HUD, Level/Difficulty controls, HARD mode, timer, win/timeout states | [`mockups/key-player-gameplay.html`](mockups/key-player-gameplay.html) (light + dark + HARD-mode state) |
| Settings | Top-bar icon, from any screen | Dedicated window, categorized sections (Appearance, Ball, Difficulty, Shortcuts, …) | spine-only (Component Patterns table) |

**Navigation model.** Home is the sole general router between Builder and Player — there is no direct top-bar switch between them (this supersedes the `.switch` control drawn in `DESIGN.md`'s source mockup; see `DESIGN.md → Components → Top bar`). The top bar instead carries a Home / breadcrumb-back affordance on every screen. **Deliberate exception:** a contextual `Test in Player` action in the Builder opens the Player directly on the current maze, bypassing Home, because that is a frequent work loop (build → test → back to editing) that a strict hub-and-spoke model would otherwise punish; the mirror action, `Edit in Builder`, exists from a maze context in the Player wherever a maze traces back to a Builder-editable source (classics and saved randoms — not procedurally-generated-and-unsaved mazes, which have no Builder file to open).

**IA closure check:** every surface above traces to a stated need — Home to the PRD's Home-screen decision (memlog) and the Personal Records ambition; Builder screens to UJ-1/UJ-B; Player screens to UJ-2/UJ-A/UJ-C; Settings to FR-6, FR-17, FR-18, FR-21, FR-22. Personal Records is scoped to **local best-times only** for this milestone — no server, no community leaderboard — but the zone is structured (a distinct, self-contained module on Home) so it can extend to a community maze library and shared leaderboards later without a Home-screen redesign; that extension is explicitly out of scope now.

Four of the seven surfaces have a promoted key-screen mock (see table above); the other three (New Maze dialog, Save dialog, Settings) are spine-only by explicit decision — their Component/State Patterns rows below are sufficient to build from. Where a mock and this spine disagree, **this spine wins** (see `DESIGN.md → Brand & Style` for the same rule stated on the visual side).

## Voice and Tone

Clear, direct, plain-language descriptions of what a control does — never baby-talk, never exclamation-driven. This follows directly from the Blueprint register (`DESIGN.md → Brand & Style`): a precise instrument doesn't cheer you on, it tells you what's true. Hover tooltips in particular describe the action's *effect*, not its name (the button label already gives the name, the shortcut tag already gives the key).

| Do | Don't |
|---|---|
| "Break Wall — removes the wall between the cursor and the next cell" | "Let's smash some walls!" |
| "Exit not set" | "Oops, you forgot something!" |
| "Columns must be between 3 and 50." | "Error! Invalid input." |
| "Solved in 00:42." | "Wow, amazing time!! 🎉" |
| "Time's up — the exit wasn't reached." | "Better luck next time :(" |

## Component Patterns

Behavioral rules only — visual specs live in `DESIGN.md.Components`.

| Component | Use | Behavioral rules |
|---|---|---|
| `tool-btn` | Side bars, Builder + Player | Grouped under a label heading (Tools, Session, Grid, Mode, …). Exactly one tool active at a time within a mutually-exclusive group (e.g. Break Wall vs Set Entry); toggles (Smooth movement, Classic mode) show a checked state instead. Click selects; the active tool persists until another is chosen or the screen changes. |
| `hud-chip` | Player HUD, Builder HUD | Read-only. The Time chip is the only one that updates continuously while a run is active; all others update on discrete events (level up, position change on move). |
| `maze-frame` | Both apps | Hosts the grid; click-to-navigate the cursor in Builder (`Go to`, FR-7). No drag behavior of its own — dragging is a `wall-bar` interaction. |
| `wall-bar` | Builder editing | Single click on a wall segment breaks/restores it (FR-1, symmetric encoding update on both cells). Click-and-drag across multiple segments defines a rectangular zone, released to destroy or restore the whole zone at once (FR-2) — a distinct gesture from single-click, not an extension of it, so a user can't accidentally zone-edit by dragging slightly on a single click. |
| `marker` (entry/exit) | Builder editing, Player display | In Builder: click a cell with the Set Entry/Set Exit tool active to place it. If an entry/exit is already set, redefining it triggers a confirm prompt — **toggleable off in Settings** per the confirmation-prompts feature (FR-17), so a user who's fine with instant redefinition isn't forced through a dialog every time. |
| `ghost-marker` | Builder editing | Not interactive on its own — it's the visual absence-of-exit state; the Set Exit tool is what places a real marker over it. |
| `ball` | Player gameplay | Moves under arrow-key input; see Interaction Primitives for Smooth vs Discrete movement. Rendered normally except during HARD-mode movement, when it is not rendered at all (see HARD-mode fog overlay). |
| Top bar / breadcrumb-Home-button | All screens | Breadcrumb reflects the actual navigation depth (e.g. "Home / Player / Classic Maze 4"); clicking any earlier crumb jumps there directly. The Home segment is always present and always clickable, since Home is the router of record. |
| `icon-btn` | Top bar | Settings and theme-toggle live here. No tool-side-bar icon-btns — those are `tool-btn` for consistency of shortcut/tooltip presentation. |
| `pill-btn` | Top bar | At most one `primary` pill per screen (the single most likely next action — New Maze, Save). Secondary pill-btns stay in the default (non-filled) style so the primary one reads unambiguously. |
| `kbd-tag` + hover tooltip | Every actionable control | Every action has **exactly one** shortcut (FR-22 — no collisions, no stale tooltip text), always visible as a printed `kbd-tag`; the tooltip is a separate, plain-language description of the action's effect, shown only on hover. Both coexist on the same control — this is the corrected, final state after the memlog's brief hover-only detour. |
| `settings-window` | Reached from any top bar | Categorized sections/tabs (Appearance, Ball, Difficulty, Shortcuts, …). Opens as its own window, not an inline panel — so Builder/Player state stays visible/paused behind it rather than being replaced. |
| First-activation explainer popup | Level/Difficulty controls | Auto-shows the first time the user activates a given Level or Difficulty tier (every tier, not just HARD). Auto-show-on-first-activation is configurable off in Settings. Independent of that setting, an ⓘ affordance next to the control always reopens the same explainer on demand. |
| Inline error/empty-state message | Any form field, any list | Renders beside/under the concerned field or list, never as a modal. Persists until the underlying condition is resolved (e.g. dimensions back in 3–50/3–35 range), not dismissed by a button. |
| `record-group` | Home, Personal Records zone | One row per maze that has at least one stored record (FR-27). A maze with exactly one (Level, Difficulty) combo renders **flat, no chevron** — there's nothing to expand. A maze with 2+ combos renders **collapsed by default**: a chevron toggle, the maze name, and a headline value that is its **single most-recently-set-or-broken combo** — never a cross-combo "fastest" figure, since Level/Difficulty times aren't comparable (FR-27's Consequences). Clicking the row (or its chevron) expands an indented combo list below the header, one line per (Level, Difficulty) the maze has a record for, tagged `L{n}` (Level 1, which has no Difficulty setting per FR-13) or `L{n} · D{n}` (Level 2 and up), ordered **canonically by Level then Difficulty ascending** — not by recency, so the expanded list stays a stable, scannable reference rather than reshuffling every time a different combo is played. The toggle is a real focusable control, activated by click or Enter/Space, per the Accessibility Floor. `[ASSUMPTION]` Expand/collapse state resets to collapsed on every Home load — nothing is persisted between visits; low-stakes, easy to revise to sticky-open if it proves annoying in practice. |
| Win banner | Player gameplay, on solve | Appears inline around the maze-frame, offers a "continue" action per UJ-2. Does not block the maze from view. |
| HARD-mode fog overlay + status light | Player gameplay, HARD mode | Fog overlay is present only while the ball is moving (the interval during which the ball itself is invisible per FR-14); at rest the maze renders normally, instantly (no fade/animation, see `DESIGN.md → components.fog-overlay`). The status light reflects ready/moving state and its color is read from the user's HARD-mode color setting (`[ASSUMPTION]` defaults before customization: `DESIGN.md → components.status-light-default`) — the same setting must drive both the "ready" and "moving" light states consistently (this fixes the legacy hardcoded-color bug in the addendum, where changing the color setting silently broke the return-to-ready toggle). |

## State Patterns

| Surface | State | Treatment |
|---|---|---|
| Home | Empty records | Personal Records zone shows an inline message inviting the user to play their first maze — no fabricated placeholder scores. |
| Home | Populated records | One `record-group` row per maze, grouped by maze and ordered most-recently-set-or-broken first; see Component Patterns → `record-group` for the flat/collapsed/expanded treatment per maze's combo count. |
| Builder | Empty new maze | Dimensions dialog is the entry state — nothing rendered in the maze-frame until dimensions are confirmed. |
| Builder | Mid-edit | Normal editing state: tools active, HUD shows live grid size and walls-broken count. |
| Builder | Entry set, exit not set | No `ghost-marker` rendered anywhere until the user clicks a cell with Set Exit active — no default/placeholder position. Save is blocked from the "Maze" (finished) path until both are set, but Sketch save remains available (a Sketch is explicitly allowed to be incomplete). |
| Builder | Draft (Sketch) saved | Status HUD chip reads "Draft"; reopenable from the New Maze dialog's "Open a Sketch" path. |
| Builder | Finished (Maze) saved | Status HUD chip reads a finished/playable state; the maze becomes selectable from the Player's classic gallery. |
| Builder | Invalid dimensions | Inline error under the dimension inputs, live-validated against the shared 3–50 col / 3–35 row bounds (FR-4) — the same bounds source Player's random-maze dialog reads, so the two surfaces can never drift apart. |
| Player — selection | Empty (no classics found) | Inline empty-state message in the gallery area with a way to generate a random maze instead, rather than a dead-end blank gallery. |
| Player — selection | Populated | Classic gallery with previous/next/jump-to-number and a generate-random entry point, per FR-9/FR-10. |
| Player — gameplay | Mid-game | Normal HUD + maze + ball state. |
| Player — gameplay | HARD mode active | Fog overlay + status light per Component Patterns above; entry/exit/walls stay fully visible throughout. |
| Player — gameplay | Win | Win banner, timer stopped, continue action offered. |
| Player — gameplay | Timeout (time limit configured) | Inline failure message per Component Patterns' Voice and Tone table ("Time's up — the exit wasn't reached."), not a modal; run is stopped, restart/continue options remain reachable. |
| Settings | Categorized, nothing exotic | Standard section navigation + form rows; no error/empty states beyond ordinary field validation. |

## Interaction Primitives

- **Keyboard shortcut model:** every action maps to exactly one shortcut (FR-22); shortcuts are always printed on their control (`kbd-tag`) — never hover-only. A separate hover tooltip describes the action's effect in plain language, never restating the key.
- **Ball movement:** arrow keys drive the ball. Two configurable modes (FR-15): **Smooth** (direction can be redirected mid-move, continuous motion) and **Discrete** (cell-by-cell, one key press = one cell), with a configurable speed shared by both modes' underlying tick/animation rate.
- **Wall editing gesture split:** a single click on a wall breaks/restores just that wall (FR-1). A click-and-drag defines a rectangular zone, resolved as one destroy-or-restore operation on release (FR-2). These are distinct gestures, not variations of one gesture, specifically so a slightly-imprecise single click never accidentally becomes a zone edit.
- **Numeric input validation:** dimension fields (columns 3–50, rows 3–35) validate live and inline, in both the Builder's New Maze dialog and the Player's random-maze dialog, reading the same shared bounds (FR-4) rather than duplicated hardcoded values (fixes the legacy "Duplicated size bounds" defect in the addendum).
- **Record-group disclosure:** a multi-combo `record-group`'s header row is a standard toggle — click or Enter/Space switches it between collapsed (headline combo only) and expanded (every combo listed), per Component Patterns above. A single-combo `record-group` has no toggle at all.

## Accessibility Floor

Visual contrast values live in `DESIGN.md`; this section states the behavioral floor and sanity-checks the locked hex pairs against it.

- **Full keyboard operability.** Every action reachable via its printed shortcut; no mouse-only affordance exists anywhere in Home, Builder, or Player — this includes the `record-group` expand/collapse toggle, a control this milestone's Personal Records feature adds to Home.
- **Visible focus indicator** on every focusable control, at a contrast that meets the same AA bar as text (see below).
- **WCAG AA text/background contrast.** Rough sanity check on the locked `DESIGN.md` token pairs (relative-luminance contrast ratios, not measured in a contrast tool — treat as directional):
  - Light mode: `{colors.ink}` on `{colors.window}` ≈ 15:1 (comfortably passes AA and AAA). `{colors.ink-soft}` on `{colors.window}`/`{colors.panel}` ≈ 5.5:1 (passes AA for normal text).
  - Dark mode: `{colors.ink-dark}` on `{colors.window-dark}` ≈ 16:1. `{colors.ink-soft-dark}` on `{colors.window-dark}` ≈ 6:1 (both comfortably pass AA).
  - **Resolved — light mode:** plain `{colors.accent}` text on `{colors.accent-bg}` (the active-tool-button text-on-tint pairing) measured roughly 4.2:1 — just under the 4.5:1 AA threshold for normal-size text. Fixed by introducing `{colors.accent-on-tint}` (`#1d4ed8`) as the dedicated text color for this exact pairing (`DESIGN.md → Components → tool-btn`).
  - **Resolved — dark mode:** near-white text on plain `{colors.accent-dark}` fill (the primary-pill-btn treatment) measured roughly 3.3:1 — under the 4.5:1 AA text threshold. Fixed by introducing `{colors.accent-strong-dark}` (`#1e40af`) as the dedicated fill for primary-emphasis controls in dark mode; `{colors.accent-dark}` remains the lighter general interactive/live accent elsewhere (`DESIGN.md → Components → pill-btn`).
  - Non-token pairings (e.g. entry/exit marker fills against corridor) are not individually verified here; those rely on shape, not contrast alone, per the next point.
- **Entry/exit/wall distinguished by shape and color, never color alone** — markers carry a distinct glyph (`DESIGN.md → Components → marker`), broken walls are a structural gap rather than a color change.
- **Screen-reader support is explicitly out of scope**, documented here as a known Tkinter platform limitation, not a silently dropped goal: today's renderer has no practical screen-reader story, and this spine does not pretend otherwise. If a future non-Tkinter renderer is adopted, screen-reader support should be revisited as a first-class requirement at that time, not assumed inherited from this milestone.

## Key Flows

### UJ-A — Priya discovers the game (first launch through a classic maze win)

*Illustrated by: [`mockups/key-home.html`](mockups/key-home.html) (step 1), [`mockups/key-player-selection.html`](mockups/key-player-selection.html) (step 2), [`mockups/key-player-gameplay.html`](mockups/key-player-gameplay.html) (steps 3–6).*

1. Priya launches the app for the first time; Home opens (cold start), showing the Builder/Player navigation cards, a Settings icon, and an empty Personal Records zone with an inviting inline message rather than fabricated scores.
2. She clicks into Player. The maze-selection screen opens (not gameplay directly) — a gallery of classic mazes plus a generate-random option.
3. She picks the first classic maze. The gameplay screen opens: HUD (Level, Difficulty, Time, Pos), the maze centered in its frame, entry marker glowing green, ball at rest on it.
4. She moves the ball with arrow keys (default Smooth movement) toward the amber exit marker, walls rendered as solid bars, corridor bright and legible.
5. She reaches the exit.
6. **Climax:** the win banner appears inline around the maze-frame — "Solved in 00:42." — with a continue action, and Home's Personal Records zone now has its first local entry the next time she returns there — a flat `record-group` row (this one Level/Difficulty combo is her only record on this maze so far, no chevron yet).

Failure path: not applicable to this journey (UJ-A is the successful-discovery path by definition); a stuck-mid-maze case is not a failure state in this product — there's no timer running unless Priya opts into one, so there is nothing to fail against on a first classic-maze run.

### UJ-B — Max builds and tests a maze (via the Test-in-Player exception)

*Illustrated by: [`mockups/key-builder-edit.html`](mockups/key-builder-edit.html) (steps 1–4, 7), [`mockups/key-player-gameplay.html`](mockups/key-player-gameplay.html) (steps 5–6).*

1. Max opens Home, goes to Builder.
2. He starts a New Maze, entering dimensions (validated inline against the shared 3–50/3–35 bounds).
3. The empty grid opens in the maze-frame. He selects Break Wall and clicks/drags through the grid, tracing a path; the HUD's "Walls broken" count updates live.
4. He selects Set Entry, clicks a cell; selects Set Exit, clicks a border cell. Both markers now show filled (no more ghost-marker).
5. He clicks the `Test in Player` action — the deliberate exception to the Home-only-router rule — and the Player opens directly on this in-progress maze, bypassing Home and the maze-selection screen entirely.
6. He plays it through as a normal gameplay screen would render it, confirming the path is solvable.
7. **Climax:** satisfied, he uses the mirror `Edit in Builder` contextual action to jump straight back to his exact editing session — no re-navigation through Home, no re-opening the file — and saves it as a finished Maze (not just a Sketch) from there.

Failure path: if the maze turns out to be unsolvable or he wants more changes, step 6 simply ends with him invoking `Edit in Builder` again rather than saving — the loop (edit → test → edit) has no dead end and no forced save.

### UJ-C — Priya tries HARD mode (first-activation explainer, timeout as the failure path)

*Illustrated by: [`mockups/key-player-gameplay.html`](mockups/key-player-gameplay.html) (HARD-mode alternate-state section, steps 3–5).*

1. Priya is mid-session in the Player, playing a classic maze at a Level she's used before.
2. She opens the Level/Difficulty control and activates HARD mode for the first time.
3. **Because this is her first activation of this tier**, the first-activation explainer popup appears automatically, describing in plain language that the ball becomes invisible while moving and that a status light shows whether it's currently moving or at rest. (Auto-show is on by default here; if she'd turned it off in Settings previously, the same explainer would still be one click away via the ⓘ affordance next to the control.)
4. She dismisses the popup and starts moving. While the ball is in motion the fog overlay appears over the maze-frame and the status light switches to its "moving" color; walls, entry, and exit stay fully visible throughout — only the ball itself is hidden.
5. She has a time limit configured for this run. She loses track of the ball's position without the visual anchor and the timer keeps counting down.
6. The time limit is reached before she finds the exit.
7. **Climax / failure path:** an inline failure message appears — "Time's up — the exit wasn't reached." — not a modal, not a scolding tone; the run stops, and restart/continue options stay reachable directly from that same message, so the setback doesn't require renavigating anywhere to try again.
