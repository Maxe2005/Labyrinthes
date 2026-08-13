---
title: 'Story 2.5: Movement modes — Smooth vs Discrete, configurable speed'
type: 'feature'
created: '2026-08-13'
status: 'ready-for-dev'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-2-context.md']
baseline_revision: '0aecc4d'
---

<intent-contract>

## Intent

**Problem:** Story 2.4's `GameplayScreen` only supports a single movement behavior: each arrow-key press snaps the ball exactly one cell, instantly (`PlayerSession.move` → `attempt_move`, rendered by `MazeCanvas.set_ball_position`). A player cannot yet choose how the ball moves, even though the product requires two configurable modes (FR-15): **Smooth** (continuous motion, redirectable mid-move without stopping at a cell boundary) and **Discrete** (one cell per press), driven by **one configurable speed** whose change is reflected identically in both modes' tick/animation rate.

**Approach:** Introduce two pure domain types -- `MovementMode` (`DISCRETE`/`SMOOTH`) and `MovementSpeed` (`SLOW`/`NORMAL`/`FAST` with `cell_crossing_duration()`) -- and rework `application/player_session.py` from a keypress-snap model into a leg/animation model: `move()` is replaced by `request_move()` (which starts a cell-crossing "leg", or banks a redirect while Smooth-moving) plus `advance_step()`, a pure fixed-duration animation tick (leg-target commit, win-check, Smooth's redirect-or-continue-straight-or-stop resolution with legacy "banked turn" retry semantics), `set_mode()` and `set_speed()`. Both modes now run through the **same** tick/animation engine -- Discrete stays one-cell-per-press (leg length exactly one cell), Smooth adds mid-leg redirects -- so the shared speed setting has exactly one place to take effect. `GameplayScreen` reads the `game`-scoped mode/speed settings at mount, renders them in a new "Movement" tool-btn sidebar group (mode toggle bound to a new `m` shortcut; a "Ball speed" button cycling Slow→Normal→Fast), and drives the animation with a `.after()` loop rescheduled at `cell_crossing_duration(speed).milliseconds // STEPS_PER_CELL` ms each step (recomputed per reschedule so a live speed change takes effect immediately). Win detection moves from the keypress handler into the animation-tick's leg-completion branch, since both modes now resolve a win at leg completion, not on keypress.

## Boundaries & Constraints

**Always:** `adapters/tkinter/player/` never imports `adapters/storage/` directly (AD-9). Movement mechanics and session orchestration stay pure: `domain/` (`MovementMode`, `MovementSpeed`, `Direction`, `attempt_move`) and `application/player_session.py` are pure functions over immutable (frozen) state with **no Tk and no wall-clock reads** -- `time.monotonic()` stays entirely in `adapters/tkinter/player/gameplay_screen.py`. `advance_step()` is a pure, fixed-duration tick: it never reads elapsed time, it simply advances the in-flight leg by one of `STEPS_PER_CELL` uniform sub-steps. Settings access goes through the `SettingsRepository` port from `application/` -- new `read_movement_mode`/`read_movement_speed`/`write_movement_mode`/`write_movement_speed` in a new `application/movement_settings.py` mirroring `maze_size_bounds.read_maze_size_bounds`'s per-field settings-fallback pattern, all `game`-scoped (`SettingsScope.GAME`), defaulting to `SMOOTH`/`NORMAL` (the legacy `Parametres_defaut.csv` defaults: `type deplacement initial = Lisse`, `decoupe du deplacement = 5`, `vitesse deplacement = 45`). New keys `MOVEMENT_MODE`/`MOVEMENT_SPEED` are declared in `application/settings_keys.py` -- never hardcoded strings elsewhere. The new `m` shortcut registers in the canonical `KEYBINDINGS` table (Story 1.10) like every other shortcut -- no ad hoc `bind_all()` outside `bind_shortcut()`. The existing toplevel-based movement focus guard (Story 2.4's review fix) stays: a movement or mode-toggle input must no-op while focus is in another toplevel (e.g. the `SaveMazeDialog`), and the mode toggle's `m` shortcut needs the same guard. A blocked direction is a silent no-op -- no error, no state change. `GameplayScreen`'s `.after()` animation-tick job is cancelled on `<Destroy>` and on solve so a pending tick never fires against a torn-down widget or a solved session. Both the movement shortcuts and the mode-toggle shortcut must be unregistered on `<Destroy>` (via `bind_shortcut`'s own cleanup). Win banner behavior is unchanged in look/feel ("Solved in MM:SS." + Continue, `primary=False`); only its *trigger* moves from the keypress path to leg completion.

**Block If:** Nothing here requires human input -- the speed-value mapping, the discrete-animation interpretation of Story 2.4's "one cell per press", the sidebar's exact placement, and the mid-leg mode-switch semantics are all resolvable design decisions (see Design Notes), not blocking gaps.

**Never:** No Pause/Restart/Sound/Legend toggles (Story 2.4 deferred the whole session sidebar; this story only adds the "Movement" group -- the other mockup sidebar tools stay out until their own stories). No Levels/Difficulty visibility rules (2.6/2.7), no HARD-mode fog/status-light (2.8), no time limit/timeout (2.9), no confirmation prompts (2.10), no Personal Records (Epic 5). No new `game`-scope settings beyond `MOVEMENT_MODE`/`MOVEMENT_SPEED`. No change to `tick()`'s elapsed-time semantics (it stays a no-op once solved). No change to `MazeCanvas`'s wall/marker rendering or to `set_ball_position`'s contract. No change to `composition_root.py` (it already threads `settings_repository` into `mount_player`). The speed is **not** user-configurable as a raw ms value and the sub-step count is **not** user-configurable (legacy had two knobs, `decoupe du deplacement` + `vitesse deplacement`; the epic context explicitly requires *one* speed setting -- see Design Notes).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Initial render | `Maze` mounted, settings resolve to `SMOOTH`/`NORMAL` | Ball at rest on entry; sidebar "Movement" group shows the mode toggle in its active (Smooth) state and the Ball-speed button labeled `Normal`; HUD/Pos chips as in Story 2.4 | No error; missing/corrupt settings fall back to defaults |
| Arrow key, Discrete, ball at rest | `request_move(UP/RIGHT/...)` with an open passage | A one-cell leg starts; the ball animates across exactly one cell over `cell_crossing_duration(speed)` ms (`STEPS_PER_CELL` uniform sub-steps); Pos chip updates at leg completion | No error |
| Arrow key, Discrete, wall blocks | `request_move` against a wall | Silent no-op: no leg starts, no state change | No error |
| Arrow key, Discrete, mid-leg | A second press while `step < STEPS_PER_CELL` | Silently ignored (Discrete never banks a direction -- one press = one cell, no queuing) | No error |
| Arrow key, Smooth, ball at rest | `request_move(UP)` with an open passage | A continuous leg starts; the ball animates without stopping at the first cell boundary -- the leg continues straight past cell one unless redirected | No error |
| Arrow key, Smooth, mid-leg | A different direction pressed while moving | The direction is banked as `pending_direction`; at the next cell boundary the ball turns into it if open (redirect mid-move, no stop), otherwise it continues straight, and the banked turn is *retried* at the following boundary (legacy un-cleared `next_dir` semantics) | No error |
| Arrow key, Smooth, wall blocks current heading | `request_move` (or boundary resolution) finds the heading blocked | The ball stops at the last open cell; the leg ends (no error, no overshoot) | No error |
| Speed changed mid-session | `set_speed`/sidebar cycles Slow→Normal→Fast | `session.speed` updates; the animation reschedule recomputes the per-step delay from the new `cell_crossing_duration(speed)`, so the change applies to both modes' next ticks immediately; persisted `game`-scoped | No error |
| Mode switched mid-session | `set_mode` toggles SMOOTH↔DISCRETE while a leg is in flight | The in-flight leg completes under the engine that started it; the *next* input applies the new mode's behavior immediately (AC4) | No error |
| Reach the exit | A leg completes with `leg_target == maze.exit` | Win banner appears (leg-completion branch); session `solved=True`; Time chip/pos freeze; animation and elapsed tick loops cancelled | No error |
| Reaching the exit mid-leg (Smooth, crossing onto exit cell) | `leg_target == maze.exit` at commit | Solve detected at leg completion, not at the earlier keypress -- the ball visibly reaches the exit cell before the banner shows | No error |
| Movement/mode input while focus is in another toplevel | Arrow key or `m` pressed while `SaveMazeDialog`'s field/button has focus | No-op -- the ball doesn't move and the mode doesn't toggle behind the dialog | No error |
| Screen destroyed mid-animation | A `.after()` animation-tick job pending | Job cancelled on `<Destroy>`; no `TclError` from a callback touching a dead widget; `bind_all()` shortcuts unregistered | No error |
| Solve then further input | Arrow key after `solved=True` | `request_move` returns the session unchanged -- no position/time change (preserves Story 2.4's post-win no-op) | No error |
| `GENERATED` maze mounted | Same as Story 2.3/2.4 | Save button/dialog flow unchanged; sidebar coexists with the save zone | No error |
| Settings corrupt/unset at mount | `MOVEMENT_MODE`/`MOVEMENT_SPEED` missing, non-enum, or invalid stored value | Each setting falls back independently to `SMOOTH`/`NORMAL` (per-field, mirroring `read_maze_size_bounds`) | No exception propagates to the UI |

</intent-contract>

## Code Map

- `src/labyrinthes/domain/movement_mode.py` -- **NEW**; `MovementMode(enum.Enum)` with `DISCRETE`/`SMOOTH` members (values `"discrete"`/`"smooth"`, matching the `SettingValue` string convention for stored settings). Pure; no Tk. Mirrors `domain/movement.py`'s minimal enum style.
- `src/labyrinthes/domain/movement_speed.py` -- **NEW**; `MovementSpeed(enum.Enum)` with `SLOW`/`NORMAL`/`FAST` plus a pure `cell_crossing_duration(speed: MovementSpeed) -> Duration` mapping: `NORMAL` = **225ms** (deliberately matches the legacy default `vitesse deplacement(45) x decoupe du deplacement(5)` = 45ms per sub-step x 5 sub-steps per cell). `SLOW`/`FAST` are this story's own design decision (e.g. 375ms / 150ms -- see Design Notes) since the legacy had no such tiers; whatever values are chosen must keep `Duration` non-negative and be listed here as the single source of truth. Pure; no Tk.
- `src/labyrinthes/domain/__init__.py` -- **UPDATE**; export `MovementMode`, `MovementSpeed`, `cell_crossing_duration`.
- `src/labyrinthes/application/player_session.py` -- **UPDATE**; rework from keypress-snap to leg/animation model (kept as free functions over the frozen `PlayerSession` dataclass, matching Story 2.4's established `maze_size_bounds.read_maze_size_bounds` style):
  - `PlayerSession` gains: `mode: MovementMode`, `speed: MovementSpeed`, `moving_direction: Direction | None` (the heading of the in-flight leg; `None` when at rest), `leg_target: Position | None` (the cell the in-flight leg commits to; `None` when at rest), `step: int` (completed sub-steps of the in-flight leg, `0..STEPS_PER_CELL`), `pending_direction: Direction | None` (Smooth's banked redirect). New module constant `STEPS_PER_CELL = 5` (mirrors legacy `decoupe_dep` default; deliberately not user-configurable -- see Design Notes).
  - `start_session(maze)` -- unchanged signature; a fresh session is at rest (`moving_direction`/`leg_target`/`pending_direction` = `None`, `step = 0`) with default `mode=SMOOTH`, `speed=NORMAL`. The screen applies the *settings-loaded* mode/speed by chaining `set_mode`/`set_speed` on the result -- `start_session` itself doesn't read settings (it stays pure with plain defaults).
  - `move(session, direction)` -- **REPLACED by** `request_move(session, direction)`: no-op once solved. If at rest: compute `leg_target = attempt_move(grid, position, direction)`; if it differs from `position` (open passage), start a leg (`moving_direction=direction`, `leg_target=...`, `step=0`) -- Discrete or Smooth alike, since Discrete's leg is exactly one cell. If already mid-leg: Discrete silently ignores the press; Smooth banks `pending_direction = direction` (no validation now -- validation happens at the boundary, so a banked turn toward a wall is retried rather than dropped; see `advance_step`).
  - `advance_step(session) -> PlayerSession` -- **NEW**, pure, fixed-duration tick: no-op once solved and no-op when at rest. Increments `step`. When `step == STEPS_PER_CELL` (leg complete): commit `position = leg_target`; check win (`position == maze.exit` -> `solved=True`); for Smooth only, resolve the next heading at the boundary: if `pending_direction` leads to an open passage (via `attempt_move` from the just-committed position) start the next leg in it and clear `pending_direction`; elif the current `moving_direction` is still open, continue straight (start the next leg in the same direction); else stop (leg ends, `moving_direction`/`leg_target`/`pending_direction` = `None`, `step=0`). If `pending_direction` was blocked, it is **not cleared** -- retried at the following boundary (legacy's un-cleared `next_dir` "banked turn" semantics, `Labyrinthes_copy.py` lines 1076-1084). When the leg is not yet complete, return the session with the updated `step` only. `pending_direction` never applies in Discrete (Discrete cannot be mid-leg when a new input arrives, and it banks nothing).
  - `set_mode(session, mode) -> PlayerSession` and `set_speed(session, speed) -> PlayerSession` -- **NEW**, pure: replace the respective field. Mid-leg behavior is the *engine's* choice, not these functions': an in-flight leg keeps its `moving_direction`/`leg_target`; the next `request_move`/`advance_step` behaves per the new `mode`/`speed`.
  - `tick(session, elapsed)` -- unchanged (still a no-op once solved).
  - Update `__all__` (`move` -> `request_move`; add `advance_step`, `set_mode`, `set_speed`).
- `src/labyrinthes/application/movement_settings.py` -- **NEW**; `read_movement_mode(settings) -> MovementMode`, `read_movement_speed(settings) -> MovementSpeed`, `write_movement_mode(settings, mode)`, `write_movement_speed(settings, speed)` -- `game`-scoped (`SettingsScope.GAME`), per-field fallback to `SMOOTH`/`NORMAL` on `SettingNotFoundError`/`SettingCorruptError`/`ValueError`/`TypeError` and on any stored value that isn't a valid member name, mirroring `maze_size_bounds._read_bound`'s per-field fallback pattern (never raises; never writes on read). `write_*` calls `settings.set(SettingsScope.GAME, key, member.value)`.
- `src/labyrinthes/application/settings_keys.py` -- **UPDATE**; add `MOVEMENT_MODE = "movement_mode"` and `MOVEMENT_SPEED = "movement_speed"` (docstring updated: this module now also declares `game`-scope keys, not only `shared`-scope).
- `src/labyrinthes/adapters/tkinter/player/maze_canvas.py` -- **UPDATE**; add `set_ball_offset(position: Position, row_delta: float, col_delta: float)` for fractional in-flight rendering (repositions the tagged `"ball"` item to a point interpolated `row_delta`/`col_delta` fractions of a cell from `position`'s center, in units of `self._cell_size`); `set_ball_position(position)` becomes a thin wrapper calling `set_ball_offset(position, 0, 0)`. No change to wall/marker rendering or `_radius`/`_cell_size` helpers.
- `src/labyrinthes/adapters/tkinter/common/tool_btn.py` -- **UPDATE**; add `ToolButton.set_text(text: str)` replacing the label text in place (mirrors `PillButton.set_text`, `pill_btn.py` line 68) -- needed for the Ball-speed button's dynamic label (`Slow`/`Normal`/`Fast`).
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- **UPDATE**; add `Keybinding("toggle_movement_mode", "Toggle movement mode", "m")` to `KEYBINDINGS` (no key collision: `m` is unused). `bind_shortcut` needs no change (`"m"` is a single alpha keysym).
- `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` -- **UPDATE**; the heart of the story:
  - `__init__` gains a required keyword-only `settings_repository: SettingsRepository` (breaking change -- the 31 `GameplayScreen(...)` call sites in `tests/adapters/tkinter/player/test_gameplay_screen.py` must all add `settings_repository=fake_settings_repository`; the `fake_settings_repository` fixture already exists in `tests/adapters/tkinter/player/conftest.py` lines 127-130).
  - At mount, read `read_movement_mode(settings_repository)`/`read_movement_speed(settings_repository)` and apply them to the session via `set_mode`/`set_speed`; read them again at each start of a new `GameplayScreen` construction (this screen is rebuilt on re-navigate, so settings loaded at mount are fresh).
  - Add a left-hand sidebar `Frame` with a "Movement" `ToolButtonGroup`: (1) a boolean-toggle `ToolButton` labelled `Smooth`, active-state reflecting the *current* mode (active when `SMOOTH`), bound to the new `toggle_movement_mode` shortcut (its `kbd-tag` shows `M`) -- clicking it toggles the mode; (2) a `ToolButton` labelled with the current speed (`Slow`/`Normal`/`Fast`), no global keyboard shortcut (see Design Notes), whose click cycles `SLOW -> NORMAL -> FAST -> SLOW` and updates its label via the new `ToolButton.set_text`. Both persist their change immediately (`write_movement_mode`/`write_movement_speed`) and apply it to the session (`set_mode`/`set_speed`). The toggle click handler and the `m` shortcut share the same toplevel focus guard as `_on_move` (extract the guard into a small helper rather than duplicating it).
  - `_on_move(direction)` -- now calls `session_request_move`; if a leg *started* (session.moving_direction changed from `None` to a direction), schedule the animation loop: `self._animation_job = self.after(per_step_ms, self._on_animation_tick)` where `per_step_ms = cell_crossing_duration(session.speed).milliseconds // STEPS_PER_CELL` -- recomputed fresh inside `_on_animation_tick` on every reschedule so a live speed change takes effect immediately. (Reuse/extend the existing `_cancel_tick_job` pattern -- both the elapsed-time tick and the animation tick need cancellation on `<Destroy>`/solve.)
  - `_on_animation_tick()` -- NEW: `self._session = session_advance_step(self._session)`; render the fractional position via `self._maze_canvas.set_ball_offset(position, row_delta, col_delta)` where the deltas are the in-flight fraction `(step / STEPS_PER_CELL)` of the leg's `moving_direction`; update the Pos chip only on leg completion (position changed); on `solved` (win detected at leg completion) refresh elapsed from `time.monotonic()`, sync the Time chip, cancel both tick jobs, and `_show_win_banner()`; otherwise reschedule `self.after(per_step_ms, self._on_animation_tick)`.
  - Win-trigger logic moves out of `_on_move` into `_on_animation_tick`'s leg-completion branch (see Design Notes for the deliberate reinterpretation of "as established in Story 2.4").
  - `_on_move`'s existing wall-clock elapsed refresh on solve (`_on_solved`, Story 2.4's review patch) is preserved but now fires from the animation-tick path.
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- **UPDATE**; pass `settings_repository=settings_repository` through to the new `GameplayScreen` kwarg (mirrors the existing `maze_repository` plumbing at `screen.py` lines 128-139). `composition_root.py` needs **no change** -- it already threads `settings_repository` into `mount_player` (`composition_root.py` lines 131-142).
- `tests/domain/test_movement_mode.py` -- **NEW**; enum member values, exhaustive iteration.
- `tests/domain/test_movement_speed.py` -- **NEW**; `cell_crossing_duration` mapping (incl. NORMAL == 225ms as the legacy-default invariant, non-negative durations, coverage of every member).
- `tests/application/test_player_session.py` -- **UPDATE**; port existing `move` tests onto `request_move`/`advance_step`; add Discrete rows (one-cell leg, blocked press no-op, mid-leg press ignored, win at leg completion, post-win no-op), Smooth rows (continuous straight legs, redirect at boundary, blocked-redirect-then-straight, banked-turn retry at the following boundary, stop at wall), `set_mode`/`set_speed` (incl. mid-leg semantics), `start_session` defaults.
- `tests/application/test_movement_settings.py` -- **NEW**; mirror `test_maze_size_bounds.py`'s per-field-fallback coverage: unset, corrupt, non-enum, and valid stored values for both keys; write round-trip; `game` scope used.
- `tests/adapters/tkinter/player/test_gameplay_screen.py` -- **UPDATE**; add `settings_repository=fake_settings_repository` to all 31 `GameplayScreen(...)` construction sites; add a `_settle()` helper that repeatedly invokes `_on_animation_tick()` until `not screen._session.moving_direction` (i.e. the leg completed) for every existing movement/win test that previously asserted an instant post-keypress state change (e.g. `test_move_through_an_open_passage_...`, `test_reaching_the_exit_...`); add sidebar tests (mode toggle click/`m` shortcut flips the session mode, persists via the injected fake, updates the button's active state; speed button cycles and relabels; both respect the toplevel focus guard; animation job cancelled on `<Destroy>`).
- `tests/adapters/tkinter/player/test_maze_canvas.py` -- **UPDATE**; `set_ball_offset` fractional-interpolation rows (positive/negative deltas, wrapper equivalence of `set_ball_position`).
- `tests/adapters/tkinter/common/test_keybindings.py` -- **UPDATE**; add `toggle_movement_mode` to the uniqueness/lookup tests (`m` is free, so no collision).
- `tests/adapters/tkinter/common/test_tool_btn.py` -- **UPDATE**; `set_text()` replaces the label in place without disturbing active/focus state.

## Tasks & Acceptance

**Execution:**
- [ ] `src/labyrinthes/domain/movement_mode.py` -- add `MovementMode` -- pure enum
- [ ] `src/labyrinthes/domain/movement_speed.py` -- add `MovementSpeed` + `cell_crossing_duration()` -- pure enum/function
- [ ] `src/labyrinthes/domain/__init__.py` -- export the two new types/functions
- [ ] `tests/domain/test_movement_mode.py` + `tests/domain/test_movement_speed.py` -- unit tests
- [ ] `src/labyrinthes/application/player_session.py` -- rework to `request_move`/`advance_step`/`set_mode`/`set_speed` + new session fields + `STEPS_PER_CELL` -- pure orchestration
- [ ] `tests/application/test_player_session.py` -- port + new Discrete/Smooth/settings-application rows
- [ ] `src/labyrinthes/application/movement_settings.py` -- read/write with per-field fallback -- port-pattern mirror of `maze_size_bounds`
- [ ] `src/labyrinthes/application/settings_keys.py` -- add `MOVEMENT_MODE`/`MOVEMENT_SPEED`
- [ ] `tests/application/test_movement_settings.py` -- fallback/round-trip coverage
- [ ] `src/labyrinthes/adapters/tkinter/common/tool_btn.py` -- add `set_text()`
- [ ] `tests/adapters/tkinter/common/test_tool_btn.py` -- test `set_text()`
- [ ] `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- add `toggle_movement_mode`/`"m"`
- [ ] `tests/adapters/tkinter/common/test_keybindings.py` -- extend for the new entry
- [ ] `src/labyrinthes/adapters/tkinter/player/maze_canvas.py` -- add `set_ball_offset`, make `set_ball_position` a wrapper
- [ ] `tests/adapters/tkinter/player/test_maze_canvas.py` -- test `set_ball_offset`
- [ ] `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` -- settings kwarg, sidebar "Movement" group, `request_move`+animation loop, win-at-leg-completion, focus-guard reuse
- [ ] `tests/adapters/tkinter/player/test_gameplay_screen.py` -- update 31 call sites, add `_settle()`, sidebar/focus/tick-cancellation rows
- [ ] `src/labyrinthes/adapters/tkinter/player/screen.py` -- thread `settings_repository` into `GameplayScreen`

**Acceptance Criteria:**
- Given Discrete mode, when an arrow key is pressed, then the ball moves exactly one cell per press (one-cell leg, one press = one cell -- the Story 2.4 behavior preserved, now animated)
- Given Smooth mode, when an arrow key is held or pressed, then the ball moves continuously and can be redirected mid-move without stopping at a cell boundary
- Given the configurable speed setting, when changed, then both modes' underlying tick/animation rate reflects it identically (single `cell_crossing_duration` shared by both modes; live reschedule)
- Given the mode is switched mid-session, when the next input arrives, then the new mode's behavior applies immediately

## Spec Change Log

## Review Triage Log

## Design Notes

**Both modes animate through one engine (deliberate reinterpretation of "as established in Story 2.4").** Story 2.4's AC ("the ball moves exactly one cell per press") described an instant snap; Story 2.5's AC3 requires one configurable speed "reflected identically in both modes' underlying tick/animation rate" -- an instant Discrete snap has no tick/animation rate to adjust, which would make AC3 vacuous for Discrete. So Discrete becomes a one-cell *leg* animated by the same `advance_step`/`.after()` engine Smooth uses; the observable AC1 property (one press = one cell, no queuing, no mid-leg redirect) is preserved. This is a documented change: existing 2.4 tests that assert a position immediately after `_on_move` must drive the animation loop to settle (the `_settle()` helper) instead.

**One speed setting, not legacy's two-knob pair.** Legacy exposed `decoupe du deplacement` (sub-steps per cell) and `vitesse deplacement` (ms per sub-step) as two independent controls. The epic context explicitly requires "one configurable speed setting" (`epic-2-context.md` line 28). Therefore `STEPS_PER_CELL` is a fixed engine constant (5, the legacy default) and only the speed tier is user-facing; `cell_crossing_duration(NORMAL) == 225ms` reproduces the legacy default *total* crossing time (45ms x 5), keeping a fresh install's feel faithful to the old app.

**Speed tiers are this story's decision.** Legacy offered a continuous ms spinbox, not tiers; the three-tier `SLOW`/`NORMAL`/`FAST` mapping is a new design choice. `NORMAL = 225ms` is pinned by the legacy invariant; pick `SLOW`/`FAST` (e.g. 375ms/150ms) as clean, distinct values and record them in `movement_speed.py` as the single source of truth.

**The Ball-speed button deliberately has no global keyboard shortcut.** The mockup shows a `±` kbd-tag, but `<KeyPress-=>` is not a valid Tk sequence (Tk wants named keysyms like `plus`; confirmed via a live Tk probe during the prior investigation), and an ugly `PLUS`/`EQUAL` tag would misprint. This follows the already-established precedent that not every action carries a global shortcut (the win banner's Continue has none either -- Tab+Enter/Space satisfies NFR6); the button stays fully keyboard-operable via Tab-to-focus + `ToolButton`'s existing `<Return>`/`<space>` bindings. The mode toggle *does* get the `m` shortcut because "m" is a clean, bindable single keysym matching the legacy `l`/`s` movement-toggle shortcuts' spirit.

**"Banked turn" retry semantics ported from legacy.** Legacy `fonction_dep` checks `next_dir` only at cell boundaries and does *not* clear it when the banked direction is blocked (`Labyrinthes_copy.py` lines 1074-1084) -- the direction is retried at the following boundary. `advance_step` reproduces this: `pending_direction` survives a blocked boundary, letting a player mash a turn slightly early and have it take effect at the next junction.

**Mid-leg mode switch: finish the in-flight leg, then apply the new mode.** AC4 ("switching modes mid-session applies immediately to the next input") is satisfied by making `request_move`/`advance_step` dispatch on the *current* `session.mode`: the leg already in flight when the toggle lands completes under its starting engine (it can't retroactively change), and the very next keypress after the toggle runs under the new mode. `set_mode`/`set_speed` are pure field replacements with no engine logic of their own.

**Sidebar placement is this story's own decision.** The mockup's gameplay screen shows a left "Session" sidebar and right "Shortcuts"/"Mode" sidebars; only the "Movement" group (mode toggle + Ball speed) is backed by this story's ACs, and the legacy puts the movement/speed controls together (`Labyrinthes_copy.py` lines 328-330, 1814-1832). A single left-hand sidebar with the "Movement" group is the minimal, mockup-consistent placement; Pause/Restart/Sound/Legend/Mode stay out per Story 2.4's explicit deferral.

**The focus guard must cover the new `m` shortcut too.** `bind_shortcut` registers interpreter-wide bindings; typing `m` (or pressing an arrow) while the `SaveMazeDialog`'s name field holds focus would otherwise toggle the mode / move the ball behind the dialog. Reuse the same toplevel check Story 2.4's review introduced (`_on_move`, `gameplay_screen.py` lines 194-196) via a shared helper so the mode toggle and movement share one source of truth.

**Settings default on the screen, not in the domain.** `start_session` carries plain defaults (`SMOOTH`/`NORMAL`); `GameplayScreen` applies the settings-loaded values at construction. This keeps `player_session.py` free of repository dependencies and mirrors how Story 2.4's screen stays decoupled from `SettingsRepository`.

## Verification

**Commands:**
- `ruff check .` -- expected: no new lint violations (line-length 100, rules `E, F, I, UP, B, SIM`; no comments unless asked)
- `ruff format --check .` -- expected: no formatting diffs
- `pytest` -- expected: full suite green, including the 31 updated `GameplayScreen` call sites and all new/updated test files

**Regression watchlist:** the 31 `GameplayScreen(...)` constructions in `test_gameplay_screen.py` (every one needs `settings_repository=`); every existing movement/win test that asserts immediately after `_on_move` (needs `_settle()`); `screen.py`'s `GameplayScreen` construction; `test_keybindings.py`'s key-uniqueness test (the new `m` must not collide); the focus-dependent GUI tests documented as flaky in `AGENTS.md` (re-run a single failing GUI test alone before assuming a regression).

## Dev Agent Record

### Agent Model Used

opencode/deepseek-v4-flash-free

### Debug Log References

Prior investigation + design for this story exists as the committed record `bmad-dev-auto-result-2-5-movement-modes-smooth-vs-discrete-configurable-speed.md` (git commit `81986d0`, bmad-loop run `20260811-181802-370f`) -- the design above is a full expansion of that record into this spec; no source changes were made by that run.

### Completion Notes List

- Created spec from epics.md Story 2.5 ACs (lines 576-599), epic-2-context.md, PRD FR-15 / EXPERIENCE.md interaction primitives, legacy `Labyrinthes_copy.py` movement code, Story 2.4's spec/review learnings, and the current `rewrite` codebase.

### File List

- This spec: `_bmad-output/implementation-artifacts/spec-2-5-movement-modes-smooth-vs-discrete-configurable-speed.md`
- Story-2.5 backlog entry in `_bmad-output/implementation-artifacts/sprint-status.yaml` (2-5: backlog -> ready-for-dev; epic-2 status left unchanged -- 2-1 through 2-4 are already done)
