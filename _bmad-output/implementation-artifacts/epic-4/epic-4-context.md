# Epic 4 Context: Review Corrections — Builder & Player Polish, Windowing, Configurable Defaults

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Epic 4 corrects and refines behavior delivered in Epics 1–3 per two course corrections (2026-08-19 and 2026-08-25). It establishes the final Builder/Player interaction semantics (distinct marker/cursor glyphs, reworked Break vs Pass-through tools, live zone selection with two gestures, live entry/exit placement), replaces the "Walls broken" HUD stat with an accessibility-critical reachability counter, adds configurable defaults for Builder tool and maze dimensions, implements a play-again action for random mazes, and completes the shell's windowing (centered, resizable, zoom, fullscreen), top-bar brand logo, and grouped screen layouts. The 2026-08-25 correction extends the epic further: a Classic-vs-Creation maze-kind distinction (matching the legacy app's shipped-vs-player-saved split), a global keybinding-dispatch fix so screen shortcuts never fire while a text-entry dialog is focused, the maze's own name appended to the breadcrumb, and a three-section grid gallery (Classic / Creations / Random) on the Player selection screen.

## Stories

- Story 4.1: Builder cursor & marker glyphs
- Story 4.2: Wall-tool semantics — Break vs Pass-through + Space toggle
- Story 4.3: Zone selection — colored outline & click-click gesture
- Story 4.4: Entry/exit live placement — ghost follows cursor, place on click or Enter
- Story 4.5: Reachability counter & click-to-highlight
- Story 4.6: Configurable defaults — Builder tool, new-maze & random dimensions
- Story 4.7: Player — Continue regenerates a random maze with the same params
- Story 4.8: Shell windowing — centered, resizable, zoom, fullscreen
- Story 4.9: Top-bar brand logo follows the logo setting
- Story 4.10: Screen layout — labeled blocks separated from the maze
- Story 4.11: Classic vs. Creation maze kind
- Story 4.12: Screen shortcuts never fire while a text-entry dialog is focused
- Story 4.13: Breadcrumb shows the maze's own name
- Story 4.14: Player selection screen — grid gallery split into Classic / Creations / Random

## Requirements & Constraints

- **FR-29 (Builder reachability feedback):** HUD shows count of cells inaccessible from the entry; clicking the counter outlines those cells. Before entry is set, counter reads "—" and is not interactive. Replaces "Walls broken" stat.
- **FR-30 (Configurable defaults):** Default Builder tool, New Maze dialog dimensions, and Generate Random dialog dimensions are user-configurable settings, clamped to the shared 3–50 cols / 3–35 rows bounds.
- **FR-31 (Window management):** App window opens centered, is freely resizable, maze canvas zooms (Ctrl+wheel, `+`/`-`), adapts to available space, F11 toggles fullscreen. Settings window gets identical treatment (minus maze zoom).
- **FR-32 (Top-bar brand mark):** Every screen's top bar shows the brand logo (per user's logo setting) before the app name.
- **FR-33 (Play again):** Win banner on a solved generated random maze offers regenerating a new random maze with same dimensions and entry position, immediately, labeled distinctly (e.g., "New random maze").
- **FR-34 (Layout grouping):** Builder and Player controls/displays grouped into labeled blocks on sides and top, clearly separated from the maze frame.
- **FR-35 (Classic vs. Creation maze):** Classic mazes are dev-authored, present at first install, never produced by player Builder saves. Creations are finished mazes (entry+exit set) a player saves via Builder — built with same tool but distinct provenance, never shipped as game content. Creations are MazeId-eligible and Personal-Record-eligible on same terms as Classic/Saved-random.
- **FR-36 (Shortcut dispatch guard):** No keyboard shortcut registered for the active screen fires while a text-entry field inside an open dialog holds focus — enforced once at the dispatch mechanism, not by per-dialog letter blocking.
- **FR-37 (Maze name in breadcrumb):** When a screen has a specific maze loaded, breadcrumb gains an additional trailing segment carrying that maze's saved name, appended after the existing kind-derived segment (e.g., "Home / Player / Classic / 10x10edf"). Kind segment is never replaced or removed.
- **FR-38 (Grid gallery, split by category):** Player's maze-selection screen presents Classic, Creation, and Random (saved) mazes as three separate, clearly labeled sections in one scrollable card grid per the locked mockup, replacing the single-item pager.
- **NFR1 (Logic/UI decoupling):** Maze engine (grid, 0/1/2/3 encoding, generation, Level/Difficulty rules) depends on no UI library — Epic 4's reachability computation lives in `domain/` as a pure function.
- **NFR2 (Data contract stability):** 0/1/2/3 cell encoding and maze CSV format are a public contract between Builder and Game. Epic 4's Creation kind extends `MazeKind` additively; `MazeId` minting rule extends to Creation identically to Classic/Saved-random.
- **NFR4 (Language convention):** All code, identifiers, comments, UI strings, on-disk data, and docs are English.
- **NFR6 (Accessibility floor):** Every action reachable via keyboard; visible focus indicator on every focusable control at AA contrast; text/background contrast meets WCAG AA; entry/exit/wall states distinguished by shape as well as color. Reachability counter's click-to-highlight must be keyboard-operable.

## Technical Decisions

- **Architecture (AD-1/AD-10/AD-11):** Single composition root (`app/`) owns the `Tk()` root and screen router; Home/Builder/Player register via `mount(parent, state: Maze | None) -> Frame`. Screens never import each other; all top-level navigation goes through the router. Shared Tkinter widgets live in `adapters/tkinter/common/` (imported by screens, never imports screens).
- **Domain immutability (AD-2/AD-3):** `Grid`, `Cell`, `Maze`, `Position`, `Level`, `Difficulty`, `Duration`, `MazeId` are immutable value objects. Engine operations are pure functions returning new state. `MazeKind` gains `CREATION` as fifth member (alongside `CLASSIC`, `SKETCH`, `SAVED_RANDOM`, `GENERATED`). `_ID_ELIGIBLE_KINDS` extends to include `CREATION` for MazeId minting and Records eligibility.
- **Reachability in domain (AD-1):** `domain/reachability.py` exposes `inaccessible_cells(maze, entry) -> frozenset[Position]` — pure BFS through open passages, no UI dependency. Called from Builder adapter for HUD counter and click-to-highlight overlay.
- **Break vs Pass-through semantics:** Break mode: cursor movement across a wall breaks it and moves. Pass-through mode: cursor ignores walls entirely, never modifies them. Space toggles between modes. Outer border stays closed in both modes.
- **Zone selection gestures:** Two distinct gestures — (1) click-drag-release, (2) click-release (arms anchor), move, click-release (commits). Esc cancels armed anchor. Live colored rectangle outline during selection (accent for Destroy, exit-color for Restore).
- **Entry/exit live placement:** Ghost square (entry) / ghost diamond (exit) follows cursor in real time. Placement on cell click or Enter key. Existing redefinition confirmation prompt honored.
- **Configurable defaults storage:** Three scopes per AD-7 — `builder` scope: `default_builder_tool`, `default_new_maze_columns`, `default_new_maze_rows`; `game` scope: `default_random_columns`, `default_random_rows`. Fallback to bounds minimum when unset. Read in adapters, passed into session services — application layer gains no settings dependency.
- **Play-again regeneration:** On `generated` maze win, win banner's continue action immediately generates new random maze at same width/height/entry and mounts it — no dialog, no re-save. For `classic`/`saved-random`, existing Continue behavior unchanged.
- **Windowing in composition root (AD-10):** Root window centering, resizability, fullscreen (F11), and zoom dispatch live in `app/composition_root.py`. Maze canvases expose zoom/auto-fit re-render hooks. Settings window (`common/settings_window.py`) gets centered, resizable, F11.
- **Top-bar brand logo (AD-11):** `common/top_bar.py` renders logo image (via `application/logos.py` loader) before "Labyrinthes" wordmark. Re-reads on screen re-mount (theme toggle triggers re-mount).
- **Screen layout blocks:** Builder tools grouped under labeled headings ("Tools", "Markers") in side blocks; HUD block on top; maze in bordered `maze-frame` separated from side blocks. Player existing groups tidied into consistent blocks. Group headings use shared typography tokens, consistent spacing.
- **Classic vs. Creation kind:** `MazeKind.CREATION` added to domain enum. Builder "Save as Maze" produces `CREATION` kind. `MazeRepository` mints `MazeId` for `CREATION` identically to `CLASSIC`/`SAVED_RANDOM`. `RecordsService` eligibility check extends to include `CREATION`. No automatic reclassification of existing `CLASSIC`-folder test fixtures — manual cleanup acceptable for dev scratch data.
- **Shortcut dispatch guard:** `common/keybindings.py::bind_shortcut` checks if focused widget is `tk.Entry`/`tk.Text` inside an open dialog — if so, skips callback but lets key event reach the entry field. Removes per-dialog `<KeyPress-x>` → `"break"` guards from `_SaveNameDialog`, `SaveMazeDialog`, `NewMazeDialog`, `GenerateRandomDialog`. Canonical keybinding table (Story 1.10) unchanged — this is a dispatch-time fix.
- **Breadcrumb maze name threading:** `Maze` domain value has no `name` field (name is storage-layer/filename concept). Name threaded from `MazeRepository`/save flow through screen's session/launch state to breadcrumb without adding UI concern to `domain/`. Builder breadcrumb grows from 2 to 3 segments; Player from 3 to 4 (kind segment stays, name appended after).
- **Grid gallery (three sections):** Replaces `ClassicMazeGallery` pager with scrollable card grid (`gallery-grid`/`maze-card` pattern from mockup). Three labeled sections: Classic, Creations, Random. Empty section shows inline empty-state message; other sections unaffected. Maze card click/Enter mounts gameplay screen. "Generate random" stays separate action, not a fourth card. Full keyboard navigation (Tab + Enter/Space) with visible focus indicator.

## UX & Interaction Patterns

- **Marker/cursor glyphs (DESIGN.md):** Three distinct shapes — square = entry, diamond = exit, circle = player/builder. Entry marker renders as filled square (green) in both Builder and Player. Exit marker keeps filled diamond (amber). Builder cursor renders as filled circle (ball glyph, accent color), never blue rectangle outline.
- **Wall editing (DESIGN.md / EXPERIENCE.md):** Single click on wall segment toggles it (Break mode). Click-and-drag defines rectangular zone for destroy/restore — distinct gesture, not variation. Broken wall renders as structural gap (nothing drawn), never dashed/patterned bar.
- **Zone selection visual feedback:** Live colored rectangle outline from anchor to current cell during selection. Distinct color per tool (accent for Destroy, exit-color for Restore). Esc cancels armed anchor.
- **Ghost markers (DESIGN.md / EXPERIENCE.md):** Ghost square (entry color) follows cursor on any cell in real time for Set Entry. Ghost diamond follows cursor on border cells only for Set Exit. Placement on click or Enter.
- **Reachability HUD chip (DESIGN.md):** "Inaccessible" chip shows live count; disabled ("—") when no entry set. Clicking chip toggles colored outline (exit-color) around every inaccessible cell, re-rendered on wall edits or entry move.
- **Design tokens (DESIGN.md):** Paired light/dark tokens for all components. Two AA-fix tokens: `accent-on-tint` (light-mode active-tool text), `accent-strong-dark` (dark-mode primary-button fill). Wall/corridor brightness relationship deliberately inverts between modes (never mechanically derived).
- **Component library (DESIGN.md / AD-11):** `tool-btn` (mutually-exclusive active group), `hud-chip` (live/accent variant for Time), `icon-btn`, `pill-btn` (at-most-one-primary-per-screen), `kbd-tag` + hover tooltip (shortcut always printed, tooltip describes effect), top-bar breadcrumb/brand-mark, `settings-window`, first-activation explainer popup, inline error/empty-state message. All in `adapters/tkinter/common/`.
- **Top-bar breadcrumb (EXPERIENCE.md):** Reflects actual navigation depth (e.g., "Home / Player / Classic / 10x10edf"). Earlier crumbs clickable for direct jump. Home segment always present. Each screen feeds dynamic sub-state label to shared breadcrumb widget.
- **HARD-mode fog overlay + status light (DESIGN.md / EXPERIENCE.md):** Translucent scrim (`bg`/`bg-dark` at 0.85 opacity, no animation) shown only while ball moving. Z-order: above corridor/ball plane, below wall-bars and markers. 10px status light reflects ready/moving state, color from user's configurable HARD-mode setting (fixes legacy hardcoded-color bug).
- **Record-group (DESIGN.md / EXPERIENCE.md):** One row per maze with stored record. Flat (no chevron) for single (Level, Difficulty) combo. Collapsed by default with chevron + most-recently-set-or-broken headline for 2+ combos. Expands to indented combo list ordered canonically by Level then Difficulty ascending. Toggle is real focusable control (click or Enter/Space).
- **Win banner / timeout message (EXPERIENCE.md):** Inline, non-blocking, appears around maze-frame. "Solved in 00:42." / "Time's up — the exit wasn't reached." Plain, non-alarmist wording. Continue/restart reachable from same message.
- **Keyboard shortcut model (EXPERIENCE.md / FR-22):** Every action maps to exactly one shortcut; shortcuts always printed on control (`kbd-tag`); separate hover tooltip describes effect in plain language. Canonical keybinding table with automated collision/label-consistency check.
- **Layout blocks (FR-34 / DESIGN.md):** Side bars with group headings in `{typography.label}`, maze in bordered `maze-frame` (`{rounded.xl}`, `{colors.border}`), consistent spacing via `{spacing}` scale. Builder: "Tools" (Break, Pass-through, Destroy, Restore) and "Markers" (Set Entry, Set Exit) groups. Player: "Movement", "Mode", "Levels", "Difficulty", "Logo" groups tidied.

## Cross-Story Dependencies

- **4.11 → 4.14:** Story 4.14 (grid gallery) depends on 4.11 (Creation kind) — the gallery's three sections need the `creation` kind to exist and be populated first.
- **4.11 → 6.1/6.2 (Epic 6):** `RecordsService.record_completion` eligibility check extends from `classic`/`saved-random` to include `creation` once Epic 6 implements it.
- **4.11 → 5.3 (Epic 5):** Migration script's MazeId backfill extends to migrated Creations (per "Creation is MazeId/record-eligible" decision).
- **4.12 (dispatch guard):** Independent of other Epic 4 stories; fixes a cross-cutting concern in `common/keybindings.py` affecting all screens' dialogs.
- **4.13 (breadcrumb name):** Independent; requires threading maze display name from storage/save flow through screen state — no domain change.
- **4.1/4.2/4.3/4.4/4.5:** Share Builder canvas and `builder/screen.py`; sequenced to minimize merge friction (glyphs → tools → zone → markers → counter).
- **4.6 (configurable defaults):** Touches `builder/screen.py` (default tool), `common/new_maze_dialog.py`, `player/generate_random_dialog.py`, `common/settings_window.py` — independent of 4.1–4.5 but reads same Builder canvas.
- **4.7 (play-again):** Touches `player/gameplay_screen.py` and `player/screen.py` — independent.
- **4.8 (windowing):** Touches `app/composition_root.py`, both maze canvases, `common/settings_window.py`, `common/keybindings.py` — independent.
- **4.9 (brand logo):** Touches `common/top_bar.py`, `app/composition_root.py`, `application/logos.py` — independent (logo assets and Settings flow already exist from Story 2.11).
- **4.10 (layout blocks):** Touches `builder/screen.py`, `player/gameplay_screen.py`, `player/screen.py` — independent but benefits from 4.1–4.5 canvas work.