---
title: 'Story 2.9: Timer — optional time limit, timeout message'
type: 'feature'
created: '2026-08-15'
status: 'done'
baseline_commit: NO_VCS
baseline_commit: 'd4d6a25'
context: ['_bmad-output/implementation-artifacts/epic-2-context.md']
---

# Story 2.9: Timer — optional time limit, timeout message

Status: ready-for-dev

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

Story 2.4 established the `Time` HUD chip and a basic `_on_tick` loop that updates every second, but it only tracks elapsed time. There is no support for a **time limit**: no setting to enable it, no setting to configure the duration, no logic to detect a timeout, and no failure UI. The legacy `Chrono` class had these concepts but they were never fully wired into the gameplay loop.

### Approach

Wire the optional time limit into the session, the HUD, and the gameplay screen:

- **Application:**
    - `PlayerSession` gains a `time_limit: Duration | None` field and a `timed_out: bool` flag.
    - `start_session(maze)` defaults to `time_limit=None` and `timed_out=False`.
    - `set_time_limit(session, limit: Duration | None) -> PlayerSession`: **NEW**, no-op once solved or timed out.
    - `ignore_timeout(session) -> PlayerSession`: **NEW**, clears `timed_out` (to `False`) and removes the `time_limit` (to `None`), letting the player continue without further pressure.
    - `tick(session, elapsed: Duration) -> PlayerSession`: **UPDATE** to check if `time_limit` is exceeded. If `time_limit` is non-None and `elapsed.milliseconds >= time_limit.milliseconds`, set `timed_out=True`.
    - `request_move`/`advance_step`: **UPDATE** to also no-op if `session.timed_out` is `True`, matching the `solved` guard.
- **Settings:**
    - Add `TIMER_LIMIT_ENABLED` (bool) and `TIMER_LIMIT_SECONDS` (int) to `settings_keys.py`.
    - Add `application/timer_settings.py` (NEW) with readers/writers for these keys, mirroring `movement_settings.py`.
- **Screen:**
    - `__init__`: read timer settings; if enabled, convert `TIMER_LIMIT_SECONDS` to a `Duration` and apply it to the session via `set_time_limit`.
    - `_on_tick`: existing loop already calls `session_tick` and updates the HUD chip.
    - `_on_animation_tick`: after calling `session_advance_step`, also check `self._session.timed_out`.
    - `_sync_timeout_visuals()`: **NEW**, if `timed_out` is `True`, show the failure banner and cancel jobs.
    - `_show_failure_banner()`: **NEW**, inline above the maze frame (mirroring the win banner). Wording: "Time's up — the exit wasn't reached.". Styling: background `{colors.exit-bg}`/`{colors.exit-bg-dark}`, text `{colors.exit}`/`{colors.exit-dark}` (using the caution/warning amber hue). Includes a "Restart" button (existing `_on_restart` or similar) and a "Continue" button.
    - `_on_continue_after_timeout()`: **NEW**, calls `ignore_timeout(self._session)`, destroys the failure banner, and reschedules the HUD tick.

## Boundaries & Constraints

**Always:** `PlayerSession` remains the source of truth for "is the run over" (via `solved` and `timed_out`). The `Duration` type's `to_clock_string()` (uncapped minutes) is the sole string-formatting source for the HUD and banners.

**Block If:** Nothing needs human input — the "restart/continue stay reachable" requirement is handled by buttons on the failure banner itself.

**Never:** No Settings UI for the timer limit yet (deferred to a future Settings-window story, just like HARD colors in 2.8). No change to `Duration`'s internal representation. No modal "Game Over" dialog (must be inline/non-modal).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| No limit set | `time_limit=None` | HUD updates normally; win banner shows "Solved in MM:SS."; no timeout possible. | No error |
| Limit set, time remains | `elapsed < time_limit` | HUD updates normally; movement possible. | No error |
| Limit reached mid-leg | `_on_animation_tick` detects `timed_out` | Ball finishes the current leg (since `advance_step` already ran) but then stops; failure banner appears; tick loop cancelled. | No error |
| Limit reached at rest | `_on_tick` detects `timed_out` | Ball stops (no more moves accepted); failure banner appears; tick loop cancelled. | No error |
| "Continue" clicked | `_on_continue_after_timeout` | Banner destroyed; `timed_out` cleared; `time_limit` removed; movement possible again; tick loop resumed. | No error |
| "Restart" clicked | `_on_restart` | Session reset to `start_session(maze)`; new timer starts from 0; banner destroyed. | No error |
| Corrupt timer settings | `read_timer_limit` | Falls back to "disabled" or a default duration (e.g. 60s). | No error |

## Code Map

- `src/labyrinthes/application/settings_keys.py` — **UPDATE**: add `TIMER_LIMIT_ENABLED = "timer_limit_enabled"` and `TIMER_LIMIT_SECONDS = "timer_limit_seconds"`.
- `src/labyrinthes/application/timer_settings.py` — **NEW**: readers/writers for timer limit settings.
- `src/labyrinthes/domain/duration.py` — No change needed.
- `src/labyrinthes/application/player_session.py` — **UPDATE**:
    - `PlayerSession`: add `time_limit: Duration | None` and `timed_out: bool`.
    - `start_session`: init new fields.
    - `tick`: add timeout check.
    - `set_time_limit`, `ignore_timeout`: **NEW** free functions.
    - `request_move`, `advance_step`, `set_mode`, `set_speed`, `set_level`, `set_difficulty`, `set_hard_mode`: add `session.timed_out` to the existing `solved` guards.
    - `__all__`: add new functions.
- `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — **UPDATE**:
    - `__init__`: read timer settings and apply to session.
    - `_on_tick`, `_on_animation_tick`: wire in timeout check/visual sync.
    - `_sync_timeout_visuals()`, `_show_failure_banner()`, `_on_continue_after_timeout()`: **NEW** helpers.
    - `_show_win_banner()`: ensure it shows "Solved in MM:SS.".
- `tests/application/test_player_session.py` — **UPDATE**: tests for timeout logic and new setters.
- `tests/application/test_timer_settings.py` — **NEW**: tests for timer settings readers/writers.
- `tests/adapters/tkinter/player/test_gameplay_screen.py` — **UPDATE**: integration tests for timer limit, timeout banner display, and continue/restart flow.

## Tasks & Acceptance

**Execution:**
- [ ] `application/settings_keys.py` — add timer limit keys
- [ ] `application/timer_settings.py` — readers/writers (NEW)
- [ ] `application/player_session.py` — `time_limit`/`timed_out` fields, `set_time_limit`/`ignore_timeout` helpers, `tick` timeout check, update guards
- [ ] `adapters/tkinter/player/gameplay_screen.py` — read settings at mount, timeout detection, failure banner with Restart/Continue
- [ ] `tests/application/test_player_session.py` — timeout coverage
- [ ] `tests/application/test_timer_settings.py` — settings coverage (NEW)
- [ ] `tests/adapters/tkinter/player/test_gameplay_screen.py` — timer limit integration coverage

**Acceptance Criteria:**
- [ ] Time HUD chip updates continuously during a run.
- [ ] No limit → win banner shows elapsed time.
- [ ] Limit reached → inline failure message appears, run stops, restart/continue reachable.
- [ ] Timer uses `Duration` type.
