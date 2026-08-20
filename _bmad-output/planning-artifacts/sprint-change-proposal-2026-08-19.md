# Sprint Change Proposal — 2026-08-19

**Project:** Labyrinthes — modular rewrite (`rewrite` lineage, active branch `epic-3-build-and-test-a-maze`)
**Author:** Max (course-correction review)
**Mode:** Batch
**Scope classification:** Moderate (backlog reorganization + Developer implementation)

---

## Section 1: Issue Summary

### Problem statement

Max reviewed the working rewrite (shell + Player + Builder, all present on the `epic-3` working tree) and found **13 corrective items** spanning three areas. They are refinements/rework of already-delivered features plus a few small new features — not a strategic pivot:

**Global (shell)**
1. The entry ("départ") marker must be a **square** so it is never confused with the round Player ball / Builder cursor.
2. The window must open **centered**, be **fully resizable** (window edges **and** a maze zoom), and support **fullscreen** — the Settings window gets the same treatment.
3. The brand **logo does not display** anywhere; it must appear **top-left before the "Labyrinthes"** name in the top bar.
4. Buttons and displays must be organized in **labeled blocks on the sides and top**, clearly separated from the maze (Player and Builder).

**Player**
5. The default width/height proposed by the **Generate Random** dialog must be **configurable**.
6. After solving a random maze, the "Continue" button must instead **generate another random maze with the same params**.

**Builder (Epic 3)**
7. The selected cell must not be blue-outlined; it must contain a **round** (like the Player ball) = the builder.
8. **Break wall / Pass-through logic reworked**: Break = the builder breaks walls (what Pass-through currently does); Pass-through = the builder traverses walls freely, walls have no effect; **Space** toggles the two modes.
9. **Destroy/Restore zone**: a **colored outline** must show the selected zone; selection must work two ways (click–drag–release, or click–release–move–click).
10. **Set entry/exit**: the entry/exit icon must **follow the builder in real time** and be placed (with the existing popup) on cell click **or the Enter key**.
11. Replace the "Walls broken" counter with a counter of **cells inaccessible from the entry**; clicking it shows a **colored outline** on those cells.
12. The **default Builder mode** on open must be **configurable**.
13. The default width/height for a **new maze** in the Builder must be **configurable**.

### Evidence

- `TopBar` (`adapters/tkinter/common/top_bar.py`) renders only the text brand (`_BRAND_TEXT = "Labyrinthes"`); no logo is loaded anywhere in the app.
- 13 logos exist on disk (`adapters/tkinter/player/assets/logos/logo-01..13.jpg`) and are wired into Settings via `application/logos.py` (key `default` → `logo-02.jpg`); PIL is available in `.venv`.
- Builder cursor = blue rectangle outline (`builder/screen.py::_draw_cursor`); entry marker = filled green circle, exit = filled amber diamond, ball = small blue circle (`player/maze_canvas.py`).
- `BuilderSession` (`application/builder_session.py`) currently: `BREAK` = click toggles a wall segment; `PASS_THROUGH` = movement breaks the blocking wall then moves (border still blocks); zone tools = drag-only, no selection rectangle.
- HUD shows a live "Walls broken" `HudChip`; `Set Exit` already shows a dashed `?` ghost that follows the cursor on border cells; `Set Entry` has no live ghost.
- `NewMazeDialog` and `GenerateRandomDialog` default their fields to `read_maze_size_bounds().min_*`; no settings exist for default dimensions or default Builder tool.
- Gameplay win banner / timeout banner use a "Continue" pill regardless of maze kind.
- Root window is created plain in `app/composition_root.py` (no centering, no zoom, no fullscreen).
- Baseline verified: `ruff check src tests` and `ruff format --check src tests` clean; 208 application/domain tests pass. (`ruff check .` noise comes only from gitignored `.agents/skills/` third-party files.)

---

## Section 2: Impact Analysis

### 2.1 Epic impact

| Epic | State | Impact |
|---|---|---|
| Epic 1 — Foundation / shell | `done`, content merged into the working tree | G2 (windowing), G3 (top-bar logo), G4 (layout) rework shell deliverables (1.6 toolkit, 1.7 router, 1.8 home/top-bar, 1.10 keybindings). No architectural AD is violated. |
| Epic 2 — Player | `done`, content on working tree | P1, P2 rework 2.2 (random generation defaults) and 2.4 (gameplay win flow); G1 touches 2.4 marker rendering. |
| Epic 3 — Builder | `in-progress` (3.1–3.5 done, 3.6–3.9 backlog) | B1–B7 rework/extend 3.2 (wall editing), 3.3 (zone editing), 3.4 (entry/exit), 3.5 (cursor). |
| Epic 4 (new) | new epic, inserted after Epic 3 | Hosts the whole correction batch (stories 4.1–4.10), reworking Epic 1–3 deliverables. |
| Epics 5–7 (renumbered from Epics 4–6) | `backlog` | No direct impact; Epic 3 content feeds 3.8/3.9 (bidirectional links) and Epic 6 (records, renumbered) unchanged. |

**Recommendation:** the batch becomes a **new Epic 4**, inserted after Epic 3; Epics 4–6 are renumbered to 5–7 (`epics.md`, `sprint-status.yaml` updated). Epic 4 branches from the current `epic-3-build-and-test-a-maze` HEAD (which already contains shell + Player + Builder), so every correction lands on the tree that holds the code it reworks. The `sprint-status.yaml` entries for the amended done stories stay `done`; the amendments are tracked via Epic 4's stories (see 2.2).

### 2.2 Story impact

New stories proposed on Epic 4 (all `backlog` until approved):

| New story | Reworks / amends | Corrections |
|---|---|---|
| 4.1 Builder cursor & marker glyphs | 3.2, 3.4, 3.5 (Builder); 2.4 (Player) | B1, G1 |
| 4.2 Wall-tool semantics (Break vs Pass-through) + Space toggle | 3.2 | B2 |
| 4.3 Zone selection: colored outline + click–click gesture | 3.3 | B3 |
| 4.4 Entry/exit live placement (ghost follows cursor, place on click or Enter) | 3.4 | B4 |
| 4.5 Reachability counter + click-to-highlight | 3.2 (HUD) | B5 |
| 4.6 Configurable defaults (Builder tool, new-maze dims, random-maze dims) | 3.1 (new-maze dialog), 2.2 (random dialog) | B6, B7, P1 |
| 4.7 Player: Continue regenerates random maze with same params | 2.4 | P2 |
| 4.8 Shell windowing: centered, resizable, maze zoom, fullscreen | 1.7, 1.8 | G2 |
| 4.9 Top-bar brand logo follows `theme_logo` | 1.6, 1.8, 2.11 | G3 |
| 4.10 Screen layout: labeled blocks, maze separation | 1.8, 2.4, 3.2 | G4 |

### 2.3 Artifact conflicts

- **PRD** — needs amendments to FR-1 (Break/Pass-through semantics), FR-2 (zone gestures), FR-3 (marker shapes, live entry/exit placement), FR-4 (configurable defaults), plus new acceptance for the reachability counter and shell windowing/zoom.
- **Architecture spine** — no AD change. Add `domain/reachability.py` (pure domain, BFS through open passages). Windowing/zoom/centering belongs to `app/` composition root (AD-10 compliant: it owns the Tk root and may import concrete screens). New settings follow AD-7 (scoped keys, single readers). The Builder tool default is read in the adapter and **passed into** `start_builder_session(...)` — the application layer stays theme/repository-agnostic.
- **UX Design / Experience** — update: brand-mark (logo in top bar), marker glyph set (square=entry, diamond=exit, circle=player/builder), zone selection rectangle, live entry ghost, layout blocks, interactive HUD chip (inaccessible counter replaces "Walls broken").
- **Epic 4 context / `epic-3-context.md`** — a new `epic-4-context.md` records the correction stories; `epic-3-context.md` stays scoped to Epic 3's FR-1/FR-2/FR-3 (the amended HUD/keybinding wording is picked up by Epic 4's stories).
- **Settings keys / dialogs** — new keys (see 4.6) + a "Defaults" category in `SettingsWindow` (Builder tool, new-maze dims, random-maze dims). No scope-model change: random dims are `game` scope, Builder defaults are `builder` scope.
- **Keybinding table** — new canonical entries: `toggle_break_pass_through` (Space, Builder), `place_marker` (Return, Builder), `toggle_fullscreen` (F11, shell), and maze-zoom (`+`/`-`, per-screen). Canonical-table uniqueness test must stay green.
- **Deferred-work / retro items** — `epic-2-retro-item-1-router-cascade` (Settings window closing on frame teardown) is directly relevant to 4.8; align it there.

### 2.4 Technical impact

- Pure-domain addition: `domain/reachability.py` (no Tkinter) + unit tests.
- `application/builder_session.py::move_cursor` semantics change (BREAK breaks-then-moves; PASS_THROUGH ignores walls) — pure logic, tests updated.
- Canvas rendering: zoom + auto-fit-to-space needs a re-render/size hook on both `player/maze_canvas.py` and the builder canvas; zone rectangle overlay + reachability overlay drawing stay adapter-local.
- Logo rendering in TopBar reuses `application/logos.py` (PIL-backed) — must not couple `common/` to `player/assets`; asset path stays under `player/` (logo choice is a `game`-scope setting shared with Player appearance).
- Existing GUI-test flakiness note (AGENTS.md): some focus-dependent GUI tests pass only in isolation — re-run a failing GUI test alone before assuming a regression.

---

## Section 3: Recommended Approach

**Option 1 — Direct Adjustment (recommended).** Modify existing stories via new amendment stories in a new Epic 4 inserted after Epic 3 (epics 4–6 renumbered to 5–7); no rollback, no MVP reduction.

- **Rollback (Option 2) — not viable:** all affected stories are done and their value is real; reverting to re-do would duplicate work and lose the delivered features.
- **MVP review (Option 3) — not needed:** the PRD MVP is intact; these are refinements that strengthen the MVP's UX, not scope reductions.

**Rationale:** lowest effort, lowest risk, keeps momentum on the active branch, and each correction maps 1:1 to a focused story with an existing test surface. Effort: **Medium** (10 stories, mostly adapter-layer rework + 2 pure-domain additions). Risk: **Low–Medium** (concentrated in Builder/Player adapters; domain/application boundaries hold; no data-model change; wall encoding 0/1/2/3 untouched — preserved per migration requirement).

**Sequencing:** 4.1 (glyphs) → 4.2 (tools) → 4.3 (zone) → 4.4 (markers) → 4.5 (counter) are independent Builder stories but share the builder canvas — do them in order to minimize merge friction. 4.6, 4.7, 4.8, 4.9, 4.10 are largely independent; 4.9 depends on `application/logos.py` (exists) and the Settings logo flow (2.11, exists). All land on the `epic-4` branch via the normal story → review → merge-to-epic flow; the epic stays off `rewrite` until every epic-3 story (3.1–3.9) and epic-4 story (4.1–4.10) is `done`.

---

## Section 4: Detailed Change Proposals

### 4.1 Story proposals (new stories on Epic 4)

---

**Story 4.1 — Builder cursor & marker glyphs**

Amends: 3.2 / 3.4 / 3.5 (Builder), 2.4 (Player).

- OLD: Builder selected cell = blue rectangle outline; entry marker = filled green circle (both Builder and Player).
- NEW: selected cell = filled **circle** (Player-ball glyph, `colors.ball`); entry marker = filled **square** (green); exit = filled **diamond** (amber). Three distinct shapes: square = entry, diamond = exit, circle = player/builder.
- Affects: `builder/screen.py::_draw_cursor`, entry-marker drawing in builder canvas; `player/maze_canvas.py::_draw_entry_marker`.
- Tests: builder-screen cursor/marker shape assertions; player canvas marker assertion.
- Rationale: round entry was indistinguishable from the round player/builder.

---

**Story 4.2 — Wall-tool semantics: Break vs Pass-through + Space toggle**

Amends: 3.2. Replaces the FR-1 semantic described in `epic-3-context.md`.

- OLD: `break_wall` toggles a wall segment on click; `pass_through` movement breaks the blocking wall then moves (border still blocks).
- NEW:
  - **Break** tool: clicking a wall segment toggles it (kept); moving the cursor across a wall **breaks it and moves** (what Pass-through did).
  - **Pass-through** tool: movement **ignores walls** — the cursor always moves to the adjacent cell within grid bounds and **never modifies walls**; walls have no effect on the builder.
  - Closed-border invariant preserved in both modes (border never opens; grid bounds limit movement).
  - **Space** toggles between Break and Pass-through.
- Affects: `application/builder_session.py::move_cursor` + tool descriptions; `builder/screen.py` (Space binding, labels/tooltips); `common/keybindings.py` (`toggle_break_pass_through` = Space, Builder scope) + `kbd_tag.py`.
- Tests: `test_builder_session.py::move_cursor` (both modes), keybinding-uniqueness, builder-screen Space toggle.
- Rationale: user-defined semantics — breaking is a deliberate act, traversal is free.

---

**Story 4.3 — Zone selection: colored outline + two gestures**

Amends: 3.3.

- OLD: drag-only selection, no visual feedback.
- NEW:
  - Live **colored rectangle outline** from anchor to current cell while selecting (`colors.accent` for Destroy, `colors.exit` for Restore).
  - Two gestures: (1) click A → drag → release on B; (2) click A → release (arms anchor, outline follows the mouse), then click B → commits zone A..B.
  - **Esc** cancels an armed anchor.
  - Single-click precision contract (FR-1 vs FR-2) preserved: a plain click never triggers a zone op.
- Affects: `builder/screen.py::_BuilderMazeCanvas` (press/release/motion, armed-anchor state, overlay). `builder_session.py` unchanged (`apply_zone_operation` already takes a rect).
- Tests: `test_builder_screen.py` (both gestures, cancellation, no-op single click).
- Note: keyboard zone selection (NFR6 gap, pre-existing) is flagged, not in scope — Esc-to-cancel only. Optionally a follow-up story.
- Rationale: visible selection + mouse ergonomics requested by Max.

---

**Story 4.4 — Entry/exit live placement (ghost follows cursor, place on click or Enter)**

Amends: 3.4.

- OLD: Set Entry had no live preview; Set Exit ghost already followed the cursor on border cells; placement only by click.
- NEW:
  - Set Entry: a **ghost square** (entry color) follows the builder cursor on any cell in real time.
  - Set Exit: ghost diamond follows the cursor on border cells (kept).
  - Placement on cell **click** or **Enter** (`place_marker` = Return, Builder scope), with the existing confirmation popup preserved.
- Affects: `builder/screen.py` (set-entry ghost, Enter handling, `_sync_markers`); `common/keybindings.py` (`place_marker`) + `kbd_tag.py`.
- Tests: builder-screen ghost-follows-cursor + Enter placement for entry and exit; keybinding table.
- Rationale: visible target before placement; keyboard placement (NFR6).

---

**Story 4.5 — Reachability counter + click-to-highlight**

Amends: 3.2 (HUD). Replaces the "Walls broken" HUD stat.

- NEW:
  - `domain/reachability.py`: `inaccessible_cells(maze, entry) -> frozenset[Position]` — pure BFS through open passages; empty when `entry is None`.
  - HUD chip "Inaccessible": live count of cells unreachable from the entry; when no entry is set the chip shows "—" and is disabled (decision 4).
  - Clicking the chip toggles a **colored outline** (`colors.exit`) around every inaccessible cell, re-rendered on session changes (wall edits, entry moved).
- Affects: `domain/reachability.py` (new, pure); `builder/screen.py` (interactive chip + overlay + recompute hook); `common/hud_chip.py` (optional `command`).
- Tests: domain BFS (reachable/inaccessible, no-entry), builder-screen chip value/disable + toggle overlay.
- Rationale: gives the Builder real feedback on what remains to open before the maze is playable.

---

**Story 4.6 — Configurable defaults (Builder tool, new-maze dims, random-maze dims)**

Amends: 3.1 (new-maze dialog), 2.2 (random dialog). New settings.

- NEW keys (AD-7):
  - Builder scope: `default_new_maze_columns`, `default_new_maze_rows` (initial New Maze dialog values; fallback/clamped to `read_maze_size_bounds()`).
  - Builder scope: `default_builder_tool` (initial active tool of a session; fallback `break`).
  - Game scope: `default_random_columns`, `default_random_rows` (initial Generate Random dialog values; fallback/clamped to bounds).
- NEW: a "Defaults" category in `SettingsWindow` with the five fields.
- Affects: `application/settings_keys.py`; new readers in `application/` (Builder tool default + dims defaults, e.g. `builder_defaults.py` / `random_maze_defaults.py`); `builder/screen.py` (read default tool, **pass it into** `start_builder_session(...)`); `common/new_maze_dialog.py` + `player/generate_random_dialog.py` (initial values from settings); `common/settings_window.py` (category + fields).
- Tests: settings round-trip per scope; dialog defaults; builder initial tool.
- Rationale: Max wants the proposed sizes/tool to match his habits without editing defaults each time.

---

**Story 4.7 — Player: Continue regenerates random maze with same params**

Amends: 2.4.

- OLD: "Continue" pill in the win/timeout banner always returned to the gallery.
- NEW: for a `generated` maze, the pill reads "New random maze" and, on click, **immediately** regenerates a fresh random maze at the same width/height/entry position and mounts it (decision 3 — no dialog, no re-save). For `classic`/`saved-random`, "Continue" behavior is unchanged.
- Affects: `player/gameplay_screen.py` (store generation params on mount; new pill + handler), `player/screen.py` (regenerate callback with `navigate`), random-generation service reuse.
- Tests: gameplay-screen banner label + regenerate behavior for generated vs saved kinds.
- Rationale: play-again loop without re-typing params.

---

**Story 4.8 — Shell windowing: centered, resizable, maze zoom, fullscreen**

Amends: 1.7, 1.8.

- NEW:
  - Root window opens **centered** on screen and is `resizable(True, True)`.
  - Maze canvases **auto-fit** the available space on window resize and support **zoom**: Ctrl+wheel (and `+`/`-`) scales the cell size; re-render on change.
  - **F11** toggles fullscreen (`toggle_fullscreen`, shell scope).
  - The **Settings window** gets the same treatment (centered, resizable, F11 fullscreen; no maze zoom inside it).
  - Aligns with `epic-2-retro-item-1-router-cascade` (Settings window must not be silently closed by frame teardown).
- Affects: `app/composition_root.py` (geometry/centering, fullscreen, zoom dispatch), `player/maze_canvas.py` + builder canvas (zoom/auto-fit re-render hook), `common/settings_window.py`, `common/keybindings.py` (`toggle_fullscreen`; `+`/`-`), `kbd_tag.py`.
- Tests: window geometry (GUI), keybinding table, canvas zoom re-render.
- Rationale: responsive, modern shell; decision 2 (zoom = maze canvas scaling).

---

**Story 4.9 — Top-bar brand logo follows `theme_logo`**

Amends: 1.6, 1.8, 2.11.

- OLD: `TopBar` shows only the text brand "Labyrinthes".
- NEW: a small logo image renders **top-left before the brand text**; the image is the current `theme_logo` (game scope, decision 1), same choice as the Player's appearance setting. It re-reads on screen re-mount (theme toggle re-mounts), no live-wiring needed.
- Affects: `common/top_bar.py` (PIL `PhotoImage` + label); reuse `application/logos.py` loader (add a small brand size); `app/composition_root.py` (pass current `theme_logo` into screens/TopBar).
- Tests: `test_top_bar.py` (logo present, correct file, order before brand text).
- Rationale: the logo picker existed but was invisible — the brand mark must appear.

---

**Story 4.10 — Screen layout: labeled blocks, maze separation**

Amends: 1.8, 2.4, 3.2.

- NEW:
  - Builder: tools grouped under labeled headings in **blocks** — e.g. "Tools" (Break, Pass-through, Destroy zone, Restore zone) and "Markers" (Set Entry, Set Exit); HUD block on top; the maze lives in its own **bordered `maze-frame`** clearly separated from the side blocks; consistent spacing.
  - Player: existing labeled groups ("Movement", "Mode", "Levels", "Difficulty", "Logo") tidied into consistent blocks, clearly separated from the maze frame.
- Affects: `builder/screen.py` (group heading labels via typography tokens, maze-frame container), `player/gameplay_screen.py`/`player/screen.py` (group structure/spacing), optional small shared group-heading helper in `common/`.
- Tests: light GUI assertions (canvas parented in maze-frame, group headings present).
- Rationale: Max wants a clear visual hierarchy — blocks around, maze in the middle.

---

### 4.2 PRD amendments (summary — detailed edits in implementation)

- **FR-1** — Break: click toggles a wall segment OR movement across a wall breaks and moves; Pass-through: movement ignores walls, never modifies them; Space toggles.
- **FR-2** — zone selection adds the click–release–move–click gesture and a visible colored selection rectangle; Esc cancels.
- **FR-3** — entry marker is a square; Set Entry shows a live ghost square following the cursor; placement on click or Enter.
- **FR-4** — default dimensions (new-maze and random) and the default Builder tool are configurable settings, bounded by the shared size bounds.
- **New FR** — Builder "Inaccessible" counter (cells unreachable from the entry) with click-to-highlight; chip disabled ("—") until an entry is set.
- **New FR / NFR** — shell windowing: centered, resizable, maze zoom (Ctrl+wheel, `+`/`-`), F11 fullscreen; Settings window identical (minus maze zoom).

### 4.3 Architecture updates

- Add `domain/reachability.py` to the domain layer (pure BFS; AD-1, AD-2 intact).
- Windowing/zoom/centering lives in `app/composition_root.py` (AD-10: owns the Tk root).
- Builder tool default is an adapter-side concern: read setting in `builder/screen.py`, pass into `start_builder_session(...)`; `application/builder_session.py` gains no repository/theme dependency.
- No data-model change; wall encoding `0/1/2/3` and CSV migration requirements untouched.

### 4.4 UX updates

- `DESIGN.md`: brand-mark block (logo before "Labyrinthes"), marker glyph table (square/diamond/circle), zone selection rectangle, layout blocks, interactive HUD chip, windowing behaviors.
- `EXPERIENCE.md`: component specs (TopBar with logo, interactive `HudChip`, zone overlay, ghost markers, keybinding additions Space/Return/F11/+/-).

---

## Section 5: Implementation Handoff

**Scope:** Moderate — 10 new stories on the new Epic 4 (backlog reorganization + Developer implementation). No PM/Architect replan required.

| Role | Responsibility |
|---|---|
| Max (Product Owner) | Approve proposal; confirm story grouping; validate against running app after each story. |
| Max (Developer) | Create `epic-4` from the current `epic-3` HEAD; implement stories in order via the standard story → review → merge flow on `epic-4` (Conventional Commits in English with story keys 4.1–4.10). |
| Code review (bmad-loop / manual) | Adversarial review on each story branch before merging into `epic-4`. |
| Docs | Update PRD, add `epic-4-context.md`, UX docs, `sprint-status.yaml` (Epic 4 stories 4-1..4-10 in `backlog`; move to `todo`/`in-progress` as each starts). |

**Sequencing:** 4.1 → 4.2 → 4.3 → 4.4 → 4.5 (shared builder canvas, in order); 4.6, 4.7, 4.8, 4.9, 4.10 independent — 4.9 after 4.6 (logo is already wired; no hard dependency), 4.8 first if windowing churn is desired before canvas tweaks.

**Verification per story:** `ruff check src tests` → `ruff format --check src tests` → `pytest` (GUI tests need `DISPLAY=:0`, present). Re-run a single failing GUI test alone before assuming a regression (AGENTS.md flakiness note).

**Success criteria:** all 13 corrections reproducible in the running app (`python -m labyrinthes.app`), all test suites green, keybinding-table uniqueness holds, and `epic-4` stays off `rewrite` until every epic-4 story (4.1–4.10) is `done`.