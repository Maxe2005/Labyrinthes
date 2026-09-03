# Epic 4 Context: Review Corrections — Builder & Player Polish, Windowing, Configurable Defaults

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Epic 4 corrects and refines Builder/Player behavior delivered in Epics 1–3, driven by two course corrections. The 2026-08-19 correction fixes interaction semantics that shipped ambiguous or incomplete: distinct marker/cursor glyphs, reworked Break vs Pass-through wall tools, visible two-gesture zone selection, live entry/exit placement, a reachability counter replacing "Walls broken," configurable defaults, a random-maze play-again action, shell windowing (centered/resizable/zoom/fullscreen), a top-bar brand logo, and grouped screen layouts. The 2026-08-25 correction goes further, fixing a definitional gap and two dispatch bugs found during Builder review: a Classic-vs-Creation maze-kind split (restoring the legacy app's shipped-vs-player-saved distinction, which the rewrite's domain model had collapsed), a global keyboard-shortcut dispatch guard so screen shortcuts never fire while a dialog's text field has focus, the maze's own saved name appended to the breadcrumb, and a three-section (Classic/Creations/Random) grid gallery replacing the Player's single-item pager.

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

- **Builder reachability feedback:** the Builder HUD shows a live count of cells unreachable from the entry through open passages; clicking it outlines those cells and toggles off again. Before an entry is set the counter reads "—" and is inert. Replaces the former "Walls broken" stat.
- **Configurable defaults:** the default Builder tool, New Maze dialog dimensions, and Generate Random dialog dimensions are user-configurable settings, clamped to the shared 3–50 column / 3–35 row bounds, falling back to the bounds' minimum when unset.
- **Window management:** the app window opens centered, resizes freely, the maze canvas zooms (Ctrl+wheel, `+`/`-`) and adapts on resize, F11 toggles fullscreen. The Settings window gets the same centered/resizable/fullscreen treatment and must never be silently closed by a navigation-triggered frame teardown.
- **Top-bar brand mark:** every screen's top bar shows the logo matching the user's logo setting, before the "Labyrinthes" wordmark.
- **Play again:** the win banner on a solved `generated` (unsaved random) maze offers regenerating a new random maze with identical width/height/entry, immediately, labeled distinctly from "Continue" (e.g. "New random maze"); `classic`/`saved-random`/`creation` wins keep the existing Continue behavior.
- **Layout grouping:** Builder and Player controls/displays are grouped into labeled blocks in side bars and a top HUD, clearly separated from the bordered maze-frame.
- **Classic vs. Creation:** a Classic maze is dev-authored, shipped content present at first install — never produced by a player's Builder save. A Creation is a finished maze (entry+exit set) a player builds and saves via the Builder — same tool, distinct provenance, never shipped. Creation is MazeId-eligible and Personal-Record-eligible on the same terms as Classic/Saved-random. No automatic reclassification of maze files already saved under the pre-correction behavior.
- **Shortcut dispatch guard:** no keyboard shortcut registered for the active screen fires while a text-entry field (`tk.Entry`/`tk.Text`) inside an open dialog holds keyboard focus — fixed once at the dispatch mechanism, not per-dialog letter-blocking; existing per-dialog `"break"` guards are deleted, not extended. The canonical keybinding table and its collision test are unaffected — this is dispatch-time only.
- **Maze name in breadcrumb:** whenever a screen has a specific maze loaded, its breadcrumb gains a trailing segment carrying that maze's own saved name, appended *after* the existing kind-derived segment (never replacing it), e.g. "Home / Player / Classic / 10x10edf". An unsaved `generated` maze gets no name segment (it has none). `Maze` (domain) stays without a `name` field — name is a storage-layer/filename concept threaded through screen state, not added to `domain/`.
- **Grid gallery, split by category:** the Player's maze-selection screen shows one scrollable card grid with three independently-populated, labeled sections — Classic, Creations, Random — each with its own empty-state when empty; the "Generate random" entry point stays a separate action, never a fourth section card. Every card is keyboard-reachable (Tab + Enter/Space) with a visible focus indicator.
- **Cross-cutting:** the maze engine (grid encoding, reachability computation) stays UI-independent; the 0/1/2/3 CSV contract and `MazeId` minting rule extend additively to `creation` without altering existing fields; every action stays keyboard-operable at AA contrast.

## Technical Decisions

- Single composition root (`app/`) owns the one `Tk()` root and screen router; Home/Builder/Player register via `mount(parent, state: Maze | None) -> Frame` and never import each other. Windowing (centering, resizability, F11, zoom dispatch) lives in the composition root; maze canvases expose zoom/auto-fit re-render hooks.
- `MazeKind` gains a fifth member, `CREATION`, alongside `CLASSIC`/`SKETCH`/`SAVED_RANDOM`/`GENERATED`; `_ID_ELIGIBLE_KINDS` extends to `{CLASSIC, SAVED_RANDOM, CREATION}`. Builder's "Save as Maze" (finished) flow now targets `CREATION`, never `CLASSIC`. `MazeRepository`'s existing minting/writer routine handles `CREATION` identically — no bespoke serializer.
- Reachability is a pure function in `domain/` (BFS through open passages, e.g. `inaccessible_cells(maze, entry)`), with no UI dependency — called from the Builder adapter for the HUD counter and highlight overlay.
- Break mode: crossing a wall breaks it and moves the cursor; a single click still toggles a wall segment. Pass-through mode: the cursor crosses walls freely, modifying nothing. Space toggles between the two. Zone selection accepts either click-drag-release or a click-click (arm anchor, then commit) gesture, with a live colored outline and Escape cancelling an armed anchor. Entry/exit ghosts (square/diamond) follow the cursor in real time and place on click or Enter.
- Configurable defaults persist per scope via the existing `SettingsRepository` (`builder` scope: default tool, new-maze dimensions; `game` scope: random dimensions); read in the adapter layer only — `application/` gains no settings dependency.
- Shortcut dispatch guard lives in the shared `bind_shortcut()` mechanism (`adapters/tkinter/common/`): it inspects the current Tk focus widget and skips the callback (letting the keystroke reach the field) when focus is inside a text-entry field of an open dialog.
- Breadcrumb name threading and the gallery rebuild are adapter-layer/storage-layer concerns only — no new domain concept beyond `MazeKind.CREATION`. The Player's flat pager component is rebuilt as a sectioned, scrollable card grid reusing existing maze-frame rendering for card thumbnails.

## UX & Interaction Patterns

- Three distinct glyphs, never color alone: filled square = entry, filled diamond = exit, filled circle = player/builder cursor (Builder cursor is the same "ball" glyph as the Player, never a rectangle outline).
- A broken wall renders as a structural gap — never dashed or patterned.
- Breadcrumb reflects actual navigation depth, Home segment always present and clickable, each earlier crumb jumps there directly; every screen feeds its own dynamic sub-state (and now maze-name) label into the one shared breadcrumb widget.
- Top bar layout: brand mark + "Labyrinthes" wordmark on the left, breadcrumb/icon/pill controls as established; IA is fixed — maze centered in its own `maze-frame`, flanked by labeled tool side bars, under a full-width top bar.
- Every focusable control (including gallery cards and the reachability counter) needs a visible, AA-contrast focus indicator and full keyboard operability — no mouse-only affordance.

## Cross-Story Dependencies

- **4.11 → 4.14:** the sectioned gallery needs the `CREATION` kind to exist first to populate its Creations section.
- **4.11 → Epic 6 (6.1/6.2):** Records eligibility extends from `classic`/`saved-random` to include `creation` once implemented there.
- **4.11 → Epic 5 (5.3):** the migration script's `MazeId` backfill extends to migrated Creations under the same eligibility decision.
- **4.12 and 4.13** are independent of each other and of the rest of the epic — 4.12 is a pure dispatch-mechanism fix, 4.13 is a pure breadcrumb/name-threading fix.
- **4.1–4.5** all touch the Builder canvas/screen and are sequenced (glyphs → tool semantics → zone → markers → counter) to minimize merge friction.
- **4.6, 4.7, 4.8, 4.9, 4.10** each touch a distinct area (settings/dialogs, Player win banner, composition root, top bar, screen layout) and are otherwise independent of one another.
