# Sprint Change Proposal — 2026-08-25

**Project:** Labyrinthes — modular rewrite (`rewrite` lineage, active branch `story/4-4-entry-exit-live-placement`)
**Author:** Max (course-correction review)
**Mode:** Batch
**Scope classification:** Mixed — Major (item A) + Moderate (items B, C, D)
**Status:** Approved by Max (2026-08-25), pending one clarification on item C (resolved: the maze name is *appended after* the kind segment in the breadcrumb, never replacing it — see Section 4.1/4.3). `epics.md` (Stories 4.11-4.14, FR-35 through FR-38) and `sprint-status.yaml` (backlog entries) updated accordingly.

---

## Section 1: Issue Summary

Max reviewed the working Builder (fresh off Story 4.4) and found **4 corrective items**. One redefines a core domain concept the PRD/Glossary already got wrong relative to the legacy app; the other three are bugs/gaps in already-`done` stories, all fixable within Epic 4 (which exists exactly for this kind of correction).

**A. "Classic" maze is wrongly conflated with a user-saved finished maze**
Per `CLAUDE.md`'s own description of the legacy app, `Labyrinthes_classiques/` (hand-built mazes the *dev* ships with the game) and `Labyrinthes_creation/` (work saved from the Builder by a *player*) are two separate folders. The rewrite's PRD Glossary defines "Classic maze" as "a hand-built maze created via the Builder and shipped with the game" — already ambiguous — and Story 3.6/the Architecture Spine's `MazeKind` enum collapsed both into one `classic` kind. A maze the author saves as "finished" from the Builder today lands in `mazes/classic/` indistinguishable from a maze the dev pre-ships at first install. There is no `creation` kind at all.

**B. Save-name text fields leak screen-wide keyboard shortcuts**
`_SaveNameDialog` (Builder) and `SaveMazeDialog` (Player) each locally block only the one or two letters their author noticed collide (`s`/`S`, `t`/`T` in the Builder's case). The Builder's canonical keybinding table registers 13 screen-scoped shortcuts via `bind_all()` (`b`, `p`, `d`, `r`, `e`, `x`, `f`, `m`, `h`, `c`, `n`, `Space`, `Return`), which fire globally regardless of focus. Typing a maze name containing any of the other 11 unblocked letters — or pressing Space/Enter — fires the corresponding Builder action (e.g. `d` fires Destroy Zone, `Return` fires Place Marker) instead of typing the character into the name field.

**C. The maze's actual name never reaches the breadcrumb**
Builder's breadcrumb is hardcoded to two segments, `Home / Builder` — no third segment at all, even once a maze is loaded/named. Player's breadcrumb adds a third segment, but it's `_KIND_LABELS[state.kind]` (a generic label like "Classic Maze"), never the specific maze's own name (e.g. "10x10edf"). The PRD's own worked example (§2.2, "Home / Player / Classic Maze 4") implies a per-maze label that isn't actually produced anywhere. The fix **adds** the maze's name as a new trailing segment, after the existing kind-derived one — it does not replace it: `Home / Player / Classic / 10x10edf`, not `Home / Player / 10x10edf`. The kind segment stays meaningful on its own (e.g. clicking back to it, once Story 4.14's sectioned gallery exists, is a natural "back to this category" affordance) and the reader still sees *what kind of maze* at a glance, not just its name.

**D. The Player selection screen never got the grid gallery the locked UX mockup specifies**
`mockups/key-player-selection.html` already draws a 4-column `gallery-grid` of `maze-card`s (thumbnail, name, dimensions, best time). Story 2.1's docstring explicitly descoped this to a single-item pager ("previous/next/jump") because no wall-rendering component existed yet to draw thumbnails from. That blocker is gone — `maze_canvas.py`'s wall/marker rendering has existed since Epic 3. Max now also wants three separate sections (Classic / Creations / Random), which follows directly from item A.

### Evidence

- `src/labyrinthes/domain/maze.py::MazeKind` — exactly four members: `CLASSIC`, `SKETCH`, `SAVED_RANDOM`, `GENERATED`. No `CREATION`.
- `src/labyrinthes/adapters/storage/paths.py::maze_file_path` — one subfolder per `kind.value`; a Builder "Save as Maze" (Story 3.6, `MazeKind.CLASSIC`) writes to `mazes/classic/`.
- Live proof on disk: `mazes/classic/10x10edf.csv` is the author's own test save from working through Story 4.4 — sitting in the same folder a dev-shipped classic would occupy.
- Epic 5's own Story 5.1 already plans to migrate the legacy `Labyrinthes_creation/` folder separately from `Labyrinthes_classiques/` — the migration epic already assumes the split this course correction restores; only Epics 1–4's domain model drifted from it.
- `src/labyrinthes/adapters/tkinter/builder/save_dialog.py:105-108` — `<KeyPress-s/S/t/T>` locally return `"break"`; no equivalent guard for `b/B/d/D/r/R/e/E/x/X/f/F/m/M/h/H/c/C/n/N/space/Return`.
- `src/labyrinthes/adapters/tkinter/common/keybindings.py:88-110` — `KEYBINDINGS` table, Builder scope (`ScreenId.BUILDER`) alone has 9 single-letter entries plus `space`/`Return`; `bind_shortcut()` always uses `widget.bind_all()`.
- `src/labyrinthes/adapters/tkinter/builder/screen.py:82-85` — `breadcrumb_segments` is a fixed 2-element list, no maze-derived third segment, in any branch of `mount()`.
- `src/labyrinthes/adapters/tkinter/player/screen.py:116-130` — three breadcrumb branches all append `_KIND_LABELS[...]`, never the maze's name.
- `ux-designs/.../mockups/key-player-selection.html:79-188` — `.gallery-grid { grid-template-columns: repeat(4, 1fr); }`, `.maze-card` with `.card-name`/`.card-meta` (dimensions, `"best 00:42"`), already drawn and captioned "Classic maze gallery... (FR-9/FR-10)".
- `src/labyrinthes/adapters/tkinter/player/classic_gallery.py` (`ClassicMazeGallery`, Story 2.1/2.3) — one-item-at-a-time pager over a flat `list[tuple[MazeKind, str]]` combining `CLASSIC` then `SAVED_RANDOM`; no grid, no per-kind sections.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Epics 1–3 `done`; Epic 4 `in-progress` (4.1–4.4 `done`, 4.5–4.10 `backlog`) — every story this proposal touches is either already `done` (needs an amendment story, Epic 4's established pattern) or still `backlog` in Epic 4 (can absorb the correction directly, e.g. 4.5's "click-to-highlight" pattern is reused by nothing here but 4.6/4.10 do touch the same screens).

---

## Section 2: Impact Analysis

### 2.1 Epic impact

| Epic | State | Impact |
|---|---|---|
| Epic 1 — Foundation | `done` | Story 1.8 (breadcrumb) and Story 1.10 (canonical keybindings) acceptance criteria are incomplete relative to items C and B — amended via new Epic 4 stories, no rework of Epic 1 itself. |
| Epic 2 — Player | `done` | Story 2.1/2.3 (`ClassicMazeGallery`) rebuilt as the 3-section grid gallery (item D); FR-9/FR-11 amended. Story 2.11 (appearance) unaffected. |
| Epic 3 — Builder | `done` | Story 3.6 (Sketch/Maze save) corrected: a finished Builder save produces `MazeKind.CREATION`, never `CLASSIC` (item A). Story 3.4 (entry/exit marking) unaffected. |
| Epic 4 — Review Corrections | `in-progress` | Natural home for all four corrections — extends the epic with new stories 4.11–4.14, same pattern already used for FR-29–FR-34. |
| Epic 5 — Legacy Migration | `backlog` | Realigned, not reworked: Story 5.1 already migrates `Labyrinthes_creation/` separately; add one line confirming it now maps onto the (already-planned) `creation/` `MazeKind`, and Story 5.3's `MazeId` backfill extends to migrated creations too (per your "Creation is MazeId/record-eligible" decision, item A). |
| Epic 6 — Home Enrichment | `backlog` | Story 6.1/6.2's `RecordsService.record_completion` eligibility check (`classic` or `saved-random`) extended to include `creation`. |

### 2.2 Story impact

New stories proposed on Epic 4 (all `backlog` until approved), inserted after the existing 4.10:

| New story | Reworks / amends | Item |
|---|---|---|
| 4.11 Classic vs. Creation maze kind | 3.6 (Builder save), 2.1/2.3 (gallery data), 6.1/6.2 (records eligibility), `MazeKind`, `paths.py` | A |
| 4.12 Screen shortcuts never fire while a text-entry dialog is focused | 1.10 (keybinding dispatch), `save_dialog.py`, `save_maze_dialog.py`, `new_maze_dialog.py`, `generate_random_dialog.py` | B |
| 4.13 Breadcrumb shows the maze's own name | 1.8 (breadcrumb), `builder/screen.py`, `player/screen.py` | C |
| 4.14 Player selection screen — grid gallery split into Classic / Creations / Random | 2.1/2.3 (`ClassicMazeGallery` → rebuilt) | D, depends on 4.11 for category data |

Sequencing: **4.11 before 4.14** (the grid gallery's three sections need the `creation` kind to exist first). 4.12 and 4.13 are independent of the others and of each other.

### 2.3 Artifact conflicts

- **PRD** — new FR numbers appended, following the FR-29–FR-34 precedent (2026-08-19 correction) rather than silently rewriting existing FR text in place:
  - **FR-35** (amends Glossary + FR-5/FR-9/FR-11/FR-20/FR-27): redefines Classic maze as dev-authored, present at first install, never produced by a player's Builder save; introduces **Creation** — a finished maze a player saves from the Builder, distinct from Classic, MazeId/Personal-Record-eligible like Classic and Saved-random.
  - **FR-36** (amends FR-22): a screen's registered keyboard shortcuts never fire while a text-entry field inside an open dialog holds focus — fixed at the dispatch mechanism, not per-dialog letter-blocking.
  - **FR-37** (amends FR-26): whenever a screen has a specific maze loaded, its breadcrumb gains an additional trailing segment carrying that maze's own saved name — appended *after* the existing kind-derived segment, which stays (e.g. `Home / Player / Classic / 10x10edf`), never replacing it.
  - **FR-38** (amends FR-9/FR-10/FR-11): the Player's maze-selection screen presents Classic, Creation, and Random (saved) mazes as three separate, clearly labeled sections in one scrollable card grid, per the locked mockup.
  - Glossary: new **Creation** entry; **Classic maze** entry reworded per FR-35.
- **Architecture Spine** — `AD-3`'s `Maze` kind tag (`classic | sketch | saved-random | generated`) gains a fifth member, `creation`, tagged `[Amended — 2026-08-25 course correction]`, mirroring its existing `[Amended]` history for `id`/`MazeId`. `_ID_ELIGIBLE_KINDS` (currently `{CLASSIC, SAVED_RANDOM}`) becomes `{CLASSIC, SAVED_RANDOM, CREATION}`. `AD-8`'s migration-script path-constants reuse still holds unchanged (`paths.py` already derives folder names from `kind.value`, so adding `creation` costs one enum member, not a new module). This is architecture-pinned, so it needs Winston's (architect) sign-off before story drafting, same as any other AD amendment.
- **UX Design / Experience** — `DESIGN.md`'s Components section gains a `gallery-grid`/`maze-card` write-up (the mockup already draws it but no prose component spec exists yet, unlike `record-group`); `EXPERIENCE.md`'s selection-screen IA row updated from "Classic maze gallery (previous/next/jump-to-number)" to the 3-section grid; breadcrumb note in `DESIGN.md` clarified to say the trailing segment is the maze's name, not its kind.
- **Keybinding table / mechanism** — no new entries; `bind_shortcut()`'s dispatch gains a focus-aware guard (item B) instead of new keys.
- **Settings / data layout** — no new settings keys. `mazes/creation/` becomes a new on-disk subfolder (mirrors `mazes/classic/`, `mazes/sketch/`, etc. — no path-constants change needed beyond the enum member).

### 2.4 Technical impact

- `domain/maze.py`: add `MazeKind.CREATION`, extend `_ID_ELIGIBLE_KINDS`.
- `adapters/storage/paths.py`: no code change — folder mapping is already `kind.value`-driven; `creation/` is created on first save.
- `builder/edit_area.py` / save flow (Story 3.6's "finished Maze" path): target kind changes from `MazeKind.CLASSIC` to `MazeKind.CREATION`.
- `application/records_service.py` (or wherever Story 6.1's eligibility check lives): extend the `classic`/`saved-random` check to include `creation`.
- `adapters/tkinter/common/keybindings.py::bind_shortcut`: guard the dispatched `handler` — skip the callback (but let the key event continue reaching the focused widget) when `widget.tk.call("focus")` resolves to a widget whose toplevel is not the screen's own root, or more simply, when the focused widget is a `tk.Entry`/`tk.Text`. This replaces `save_dialog.py`'s and `save_maze_dialog.py`'s per-letter `<KeyPress-x>` → `"break"` blocks, which can then be deleted rather than extended.
- `adapters/tkinter/builder/screen.py`, `adapters/tkinter/player/screen.py`: a new trailing `BreadcrumbSegment` built from `state.name`-equivalent (the maze's on-disk/save name) is *appended* — Builder's list grows from 2 to 3 segments, Player's from 3 to 4; `_KIND_LABELS[state.kind]` stays exactly where it is today, it is not replaced. Requires `Maze` or its wrapping state to actually carry a display name through to the screen — currently `Maze` (domain) has no `name` field (name is a storage-layer concept, keyed by filename via `MazeRepository`); this needs a small carried-through value (e.g. the screen's own session/launch state already threading a name, or `MazeRepository.list_names()`'s reverse lookup) — flagged as a design decision for the story, not resolved here.
- `adapters/tkinter/player/classic_gallery.py`: rebuilt as a scrollable, sectioned card grid (`Classic` / `Creations` / `Random`) reusing `maze_canvas.py`'s rendering for card thumbnails (or a simplified static render — a story-level decision) instead of the current one-item pager. Likely renamed (`ClassicMazeGallery` → e.g. `MazeSelectionGallery`) given it's no longer classic-only.

---

## Section 3: Recommended Approach

**Option 1 — Direct Adjustment (recommended).** Add stories 4.11–4.14 to the existing, still-open Epic 4 — no new epic, no renumbering (unlike the 2026-08-19 correction, Epic 4 already exists and is exactly the epic for this). No rollback, no MVP/PRD scope reduction.

- **Rollback (Option 2) — not viable:** Stories 3.6, 2.1/2.3, 1.8, 1.10 all deliver real, correct-as-far-as-they-went value; reverting would lose delivered work to fix what's really a definitional gap and two bugs.
- **MVP review (Option 3) — not needed:** all four items are corrections/refinements within the existing FR set (extended, not reduced) — no PRD goal changes.

**Rationale:** three of the four items (B, C, D) are straightforward, low-risk adapter-layer fixes with an existing test surface (keybinding collision test, breadcrumb rendering tests, gallery tests). Item A is the one that reaches into a pinned architecture decision (`AD-3`) and five FRs — routed separately for sign-off before its story is drafted, so the Epic 4 story doesn't start from an un-ratified assumption. Effort: **Medium** (4 stories: 1 domain/storage change + 3 adapter-layer fixes, one of which — 4.14 — is a real UI rebuild). Risk: **Low** for B/C; **Low–Medium** for A (touches the `_ID_ELIGIBLE_KINDS` invariant and Records eligibility, both covered by existing tests to extend) and D (biggest surface-area change, but additive — no existing gallery behavior is removed, only reorganized/extended).

---

## Section 4: Detailed Change Proposals

### 4.1 PRD proposals

**New FR-35 — Classic vs. Creation maze**

- OLD (Glossary): "Classic maze — a hand-built maze created via the Builder and shipped with the game."
- NEW (Glossary): "Classic maze — a hand-built maze present at first install, authored by the project's developer as part of the game's shipped content; never produced by a player's own Builder save." Plus a new entry: "Creation — a finished maze (entry and exit set) a player builds and saves via the Builder; built with the same tool as a Classic maze, but distinct in provenance and never shipped as game content."
- OLD (FR-5 consequence, implicit): a finished "Maze" save has no distinct identity from a Classic maze.
- NEW: a finished Builder save always produces a `Creation`-kind maze; `Classic` mazes are never created through the app's normal Builder-save flow (a dev may hand-place a file directly into the classic store, outside this FR's scope — same as the legacy app).
- NEW (FR-9/FR-11 consequence): the Player's selector distinguishes Classic, Creation, and Random (saved) as separate categories (see FR-38).
- NEW (FR-20/FR-27 consequence): `Creation` is `MazeId`-eligible and Personal-Record-eligible, on the same terms as `Classic`/`Saved-random` (Max's decision, 2026-08-25).
- Rationale: matches the legacy app's own `Labyrinthes_classiques/` vs. `Labyrinthes_creation/` split (`CLAUDE.md`), which the rewrite's PRD/domain model had drifted from.

**New FR-36 — Screen shortcuts never leak into a focused text field**

- OLD (FR-22 consequence, implicit): dialogs individually block the one or two shortcut letters their author noticed collide with a name field.
- NEW: no keyboard shortcut registered for the active screen fires while a text-entry field inside an open dialog holds keyboard focus — enforced once, at the shortcut-dispatch mechanism.
- Rationale: the current per-dialog letter-blocking approach is enumerably incomplete (11 of 13 Builder shortcuts, plus Space/Enter, are still unblocked in the Save dialog).

**New FR-37 — Maze name in the breadcrumb**

- OLD (FR-26 consequence, implicit): a screen's breadcrumb's trailing segment is a generic kind label (or, in Builder's case, absent).
- NEW: whenever a screen has a specific maze loaded, the breadcrumb gains one additional trailing segment carrying that maze's own saved name — appended *after* the existing kind-derived segment, not replacing it (e.g. `Home / Player / Classic / 10x10edf`).
- Rationale: realizes the PRD's own worked example (§2.2) while keeping the "what kind" cue the kind segment already gives — the name adds "which specific one" on top, it doesn't trade one piece of information for the other.

**New FR-38 — Grid gallery, split by category**

- OLD (FR-9/FR-10/FR-11 consequence, Story 2.1's descoping): the Player's selection screen is a single-item pager (previous/next/jump-to-number) over a flat Classic+Saved-random list.
- NEW: the selection screen shows a scrollable card grid (per the locked `key-player-selection.html` mockup), split into three clearly labeled sections — Classic, Creations, Random — each independently populated (an empty section shows its own inline empty-state, not the whole screen's).
- Rationale: the technical blocker cited for the original descoping (no wall-rendering component to draw thumbnails from) no longer exists; the mockup already specified this and was never revisited.

### 4.2 Architecture Spine proposal

- OLD (`AD-3`): `Maze` kind tag = `classic | sketch | saved-random | generated`.
- NEW: `Maze` kind tag = `classic | creation | sketch | saved-random | generated` `[Amended — 2026-08-25 course correction, Max's decision]`. `creation` sits alongside `classic`/`saved-random` in `_ID_ELIGIBLE_KINDS` (MazeId-eligible, Personal-Record-eligible) — it differs from them only in *how* a maze reaches that state (a player's Builder "Save as Maze" vs. dev-authored content vs. a saved random generation), not in what it's eligible for downstream.
- Needs Winston's (architect) sign-off before Story 4.11 is drafted — this is a change to a pinned AD, same bar as the original FR-27 amendment that added `id`/`MazeId`.

### 4.3 Story proposals (new stories on Epic 4)

---

**Story 4.11 — Classic vs. Creation maze kind**

Amends: 3.6 (Builder save), 2.1/2.3 (gallery data source), 6.1/6.2 (records eligibility, once implemented).
Realizes: FR-35.

- **Given** the Builder's "Save as Maze" (finished) flow **When** confirmed **Then** the resulting `Maze` carries `MazeKind.CREATION`, never `MazeKind.CLASSIC`.
- **Given** `MazeKind.CREATION` **When** a `Maze` of that kind is saved **Then** `MazeRepository` mints a `MazeId` exactly as it does for `CLASSIC`/`SAVED_RANDOM` (Story 1.4's minting rule extended).
- **Given** the Records eligibility check (Story 6.1's `RecordsService.record_completion`, once implemented) **When** a `CREATION` maze is won **Then** a record is written, on the same terms as `CLASSIC`/`SAVED_RANDOM`.
- **Given** existing `CLASSIC`-folder test fixtures/local saves made under the pre-correction behavior (e.g. the author's own `mazes/classic/10x10edf.csv`) **When** this story lands **Then** they are not silently reinterpreted — no automatic reclassification is in scope here (that's Epic 5/migration territory if ever needed for real shipped data); local dev scratch files can simply be moved/deleted by hand.

---

**Story 4.12 — Screen shortcuts never fire while a text-entry dialog is focused**

Amends: 1.10 (`bind_shortcut` dispatch).
Realizes: FR-36.

- **Given** any screen-scoped keyboard shortcut registered via `bind_shortcut()` **When** the current Tk focus widget is a text-entry field (`tk.Entry`/`tk.Text`) inside an open dialog **Then** the shortcut's callback does not fire and the keystroke reaches the entry field normally.
- **Given** `_SaveNameDialog` and `SaveMazeDialog`'s per-letter `<KeyPress-s/S/t/T>` `"break"` guards **When** this story lands **Then** they are deleted — the general dispatch guard supersedes them, so no dialog needs its own allowlist.
- **Given** `NewMazeDialog` and `GenerateRandomDialog`'s numeric entry fields **When** checked against this same guard **Then** they are covered too, even though no prior collision was reported for them (defense-in-depth, not a per-field patch).
- **Given** the canonical keybinding table's collision test (Story 1.10) **When** this story lands **Then** it still passes unchanged — this is a dispatch-time fix, not a table change.

---

**Story 4.13 — Breadcrumb shows the maze's own name**

Amends: 1.8 (breadcrumb), `builder/screen.py`, `player/screen.py`.
Realizes: FR-37.

- **Given** the Builder with a maze loaded (new, opened sketch, or Test-in-Player round-trip) **When** the top bar renders **Then** a new trailing segment carrying that maze's saved name is appended after "Builder" (or an in-progress/unsaved indicator per the story's own resolution, for a maze with no name yet) — "Builder" itself is untouched.
- **Given** the Player with a maze mounted (classic, creation, saved-random, or generated) **When** the top bar renders **Then** a new trailing segment carrying that maze's saved name is appended *after* the existing kind-derived segment (e.g. `Home / Player / Classic / 10x10edf`) — the kind segment is never replaced or removed, including for an unsaved `generated` maze, which simply gets no name segment appended (it has none).
- **Given** the current `Maze` domain value **When** inspected **Then** it has no `name` field (name is a storage-layer/filename concept) — this story resolves how the name is threaded from `MazeRepository`/the save flow through to the screen's breadcrumb without adding a UI concern to `domain/`.

---

**Story 4.14 — Player selection screen: grid gallery split into Classic / Creations / Random**

Amends: 2.1/2.3 (`ClassicMazeGallery` rebuilt).
Realizes: FR-38.
Depends on: 4.11 (needs the `creation` kind to populate its section).

- **Given** the Player's maze-selection screen **When** it renders **Then** it shows a scrollable card grid with three labeled sections — Classic, Creations, Random — per `key-player-selection.html`'s `gallery-grid`/`maze-card` pattern.
- **Given** a section with no mazes **When** rendered **Then** that section alone shows an inline empty-state message (e.g. Creations before the player has saved one) — the other populated sections stay unaffected.
- **Given** a maze card **When** clicked or activated via keyboard **Then** the router mounts the gameplay screen with that Maze as state (same commit behavior as today's pager).
- **Given** the "Generate random" entry point **When** rendered **Then** it stays a clearly separate action, not a fourth section card (existing behavior, FR-10).
- **Given** the accessibility floor (NFR6) **When** the grid is keyboard-navigated **Then** every card is reachable and operable via Tab + Enter/Space, with a visible focus indicator.

---

## Section 5: Implementation Handoff

**Major — route to PM (John) then Architect (Winston):**
- PRD: FR-35 (Glossary + FR-5/9/11/20/27 consequences), plus FR-36/37/38 for the record.
- Architecture Spine: `AD-3` amendment (add `creation` to the kind tag + `_ID_ELIGIBLE_KINDS`).
- Deliverable: updated `prd.md`/Glossary and `ARCHITECTURE-SPINE.md`, both marked `[Amended]`, before Story 4.11 is drafted in full detail.

**Moderate — route to PO/Dev (Amelia), directly implementable once the Major piece lands for 4.11/4.14:**
- `epics.md`: append Stories 4.11–4.14 to Epic 4 (as drafted in Section 4.3 above).
- `sprint-status.yaml`: add `4-11-classic-vs-creation-maze-kind`, `4-12-screen-shortcuts-never-leak-into-dialogs`, `4-13-breadcrumb-shows-maze-name`, `4-14-player-selection-grid-gallery` under `development_status`, all `backlog`.
- Implementation order: 4.12 and 4.13 can start immediately (no dependency on the Major piece); 4.11 waits on the PRD/Architecture sign-off; 4.14 waits on 4.11.

**Success criteria:** all four new stories pass their acceptance criteria under `pytest`/`ruff` per NFR3; the keybinding collision test (1.10) and the `_ID_ELIGIBLE_KINDS` invariant test stay green; the author's own local `mazes/` scratch data is manually tidied (moved/deleted), not auto-migrated, since it's dev scratch data, not shipped content.
