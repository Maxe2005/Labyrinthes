---
title: 'Story 2.4: Gameplay screen foundation — rendering, HUD, baseline movement, win detection'
type: 'feature'
created: '2026-08-10'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-2-context.md']
warnings: [oversized]
baseline_revision: 'd8919652407890b7abdb45fb0f1fc1e98994e3fa'
final_revision: '82cbe52dbc2b2bfabebc14044188f106872c9095'
---

<intent-contract>

## Intent

**Problem:** `GameplayPlaceholder` (Story 2.3) only ever shows a plain-text summary of the mounted `Maze` plus a Save action — no wall/marker/ball rendering, no HUD, no movement, no win detection, so a player still cannot actually play a maze end to end.

**Approach:** Replace `GameplayPlaceholder` with `GameplayScreen`: a `MazeCanvas` draws wall-bars/entry/exit/ball once from the `Maze`, an HUD row shows Level/Difficulty/Time/Pos `HudChip`s, arrow keys drive a pure `domain.movement.attempt_move` + `application.player_session` orchestration loop (Discrete, one cell per press — this story's baseline), and reaching `maze.exit` shows an inline win banner ("Solved in 00:42.") with a Continue action. Story 2.3's Save flow (shown only for `MazeKind.GENERATED`) is preserved unchanged inside the new screen.

## Boundaries & Constraints

**Always:** `adapters/tkinter/player/` never imports `adapters/storage/` directly (AD-9). Movement mechanics (`Direction`, `attempt_move`) live in `domain/` as pure functions; session orchestration (`PlayerSession`, `start_session`/`move`/`tick`) lives in `application/player_session.py` as pure functions over immutable state (no Tk, no wall-clock reads) — only rendering, HUD, input-wiring, and `.after()` timer scheduling live in `adapters/tkinter/player/`. Walls draw as solid bars; an absent (broken) wall is a structural gap — never dashed/patterned. Entry (circle), exit (diamond), and the ball (circle, distinct color) are shape *and* color distinguished, never color alone (NFR6). A blocked arrow-key press is a silent no-op: no error, no state change. `GameplayScreen`'s `.after()` tick job is cancelled on `<Destroy>` so a pending tick never fires against a torn-down widget. The movement keybindings extend `KEYBINDINGS` (Story 1.10) like every other shortcut — no ad hoc `bind_all()` outside that table.

**Block If:** Nothing here requires human input — canvas sizing, the Pos-chip format, the breadcrumb's kind-derived label, and Continue's semantics are resolvable design decisions (see Design Notes), not blocking gaps.

**Never:** No Smooth movement or configurable speed (Story 2.5). No Level/Difficulty selection UI or their real visibility rules (Stories 2.6/2.7) — Level/Difficulty chips pin fixed placeholder values this story. No HARD-mode fog/status light (Story 2.8). No optional time-limit/timeout message (Story 2.9) — only continuous elapsed-time ticking. No confirmation prompts (Story 2.10). No session tool-btn sidebar (Pause/Restart/Sound/Legend/Ball speed/Mode toggles) — shown in the locked mockup but not backed by any Story 2.4 AC. No Personal Records wiring (Epic 5) — win detection stops at marking the session solved. No fix for the pre-existing "theme toggle re-navigates with stale `state`" gap (deferred from Story 2.1 for the gallery's browse position) — it now also resets an in-progress gameplay session (position/timer) on a mid-play theme toggle; not fixed here, same already-deferred root cause.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Initial render | `Maze` mounted, ball at `entry` | Wall-bars for every set wall bit, entry circle + exit diamond at their positions, ball circle at `entry`; HUD shows Level 1, Difficulty "—", Time 00:00, Pos matching `entry` | No error |
| Arrow key, open passage | `attempt_move` returns a new `Position` | Ball redraws at the new cell; Pos chip updates | No error |
| Arrow key, wall blocks | `attempt_move` returns the same `Position` | No redraw, no chip change | No error, no exception |
| Reach the exit | New position `== maze.exit` | Win banner appears inline ("Solved in MM:SS."), session `solved=True`, Time chip and tick loop freeze | No error |
| Movement after solved | Arrow key pressed once `solved=True` | `move()` returns the session unchanged — no position/time change | No error |
| Continue clicked | Win banner showing | Banner destroyed; `solved` stays `True` | No error |
| Elapsed ticking | Screen mounted, not yet solved | Time chip updates once per second via `.after(1000, ...)` | No error |
| Screen destroyed mid-tick | A tick `.after()` job is pending | Job is cancelled on `<Destroy>`; no `TclError` from a callback touching a dead widget | No error |
| `GENERATED` maze mounted | Same as Story 2.3 | Save button still shown; Save dialog flow unchanged | No error |
| Typing in the Save dialog's name field | Arrow key pressed while the field has focus | Cursor moves locally; the global `move_*` shortcut does not also move the ball | No error |
| Gameplay breadcrumb | `state` is a `Maze` of a given `kind` | 3 segments: "Home" (clickable), "Player" (clickable, back to the gallery), "\<kind label\>" (trailing, non-clickable) | No error |

</intent-contract>

## Code Map

- `src/labyrinthes/domain/movement.py` -- new; `Direction` enum (`UP`/`DOWN`/`LEFT`/`RIGHT`, row/col deltas) + `attempt_move(grid, position, direction) -> Position`, pure, mirrors `maze_generation._open_neighbors`'s per-direction wall-bit check (up/left check the current cell's top/left bit, down/right check the neighbor's, via `Grid.cell_at`'s existing padding-row/col range)
- `src/labyrinthes/domain/duration.py` -- add `Duration.to_clock_string() -> str` ("MM:SS", total minutes uncapped — deliberately not reproducing legacy `Chrono`'s 60-minute wraparound bug)
- `src/labyrinthes/domain/__init__.py` -- export `Direction`, `attempt_move`
- `src/labyrinthes/application/player_session.py` -- new; `PlayerSession` (frozen dataclass: `maze`, `position`, `elapsed: Duration`, `solved: bool`) + `start_session(maze) -> PlayerSession`, `move(session, direction) -> PlayerSession` (no-ops once `solved`; sets `solved` on reaching `maze.exit`), `tick(session, elapsed) -> PlayerSession` (no-ops once `solved`) -- free functions, matching `maze_size_bounds.read_maze_size_bounds`'s established style, not a stateless class
- `src/labyrinthes/adapters/tkinter/player/maze_canvas.py` -- new; `MazeCanvas(tk.Canvas)` -- draws wall-bars (tag `"wall"`), entry/exit markers (tags `"entry-marker"`/`"exit-marker"`) once from a `Maze` + `theme`; `set_ball_position(position)` moves the tagged `"ball"` item via `canvas.coords(...)`, no full redraw
- `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` -- new, replacing `gameplay_placeholder.py`; `GameplayScreen(tk.Frame)` -- builds the HUD row (4 `HudChip`s), `MazeCanvas` inside a maze-frame `Frame`, registers `move_up`/`move_down`/`move_left`/`move_right` via `bind_shortcut(self, ...)`, runs the elapsed-time `.after()` tick loop (cancelled on `<Destroy>`), shows/destroys the win banner on solve/Continue, and keeps Story 2.3's Save button/`SaveMazeDialog` wiring (same `_maze`/`_on_save_clicked`/`_on_save_confirmed` shape, now scoped to its own save-zone `Frame` so saving never rebuilds the HUD/canvas/banner)
- `src/labyrinthes/adapters/tkinter/player/gameplay_placeholder.py` -- delete; superseded by `gameplay_screen.py`
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- add `Keybinding("move_up", "Move up", "Up")`, `("move_down", "Move down", "Down")`, `("move_left", "Move left", "Left")`, `("move_right", "Move right", "Right")`; fix `bind_shortcut`'s uppercase case-variant to only apply when `len(kb.key) == 1 and kb.key.isalpha()` -- unguarded, `f"<KeyPress-{kb.key.upper()}>"` on a multi-char keysym (e.g. `"UP"`) raises `TclError: bad event type or keysym` (confirmed against a live Tk instance), which would break every movement-key registration
- `src/labyrinthes/adapters/tkinter/player/save_maze_dialog.py` -- extend `_name_entry`'s existing "s"/"S" `<KeyPress>` `"break"` guard with the same guard for `Up`/`Down`/`Left`/`Right`, so typing/cursor-editing the save name doesn't leak into the now-global movement shortcuts and move the ball behind the dialog
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- swap `GameplayPlaceholder` for `GameplayScreen`; when `state is not None`, breadcrumb becomes 3 segments (`Home`, `Player` now clickable → `navigate(ScreenId.PLAYER, None)`, trailing kind-derived label: `CLASSIC`→"Classic Maze", `SAVED_RANDOM`→"Saved Random Maze", `GENERATED`→"Random Maze", `SKETCH`→"Sketch")
- `tests/domain/test_movement.py` -- new; `attempt_move` against open/blocked/border cases in every direction
- `tests/domain/test_duration.py` -- extend for `to_clock_string()` (0s, sub-minute, exact minute, >1hr uncapped)
- `tests/application/test_player_session.py` -- new; `start_session`/`move`/`tick` including the solved-freezes-further-move/tick rows
- `tests/adapters/tkinter/player/test_maze_canvas.py` -- new; wall-bar count against a known grid, marker tags/positions, `set_ball_position` moving the tagged item without touching wall/marker items
- `tests/adapters/tkinter/player/test_gameplay_screen.py` -- new, replacing `test_gameplay_placeholder.py`; ports its Save-flow tests onto `GameplayScreen`, adds the I/O matrix's rendering/movement/win/tick-cancellation rows
- `tests/adapters/tkinter/player/test_player_screen.py` -- update `GameplayPlaceholder`→`GameplayScreen` references; replace `test_breadcrumb_stays_two_segments_in_the_gameplay_placeholder_view` with a 3-segment assertion per kind
- `tests/adapters/tkinter/common/test_keybindings.py` -- add movement-key entries to the uniqueness/lookup tests; add a regression test that `bind_shortcut` does not attempt (and does not raise on) a multi-char keysym's uppercase variant
- `tests/adapters/tkinter/player/test_save_maze_dialog.py` -- add arrow-key guard tests mirroring the existing "s"/"S" ones

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/domain/movement.py` -- add `Direction`/`attempt_move` -- pure movement mechanics domain functions
- [x] `tests/domain/test_movement.py` -- unit-test `attempt_move`
- [x] `src/labyrinthes/domain/duration.py` -- add `to_clock_string()` -- shared MM:SS formatting for the Time chip and win banner
- [x] `tests/domain/test_duration.py` -- extend for `to_clock_string()`
- [x] `src/labyrinthes/domain/__init__.py` -- export `Direction`, `attempt_move`
- [x] `src/labyrinthes/application/player_session.py` -- add `PlayerSession`/`start_session`/`move`/`tick` -- pure session orchestration
- [x] `tests/application/test_player_session.py` -- unit-test session orchestration
- [x] `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- add movement keybindings, fix `bind_shortcut`'s case-variant guard
- [x] `tests/adapters/tkinter/common/test_keybindings.py` -- extend for movement keys + the case-variant regression
- [x] `src/labyrinthes/adapters/tkinter/player/maze_canvas.py` -- add `MazeCanvas` -- wall/marker/ball rendering
- [x] `tests/adapters/tkinter/player/test_maze_canvas.py` -- unit-test rendering
- [x] `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` -- add `GameplayScreen`, delete `gameplay_placeholder.py` -- HUD, canvas, movement, timer, win banner, preserved Save flow
- [x] `tests/adapters/tkinter/player/test_gameplay_screen.py` -- unit-test `GameplayScreen`, replacing `test_gameplay_placeholder.py`
- [x] `src/labyrinthes/adapters/tkinter/player/save_maze_dialog.py` -- extend the name entry's key guard to arrow keys
- [x] `tests/adapters/tkinter/player/test_save_maze_dialog.py` -- test the extended guard
- [x] `src/labyrinthes/adapters/tkinter/player/screen.py` -- swap in `GameplayScreen`, add the dynamic 3-segment breadcrumb
- [x] `tests/adapters/tkinter/player/test_player_screen.py` -- update for the rename and the 3-segment breadcrumb

**Acceptance Criteria:**
- Given a `Maze` mounted into `GameplayScreen`, when it renders, then walls draw as solid bars with broken walls as structural gaps (never dashed), entry/exit render with distinct glyphs, and the ball starts at rest on the entry cell
- Given the HUD, when the screen is active, then Level/Difficulty/Time/Pos chips are shown, with Time ticking once per second and Pos updating on every successful move
- Given arrow-key input, when pressed, then the ball moves exactly one cell per press, respecting wall collisions (blocked presses are no-ops)
- Given the ball reaches the exit cell, when that happens, then an inline, non-blocking win banner appears around the maze-frame with a Continue action, and the session is marked solved
- Given a `GENERATED` maze mounted into `GameplayScreen`, when rendered, then the Story 2.3 Save button/dialog flow behaves exactly as before

## Spec Change Log

## Review Triage Log

### 2026-08-10 — Review pass

- intent_gap: 0
- bad_spec: 0
- patch: 5 (high 1, medium 1, low 3)
- defer: 2
- reject: 4
- addressed_findings:
  - `[high]` `[patch]` `SaveMazeDialog._name_entry`'s new `<KeyPress-Up/Down/Left/Right>` `"break"` guards (added to prevent Story 2.4's global movement shortcuts from firing while editing the save name) also disabled the field's own default cursor-navigation behavior — confirmed live: an instance-level `"break"` stops Tk's bindtag scan before the `Entry`'s *class* binding (which performs cursor movement/self-insert) ever runs, so arrow keys stopped moving the text cursor entirely, not just the shortcut. Fixed by removing those four guards and instead guarding centrally in `GameplayScreen._on_move`, which no-ops when `isinstance(self.focus_get(), tk.Entry)` — `focus_get()` is confirmed application-wide (not scoped to this screen's own toplevel), so this correctly covers `SaveMazeDialog`'s separate `Toplevel` too, while leaving the `Entry`'s own key handling completely undisturbed.
  - `[medium]` `[patch]` `MazeCanvas` drew the ball at the exact same radius as the entry/exit markers, so the ball (opaque, drawn last/on top) fully occluded the entry marker at initial render and would fully occlude the exit marker at the instant of winning — defeating the "shape *and* color, never color alone" (NFR6) requirement at exactly the two moments a player most needs it, and the one existing test asserting `ball_coords == entry_coords` locked the overlap in as expected rather than catching it. Fixed by giving the ball its own, smaller `_BALL_SCALE` (0.42 vs. the markers' 0.6), so a marker's shape remains visible as a ring around the ball; updated the affected test plus `test_gameplay_screen.py`'s equivalent assertion to check same-center/smaller-bounding-box instead of coordinate equality.
  - `[low]` `[patch]` `_on_solved()` rendered the win banner from `self._session.elapsed`, which is only refreshed once per second by `_on_tick()` — a win could display up to ~1s less than the true elapsed time. Fixed by refreshing `self._session.elapsed` from `time.monotonic()` directly in `_on_move()` the moment `solved` newly flips `True` (via `dataclasses.replace`, since `player_session.tick()`'s own no-op-once-solved guard would otherwise defeat a straight call), and syncing the Time chip to the same refreshed value before showing the banner so the two never disagree.
  - `[low]` `[patch]` `_on_save_confirmed` updated `self._maze` to the repository's returned (now `SAVED_RANDOM`, freshly-id'd) `Maze` but left `self._session.maze` pointing at the original `GENERATED` object — no observable effect today (grid/entry/exit are unchanged by the kind/id transition), but a latent trap for any future code reading `session.maze.kind`/`id`. Fixed by also replacing `self._session.maze` in the same method; added a regression test.
  - `[low]` `[patch]` The ball/marker radius formula (`self._cell_size * scale / 2`) was duplicated verbatim across four call sites in `maze_canvas.py`. Fixed by extracting a shared `_radius(scale)` helper, used by all four (and now parameterized by the new `_BALL_SCALE`/`_MARKER_SCALE` split above).

Deferred (see `deferred-work.md`): `SaveMazeDialog._name_entry`'s pre-existing "s"/"S" `"break"` guard (Story 2.3) has the identical class-binding-suppression defect confirmed above — it has silently prevented typing the letter "s"/"S" into the save-name field at all since Story 2.3, never caught because that guard's own tests only used `.insert()`, never a real keystroke; not touched here to keep this story's diff scoped to its own new shortcuts. `Maze.__post_init__` doesn't validate `entry`/`exit` against the playable `[0, width) x [0, height)` region (only that `Grid.cell_at()` succeeds, which also accepts the closed-border padding row/column) or forbid `entry == exit` — a malformed classic-maze CSV with either property can crash `attempt_move`, render markers/the ball off-canvas, or (for `entry == exit`) delay win detection by one press and then falsely trigger it on a blocked move; inert before this story, newly reachable now that `PlayerSession`/`MazeCanvas` actually compute against `entry`/`exit`, but the fix belongs in `Maze.__post_init__` (Story 1.1/1.4 territory), not this story's rendering/movement code.

Rejected as noise or as already-deliberate: `screen._KIND_LABELS`' hand-maintained dict (no exhaustiveness check against `MazeKind`) flagged as a future `KeyError` risk if the enum gains a member — matches `ClassicMazeGallery._position_text`'s identical non-exhaustive `if`/`else` pattern, already reviewed and explicitly rejected as noise in Story 2.3's own review ("unreachable with the current code, not a latent bug"); same reasoning applies here. Movement/keybinding tests invoking `_on_move()`/checking `bind_all()` registration directly, rather than dispatching synthetic `<KeyPress>` events, flagged as unable to catch the exact regression above by construction — true, but this is the codebase's own long-established, explicitly-documented testing convention (`bind_shortcut`'s docstring: "mirrors this codebase's `_on_click()` convention for widgets whose real X11 events can't be reliably synthesized under a withdrawn `tk_root`"), not a defect introduced by this story. The win banner's "Continue" `PillButton` having no *global* `kbd-tag` shortcut flagged as an accessibility inconsistency — already keyboard-operable via standard Tab-to-focus plus `PillButton`'s existing `<Return>`/`<space>` bindings, satisfying the NFR6 keyboard-operable floor; not every action in this codebase carries a global shortcut (e.g. Cancel buttons elsewhere don't either). `_build_save_zone()`'s `hasattr`/`del` cleanup pattern flagged as "silently tolerating" being called before `_save_button` was ever set — by the finding's own admission this is harmless (mirrors Story 2.3's original `_build()` precedent exactly), not an actual failure scenario.

### 2026-08-10 — Follow-up review pass

- intent_gap: 0
- bad_spec: 0
- patch: 5 (high 0, medium 2, low 3)
- defer: 1
- reject: 4
- addressed_findings:
  - `[medium]` `[patch]` `GameplayScreen._on_move`'s focus guard checked `isinstance(self.focus_get(), tk.Entry)`, which only covers `SaveMazeDialog`'s name field — tabbing from there to the dialog's own Save/Cancel `PillButton`s (also `takefocus=True`, not an `Entry`) escaped the guard entirely, letting arrow keys move the ball behind the still-open dialog (confirmed live). Fixed by guarding on *toplevel* instead (`focused.winfo_toplevel() is not self.winfo_toplevel()`), which covers every widget any current or future dialog might contain, not just `Entry`; added a regression test using the dialog's Save button.
  - `[medium]` `[patch]` Saving a `GENERATED` maze in place transitions `screen._maze.kind`/`session.maze.kind` to `SAVED_RANDOM`, but the 3-segment breadcrumb built once in `screen.py`'s `mount()` was never told — it kept showing "Random Maze" instead of "Saved Random Maze" for the rest of the session (confirmed live end-to-end). Fixed by adding `Breadcrumb.set_label()`/`TopBar.set_breadcrumb_label()` and a new `GameplayScreen(..., on_kind_changed=...)` callback, invoked from `_on_save_confirmed`; `screen.py` wires it to update the trailing breadcrumb segment. Added unit tests for `Breadcrumb.set_label`/`TopBar.set_breadcrumb_label` plus an end-to-end `mount()` → save → breadcrumb-updates test.
  - `[low]` `[patch]` The win banner's "Continue" `PillButton` was `primary=True` at the same time a `GENERATED` maze's Save pill (still showing underneath, winning doesn't hide it) is also `primary=True` — two simultaneous primary pills, violating `PillButton`'s own documented "at most one `primary` pill per screen" rule. Fixed by setting Continue's `primary=False`; added a regression test.
  - `[low]` `[patch]` `tests/domain/test_movement.py`'s malformed-maze defensive-guard test only parametrized `UP`/`LEFT` (which check `position`'s own cell), never `DOWN`/`RIGHT` (which check the *neighbor* cell) — the same bounds-check code path, left untested for two of its four call sites. Fixed by using a fully wall-less 1x1 grid (padding cells included) and parametrizing all four directions.
  - `[low]` `[patch]` `_on_solved()`/`_on_destroy()` duplicated the identical three-line "cancel `self._tick_job` if pending" block. Fixed by extracting a shared `_cancel_tick_job()` helper, used by both.

Deferred (see `deferred-work.md`): `MazeCanvas._cell_size` divides by `width`/`height` with no zero-guard — a domain-legal degenerate `Grid` (playable `width == 0` or `height == 0`, permitted by `Grid.__post_init__` alone; only the separate `Grid.filled()` factory forbids it) crashes construction with a raw `ZeroDivisionError`. Same root-cause class as this story's already-deferred `Maze.__post_init__` entry/exit validation gap (a malformed classic-maze CSV reaching newly-reachable rendering/movement code), but a distinct symptom; not fixed here to keep this pass's diff scoped to its own patches rather than opening a new `Maze`/`Grid` validation surface.

Rejected as noise or as already-covered: a `classic_gallery.py` docstring line referencing "Story 2.3's `GameplayPlaceholder`" flagged as a stale reference to a deleted class — it is accurate as written, a historical note about what that class was called in that story (the same pattern `gameplay_screen.py`'s own module docstring uses), not stale or misleading. `player_session.move()` marking `solved=True` whenever `entry == maze.exit` (even via a blocked move) flagged as a bug — already logged verbatim in this story's own `deferred-work.md` entry ("that first move -- even one blocked by a wall... would incorrectly mark the session solved"), not new information. Toggling the theme mid-`GameplayScreen` session silently resetting position/elapsed (via `start_session(maze)` unconditionally re-running on re-mount) flagged as a bug — explicitly acknowledged and declared out of scope in this story's own `<intent-contract>` Boundaries & Constraints ("it now also resets an in-progress gameplay session... not fixed here, same already-deferred root cause"), not new information.

## Design Notes

**Canvas sizing is this story's own decision (no locked token exists for it).** `MazeCanvas` computes `cell_size = clamp(min(480 // width, 480 // height), 16, 40)` in pixels — legible for both a small classic maze and a 50x35 random one, without a token in `tokens.py` (which itself notes `RADII` is "recorded here as data for later canvas-drawn components" but stops short of pixel/cell sizing).

**The Pos chip reads `f"({position.row}, {position.col})"`**, matching `test_hud_chip.py`'s own existing illustrative example (`HudChip(tk_root, "pos", "(0, 0)", ...)`) rather than inventing a new format.

**The breadcrumb's trailing label is kind-derived, not index-derived.** The locked mockup shows "Classic Maze 4" (with the gallery's own position number), but `navigate(ScreenId.PLAYER, maze)` only ever carries a bare `Maze` — no name/ordinal — and `state is not None` mounting must never read `maze_repository` (existing, still-enforced test). Threading the gallery's index through `navigate()`'s shared `Maze | None` state channel would be a cross-cutting change to a signature Home/Builder share too; out of this "foundation" story's scope. A kind-derived label ("Classic Maze", "Saved Random Maze", "Random Maze") is the two-segment-when-browsing / three-segment-when-playing shape the Technical Decisions call for, without that change.

**Continue only dismisses the banner.** Once `solved=True`, `player_session.move`/`tick` are no-ops (frozen elapsed, frozen position) — this keeps "the run is marked solved" unambiguous and avoids inventing post-win exploration behavior no AC asks for.

## Verification

**Commands:**
- `ruff check .` -- expected: no new lint violations
- `ruff format --check .` -- expected: no formatting diffs
- `pytest` -- expected: full suite green, including all new/renamed test files

## Auto Run Result

**Summary:** This session ran an unattended follow-up review pass on Story 2.4's already-implemented `GameplayScreen` (rendering, HUD, arrow-key movement, win detection, preserved Save flow). Two independent review subagents (adversarial + edge-case) audited the full diff against baseline `d891965`; 5 real findings were patched directly, 1 was deferred, and 4 were rejected as noise or already-known/out-of-scope.

**Files changed this pass** (on top of the prior implementation commit):
- `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` -- broadened the movement focus-guard from `isinstance(..., tk.Entry)` to a toplevel check (fixes escaping the guard via Tab-focus on a dialog button); added `on_kind_changed` callback fired after a save; made the win banner's Continue pill `primary=False`; extracted `_cancel_tick_job()` to de-duplicate tick-cancellation logic
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- wires `on_kind_changed` into `GameplayScreen` so the breadcrumb's trailing kind label updates after a save
- `src/labyrinthes/adapters/tkinter/common/breadcrumb.py` -- new `Breadcrumb.set_label(index, label)`
- `src/labyrinthes/adapters/tkinter/common/top_bar.py` -- new `TopBar.set_breadcrumb_label(index, label)`, delegating to the breadcrumb when one exists
- `tests/domain/test_movement.py` -- extended the malformed-maze defensive-guard test to cover all four directions (was UP/LEFT only)
- `tests/adapters/tkinter/player/test_gameplay_screen.py` -- regression tests for the broadened focus guard, the `on_kind_changed` callback, and Continue's non-primary styling
- `tests/adapters/tkinter/player/test_player_screen.py` -- end-to-end test: `mount()` a `GENERATED` maze, save it, assert the breadcrumb's trailing label updates from "Random Maze" to "Saved Random Maze"
- `tests/adapters/tkinter/common/test_breadcrumb.py`, `tests/adapters/tkinter/common/test_top_bar.py` -- unit tests for the two new methods
- `_bmad-output/implementation-artifacts/deferred-work.md` -- new deferred entry (see below)

**Review findings breakdown:**
- Patched (5, medium 2 / low 3): movement focus-guard escaping via a non-`Entry` dialog widget (medium); stale breadcrumb kind label surviving a save (medium); two simultaneous `primary=True` pills (Save + Continue) after winning a `GENERATED` maze (low); untested `DOWN`/`RIGHT` branches of `attempt_move`'s malformed-maze defensive guard (low); duplicated tick-cancellation logic (low).
- Deferred (1): `MazeCanvas._cell_size` has no zero-guard, so a domain-legal degenerate `Grid` (width/height 0, reachable only via a malformed classic-maze CSV bypassing `Grid.filled`'s own guard) crashes with `ZeroDivisionError` -- logged in `deferred-work.md`, same root-cause class as this story's already-deferred `Maze` entry/exit validation gap.
- Rejected (4): a `classic_gallery.py` docstring's historical reference to "Story 2.3's `GameplayPlaceholder`" (accurate, not stale); `entry == maze.exit` auto-solving on the first move (already logged verbatim in this story's own `deferred-work.md` entry from the first review pass); mid-session theme toggle resetting position/elapsed (explicitly declared out of scope in the story's own `<intent-contract>`); a "focus-guard fix narrower than the hazard class" observation subsumed by the toplevel-guard patch above.

**Verification performed:** `ruff check .` -- clean. `ruff format --check .` -- clean (one file auto-reformatted, then re-verified clean). `pytest` -- 490 passed (up from 480 before this pass's new tests), 0 failed.

**Residual risks:** The deferred `ZeroDivisionError` gap requires a hand-malformed classic-maze CSV to reach in practice -- no code path in this app currently writes such a file. The new `Breadcrumb.set_label`/`TopBar.set_breadcrumb_label` methods are small, mechanical additions to already-tested shared widgets; both are covered by dedicated unit tests plus one end-to-end `mount()`-level test. No behavior, security, or persisted-data-format changes were made this pass.

**Follow-up review recommendation:** Not recommended (`followup_review_recommended: false`). All five patches this pass were small, mechanical, fully unit- and/or end-to-end-tested, and localized to the files listed above; none touches persistence, security, or the domain layer's public contracts.

