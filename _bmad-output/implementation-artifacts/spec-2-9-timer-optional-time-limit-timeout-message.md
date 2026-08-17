---
title: 'Story 2.9: Timer — optional time limit, timeout message'
type: 'feature'
created: '2026-08-17'
status: 'review'
baseline_commit: '0f7cbbd'
context: ['_bmad-output/implementation-artifacts/epic-2-context.md']
---

# Story 2.9: Timer — optional time limit, timeout message

Status: review

## Story

As a player,
I want to time my solve, optionally against a configurable limit,
So that I can challenge myself and get clear feedback if I run out of time.

## Acceptance Criteria

1. **Given** a run in progress, **when** the gameplay screen is active, **then** the Time HUD chip updates continuously.
2. **Given** no time limit configured, **when** the player solves the maze, **then** the elapsed time is shown in the win banner (e.g. "Solved in 00:42.").
3. **Given** a time limit configured, **when** the limit is reached before the exit is found, **then** an inline, non-modal failure message appears ("Time's up — the exit wasn't reached."), the run stops, and restart/continue options remain reachable from that message.
4. **Given** the timer, **when** started, **then** it uses the same `Duration` type used elsewhere in the domain (Story 1.1).

## Intent Contract

### Problem

AC-1, AC-2, and AC-4 are **already implemented** by Stories 2.4/2.5/2.8:

- AC-1 — the Time HUD chip already updates every second: `_on_tick()` (`gameplay_screen.py:679`) recomputes `elapsed` from `time.monotonic()` against `self._start_time`, routes it through `session_tick`, and refreshes the `live=True` Time chip.
- AC-2 — the win banner already shows `f"Solved in {self._session.elapsed.to_clock_string()}."` (`_show_win_banner`, `gameplay_screen.py:710-740`), with elapsed refreshed from the wall clock at solve time (`_on_animation_tick` solved branch, lines 503-517).
- AC-4 — `PlayerSession.elapsed` is already a `Duration` (`domain/duration.py`), constructed from milliseconds; `to_clock_string()` renders `"MM:SS"` with minutes uncapped (deliberately fixing the legacy `Chrono`'s wrap-past-60 bug — `duration.py:23-31`).

The **entire gap** is AC-3's optional time limit and timeout behavior — which the legacy app never wired either: `Chrono` (`Labyrinthes_copy.py:1479-1524`) is complete (start/stop/reset, `max_time`) but its instantiation and label update are commented out (`addendum.md:38`), and its timeout path was a modal `messagebox` (`test_fin`, line 1524) — exactly the modal-takeover the UX spec rejects. This story finishes wiring the timer end-to-end.

### Approach

Four layers, mirroring the established per-story seams:

- **Persistence** — a `game`-scoped `TIME_LIMIT_SECONDS` key in `settings_keys.py` plus a new never-raises `application/time_limit_settings.py` (mirrors `movement_settings.py`/`hard_mode_settings.py`): `read_time_limit(settings) -> Duration | None` and `write_time_limit(settings, limit: Duration | None) -> None`. `None`/`0`/absent/invalid = no limit (the default); a positive whole-second integer = a limit expressed as a `Duration` (AC-4). No Settings UI exists to configure it (the `SettingsWindow` is still the Story 1.8/1.11 placeholder) — exactly like the HARD-color writers in Story 2.8, the writer is the tested persistence seam a future Settings control consumes, and AC-3 is exercised at the repository seam + read-on-mount.
- **Session** — a terminal `timed_out: bool = False` field on `PlayerSession` plus `set_timed_out(session, timed_out) -> PlayerSession`, mirroring `solved`: once `timed_out`, `request_move`/`advance_step`/`set_mode`/`set_speed`/`set_level`/`set_difficulty`/`set_hard_mode`/`tick` all return the session unchanged. This is the "run stops" half of AC-3, kept in the pure domain layer so the screen never has to special-case input itself.
- **Tick-loop trigger** — `GameplayScreen` reads the limit once at mount into `self._time_limit: Duration | None` (fresh, like `read_movement_mode`/`read_movement_speed` at lines 194-195). `_on_tick()` gains a check after updating the chip: if a limit is set, the run is not solved, and `elapsed_ms >= limit.milliseconds`, call `_on_timeout()` instead of rescheduling. Timeout granularity is the tick cadence (≤1s late), matching the legacy per-second `Chrono` and the Time chip's whole-second display.
- **Timeout surface** — `_on_timeout()` cancels the tick and animation jobs, marks the session timed out, freezes the Time chip, and shows an inline non-modal banner that mirrors the win banner's styling (`accent-bg`/`accent`, `rounded.lg`, packed `before=self._maze_frame` — UX-DR9, `DESIGN.md:337`): the message `"Time's up — the exit wasn't reached."` (exact Voice-and-Tone wording, `EXPERIENCE.md:43`) plus two `PillButton`s — **Restart** (resets the run for the same maze via a new `_restart_run()`) and **Continue** (dismisses the message; the run stays stopped and the breadcrumb/selection navigation remains available). Both pills are `primary=False` (the at-most-one-primary rule: a `GENERATED` maze's Save pill can still be showing below).

`_restart_run()` is the restart capability AC-3's message must offer. It rebuilds the run in place: cancel tick/animation jobs, `start_session(self._maze)` re-applied with the persisted `read_movement_mode`/`read_movement_speed` (and a fresh `read_time_limit`), reset `_start_time`/`_rendered_visibility`/`_last_hard_sync_state`, re-render the structure, move the ball back to entry, reset the Level/Difficulty/Time/Pos chips, hide any banner, and reschedule the tick job. A restart is a *fresh run*: Level ONE, Difficulty ONE, HARD off (session-scoped, never persisted — `start_session` defaults, matching a re-mount), while persisted mode/speed/limit are re-applied.

## Boundaries & Constraints

**Always:** `adapters/tkinter/player/` never imports `adapters/storage/` directly (AD-9); the screen reaches settings only through `application/` (`read_time_limit`, never a raw `settings.get`). `time_limit_settings.py` and `player_session.py` import no `tkinter` and nothing from `adapters/` (AD-1). `Duration` is the one time type in the domain; no wall-clock read ever enters `player_session.py` (`time.monotonic()` stays in `gameplay_screen.py`, which passes the computed `Duration` in — the module's existing contract, `player_session.py:1-8`). The timeout check lives in the tick loop and never in `advance_step` — a timeout is wall-clock-driven and orthogonal to movement; the session merely records the terminal state. The `_on_tick` timeout branch must skip when `self._session.solved` (solve and timeout can race on the event loop; whichever `.after()` callback runs first wins). `_on_timeout()` never redraws structure and never reschedules work; `_restart_run()` is the only place that rebuilds state, and it must leave the screen fully interactive again (a `_tick_job` rescheduled). The existing `.after()` cancellation conventions (`_cancel_tick_job`/`_cancel_animation_job`, `<Destroy>` cleanup) stay intact and are reused. Timeout-message buttons are banner pills with no global shortcut — they don't need the `_toplevel_has_focus()` guard (that guard guards `bind_all()` shortcuts; a pill click is local).

**Block If:** Nothing needs human input — the no-Settings-UI deferral, the strict-int reader, the session-level `timed_out`, the 1s granularity, and the fresh-run restart semantics are all documented decisions below.

**Never:** No Settings time-limit UI (no story owns it; `SettingsWindow` stays its placeholder). No new keybinding — the mockup shows a global `Restart` (`R`) pill in a "Session" sidebar group, but no AC requires a restart shortcut, and the legacy `r` collision (Settings vs Restart, `addendum.md:41`, FR-22) must not be reproduced by wiring an ad-hoc `r` binding here; the banner's Restart is click-only, and any future global `restart` shortcut registers in the canonical table (`common/keybindings.py`) with a collision-free key. No `solved`-style timeout handling inside `advance_step` (see Always). No change to `_show_win_banner`/`_on_solved` or to `Duration`'s `to_clock_string`. No modal dialog anywhere — the timeout message is inline and non-modal (UX-DR9). No timer UI in the sidebar (no Pause/elapsed-countdown control; the mockup's `Pause`/`Space` is not owned by any AC). No per-move or per-animation-sub-step timeout polling — the 1s tick is the granularity.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Mount, no limit | no `TIME_LIMIT_SECONDS` stored | `self._time_limit is None`; `_on_tick` keeps rescheduling indefinitely; solve shows the win banner with the elapsed clock string (unchanged Story 2.4 behavior) | No error |
| Mount, limit stored | `write_time_limit(..., Duration(90_000))` then mount | `self._time_limit == Duration(90000)` (read fresh, like mode/speed) | No error |
| Mount, corrupt limit | stored `"garbage"`/`3.9`/`true`/`0`/`-5`/missing | `self._time_limit is None` — no limit, no raise (reader never-raises) | Invalid stored value → `None` |
| Timeout reached | limit `Duration(5000)`, `_on_tick` computes `elapsed_ms >= 5000`, not solved | `session.timed_out is True`; tick job cancelled (no reschedule); animation job cancelled; Time chip frozen at the timeout value; timeout banner shown with "Time's up — the exit wasn't reached." | No error |
| Timeout mid-leg | a leg is in flight when `_on_tick` fires the timeout | `_cancel_animation_job()` stops the leg where it is (ball frozen at its current offset); `advance_step`/`request_move` are no-ops once `timed_out`; a later Restart repositions the ball at entry | No error |
| Movement after timeout | arrow key with `session.timed_out` | No-op — no leg starts, no animation job scheduled (domain guard) | No error |
| Mode/speed/level/difficulty/HARD toggle after timeout | any `set_*` with `timed_out` | Session no-op (button label/active cosmetic flips are the already-accepted Story 2.5 deferred behavior) | No error |
| Solve/timeout race | `_on_animation_tick` marks solved just before the next `_on_tick` | `_on_tick`'s timeout branch is skipped when `solved`; win banner path wins; tick job already cancelled by the solved branch | No error |
| Restart from the timeout message | click Restart while `timed_out` | Fresh run: `session.timed_out is False`, ball at entry, elapsed 0, Time chip "00:00", Level ONE/Difficulty ONE/HARD off, persisted mode/speed/limit re-applied, structure re-rendered, banner destroyed, tick job rescheduled, movement works again | No error |
| Continue from the timeout message | click Continue while `timed_out` | Banner destroyed only; `timed_out` stays True; run stays stopped; breadcrumb/selection navigation still available | No error |
| Timeout granularity | limit `Duration(1000)`, `elapsed_ms == 1000` | Timeout fires (`>=`) | No error |
| Screen destroyed mid-timeout | `.after()` jobs pending, banner showing | Existing `<Destroy>` cancellation unchanged (`_on_destroy` cancels tick + animation) | No error |
| HARD active at timeout | HARD on, ball mid-leg | Fog stays shown, ball stays hidden (run frozen); restart clears both via the fresh session + `_sync_hard_mode_visuals` | No error |

## Code Map

- `src/labyrinthes/application/settings_keys.py` — **UPDATE**: add `TIME_LIMIT_SECONDS = "time_limit_seconds"` (the `game`-scope key named in the epic context's settings list, `epic-2-context.md:50`).
- `src/labyrinthes/application/time_limit_settings.py` — **NEW**, mirroring `movement_settings.py`/`hard_mode_settings.py`:
  - `read_time_limit(settings) -> Duration | None` — **NEW**: reads `TIME_LIMIT_SECONDS` in `SettingsScope.GAME`; returns `Duration(milliseconds=seconds * 1000)` only when the stored value is a positive integer; returns `None` on `SettingNotFoundError`/`SettingCorruptError`/`TypeError` and on any stored value that isn't an actual `int` (`type(value) is int` — rejects bool/float/str, matching the strictness precedent set by `_read_color` in Story 2.8) or isn't `> 0`. Never raises, never writes on read.
  - `write_time_limit(settings, limit: Duration | None) -> None` — **NEW**: persists the whole-second count (`limit.milliseconds // 1000`) via `settings.set(SettingsScope.GAME, TIME_LIMIT_SECONDS, seconds)`; a `None` limit persists `0` (the on-disk encoding for "no limit" — the port has no delete, so `0` is the documented sentinel). Unused by this story's screen (no Settings UI); it is the tested persistence seam the future time-limit picker consumes — log a deferred-work note, exactly like the HARD-color writers (Story 2.8).
  - Update the module docstring and `__all__`.
- `src/labyrinthes/application/player_session.py` — **UPDATE**:
  - `PlayerSession`: add `timed_out: bool = False` field (default in `start_session`).
  - `set_timed_out(session, timed_out: bool) -> PlayerSession` — **NEW**, mirroring `set_hard_mode`: no-op once solved; otherwise `replace(session, timed_out=timed_out)`. Session-scoped, never persisted; a fresh `start_session` starts not-timed-out.
  - Guard **all** of `request_move`, `advance_step`, `set_mode`, `set_speed`, `set_level`, `set_difficulty`, `set_hard_mode`, and `tick` to return the session unchanged when `session.timed_out` (extend each existing `if session.solved` guard with `or session.timed_out`). Update the module docstring and `__all__`.
- `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — **UPDATE**:
  - Imports: alias `set_timed_out as session_set_timed_out` (matching the `session_set_*` import block, lines 91-114) and `read_time_limit` from `application/time_limit_settings.py`.
  - Constructor: after the mode/speed application (lines 194-195), add `self._time_limit: Duration | None = read_time_limit(settings_repository)`. Initialize `self._timeout_banner: tk.Frame | None = None` next to `self._win_banner`.
  - `_on_tick()` (lines 679-683): after the `_time_chip.set_value(...)` line, add the timeout check before the reschedule — `if (not self._session.solved and self._time_limit is not None and elapsed_ms >= self._time_limit.milliseconds): self._on_timeout(); return`. The existing reschedule stays the not-timeout path.
  - `_on_timeout() -> None` — **NEW**: `self._cancel_tick_job()`; `self._cancel_animation_job()`; `self._session = session_set_timed_out(self._session, True)`; `self._time_chip.set_value(self._session.elapsed.to_clock_string())`; `self._show_timeout_banner()`. No work is scheduled.
  - `_show_timeout_banner() -> None` — **NEW**: mirrors `_show_win_banner` (lines 710-740) — a `tk.Frame` with `background=colors.accent_bg`, 1px `colors.accent` highlight, packed `fill="x"`, `pady=(0, SPACING["lg"])`, `before=self._maze_frame`; a `tk.Label` with `"Time's up — the exit wasn't reached."` (`TYPOGRAPHY.body`, `colors.ink`), and two `PillButton`s **Restart** (`command=self._restart_run`) and **Continue** (`command=self._on_timeout_continue_clicked`), both `primary=False` (the Save-pill rule — see Design Notes). Store as `self._timeout_banner`.
  - `_on_timeout_continue_clicked() -> None` — **NEW**: mirrors `_on_continue_clicked` (lines 742-748): destroy `self._timeout_banner` and set it to `None`. The session stays `timed_out`; nothing else resets.
  - `_restart_run() -> None` — **NEW**: fresh run for the same maze — `self._cancel_tick_job()`; `self._cancel_animation_job()`; `self._session = start_session(self._maze)` then re-apply `session_set_mode(self._session, read_movement_mode(settings_repository))` and `session_set_speed(self._session, read_movement_speed(settings_repository))`; `self._time_limit = read_time_limit(settings_repository)`; `self._start_time = time.monotonic()`; `self._maze_canvas.redraw_structure(self._session.visibility)` + `self._rendered_visibility = self._session.visibility`; `self._maze_canvas.set_ball_position(self._session.position)`; reset the Level chip/value-label and Difficulty chip/value-label/widgets and the mode button to the fresh session (`_sync_level_widgets`/`_sync_difficulty_widgets`/`_sync_mode_button`); `self._time_chip.set_value("00:00")`; `self._pos_chip.set_value(_pos_text(self._session.position))`; destroy `self._timeout_banner`/`self._win_banner` (set both `None`); `self._last_hard_sync_state = None` + `self._sync_hard_mode_visuals()` (fresh session has HARD off → status light hidden, ball shown); `self._tick_job = self.after(_TICK_INTERVAL_MS, self._on_tick)`.
- `tests/application/test_player_session.py` — **UPDATE**: `set_timed_out` sets the field; no-op once solved; once timed out, `request_move`/`advance_step`/`tick`/`set_mode`/`set_speed`/`set_level`/`set_difficulty`/`set_hard_mode` are all no-ops. Mirror the `set_hard_mode`/solved-guard test shapes.
- `tests/application/test_time_limit_settings.py` — **NEW**, mirroring `test_hard_mode_settings.py`/`test_movement_settings.py`: absent → `None`; corrupt → `None`; stored non-int (`"60"`, `3.9`, `True`, `0`, `-5`) → `None`; valid `60` → `Duration(60000)`; `write_time_limit(None)` stores `0` and reads back `None`; `write_time_limit(Duration(75_000))` stores `75` and reads back `Duration(75000)`; never-writes-on-read; both functions use the GAME scope.
- `tests/application/test_settings_keys.py` — **UPDATE**: add `TIME_LIMIT_SECONDS` to `_KEY_NAMES`.
- `tests/adapters/tkinter/player/test_gameplay_screen.py` — **UPDATE**:
  - Mount reads the limit: with `write_time_limit(settings, Duration(90000))` before construction, `screen._time_limit == Duration(90000)`; with nothing stored, `is None`.
  - Timeout: write a 5s limit (or set `screen._time_limit` directly), fake `screen._start_time = time.monotonic() - 5.0` (the existing `_on_tick` test convention, line 663), call `_on_tick()` → `session.timed_out is True`, `_tick_job is None`, the timeout banner exists with the exact message text, the Time chip shows `"00:05"`.
  - Timeout cancels an in-flight animation: start a leg (`_on_move` without settling), fake a past start, call `_on_tick()` → `_animation_job is None`, `session.timed_out is True`.
  - Restart from the banner: after a timeout, call `screen._restart_run()` (or fire the Restart pill) → `timed_out is False`, position at entry, `elapsed == Duration(0)`, Time chip `"00:00"`, banner destroyed, `_tick_job is not None`, a subsequent `_on_move` starts a leg again.
  - Continue from the banner: after a timeout, fire Continue → banner destroyed, `timed_out` stays `True`, `_tick_job is None`.
  - No limit: `_on_tick` past 5s with no limit keeps `timed_out is False` and reschedules (no behavior change).
  - Movement after timeout is a no-op at the screen level: `_on_move` with `timed_out` schedules no animation job.
  - Solve wins the race: `session.solved = True`, past start, `_on_tick()` does not time out.
  - Restart with a solved win banner: `_restart_run()` destroys `self._win_banner` and resets the run.
  - Save-pill interaction: with a `GENERATED` maze + a limit, after timeout the banner's Restart/Continue pills are not primary (`_primary is False`), mirroring `test_continue_button_is_not_a_primary_pill` (lines 364-387).

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/application/settings_keys.py` — add `TIME_LIMIT_SECONDS`
- [x] `src/labyrinthes/application/time_limit_settings.py` — never-raises `read_time_limit`/`write_time_limit` (NEW)
- [x] `src/labyrinthes/application/player_session.py` — `timed_out` field + `set_timed_out`; extend every solved-guard with `or session.timed_out`
- [x] `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — `self._time_limit` at mount, `_on_tick` timeout check, `_on_timeout`, `_show_timeout_banner`, `_on_timeout_continue_clicked`, `_restart_run`
- [x] `tests/application/test_player_session.py` — `set_timed_out` + timed-out guards coverage
- [x] `tests/application/test_time_limit_settings.py` — readers/writers coverage (NEW)
- [x] `tests/application/test_settings_keys.py` — add `TIME_LIMIT_SECONDS`
- [x] `tests/adapters/tkinter/player/test_gameplay_screen.py` — mount-read, timeout, restart/continue, race, save-pill coverage
- [x] `_bmad-output/implementation-artifacts/deferred-work.md` — append the no-Settings-UI time-limit picker deferral note

**Acceptance Criteria:**
- [x] Given a run in progress → Time HUD chip updates continuously (already green via Story 2.4's `_on_tick`; keep it green — no regression)
- [x] Given no limit → win banner shows "Solved in MM:SS." (already green via Story 2.4; keep it green — no regression)
- [x] Given a limit reached before the exit → inline non-modal "Time's up — the exit wasn't reached." banner, run stopped, Restart/Continue reachable from it
- [x] Given the timer → `Duration` is the only time type (session `elapsed` and the limit are both `Duration`)

## Design Notes

**The time limit is read once at mount, like mode/speed.** The limit scopes a run the same way `MOVEMENT_MODE`/`MOVEMENT_SPEED` do (both read once at mount, `gameplay_screen.py:194-195`), so a mid-run settings change does not retroactively retime the active run — it applies to the next mount/restart. This is why `_restart_run()` re-reads it. (The HARD-color readers are the deliberate exception to this rule — AC-4 there *requires* per-sync freshness; a time limit has no such requirement.)

**`timed_out` is a session-level terminal state, parallel to `solved`.** The "run stops" half of AC-3 belongs in the domain, not in the screen's input handlers: every `PlayerSession` operation already documents "no-op once solved", and extending the same guard to `timed_out` means the screen, tests, and any future caller all get frozen-movement behavior for free — the screen never has to remember to check a flag before each handler. `set_timed_out` mirrors `set_hard_mode` (session-scoped, never persisted, fresh `start_session` clears it).

**Timeout granularity is the 1s tick.** `_on_tick` is the only wall-clock poll and already owns the elapsed computation; the Time chip displays whole seconds; the legacy `Chrono` also ticked per second (`update_time`, `Labyrinthes_copy.py:1508-1513`). A limit is therefore enforced to within ≤1s, which matches the displayed granularity. The `>=` comparison (`elapsed_ms >= limit.milliseconds`) fires exactly at the boundary.

**Restart = fresh run, HARD off.** `_restart_run()` rebuilds exactly what a fresh mount would build: `start_session` defaults (Level ONE, Difficulty ONE, HARD off — HARD is session-scoped and not persisted per Story 2.8, and a re-mount starts HARD off) plus re-applied persisted mode/speed/limit. This is the predictable, testable choice; preserving mid-run toggles across a "start over" would blur what a restart means. Documented so the dev does not attempt to carry HARD/Level/Difficulty across.

**Restart and Continue are banner pills, not shortcuts.** No AC requires a global restart keybinding, and the legacy `r` collision (Settings vs Restart — `addendum.md:41`) is exactly the class of bug the canonical keybinding table + `test_keybindings.py` exist to prevent. The pills are local click targets, so they need no `_toplevel_has_focus()` guard (that guard protects `bind_all()`-level shortcuts; a pill click is a direct command). Both are `primary=False`: a `GENERATED` maze's Save pill can still be showing below the banner (winning/timeout doesn't hide it), and the at-most-one-primary rule (`PillButton` docstring, Story 2.4) forbids a second one.

**Timeout while a leg is in flight freezes the ball mid-cell.** The animation job is cancelled and the canvas is not touched, so the ball stays at its current sub-step offset with `session.moving_direction` set but inert (`advance_step` no-ops once `timed_out`). Restart repositions it via `set_ball_position(entry)`. Acceptable — the run stopped, and the frozen frame is an honest picture of "the timer ran out mid-move".

**No Settings UI, mirroring the Story 2.8 color-picker deferral.** The `SettingsWindow` is still the Story 1.8/1.11 placeholder and no story in Epics 1–5 owns a time-limit picker. AC-3 is therefore exercised by tests that `write_time_limit` a value and then drive a fake-elapsed `_on_tick` — the writer is the documented seam the future picker consumes. Log the deferral in `deferred-work.md` (same pattern as Story 2.8's color-picker note).

**The `0`-sentinel encodes "no limit" on disk.** The port has no delete operation (`settings_repository.py` exposes only `get`/`set`), so "turn the limit off" must persist a value: `0` (meaningless as a time limit) is the documented sentinel, and the reader maps `0`/negative/absent/invalid all to `None`. The strict `type(value) is int` check rejects `bool` (`True` would otherwise parse as 1s), float (`3.9` silently truncating to 3 is exactly the Story 2.2 deferred hazard), and string (`"60"`) stored values.

## Previous Story Intelligence

- **Story 2.4** owns the surface this story extends: the `_on_tick` loop, the `live` Time chip, `_show_win_banner` (the styling/placement template for the timeout banner), and the win-banner Continue behavior (the template for the timeout Continue). Its tests (`test_on_tick_updates_the_time_chip_and_reschedules` line 652, `test_win_banner_text_reports_the_elapsed_clock_string` line 344, `test_continue_button_is_not_a_primary_pill` line 364) are the templates for this story's tests.
- **Story 2.5** establishes the `.after()` cancellation conventions (`_cancel_tick_job`/`_cancel_animation_job`, `<Destroy>` cleanup) and the mount-time `read_movement_mode`/`read_movement_speed` application this story extends with `read_time_limit`.
- **Story 2.8** is the closest seam: `hard_mode_settings.py`'s never-raises reader/writer pair (with the strict-value precedent) is the direct template for `time_limit_settings.py`; `set_hard_mode` is the template for `set_timed_out`; the `_last_hard_sync_state` reset in `_restart_run()` is required so a restart never leaves a stale fog/ball state; its deferred-work note ("no Settings color picker") is the template for this story's time-limit-picker deferral.
- **Regression watchlist:** the `_on_tick` reschedule (timeout branch must keep the not-timeout path identical); the win-banner text tests (unchanged); the keybinding-uniqueness test (no new binding — nothing to add); the AD-9 import-boundary test (`time_limit_settings.py` imports nothing from `adapters/` or `tkinter`); `GameplayScreen(...)` construction sites (a new optional `_time_limit` field must not break any existing constructor call); `_sync_hard_mode_visuals`'s per-tick early-return (a timeout must not reschedule it). Run a single failing GUI test alone before assuming a regression (flaky focus tests, AGENTS.md).

## Git Intelligence

- Working branch: `epic-2-play-a-maze-game-player` (epic-2 accumulation branch, current HEAD `0f7cbbd` = Story 2.8 merge). **Never commit directly to it** — create `story-2-9-timer-optional-time-limit-timeout-message` from it, merge story → epic via `git merge --no-ff` when done; epic → `rewrite` only via PR once the whole epic is done.
- Mirror the per-story rhythm: `feat(player): ...` (feature) → `test(player): ...` (tests) → `docs(planning): record Story 2.9 ...` (status + deferred-work note) → `Merge story-2-9-... into epic-2-... (story 2.9)`. Conventional Commits in English, story number in the subject (`(story 2.9)`).
- `uv.lock` is untracked — leave it alone.

## Latest Technical Information

No new external dependencies: the stack is pinned in `pyproject.toml` (Python ≥3.12, tkinter, pytest ≥8.0, ruff ≥0.6, hatchling). Everything uses stdlib (`dataclasses`, `enum`, `tkinter`, `time`) and the existing `domain/`/`application/`/`common/` types — no web research needed. The one behavioral fact this story relies on (`tk.Frame.pack(..., before=...)` to place the timeout banner above the maze-frame) is the same standard Tk call Story 2.4's `_show_win_banner` already uses.

## Verification

**Commands:**
- `ruff check .` — expected: no new lint violations (line-length 100, rules `E, F, I, UP, B, SIM`; no comments unless asked)
- `ruff format --check .` — expected: no formatting diffs
- `pytest` — expected: full suite green, including the new `time_limit_settings`/`set_timed_out`/timeout-banner tests

**Regression watchlist:** `_on_tick` reschedule semantics; win-banner text/styling tests; `test_keybindings.py` (untouched); `test_settings_keys.py` (one new name); the AD-9 import-boundary test; `PlayerSession` solved-guard tests (the extended `or session.timed_out` must not alter solved behavior); the HARD fog/status-light tests (restart must reset `_last_hard_sync_state`); the `GameplayScreen` construction sites.

## Project Structure Notes

- All timeout state lives on `PlayerSession` (`application/`); the limit's persistence lives in a new `application/time_limit_settings.py` + one key in `application/settings_keys.py`; only rendering/input wiring lands in `adapters/` (`player/gameplay_screen.py`). No new screen, no new port, no domain change.
- Naming is English throughout (NFR4); maze data (`0/1/2/3`) untouched; the new settings key uses the existing `snake_case` convention.
- No `tkinter`/`adapters` import may appear in `player_session.py`, `settings_keys.py`, or `time_limit_settings.py` (AD-1, AD-9).

## References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 2.9 ACs (lines 672-694); UX-DR9 win banner + timeout message (line 129); FR-16 coverage (line 154)]
- [Source: `_bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/prd.md` — FR-16 (lines 155-157)]
- [Source: `_bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/addendum.md` — disabled `Chrono` (line 38), legacy `r` collision (line 41)]
- [Source: `_bmad-output/implementation-artifacts/epic-2-context.md` — timer paragraph (line 37), game-scoped settings list incl. time-limit (line 50), cross-story dependency on Story 2.4 (line 68)]
- [Source: `_bmad-output/planning-artifacts/ux-designs/ux-Labyrinthes-2026-08-04/EXPERIENCE.md` — timeout state pattern (line 86), Voice and Tone "Time's up" (lines 42-43), UJ-C timeout path (lines 149-151)]
- [Source: `_bmad-output/planning-artifacts/ux-designs/ux-Labyrinthes-2026-08-04/DESIGN.md` — `win-banner` component (line 206), win-banner styling (line 337)]
- [Source: `Labyrinthes_copy.py` (legacy, read-only) — `Chrono` incl. the modal `test_fin` timeout (lines 1479-1524), commented-out wiring (lines 373-374, 425)]
- [Source: `src/labyrinthes/domain/duration.py` — the shared `Duration` type and `to_clock_string` (AC-4); `src/labyrinthes/application/player_session.py` (`start_session`, `tick`, the solved-guard setters, the module's no-wall-clock contract); `src/labyrinthes/application/settings_keys.py`; `src/labyrinthes/application/movement_settings.py`/`hard_mode_settings.py` (never-raises reader/writer templates); `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` (`_on_tick` lines 679-683, `_show_win_banner`/`_on_continue_clicked` lines 710-748, mount-time settings application lines 194-195, focus guard, `.after()` cancellation); `tests/adapters/tkinter/player/test_gameplay_screen.py` (elapsed-ticking test lines 649-687, win-banner/continue/primary-pill tests lines 323-470)]

## Dev Agent Record

### Agent Model Used

opencode/deepseek-v4-flash-free

### Debug Log References

- 2026-08-17: Story 2.9 spec created on branch `epic-2-play-a-maze-game-player` (HEAD `0f7cbbd`) via the `bmad-create-story` workflow. Full-artifact analysis confirmed AC-1/AC-2/AC-4 are already green from Stories 2.4/2.5/2.8 (Time chip tick loop, win-banner elapsed text, `Duration`-typed session elapsed); the story's new scope is AC-3 only: the `game`-scoped time-limit setting, the session `timed_out` terminal state, the tick-loop timeout trigger, the inline timeout banner, and the in-place restart capability. Legacy `Chrono` (lines 1479-1524) verified as the disabled/buggy baseline; its modal `messagebox` timeout is rejected per UX-DR9.
- 2026-08-17: Implemented on branch `story-2-9-timer-optional-time-limit-timeout-message` (baseline `0f7cbbd`). Added `TIME_LIMIT_SECONDS` to `settings_keys.py`; new `application/time_limit_settings.py` with never-raises `read_time_limit`/`write_time_limit` (strict `type(value) is int` reader, `0`-sentinel writer); `PlayerSession.timed_out` field + `set_timed_out`, extended every `if session.solved` guard with `or session.timed_out`; `GameplayScreen` reads the limit once at mount into `self._time_limit`, `_on_tick()` fires `_on_timeout()` once `elapsed_ms >= limit` on an unsolved run (solve wins the race), `_on_timeout` cancels both jobs + freezes the chip + shows the inline non-modal banner, `_on_timeout_continue_clicked` dismisses only, `_restart_run` rebuilds a fresh run (session defaults + re-applied persisted mode/speed + fresh `read_time_limit`, destroys win/timeout banners, resets `_last_hard_sync_state`). No Settings UI, no global restart shortcut, no `advance_step` timeout polling, no modal (per spec Boundaries). Deferred-work note appended (no time-limit picker UI).

### Completion Notes List

- Implemented Story 2.9 end-to-end. AC-3 now green: a configured time limit stops the run with an inline, non-modal `"Time's up — the exit wasn't reached."` banner (UX-DR9) and Restart/Continue pills; AC-1/AC-2/AC-4 kept green (no regression in the tick loop, win banner, or `Duration` usage).
- Test coverage: `tests/application/test_time_limit_settings.py` (new — reader/writer matrix: absent/corrupt/non-int/`0`/negative → `None`, positive int → `Duration`, `0`-sentinel write, never-writes-on-read, GAME scope); `tests/application/test_player_session.py` (+12: `set_timed_out` sets/clears/preserves fields, no-op once solved, and every operation is a no-op once timed out); `tests/application/test_settings_keys.py` (+`TIME_LIMIT_SECONDS`); `tests/adapters/tkinter/player/test_gameplay_screen.py` (+13: mount-read of the limit, corrupt-stored → `None`, timeout at the limit freezes chip + cancels tick job + shows the exact message, no-limit keeps rescheduling, timeout cancels an in-flight animation job, movement after timeout is a no-op, solve wins the race, restart produces a fresh run (entry/elapsed 0/`"00:00"`/banner gone/`_tick_job` rescheduled/movement works again), restart re-reads the limit, restart with a win banner destroys it, continue keeps the run stopped, banner pills not primary with a `GENERATED` maze, restart resets HARD fog/ball/light).
- `ruff check src/ tests/` clean, `ruff format --check` clean, full suite 680 passed. `.agents/` lint noise is pre-existing third-party skill code, untouched.

### File List

- This spec: `_bmad-output/implementation-artifacts/spec-2-9-timer-optional-time-limit-timeout-message.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — 2-9: ready-for-dev -> in-progress -> review
- `_bmad-output/implementation-artifacts/deferred-work.md` — appended the no-Settings time-limit-picker deferral note
- `src/labyrinthes/application/settings_keys.py` — added `TIME_LIMIT_SECONDS`
- `src/labyrinthes/application/time_limit_settings.py` — NEW: `read_time_limit`/`write_time_limit`
- `src/labyrinthes/application/player_session.py` — `timed_out` field, `set_timed_out`, extended solved-guards
- `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — `_time_limit` at mount, `_on_tick` timeout check, `_on_timeout`, `_show_timeout_banner`, `_on_timeout_continue_clicked`, `_restart_run`
- `tests/application/test_time_limit_settings.py` — NEW
- `tests/application/test_player_session.py` — `set_timed_out` + timed-out guard tests
- `tests/application/test_settings_keys.py` — added `TIME_LIMIT_SECONDS`
- `tests/adapters/tkinter/player/test_gameplay_screen.py` — mount-read/timeout/restart/continue/race/save-pill/HARD-reset tests

## Change Log

- 2026-08-17: Implemented Story 2.9 (AC-3): time-limit settings seam (`application/time_limit_settings.py` + `TIME_LIMIT_SECONDS`), session `timed_out` terminal state with `set_timed_out`, tick-loop timeout trigger, inline non-modal timeout banner with Restart/Continue, and in-place fresh-run restart. Added 26 new/updated tests; full suite green (680 passed); lint/format clean. Logged the no-Settings-UI time-limit-picker deferral.