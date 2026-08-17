---
title: 'Story 2.8: HARD mode — invisible ball, fog overlay, status light'
type: 'feature'
created: '2026-08-14'
status: 'done'
baseline_commit: 'd4d6a25'
context: ['_bmad-output/implementation-artifacts/epic-2/epic-2-context.md']
---

# Story 2.8: HARD mode — invisible ball, fog overlay, status light

Status: done

## Story

As a player,
I want to enable HARD mode, where the ball is invisible while moving and a status light shows ready/moving state in a color I configure,
So that I can play a more demanding hidden-position challenge.

## Acceptance Criteria

1. **Given** HARD mode is active, **when** the ball is moving, **then** it is not rendered, and a translucent fog scrim covers the maze-frame above the corridor/ball plane but below wall-bars/markers.
2. **Given** the ball comes to rest, **when** movement stops, **then** the fog overlay disappears instantly (no fade) and the ball renders normally.
3. **Given** the status light, **when** ready vs. moving, **then** its color follows the user's configured HARD-mode color setting consistently in both states.
4. **Given** the user changes the color setting, **when** HARD mode is next used, **then** both ready and moving states use the new color without the return-to-ready toggle breaking.

## Intent Contract

### Problem

Stories 2.4–2.7 built the gameplay surface (rendering, HUD, movement, Levels, Difficulty) but shipped **no HARD mode**: the ball is always rendered, there is no fog overlay, no status light, and no persisted HARD-color setting. The legacy app's HARD mode was fully implemented but buggy (`Labyrinthes_copy.py` lines 224–256, 1014–1118): the status-light "ready" color was hardcoded as `"blue"` (`change_voyant_mode_hard("ready", "blue")`, line 1041) while the "moving" color came from a configurable setting — so changing that setting silently broke the return-to-ready toggle. That bug must not be reproduced (FR-14 consequence, addendum line 40).

### Approach

Wire HARD mode end-to-end on the session, the maze canvas, and the gameplay screen, with two persisted `game`-scoped color settings:

- **Application:** add a `hard_mode: bool = False` field to `PlayerSession` and a `set_hard_mode(session, enabled) -> PlayerSession` operation mirroring `set_mode`/`set_speed` exactly (no-op once solved; no visibility re-init — HARD mode is purely presentational and never changes movement math). Add two `game`-scope color keys to `settings_keys.py` and a new `application/hard_mode_settings.py` mirroring `movement_settings.py`'s never-raises reader pattern, with the theme's default color passed in as a parameter by the screen (the application layer must not import `adapters/tkinter/common/tokens.py`, AD-1/AD-9). **HARD on/off is session-scoped, not persisted** — the epic context's game-scoped list (`epic-2-context.md` line 50) contains "HARD-mode color" but no HARD-mode on/off; a fresh mount starts with HARD off.
- **Keybinding:** add `Keybinding("toggle_hard_mode", "Toggle HARD mode", "h")` to the canonical table — `h` is free (collision-tested by `test_keybindings.py`), matches the legacy `self.bind("<KeyRelease-h>", self.big_boss.mode_HARD)` (line 336), and the screen binds it via `bind_shortcut` exactly like `toggle_movement_mode`.
- **Canvas:** `MazeCanvas` gains a fog rectangle item (tag `"fog"`, fill `colors.bg`, `state="hidden"` by default) created **first** in the constructor so every wall-bar/marker/ball item stacks above it (load-bearing z-order — see Design Notes), plus `set_hard_mode_moving(moving: bool)` which toggles `state="normal"/"hidden"` on the fog and `state="hidden"/"normal"` on the ball. The ball is genuinely not rendered (canvas `state="hidden"`), not merely occluded — matching the mockup's "ball intentionally not rendered while moving" (key-player-gameplay.html line 379) and EXPERIENCE.md line 57.
- **Screen:** add a "Mode" sidebar group (label + a single HARD `ToolButton` with kbd-tag `H`, active when HARD is on — mirroring the mockup's right-aside `Mode`/`HARD` button at key-player-gameplay.html lines 383–385) and a status light in the HUD row (a 10px round light + a Ready/Moving label, per the mockup's `.status-wrap` at lines 172–174, 365–368) shown only while HARD is active. `_toggle_hard_mode` (focus-guarded) flips `set_hard_mode`, re-activates the button, and re-reads **both** colors fresh from the repository on every activation/state sync (`_hard_mode_colors()`), which is the AC-4 mechanism: the two states always read the same current setting, no literal ever enters the code, so a color change can't break the ready↔moving toggle. `_sync_hard_mode_visuals()` is called from `_on_move`, `_on_animation_tick`, and `_toggle_hard_mode` so fog/ball/light track the moving state on every leg start and stop.

## Boundaries & Constraints

**Always:** `adapters/tkinter/player/` never imports `adapters/storage/` directly (AD-9). All HARD presentational logic stays adapter-side; the session only carries the `hard_mode` boolean and never imports `tkinter` (AD-1). The `GameplayScreen` `.after()` loops and toplevel focus guard stay intact — the HARD toggle shares the same guard, and `_sync_hard_mode_visuals()` never schedules work. The status-light colors are read through the `application/` service (`read_hard_mode_ready_color`/`read_hard_mode_moving_color`), never via a direct settings call in the screen. Leave the HARD control's location/state in a shape that won't block later ⓘ-anchor wiring (FR-28/Story 5.5) — but do **not** implement the explainer (Epic 5 scope, `epic-2-context.md` line 60).

**Block If:** Nothing needs human input — the session-scoped non-persistence, dual-key color model, `h` shortcut, fog z-order, two-state (ready/moving) light, and the Settings-UI deferral are all documented decisions below.

**Never:** No Settings color-picker UI (no story owns it yet — `SettingsWindow` stays its Story 1.8/1.11 placeholder; AC-4 is exercised at the repository seam + read-on-activation, see Design Notes). No timer/timeout (2.9), no confirmation prompts (2.10), no appearance/theme work (2.11). No FR-28 first-activation explainer (Story 5.5). No legacy "impossible"/"change direction" light states and no multi-color moving palette — the design system defines exactly **ready/moving** (DESIGN.md `status-light-default`; FR-14). No change to `PlayerSession`'s existing `mode`/`speed`/`level`/`difficulty`/leg fields, to `attempt_move`/`Duration`, to `MazeCanvas.redraw_structure`'s contract, or to `composition_root.py`/`screen.py`. No change to `tick()` semantics. No redraw on every animation sub-step — `_sync_hard_mode_visuals()` only toggles canvas item `state`, never redraws structure. No fade/animation on fog show/hide (instant, per DESIGN.md `components.fog-overlay.animation: none`).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Initial mount | Fresh session, HARD off | No fog (hidden), ball rendered, status light hidden (`pack_forget`), HARD button inactive | No error |
| HARD activated at rest | `_toggle_hard_mode` | `session.hard_mode == True`; button active; status light shown with the **ready** color + "Ready" label; ball still rendered; no fog | No error |
| HARD active, movement starts | `_on_move` starts a leg | `set_hard_mode_moving(True)`: ball `state="hidden"`, fog `state="normal"` (covers corridor/ball plane; walls/markers crisp above) | No error |
| HARD active, movement stops | leg commits, `moving_direction` becomes `None` | `set_hard_mode_moving(False)`: fog `state="hidden"` (instant, no fade), ball `state="normal"`; status light switches to the **moving→ready** color on the same tick | No error |
| HARD active, ball moving | mid-leg | Status light shows the **moving** color + "Moving" label | No error |
| HARD deactivated mid-session | `_toggle_hard_mode` while a leg is in flight | `session.hard_mode == False`; button inactive; status light hidden; the in-flight leg's ball is shown again on the next `_on_animation_tick` (moving-state predicate includes `hard_mode`) | No error |
| Color setting changed | `write_hard_mode_ready_color`/`write_hard_mode_moving_color`, then next HARD activation or state sync | Both ready and moving states use the newly-read values; no literal/`"blue"` anywhere; toggle keeps working (AC-4) | SettingNotFound/Corrupt/invalid → reader falls back to the screen-supplied theme default |
| HARD toggle once solved | `_toggle_hard_mode` with `solved=True` | No-op — `set_hard_mode` returns the session unchanged (Story 2.5/2.6/2.7 convention) | No error |
| Input while focus is in another toplevel | HARD button clicked/`h` pressed while `SaveMazeDialog` has focus | No-op — HARD state unchanged behind the dialog (shared toplevel focus guard) | No error |
| Screen destroyed mid-session | `.after()` jobs pending, HARD active | Existing tick/animation cancellation + `bind_shortcut` cleanup on `<Destroy>` unchanged | No error |
| Fog z-order | any wall redraw via `redraw_structure` | New wall items stack above the pre-existing fog item (fog created first) — structure stays crisp on top | No error |

## Code Map

- `src/labyrinthes/application/player_session.py` — **UPDATE**:
  - `PlayerSession`: add `hard_mode: bool` field (default `False` in `start_session`).
  - `set_hard_mode(session, enabled: bool) -> PlayerSession` — **NEW**, mirroring `set_mode`/`set_speed` (lines 241–262): no-op once solved; otherwise `replace(session, hard_mode=enabled)`. **No** visibility re-init — HARD is presentational. Update the module docstring (Story 2.8 paragraph) and `__all__`.
- `src/labyrinthes/application/settings_keys.py` — **UPDATE**: add `HARD_MODE_READY_COLOR = "hard_mode_ready_color"` and `HARD_MODE_MOVING_COLOR = "hard_mode_moving_color"` (the two-state counterparts of legacy `color mode hard ready` / `colors mode hard moving` — `Parametres_defaut.csv` lines 22–23).
- `src/labyrinthes/application/hard_mode_settings.py` — **NEW**, mirroring `movement_settings.py`:
  - `read_hard_mode_ready_color(settings, default: str) -> str` — **NEW**: reads `HARD_MODE_READY_COLOR` in `SettingsScope.GAME`; falls back to `default` on `SettingNotFoundError`/`SettingCorruptError`/`TypeError`/non-string stored value. Never raises, never writes on read. The `default` is the screen-supplied theme default (`colors.accent` for ready, `colors.exit` for moving — DESIGN.md `status-light-default`).
  - `read_hard_mode_moving_color(settings, default: str) -> str` — **NEW**: same, for `HARD_MODE_MOVING_COLOR`.
  - `write_hard_mode_ready_color(settings, color: str) -> None` / `write_hard_mode_moving_color(settings, color: str) -> None` — **NEW**: persist via `settings.set(SettingsScope.GAME, ...)`. (Unused by this story's screen — see the AC-4/Settings-UI deferral in Design Notes — but they are the tested persistence seam the future color picker calls.)
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` — **UPDATE**: append `Keybinding("toggle_hard_mode", "Toggle HARD mode", "h")` to `KEYBINDINGS` (keeps the table collision-free; `test_keybindings.py` re-checks uniqueness).
- `src/labyrinthes/adapters/tkinter/player/maze_canvas.py` — **UPDATE**:
  - Constructor: call `self._draw_fog(colors)` **before** `_draw_walls`/markers/ball — a `create_rectangle(0, 0, width, height, fill=colors.bg, outline="", tags=("fog",), state="hidden")` spanning the full canvas. Creating it first guarantees it sits above the corridor background but below every wall/marker/ball item even after later `redraw_structure` calls recreate walls (load-bearing z-order — see Design Notes).
  - `set_hard_mode_moving(moving: bool) -> None` — **NEW**: `self.itemconfigure("fog", state="normal" if moving else "hidden")` and `self.itemconfigure(self._ball_id, state="hidden" if moving else "normal")`. Callable repeatedly; idempotent. When HARD is off, the screen simply never calls it with `True`.
- `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — **UPDATE**:
  - Imports: alias `set_hard_mode as session_set_hard_mode` (matching the `session_set_*` import block) and the `read_hard_mode_*`/`write_hard_mode_*` functions from `application/hard_mode_settings.py`.
  - `_build_hud`: after the Pos chip, add a status light — a small frame holding a 10px `tk.Canvas` (10×10, with a filled `create_oval`) + a `Ready`/`Moving` label (`TYPOGRAPHY.label`, `colors.ink_soft`), mirroring the mockup `.status-wrap`. Store `self._status_light_canvas`/`self._status_label`; start hidden (`pack_forget`).
  - `_build_sidebar`: add a "Mode" group (label + a `ToolButton` "HARD", `shortcut=keybinding("toggle_hard_mode").display`, `command=self._toggle_hard_mode`) between the "Movement" and "Levels" groups.
  - `_hard_mode_colors() -> tuple[str, str]` — **NEW**: `(read_hard_mode_ready_color(self._settings_repository, colors.accent), read_hard_mode_moving_color(self._settings_repository, colors.exit))` with `colors = colors_for(self._theme)`. Never caches — this is the AC-4 freshness mechanism.
  - `_toggle_hard_mode() -> None` — **NEW**: focus-guard with `_toplevel_has_focus()`; `new = not self._session.hard_mode`; `self._session = session_set_hard_mode(self._session, new)`; `self._mode_hard_button.set_active(new)`; `_sync_hard_mode_visuals()`.
  - `_sync_hard_mode_visuals() -> None` — **NEW**: `moving = self._session.hard_mode and self._session.moving_direction is not None`; `self._maze_canvas.set_hard_mode_moving(moving)`; if HARD off → `pack_forget` the status light; if on → `pack` it and set the oval fill + label from `_hard_mode_colors()` (`moving_color` when moving else `ready_color`; label `"Moving"`/`"Ready"`).
  - Call `_sync_hard_mode_visuals()` from `_on_move` (after `_sync_visibility`) and `_on_animation_tick` (after `_sync_visibility`, before the solved branch) so the fog/ball/light track leg start and stop — including the rest-after-solve case where `moving_direction` is `None`.
  - Bind the shortcut: `hard_kb = keybinding("toggle_hard_mode"); bind_shortcut(self, hard_kb, self._toggle_hard_mode)` (next to the `toggle_movement_mode` binding, lines 193–194).
- `tests/application/test_player_session.py` — **UPDATE**: `set_hard_mode` sets the field; no-op once solved. Mirror the `set_mode` tests.
- `tests/application/test_hard_mode_settings.py` — **NEW**, mirroring `test_movement_settings.py`: defaults on unset/corrupt/non-string; valid stored values round-trip; independent fallback (ready set, moving unset → moving defaults); never-writes-on-read; `write_*` persists in the GAME scope.
- `tests/application/test_settings_keys.py` — **UPDATE**: add `HARD_MODE_READY_COLOR` and `HARD_MODE_MOVING_COLOR` to `_KEY_NAMES`. (Note: `MOVEMENT_MODE`/`MOVEMENT_SPEED` are also absent from `_KEY_NAMES` today — a pre-existing gap, not this story's concern; do not add them here.)
- `tests/adapters/tkinter/common/test_keybindings.py` — **UPDATE**: `toggle_hard_mode` is registered on `"h"`, `display == "H"`, `event == "<KeyPress-h>"`, and `h` collides with no other key.
- `tests/adapters/tkinter/player/test_maze_canvas.py` — **UPDATE**: fog item exists, spans the canvas, hidden by default, and stacks **below** the first wall item in `canvas.find_all()` order; `set_hard_mode_moving(True)` shows fog + hides ball (`itemcget(..., "state")`); `set_hard_mode_moving(False)` restores both; repeated calls are idempotent.
- `tests/adapters/tkinter/player/test_gameplay_screen.py` — **UPDATE**: HARD toggle flips `session.hard_mode`, activates the button, and shows the status light with the **ready** color; moving hides the ball (`canvas.itemcget(ball, "state") == "hidden"` mid-leg via `_on_move` without `_settle`) and shows fog; rest restores ball/fog and flips the light to **moving→ready** on the same settle; `write_*` then next `_toggle_hard_mode`/sync re-colors both states from the new values (AC-4); focus-guard no-op; no-op once solved; light hidden while HARD off.

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/application/player_session.py` — add `hard_mode` field + `set_hard_mode` (no-op once solved); update docstring + `__all__`
- [x] `src/labyrinthes/application/settings_keys.py` — add `HARD_MODE_READY_COLOR`/`HARD_MODE_MOVING_COLOR`
- [x] `src/labyrinthes/application/hard_mode_settings.py` — never-raises readers (with screen-supplied default) + writers
- [x] `src/labyrinthes/adapters/tkinter/common/keybindings.py` — `toggle_hard_mode` on `h`
- [x] `src/labyrinthes/adapters/tkinter/player/maze_canvas.py` — fog item (created first, hidden) + `set_hard_mode_moving`
- [x] `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — "Mode" group HARD button, HUD status light, `_toggle_hard_mode`/`_sync_hard_mode_visuals`/`_hard_mode_colors`, `h` binding, sync calls in `_on_move`/`_on_animation_tick`
- [x] `tests/application/test_player_session.py` — `set_hard_mode` coverage
- [x] `tests/application/test_hard_mode_settings.py` — readers/writers coverage
- [x] `tests/application/test_settings_keys.py` — add the two HARD keys
- [x] `tests/adapters/tkinter/common/test_keybindings.py` — `toggle_hard_mode` on `h`, collision-free
- [x] `tests/adapters/tkinter/player/test_maze_canvas.py` — fog hidden-by-default, z-order, `set_hard_mode_moving` toggles
- [x] `tests/adapters/tkinter/player/test_gameplay_screen.py` — toggle/light/AC-4/focus-guard/solved coverage

**Acceptance Criteria:**
- [x] Given HARD active + ball moving → ball not rendered (canvas `state="hidden"`), fog scrim shown above corridor/ball plane, below wall-bars/markers
- [x] Given ball comes to rest → fog disappears instantly (no fade), ball renders normally
- [x] Given status light ready vs. moving → color follows the configured HARD-mode color in both states (same read source)
- [x] Given a color-setting change → next HARD use shows the new color in both states without breaking the ready↔moving toggle (no literal color anywhere)

### Review Findings

- [x] [Review][Patch] Per-sub-step sync does redundant work when it should fire only on leg start/stop [src/labyrinthes/adapters/tkinter/player/gameplay_screen.py:635] — `_sync_hard_mode_visuals()` runs from `_on_animation_tick` on every sub-step; when HARD is off it still does 2 `itemconfigure` + `pack_forget` per tick, and when HARD is on + moving it rebuilds `colors_for()` and issues 2 repository file reads (`JsonSettingsRepository.get` re-reads disk, no cache) per sub-step — contradicting the Design Note "fires only on leg start/stop — never per sub-step". Fix: early-return when `hard_mode` is off, and only re-read colors when the moving-state actually changed (or once per leg). — fixed: `_sync_hard_mode_visuals` now caches the last `(hard_mode, moving)` state and returns a tuple compare when unchanged, so the per-tick path only does work on leg start/stop and toggle transitions.
- [x] [Review][Patch] Stored non-color string reaches `itemconfigure(fill=...)` and raises `TclError` [src/labyrinthes/application/hard_mode_settings.py:38] — `_read_color` returns any `str` without validating it is a usable color, so a stored `""`/`"garbage"` passes the `isinstance` check and crashes the render, breaking the documented "invalid → theme default" fallback (I/O matrix). Fix: validate the string looks like a color (e.g. hex pattern) before returning it. — fixed: `_read_color` now falls back to `default` unless the stored value is a `#`-prefixed hex color in Tk's supported lengths (3/6/9/12 digits, verified against a live `Canvas.itemconfigure`); named colors are also rejected since they can't be validated without `tkinter` (AD-1) and the theme/color-picker are hex-based. Tests added for the fallback and for valid hex round-tripping.
- [x] [Review][Patch] Post-solve HARD toggle flips the button's active flag although the session is unchanged [src/labyrinthes/adapters/tkinter/player/gameplay_screen.py:632] — `_toggle_hard_mode` calls `set_active(new)` unconditionally; once solved `session_set_hard_mode` is a no-op, so the button can show "active" while `session.hard_mode` stays `False`. `_toggle_mode` avoids this by syncing the button from the session (`_sync_mode_button` reads `self._session.mode`); the HARD button should likewise derive from the session (`set_active(self._session.hard_mode)`). The Dev Agent Record's "mirrors _toggle_mode" justification is inaccurate — `_toggle_mode` never diverges this way. — fixed: `_toggle_hard_mode` now calls `set_active(self._session.hard_mode)`; `test_hard_mode_toggle_is_a_no_op_once_solved` asserts the button stays inactive.
- [x] [Review][Patch] Test gaps: no screen-level assertion that pressing `h` invokes the toggle, and no test toggling HARD **on** mid-leg [tests/adapters/tkinter/player/test_gameplay_screen.py:1449] — `test_hard_mode_shortcut_h_is_registered` only asserts a binding exists, never that it fires `_toggle_hard_mode`; mid-leg coverage only exercises deactivation (off), not activation while a leg is in flight. — fixed: the screen now stores the `bind_shortcut`-returned handler as `_hard_mode_handler` and `test_hard_mode_shortcut_h_invokes_the_toggle` fires it (a synthetic key can't reach `bind_all` on a withdrawn root); added `test_enabling_hard_mode_mid_leg_hides_the_ball_and_shows_the_fog_immediately`.

## Design Notes

**Z-order is load-bearing — create the fog first.** DESIGN.md's HARD-mode note and its `.memlog` clarification pin the scrim *below* wall-bars/markers and *above* the corridor/ball plane, so walls/entry/exit stay crisp. On a `tk.Canvas`, items draw in creation order and later items stack on top, so the fog must be the **first** item created: every wall-bar, marker, and the ball then sit above it, and `redraw_structure`'s future wall recreations keep stacking above it. The canvas background (the corridor plane, `colors.corridor`) is beneath all items, so a first-created rectangle still covers it. The ball being *above* the fog is harmless because during HARD movement it is `state="hidden"` — genuine non-render (EXPERIENCE.md line 57, mockup line 379), not occlusion.

**Opacity has no Tk alpha.** DESIGN.md specifies `opacity: 0.85` (`components.fog-overlay`), but Tk `Canvas` items have no per-item alpha channel (only a `stipple` pattern). The faithful-enough approximation is a **solid `colors.bg` fill** for the fog item — the scrim reads as a translucent veil over the corridor because the corridor is the lightest/darkest surface, and the exact hex is still the design token. No fade/animation (instant `state` toggle, per `animation: none`). Document this limitation in the `_draw_fog` docstring.

**Dual-key color model fixes the legacy bug by construction.** Legacy hardcoded the ready color (`change_voyant_mode_hard("ready", "blue")`, line 1041) while moving came from a configurable setting — so changing the setting silently broke the return-to-ready toggle. This story persists **both** states as separate `game`-scoped keys and the screen re-reads **both** on every activation/state sync (`_hard_mode_colors()`); no color literal ever appears in screen/canvas code. Changing a setting therefore re-colors ready *and* moving consistently and can't break the toggle (AC-4, FR-14 consequence, addendum line 40). Defaults (`accent`/`exit`) come from DESIGN.md `status-light-default` via the screen's `colors_for(self._theme)` and are passed into the readers as parameters, keeping `application/` theme-agnostic (AD-1).

**HARD on/off is session-scoped, not persisted.** The epic context's game-scoped settings list (`epic-2-context.md` line 50) names "HARD-mode color" but no HARD-mode on/off; legacy `mode_hard` was a runtime boolean (`init_mode_hard`, line 225). So the toggle lives on `PlayerSession` (like Level/Difficulty/mode/speed) and a fresh mount starts HARD-off. Only the two colors persist. Do not add a `game`-scoped `HARD_MODE` key.

**Two-state light (ready/moving), not the legacy three.** The legacy light had ready/moving/impossible plus a multi-color moving palette for Smooth direction changes. FR-14, DESIGN.md `status-light-default`, and the mockup's `.status-light` define exactly ready/moving; the "impossible" and direction-change states are dropped by design. The status light shows only while HARD is on (pack/pack_forget), and its label reads `Ready`/`Moving`.

**Settings color-picker UI is deferred — AC-4 lives at the repository seam.** No story in Epics 1–5 owns a Settings window color picker for the HARD colors (`SettingsWindow` remains the Story 1.8/1.11 "Appearance coming soon" placeholder, `settings_window.py`). This story therefore ships the readers/writers + read-on-activation (`_hard_mode_colors()`), and AC-4 is exercised by tests that `write_*` a new color and assert the next activation/sync re-colors both states. The writers are tested but not yet called by any UI — they are the documented persistence seam the future color picker consumes (log a deferred-work note). The HARD control keeps a stable location/state (sidebar "Mode" group) so Story 5.5's ⓘ-anchor can attach later (`epic-2-context.md` line 60).

**Placement & interaction.** The HARD toggle is a "Mode" sidebar group (`ToolButton`, kbd-tag `H`, active-styled when on — no `ToolButtonGroup`, it's an independent toggle like the Smooth button) bound to the `h` shortcut via `bind_shortcut`, exactly like `toggle_movement_mode`; it shares the Story 2.5/2.6/2.7 toplevel focus guard. The status light sits at the end of the HUD row per the mockup `.status-wrap`. `_sync_hard_mode_visuals` is driven by `session.moving_direction` (not animation sub-steps), so it fires only on leg start/stop — never per sub-step — and never redraws structure.

## Previous Story Intelligence

- **Story 2.7 (difficulty)** is the template for `set_hard_mode`: `set_mode`/`set_speed`/`set_level`/`set_difficulty` all follow "no-op once solved, `replace()` on a frozen dataclass, session-scoped, never persisted"; `_toplevel_has_focus()` guarding, the `session_set_*` import-alias block, and the `_settle()` test-driver convention all carry over. Its "Never" line explicitly reserved "HARD-mode fog/status light" for this story.
- **Story 2.5 (movement)** supplies the sidebar `ToolButton` pattern, the `bind_shortcut` wiring (mode toggle on `m`), and the `.after()` reschedule/cancel conventions this story extends with `_sync_hard_mode_visuals` calls.
- **Story 2.4/2.6** own `MazeCanvas` — this story only *adds* the fog item and `set_hard_mode_moving`; it must not disturb `redraw_structure`'s wall/contour/idempotence contract or `set_ball_position`/`set_ball_offset`.
- **Regression watchlist:** the `GameplayScreen(...)` construction sites in `test_gameplay_screen.py` (all pass `settings_repository=`); the keybinding-uniqueness test (new `h` must not collide); the AD-9 import-boundary test (player never imports storage); `MazeCanvas` wall-count/coords tests (fog is a separate tag, must not be counted as a wall or shift `find_all` assertions); the `_on_animation_tick` solved-branch ordering (sync before the solved return keeps the ball visible at rest on solve).

## Git Intelligence

- Working branch: `epic-2-play-a-maze-game-player` (epic-2 accumulation branch, current HEAD `d4d6a25` = Story 2.7 merge). **Never commit directly to it** — create `story-2-8-hard-mode-invisible-ball-fog-overlay-status-light` from it, merge story → epic via `git merge --no-ff` when done; epic → `rewrite` only via PR once the whole epic is done.
- Mirror the per-story rhythm: `feat(player): ...` (feature) → `test(player): ...` (tests) → `docs(planning): record Story 2.8 ...` (status + deferred-work note) → `Merge story-2-8-... into epic-2-... (story 2.8)`. Conventional Commits in English, story number in the subject (`(story 2.8)`).
- `uv.lock` is untracked — leave it alone.

## Latest Technical Information

No new external dependencies: the stack is pinned in `pyproject.toml` (Python ≥3.12, tkinter, pytest ≥8.0, ruff ≥0.6, hatchling). Everything here uses stdlib (`enum`, `dataclasses`, `functools`, `tkinter`) and the existing `domain/`/`application/`/`common/` types — no web research was needed. The one platform fact this story documents (Tk `Canvas` has no item alpha; `state="hidden"` is the non-render mechanism) is standard Tk behavior, verified against the existing `MazeCanvas` implementation.

## Verification

**Commands:**
- `ruff check .` — expected: no new lint violations (line-length 100, rules `E, F, I, UP, B, SIM`; no comments unless asked)
- `ruff format --check .` — expected: no formatting diffs
- `pytest` — expected: full suite green, including the new `set_hard_mode`/`hard_mode_settings`/fog/status-light tests

**Regression watchlist:** `ToolButton` active-styling tests (the HARD button must not disturb them); `MazeCanvas` wall-count/coords/idempotence tests (fog is additive); `test_keybindings.py` uniqueness (new `h`); `test_settings_keys.py` (two new names added); `_on_animation_tick` solved-path (ball visible at rest); the AD-9 import-boundary test; the `GameplayScreen` construction sites.

## Project Structure Notes

- All HARD state lives on `PlayerSession` (`application/`); only rendering/input/status-light styling lands in `adapters/` (`player/maze_canvas.py` + `player/gameplay_screen.py`); the color persistence lives in a new `application/hard_mode_settings.py` + two keys in `application/settings_keys.py`. No new screen, no new port, no domain change.
- Naming is English throughout (NFR4); maze data (`0/1/2/3`) untouched; the two new settings keys use the existing `snake_case` key convention.
- No `tkinter`/`adapters` import may appear in `player_session.py`, `settings_keys.py`, or `hard_mode_settings.py` (AD-1, AD-9).

## References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 2.8 ACs (lines 648-670)]
- [Source: `_bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/prd.md` — FR-14 (lines 164-168); FR-28 explainer (lines 148-153)]
- [Source: `_bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/addendum.md` — hardcoded HARD-color bug (line 40)]
- [Source: `_bmad-output/implementation-artifacts/epic-2-context.md` — HARD-mode behavior (line 36), game-scoped settings list (line 50), UX patterns incl. fog/status-light (lines 56-57), ⓘ-anchor/FR-28 note (line 60), cross-story dependency (line 68)]
- [Source: `_bmad-output/planning-artifacts/ux-designs/ux-Labyrinthes-2026-08-04/DESIGN.md` — `components.status-light`/`fog-overlay`/`status-light-default` (lines 231-243); HARD-mode fog+status-light note (line 339)]
- [Source: `_bmad-output/planning-artifacts/ux-designs/ux-Labyrinthes-2026-08-04/EXPERIENCE.md` — `ball` non-render during HARD movement (line 57), HARD-mode fog overlay + status light component (line 67), State Patterns (line 84), UJ-C (lines 141-151)]
- [Source: `_bmad-output/planning-artifacts/ux-designs/ux-Labyrinthes-2026-08-04/mockups/key-player-gameplay.html` — `.status-wrap`/`.status-light`/`.status-label` (172-174), `.fog` z-index (191-193), HARD-mode alternate state incl. status light + missing ball + Mode/HARD button (333-386)]
- [Source: `Labyrinthes_copy.py` (legacy, read-only) — `init_mode_hard` (224-232), `mode_HARD` toggle + `h` binding (234-241, 335-336), `change_voyant_mode_hard` incl. the `"blue"` hardcode (243-256), movement firing `change_voyant_mode_hard("ready", "blue")` (1039-1041)]
- [Source: `Autres/Parametres_defaut.csv` (legacy) — `color mode hard ready` / `colors mode hard moving` (lines 22-23)]
- [Source: `src/labyrinthes/application/player_session.py` (`set_mode`/`set_speed` templates, lines 241-262), `application/settings_keys.py`, `application/movement_settings.py`, `adapters/tkinter/common/keybindings.py` (canonical table, `bind_shortcut`), `adapters/tkinter/player/maze_canvas.py` (constructor + `redraw_structure`), `adapters/tkinter/player/gameplay_screen.py` (`_build_hud`, `_build_sidebar`, `_on_move`, `_on_animation_tick`, focus guard), `adapters/tkinter/common/hud_chip.py`, `common/tokens.py` (`colors.bg`/`accent`/`exit`, `TYPOGRAPHY.label`), `common/settings_window.py` (placeholder)]

## Dev Agent Record

### Agent Model Used

opencode/deepseek-v4-flash-free

### Debug Log References

- 2026-08-14: Story 2.8 developed on branch `story-2-8-hard-mode-invisible-ball-fog-overlay-status-light` (from `epic-2-play-a-maze-game-player`, HEAD `d4d6a25`). All red-green-refactor cycles run: application layer (session + settings) RED confirmed, then GREEN; keybinding + canvas fog RED confirmed, then GREEN; gameplay screen RED confirmed (11 new tests failing before implementation), then GREEN (70 pass). Full suite 642 passed at completion. No HALT conditions triggered; no new dependencies; no config missing.
- 2026-08-14: One test-side alignment: the screen-level "no-op once solved" test asserts the frozen session/light rather than the HARD button's active flag -- `_toggle_hard_mode` mirrors `_toggle_mode`'s accepted cosmetic post-solve button flip (documented in `deferred-work.md` Story 2.5); `session_set_hard_mode` itself stays a strict no-op once solved.

### Completion Notes List

- Implemented HARD mode end-to-end per the story spec: session-scoped `hard_mode` flag + `set_hard_mode` (no-op once solved, no visibility re-init) in `application/player_session.py`; two `game`-scoped color keys in `application/settings_keys.py`; a new never-raises `application/hard_mode_settings.py` (readers take a screen-supplied theme default, never write on read; writers are the tested persistence seam the future color picker consumes); `toggle_hard_mode` keybinding on `h` in `common/keybindings.py`; `MazeCanvas` fog item (created *first* for load-bearing z-order, `colors.bg` solid-fill scrim per the documented no-alpha Tk limitation, hidden by default) + idempotent `set_hard_mode_moving(moving)` toggling fog/ball `state`; `GameplayScreen` "Mode" sidebar group with a single HARD `ToolButton`, a HUD status light (10px round light + Ready/Moving label, hidden unless HARD active), `_toggle_hard_mode` (focus-guarded), `_sync_hard_mode_visuals` (driven by `session.moving_direction`, wired into `_on_move`/`_on_animation_tick` before the solved branch), and `_hard_mode_colors` (fresh read of both states every sync -- AC-4 mechanism). No color literal enters the codebase: the legacy `"blue"` ready-color bug is fixed by construction. No Settings color-picker UI (explicitly deferred; logged in `deferred-work.md`). HARD on/off is session-scoped, never persisted; the `h` key is collision-free (keybinding table test).
- All four acceptance criteria satisfied and pinned by tests: ball genuinely not rendered (`canvas.itemcget(ball, "state") == "hidden"`) + fog below wall-bars while moving; instant fog hide + ball restore at rest; both light states read the configured color from the same source; a written color change recolors both states on next activation/sync without breaking the ready↔moving toggle.

### File List

- This spec: `_bmad-output/implementation-artifacts/spec-2-8-hard-mode-invisible-ball-fog-overlay-status-light.md` (tasks checked, status -> review, Dev Agent Record filled)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — 2-8: ready-for-dev -> in-progress -> review
- `_bmad-output/implementation-artifacts/deferred-work.md` — HARD color-picker Settings-UI deferral note appended
- `src/labyrinthes/application/player_session.py` — `hard_mode` field + `set_hard_mode`
- `src/labyrinthes/application/settings_keys.py` — `HARD_MODE_READY_COLOR`/`HARD_MODE_MOVING_COLOR`
- `src/labyrinthes/application/hard_mode_settings.py` — readers/writers (NEW)
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` — `toggle_hard_mode` on `h`
- `src/labyrinthes/adapters/tkinter/player/maze_canvas.py` — fog item + `set_hard_mode_moving`
- `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — Mode group, status light, toggle/sync/colors helpers, `h` binding
- `tests/application/test_player_session.py` — `set_hard_mode` coverage
- `tests/application/test_hard_mode_settings.py` — readers/writers coverage (NEW)
- `tests/application/test_settings_keys.py` — the two HARD keys
- `tests/adapters/tkinter/common/test_keybindings.py` — `toggle_hard_mode` on `h`, collision-free
- `tests/adapters/tkinter/player/test_maze_canvas.py` — fog z-order / default / `set_hard_mode_moving` toggles
- `tests/adapters/tkinter/player/test_gameplay_screen.py` — toggle/light/AC-4/focus-guard/solved coverage

## Review Triage Log

- 2026-08-14 — Code review (17 blind-hunter findings, 1 edge-case-hunter; verification-gap layer returned empty and was marked failed; acceptance auditor: all 4 ACs satisfied + 3 minor non-AC notes). 4 findings classified `patch`, all applied: `_sync_hard_mode_visuals` now caches the `(hard_mode, moving)` state and early-returns on unchanged sub-steps (no per-tick `itemconfigure`/disk reads); `_read_color` validates stored values are Tk-usable hex (3/6/9/12 digits) and falls back to the theme default otherwise; `_toggle_hard_mode` derives the button's active flag from the session (no post-solve phantom "active"); screen stores the `bind_shortcut`-returned handler + new `h`-invocation and mid-leg-activation tests. 12 findings dismissed (incl. the non-defaulted `PlayerSession.hard_mode` and legacy named-color concerns); 0 decision-needed, 0 deferred. Full suite 646 passed; `ruff check`/`ruff format --check` clean on `src/`/`tests/`. Status `review` -> `done`.

## Change Log

- 2026-08-14: Implemented Story 2.8 (HARD mode — invisible ball, fog overlay, status light). Added session `hard_mode` + `set_hard_mode`; two `game`-scope color keys + new `hard_mode_settings` readers/writers; `h` keybinding; canvas fog item + `set_hard_mode_moving`; screen Mode-group toggle, HUD status light, and fresh-read color sync. Verified: `ruff check src/labyrinthes tests`, `ruff format --check`, full `pytest` (642 passed). Status -> review; deferred-work note logged.
- 2026-08-14: Code review complete — all 4 `patch` findings applied (state-cached `_sync_hard_mode_visuals`, hex-validating `_read_color`, session-derived HARD button state, shortcut-invocation + mid-leg-activation tests), 12 dismissed, 0 deferred. Full suite 646 passed; `ruff` clean. Status `review` -> `done`.
