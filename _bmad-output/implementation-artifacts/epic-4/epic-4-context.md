# Epic 4 Context: Review Corrections — Builder & Player Polish, Windowing, Configurable Defaults

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Deliver the 2026-08-19 course correction approved by Max: distinct marker/cursor glyphs, reworked Break vs Pass-through semantics, visible zone selection with a second gesture, live entry/exit placement, a reachability counter replacing "Walls broken", configurable defaults (Builder tool, new-maze and random dimensions), a play-again win-banner action, shell windowing (centered, resizable, zoom, fullscreen), a top-bar brand logo, and grouped screen layouts. The batch refines acceptance criteria delivered by Epics 1–3 (FR-1/2/3/4/10/18) and adds FR-29 through FR-34.

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

## Requirements & Constraints

- Glyphs (amends FR-1/FR-3, NFR6): entry = square, exit = diamond, player/builder = circle — states are distinguished by shape as well as color. The Builder cursor renders as a filled circle, never a rectangle outline.
- Wall-tool semantics (amends FR-1): Break breaks walls as the cursor moves across them (the former Pass-through behavior) and toggles on click; Pass-through moves through walls freely without modifying them. Closed-border invariant holds in both modes; `space` toggles the two, registered in the canonical keybinding table.
- Zone selection (amends FR-2): a live colored rectangle outline follows the selection; a plain click arms the anchor and a second click commits (single click never applies a zone op); Escape cancels.
- Entry/exit (amends FR-3): Set Entry shows a ghost square following the cursor; placement on click or Enter; the existing redefinition confirmation is honored.
- Reachability (new FR-29): the HUD counts cells inaccessible from the entry via a pure `domain/` BFS; "—" and non-interactive before an entry is set; clicking toggles an outline on those cells.
- Defaults (new FR-30): default Builder tool and default new-maze/random dimensions are scoped settings, clamped to the shared 3–50 / 3–35 bounds; the tool default is read in the adapter and passed into the session service.
- Play again (new FR-33): the win banner of a `generated` maze regenerates a random maze with the same width/height/entry immediately; `classic`/`saved-random` keep the existing Continue.
- Windowing (new FR-31): root window centered and freely resizable; maze canvases auto-fit and zoom (Ctrl+wheel, `+`/`-`); F11 fullscreen; Settings window centered/resizable/fullscreen and never silently closed by frame teardown (aligns with `epic-2-retro-item-1-router-cascade`).
- Brand mark (new FR-32): the top bar shows the brand logo per the logo setting before the app name.
- Layout (new FR-34): Builder/Player controls and displays are grouped into labeled blocks on the sides and top, separated from a bordered maze-frame.

## Technical Decisions

- Reachability is pure domain work (`domain/reachability.py`, a BFS through open passages); only rendering and input wiring live in adapters.
- Wall-tool semantics change lives in `application/builder_session.py::move_cursor` (pure logic); no data-model change, wall encoding `0/1/2/3` untouched.
- Windowing/zoom/centering lives in `app/composition_root.py` (AD-10: it owns the single `Tk()` root and may import concrete screens).
- The default Builder tool is an adapter-side concern: read the setting in `builder/screen.py`, pass it into `start_builder_session(...)` — the application layer gains no settings dependency.
- New settings follow AD-7 (scoped keys, single readers): `game` scope for random defaults, `builder` scope for Builder defaults, plus a "Defaults" category in the shared `SettingsWindow`.
- The top-bar logo reuses the shared loader in `application/logos.py`; `common/` never couples to a screen's asset folder.
- Keybindings added to the one canonical table (Story 1.10): `toggle_break_pass_through` (Space), `place_marker` (Return), `toggle_fullscreen` (F11) — the collision/label-consistency test must stay green.

## UX & Interaction Patterns

- Marker glyph set (square/diamond/circle) is the shared shape language across Builder and Player.
- Zone selection: drag gesture kept; click-click gesture added; colored outline always visible while selecting; Escape cancels an armed anchor.
- Entry/exit ghosts track the cursor in real time; placement by click or Enter.
- The interactive HUD chip (Inaccessible counter) toggles a colored cell outline; a `HudChip` gains an optional command.
- Windows: centered, resizable, zoomable maze canvas, F11 fullscreen; the Settings window behaves identically (minus maze zoom).
- Top bar: logo image before the brand text on every screen.
- Voice and Tone stays plain and non-alarmist.

## Cross-Story Dependencies

- Epic 1 supplies the router, `common/` toolkit, tokens, settings scoping, and the canonical keybinding table (1.6–1.10); `application/logos.py` and the logo setting flow come from Epic 2's 2.11.
- Epic 2's maze canvas, generate-random dialog, and gameplay win banner are the Player surfaces 4.6/4.7/4.8 touch; Epic 3's builder canvas, session, and dialogs are the surfaces 4.1–4.5/4.8/4.10 touch.
- Internal: 4.1 (glyphs) → 4.2 (tools) → 4.3 (zone) → 4.4 (markers) → 4.5 (counter) share the builder canvas and should land in order; 4.6, 4.7, 4.8, 4.9, 4.10 are largely independent.
- Epic 4 branches from the current `epic-3-build-and-test-a-maze` HEAD (which already contains shell + Player + Builder) and stays off `rewrite` until every epic-3 (3.1–3.9) and epic-4 story is `done`.