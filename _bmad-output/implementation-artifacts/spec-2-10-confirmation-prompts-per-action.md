---
title: 'Story 2.10: Confirmation prompts per action'
type: 'feature'
created: '2026-08-17'
status: 'ready-for-dev'
baseline_commit: '5ce301d'
context: ['_bmad-output/implementation-artifacts/epic-2-context.md']
---

# Story 2.10: Confirmation prompts per action

Status: ready-for-dev

## Story

As a player,
I want to enable/disable, per action, a confirmation prompt before it applies,
So that I don't get interrupted by dialogs I don't want, while keeping guardrails for actions I do.

## Acceptance Criteria

1. **Given** switching mazes, restarting, changing Level, or invalid input, **when** the corresponding confirmation setting is on, **then** a confirm prompt appears before the action applies.
2. **Given** the same actions, **when** the corresponding setting is off, **then** the action applies immediately, with no prompt.
3. **Given** each action's confirmation setting, **when** changed in Settings, **then** it persists via the game-scoped `SettingsRepository` and takes effect without an app restart.

## Intent Contract

### Problem

Four actions in the Player need per-action confirmation guardrails — switching mazes, restarting, changing Level, and invalid input — each toggleable independently in Settings (FR-17, `epic-2-context.md:38`). The legacy app had all four as separate CSV flags with `messagebox.askquestion` prompts (`Labyrinthes_copy.py:132/140/155`, `2015-2048`; `Autres/Outils.py:124`), but nothing reusable survives from it — the rewrite has **no confirmation-prompt dialog widget** in `common/` yet (AD-11 names "confirmation-prompt dialogs" as a shared component to build, `ARCHITECTURE-SPINE.md:131-132`), the **`SettingsWindow` is still the Story 1.8/1.11 placeholder** (one "Appearance" category, "coming soon" content, no `settings_repository` — so AC-3 has no UI to change a setting through), and only **Player** currently receives a `settings_repository` (Home/Builder `mount()` signatures don't have one, so Settings can't read/write game-scoped values from those screens).

The **entire** story is new surface: no AC is already green.

### Approach

Four layers, mirroring the established per-story seams:

- **Persistence** — four `game`-scoped boolean keys in `settings_keys.py` plus a new never-raises `application/confirmation_settings.py` (mirrors `movement_settings.py`/`hard_mode_settings.py`): `read_confirm_switch_maze`, `read_confirm_restart`, `read_confirm_level_change`, `read_confirm_invalid_input` (all `-> bool`) and the matching `write_confirm_*`. Each reader falls back to its documented default on `SettingNotFoundError`/`SettingCorruptError`/`TypeError` and on any stored value that isn't an actual `bool` (`type(value) is bool` — rejects `1`/`0`/`"true"`/`"false"`/`None`, the strictness precedent set by `_read_color` in Story 2.8). Defaults carry the legacy CSV values forward (`Autres/Parametres_defaut.csv`): switch = **OFF** (lines 15-16), restart = **ON** (line 17), level change = **OFF** (lines 18-21; the legacy "max" flag defaulted on but the per-level flags collapse into one unified toggle and the majority default is off), invalid input = **ON** (line 7).
- **Dialog widget** — a new `common/confirm_dialog.py` `ConfirmDialog` (AD-11's "confirmation-prompt dialogs" component, the first one): a themed `Toplevel` with the message, a primary Confirm pill, and an optional Cancel pill; `<Return>` confirms, `<Escape>`/WM-close cancels, initial focus on the Confirm pill (NFR6). **Non-modal** (no `grab_set()`) per the codebase-wide dialog convention (`SettingsWindow`/`SaveMazeDialog`/`GenerateRandomDialog` all non-modal; a `grab_set()` under the withdrawn `tk_root` test fixture would raise `TclError: grab failed: window not viewable`). Because it can't block input, every gated action carries an explicit open-dialog guard (`_confirm_dialog is not None` → no-op) so a second trigger never stacks a second dialog on top — see Design Notes.
- **Settings UI** — `SettingsWindow` gains a required, keyword-only `settings_repository: SettingsRepository` and its first real content (AC-3's "changed in Settings" surface): the category nav becomes clickable/keyboard-operable (`takefocus=True` labels, `<Button-1>`/`<Return>`/`<Space>`, active category in accent foreground — NFR6), a new "Confirmation" category holds four themed `tk.Checkbutton` rows (one per action), each initialised from `read_confirm_*` and persisted via `write_confirm_*` on toggle. The "Appearance" category keeps its placeholder. This is the first real Settings content; it's also the first consumer of the deferred `movement`/`hard_mode`/`time_limit` writers' pattern as a *reader+writer* pair.
- **Wiring + gating** — thread `settings_repository` into Home and Builder `mount()` as a required keyword-only port (same shape as Player, Story 2.1/2.2) via `functools.partial` in `composition_root.py`, so every screen's `open_settings()` passes it to `SettingsWindow`. Gate the four action surfaces: `ClassicMazeGallery._on_previous/_on_next/_on_restart/_on_jump` (valid branch) behind `confirm_switch_maze`, its invalid-jump branch behind `confirm_invalid_input` (an OK-only alert — legacy `alerte mauvaise entree`); `GameplayScreen._cycle_level` behind `confirm_level_change`, `_restart_run` behind `confirm_restart`. **AC-3 ("takes effect without an app restart") is structural**: `JsonSettingsRepository.get()` re-reads its file on every call (`json_settings_repository.py`), and the gated methods call `read_confirm_*` *fresh at action time* (like `read_hard_mode_moving_color` in Story 2.8) — no observer, no restart, no caching.

## Boundaries & Constraints

**Always:** `adapters/tkinter/player/` and `adapters/tkinter/common/` never import `adapters/storage/` directly (AD-9) — the screen reaches settings only through `application/` (`read_confirm_*`, never a raw `settings.get`). `confirmation_settings.py` imports no `tkinter` and nothing from `adapters/` (AD-1). `ConfirmDialog` lives in `common/` (AD-11) and imports only `common/` widgets/tokens — never a screen. Every gated action reads its setting **at action time**, never cached at mount (that is exactly what makes AC-3 true). The gallery invalid-jump revert (restore the entry text) happens immediately whether or not the alert shows — the alert is informational, not a gate. The `_toplevel_has_focus()` guard in `gameplay_screen.py` stays exactly as-is: while a `ConfirmDialog` (a separate toplevel) holds focus it already returns `False`, so keyboard shortcuts no-op behind the dialog for free. The open-dialog guard (`_confirm_dialog is not None`) is what stops *clicks* (which move focus back to the screen) from stacking dialogs. `ConfirmDialog` registers **no** keybinding in the canonical table (Story 1.10) — `<Return>`/`<Escape>` are standard dialog affordances, not app shortcuts, and Escape has no collision risk inside a dedicated toplevel. SettingsWindow remains non-modal (`grab_status() is None` — the existing home/builder/player tests assert this) and keeps the Story 1.11 lifecycle (`SettingsWindow(parent, theme=...)` master = the persistent container).

**Block If:** nothing needs human input — the four defaults, the non-modal+guard dialog decision, the alert-mode reuse for invalid input, the unified level toggle (vs. legacy per-level flags), and gating `_restart_run` (including from the timeout banner) are all documented decisions below.

**Never:** no `grab_set()`/`wait_window()`/`messagebox` anywhere — confirmation prompts are non-modal `common/` Toplevels (UX-DR9 rejects modal takeover; `messagebox` also can't be styled and blocks the event loop). No new setting beyond the four AC'd actions (entry/exit redefinition is Epic 3 Story 3.4's concern, FR-17's "..." tail — explicitly out of scope). No per-level granularity for level changes (legacy `passage niveau 2/3/4/max` collapse into one `confirm_level_change` toggle). No gating of `_on_play` or `_on_generate_random` — committing to the shown maze / opening the generation dialog is not "switching mazes". No change to `_cycle_difficulty` (Difficulty is not in the AC's action list). No `on_confirm` called for cancel/Escape/WM-close. No new pyproject dependencies.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Reader, key absent | empty repo, any `read_confirm_*` | switch/level → `False`, restart/invalid → `True` (legacy defaults) | `SettingNotFoundError` caught → default |
| Reader, corrupt value | double raising `SettingCorruptError` | default (same as absent) | `SettingCorruptError` caught → default |
| Reader, stored non-bool | `1`, `0`, `"true"`, `"false"`, `None` stored | default — never accepted | `type(value) is bool` fails → default |
| Reader, stored bool | `True` / `False` stored | returned verbatim | No error |
| Writer | `write_confirm_restart(settings, False)` | `settings.get(GAME, CONFIRM_RESTART) is False` (raw `set`, no encoding) | No error |
| Never-writes-on-read | reader over a double whose `get` sets a flag | `set` never called | No error |
| Switch maze ON | `read_confirm_switch_maze` true, `_on_next()` | `_confirm_dialog` set; index unchanged; ConfirmDialog with "Switch to the next maze?" | No error |
| Switch maze ON, confirm | fire the dialog's Confirm pill | index moves +1, entry/label refreshed, `_confirm_dialog` cleared | No error |
| Switch maze ON, cancel | fire Cancel / Escape / WM-close | dialog destroyed, index unchanged, `_confirm_dialog` cleared | No error |
| Switch maze OFF | default, `_on_next()` | index moves +1 immediately, no dialog (existing tests stay green) | No error |
| Switch maze ON, double trigger | `_on_next()` twice before answering | second call no-ops (`_confirm_dialog` guard) — one dialog only | No error |
| Restart (gallery) ON/OFF | `_on_restart()` | gated exactly like previous/next (`confirm_switch_maze` — it changes the selected maze); index → 0 on confirm/immediate | No error |
| Jump valid ON/OFF | `_on_jump()` with a valid number | gated by `confirm_switch_maze`; index → number on confirm/immediate | No error |
| Jump invalid, alert ON | default, `_on_jump()` with `"abc"` / out-of-range | entry text reverted immediately; OK-only alert "That's not a valid maze number."; no index change | No error |
| Jump invalid, alert OFF | `write_confirm_invalid_input(False)`, invalid jump | entry text reverted silently (existing behavior), no dialog | No error |
| Play NOT gated | `confirm_switch_maze` true, `_on_play()` | navigates immediately, no dialog (commit action) | No error |
| Level change ON | `_cycle_level(+1)` from Level 1 | dialog "Change the level to Level 2?"; session level unchanged until Confirm | No error |
| Level change OFF | default, `_cycle_level(+1)` | level applies immediately (existing tests stay green) | No error |
| Level change, dialog open | keyboard shortcut for level while dialog focused | `_toplevel_has_focus()` false → no-op; pill click behind dialog → guard no-op | No error |
| Restart (gameplay) ON | default, `_restart_run()` (e.g. timeout banner Restart pill) | dialog "Restart the run for this maze?"; run unchanged until Confirm; Confirm = fresh run (Story 2.9 semantics) | No error |
| Restart (gameplay) OFF | `write_confirm_restart(False)`, `_restart_run()` | fresh run immediately, no dialog | No error |
| Toggle then act (AC-3) | toggle "Confirm before switching mazes" in SettingsWindow, then `_on_next()` on the mounted gallery sharing one repo | prompt appears without an app restart — reader reads fresh at action time | No error |
| SettingsWindow nav | click / Enter / Space on "Confirmation" label | content pane swaps to the four toggle rows; "Appearance" placeholder returns when selected back | No error |
| SettingsWindow persistence | toggle a `Checkbutton` | `write_confirm_*` called; reopening the window reflects the stored value; `grab_status() is None` (still non-modal) | No error |
| ConfirmDialog keys | `<Return>` on the dialog | confirms (invokes `on_confirm` after close) | No error |
| ConfirmDialog keys | `<Escape>` / WM-close | cancels (destroys, no `on_confirm`) | No error |
| Alert mode | `confirm_label="OK"`, `cancel_label=None`, `on_confirm=None` | single OK pill; OK/Escape/WM-close all dismiss; no `on_confirm` invoked | No error |
| Screen destroyed mid-dialog | navigate away while a ConfirmDialog is open | dialog parented to the screen frame → cascades-destroyed with it (same as `GenerateRandomDialog`); no orphaned window | No error |

## Code Map

- `src/labyrinthes/application/settings_keys.py` — **UPDATE**: add `CONFIRM_SWITCH_MAZE = "confirm_switch_maze"`, `CONFIRM_RESTART = "confirm_restart"`, `CONFIRM_LEVEL_CHANGE = "confirm_level_change"`, `CONFIRM_INVALID_INPUT = "confirm_invalid_input"` (all `game`-scope, per `epic-2-context.md:50`'s "per-action confirmation toggles").
- `src/labyrinthes/application/confirmation_settings.py` — **NEW**, mirroring `movement_settings.py`/`hard_mode_settings.py`:
  - `_read_bool(settings, key, default) -> bool` — **NEW**: `settings.get(SettingsScope.GAME, key)`, returns the value only when `type(value) is bool`, else `default`; catches `SettingNotFoundError`/`SettingCorruptError`/`TypeError`. Never raises, never writes on read.
  - `read_confirm_switch_maze(settings) -> bool` — **NEW**, default `False` (legacy `lab suivant`/`lab precedent` = 0).
  - `read_confirm_restart(settings) -> bool` — **NEW**, default `True` (legacy `recomencer lab` = 1).
  - `read_confirm_level_change(settings) -> bool` — **NEW**, default `False` (legacy `passage niveau 2/3/4` = 0).
  - `read_confirm_invalid_input(settings) -> bool` — **NEW**, default `True` (legacy `alerte mauvaise entree` = 1).
  - `write_confirm_switch_maze(settings, enabled: bool) -> None`, `write_confirm_restart`, `write_confirm_level_change`, `write_confirm_invalid_input` — **NEW**: `settings.set(SettingsScope.GAME, key, enabled)` (raw bool, no encoding). This story's screen *does* consume the writers (unlike the deferred HARD/time-limit pickers) — through the new Settings toggles.
  - Update the module docstring and `__all__`.
- `src/labyrinthes/adapters/tkinter/common/confirm_dialog.py` — **NEW** (AD-11 "confirmation-prompt dialogs"):
  - `ConfirmDialog(parent, *, theme, message, on_confirm=None, on_close=None, confirm_label="Confirm", cancel_label="Cancel")` — **NEW**: a themed `tk.Toplevel` (title "Confirm", `colors.window` background), the `message` as a `TYPOGRAPHY.body` label (`colors.ink`, `wraplength`, `justify="left"`), and two `PillButton`s — Confirm (`primary=True`, `command=self._on_confirm_clicked`) and, when `cancel_label is not None`, Cancel (`primary=False`). Toplevel-level `<Return>` → confirm, `<Escape>`/WM-delete → cancel; initial `focus_set()` on the Confirm pill. **Non-modal** (no `grab_set()` — see Boundaries; tests construct under a withdrawn `tk_root`). `_on_confirm_clicked()`/`_on_cancel_clicked()` both call `on_close()` (the owning screen's guard-clear), destroy, and only then call `on_confirm()` (confirm path) — `on_confirm`/`on_close` are optional and skipped when `None`. `transient(parent)` + `lift()` so the dialog sits above the screen. Alert mode = `cancel_label=None` + `on_confirm=None` + `confirm_label="OK"` (the invalid-input prompt).
  - Export from `common/__init__.py` (`ConfirmDialog` in `__all__`).
- `src/labyrinthes/adapters/tkinter/common/settings_window.py` — **UPDATE**:
  - `__init__(self, parent, *, theme, settings_repository)` — add required, keyword-only `settings_repository`.
  - `_CATEGORIES = ("Appearance", "Confirmation")`; the category nav labels become focusable (`takefocus=True`) controls bound to `<Button-1>`/`<Return>`/`<Space>` calling `_select_category(name)`; the active category renders in `colors.accent` foreground (visible selected state), focus ring on `<FocusIn>` (FOCUS_RING tokens, Story 1.10). Labels stay `TYPOGRAPHY.label` per the DESIGN.md `settings-window` component spec.
  - `_select_category(name) -> None` — clears the content pane (`tk.Frame` swap) and rebuilds it from `_build_appearance(...)` (the existing "coming soon" placeholder) or `_build_confirmation(...)`.
  - `_build_confirmation(container) -> None` — **NEW**: four themed `tk.Checkbutton` rows, one per action — "Confirm before switching mazes", "Confirm before restarting", "Confirm before changing level", "Alert me about invalid input" — `background=colors.window`, `foreground=colors.ink`, `font=TYPOGRAPHY.body`, `activebackground=colors.window`, `selectcolor` per tokens, `variable=tk.BooleanVar(...)` pre-set from `read_confirm_*(settings_repository)`, `command=` a closure calling the matching `write_confirm_*` on toggle. Checkbutton is natively keyboard-operable (Space toggles when focused) — NFR6.
- `src/labyrinthes/adapters/tkinter/home/screen.py` — **UPDATE**: `mount()` gains required, keyword-only `settings_repository: SettingsRepository`; `open_settings()` becomes `SettingsWindow(parent, theme=theme, settings_repository=settings_repository)`. Update the module docstring.
- `src/labyrinthes/adapters/tkinter/builder/screen.py` — **UPDATE**: same as Home.
- `src/labyrinthes/adapters/tkinter/player/screen.py` — **UPDATE**: `open_settings()` passes `settings_repository` into `SettingsWindow(parent, theme=theme, settings_repository=settings_repository)`.
- `src/labyrinthes/app/composition_root.py` — **UPDATE**: wrap Home and Builder in `functools.partial(mount_home, settings_repository=settings_repository)` / `partial(mount_builder, ...)` before `_bind_screen(...)` (Player already is, lines 131-142); extend the module docstring's Story 2.x wiring note.
- `src/labyrinthes/adapters/tkinter/player/classic_gallery.py` — **UPDATE**:
  - Constructor: `self._confirm_dialog: ConfirmDialog | None = None`.
  - `_maybe_confirm(enabled, *, message, on_confirm, confirm_label="Confirm", cancel_label="Cancel") -> None` — **NEW**: `if self._confirm_dialog is not None: return`; if `enabled`, open `ConfirmDialog(self, theme=self._theme, message=message, on_confirm=on_confirm, on_close=self._clear_confirm_dialog, confirm_label=..., cancel_label=...)` and store it; else `on_confirm()` if not `None`.
  - `_clear_confirm_dialog() -> None` — sets `self._confirm_dialog = None`.
  - `_on_previous()`/`_on_next()`/`_on_restart()` — gate: `self._maybe_confirm(read_confirm_switch_maze(self._settings_repository), message=..., on_confirm=self._apply_previous/_apply_next/_apply_restart)`; the existing bodies move to private `_apply_previous`/`_apply_next`/`_apply_restart`.
  - `_on_jump()` — valid branch gates via `read_confirm_switch_maze` (message "Jump to maze {n}?"); invalid branch keeps the immediate revert and adds `self._maybe_confirm(read_confirm_invalid_input(self._settings_repository), message="That's not a valid maze number.", confirm_label="OK", cancel_label=None)` (on_confirm `None` → alert mode).
  - `_on_play()`/`_on_generate_random()` unchanged (not gated). Update the module docstring.
- `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — **UPDATE**:
  - Constructor: `self._confirm_dialog: ConfirmDialog | None = None`.
  - `_maybe_confirm`/`_clear_confirm_dialog` helpers as in the gallery (parent `self`, no alert-mode kwargs needed for this screen's two actions).
  - `_cycle_level(delta)` — after the existing `_toplevel_has_focus()` guard, compute `new_level` (existing cycle math), then `self._maybe_confirm(read_confirm_level_change(self._settings_repository), message=f"Change the level to {_level_label(new_level)}?", on_confirm=lambda: self._apply_cycle_level(delta))`; the existing body moves to `_apply_cycle_level(delta)` (recomputes `new_level` — same result since level is unchanged until the dialog resolves).
  - `_restart_run()` — gates via `read_confirm_restart(self._settings_repository)` with message "Restart the run for this maze?", `on_confirm=self._apply_restart`; the existing fresh-run body (Story 2.9) moves to `_apply_restart()`. The timeout banner's Restart pill `command=self._restart_run` stays and now prompts by default.
- `tests/adapters/tkinter/conftest.py` — **UPDATE**: hoist `FakeSettingsRepository` here (the shared in-memory `SettingsRepository` double, currently duplicated... actually currently defined only in `player/conftest.py`) so Home/Builder/common settings tests can use it; mirror the Story 1.7 hoisting precedent noted in the module docstring.
- `tests/adapters/tkinter/player/conftest.py` — **UPDATE**: import `FakeSettingsRepository` from `tests.adapters.tkinter.conftest` and re-export it, keeping the existing `fake_settings_repository` fixture; remove the local class definition (one source of truth). If the cross-conftest import proves fragile, the fallback is leaving the local copy — note the choice in the review.
- `tests/app/test_composition_root.py` — **UPDATE**: the monkeypatched `capturing_mount_home`/`failing_mount_home` stubs (lines 46-70, 100-157) take a 5-arg shape; with Home/Builder now `partial`-bound, `build_app` calls them with a `settings_repository=` keyword — widen the stubs (e.g. add `settings_repository=None` or `**kwargs`) so the existing `build_app` wiring tests stay green.
- `tests/application/test_confirmation_settings.py` — **NEW**, mirroring `test_hard_mode_settings.py`/`test_movement_settings.py` (including their corrupt-double pattern): for each of the 4 readers — absent → default (`False`/`True`/`False`/`True`); corrupt → default; stored non-bool (`1`, `0`, `"true"`, `"false"`, `None`) → default; stored `True`/`False` → returned; writers store the raw bool in `SettingsScope.GAME`; never-writes-on-read.
- `tests/application/test_settings_keys.py` — **UPDATE**: add the 4 new names to `_KEY_NAMES`.
- `tests/adapters/tkinter/common/test_confirm_dialog.py` — **NEW**: is a `Toplevel`; shows the message text and the default Confirm/Cancel labels; Confirm pill (`_on_confirm_clicked`) invokes `on_confirm` and destroys; Cancel pill / `<Escape>` / WM-close destroy without `on_confirm`; `on_close` invoked on every close path; `cancel_label=None` renders no Cancel pill; alert mode (`on_confirm=None`, `confirm_label="OK"`) dismisses without invoking anything; `<Return>` confirms; window background is `colors.window`.
- `tests/adapters/tkinter/common/test_settings_window.py` — **UPDATE**: pass a `FakeSettingsRepository` to the 3 existing construction tests (still non-modal, still shows the Appearance placeholder); new tests: Confirmation category present in the nav; clicking (invoking the label's select handler) swaps the content pane to 4 Checkbutton rows and back; toggling a row calls the matching writer (assert via `read_confirm_*`); a stored value is reflected in the row's initial state; the category nav is keyboard-operable (Enter/Space handlers wired).
- `tests/adapters/tkinter/home/test_home_screen.py` — **UPDATE**: every `mount(...)` call gains `settings_repository=` (a `FakeSettingsRepository` fixture from the shared conftest); new test: `open_settings` from Home constructs a `SettingsWindow` that reflects a stored confirmation value (shared repo ⇒ AC-3 end-to-end from Home).
- `tests/adapters/tkinter/builder/test_builder_screen.py` — **UPDATE**: same as Home.
- `tests/adapters/tkinter/player/test_classic_gallery.py` — **UPDATE**: with the settings at defaults (all off except invalid-input), every existing test stays green (off = immediate, no dialog); new tests: each of `_on_previous`/`_on_next`/`_on_restart`/`_on_jump`(valid) with `write_confirm_switch_maze(True)` opens one `ConfirmDialog` and leaves the index unchanged until Confirm, cancelling leaves it unchanged, and a second trigger no-ops while one is open; invalid jump with default `confirm_invalid_input` shows the OK-only alert and reverts the entry; `write_confirm_invalid_input(False)` restores the silent revert; `_on_play` navigates immediately even with the switch setting on; AC-3: toggle through a `SettingsWindow` sharing the repo, then act.
- `tests/adapters/tkinter/player/test_gameplay_screen.py` — **UPDATE**: the existing `_cycle_level` tests stay green at the default (off ⇒ immediate); new: level change with `write_confirm_level_change(True)` opens a dialog and leaves the session level unchanged until Confirm; **`_restart_run` regression surface**: the Story 2.9 restart tests (lines 1972-2185) call `screen._restart_run()` directly and now hit the default-ON `confirm_restart` — update them to `write_confirm_restart(settings, False)` first (or confirm through the dialog) so the fresh-run assertions still exercise `_apply_restart`; new tests: restart with the setting on prompts (default behavior, including the timeout-banner Restart pill), and a keyboard shortcut while a confirm dialog holds focus is a no-op (`_toplevel_has_focus` interplay).
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — **UPDATE**: `2-10-confirmation-prompts-per-action`: `backlog` → `ready-for-dev`; bump `last_updated`.

## Tasks & Acceptance

**Execution:**
- [ ] `src/labyrinthes/application/settings_keys.py` — add the 4 `CONFIRM_*` keys
- [ ] `src/labyrinthes/application/confirmation_settings.py` — never-raises `read_confirm_*`/`write_confirm_*` (NEW)
- [ ] `src/labyrinthes/adapters/tkinter/common/confirm_dialog.py` — `ConfirmDialog` (NEW) + `common/__init__.py` export
- [ ] `src/labyrinthes/adapters/tkinter/common/settings_window.py` — `settings_repository` port, clickable category nav, Confirmation category with 4 persisted toggles
- [ ] `src/labyrinthes/adapters/tkinter/home/screen.py` + `builder/screen.py` — required keyword-only `settings_repository`; `player/screen.py` passes it to `SettingsWindow`
- [ ] `src/labyrinthes/app/composition_root.py` — partial-bind Home/Builder with `settings_repository`; extend the docstring
- [ ] `src/labyrinthes/adapters/tkinter/player/classic_gallery.py` — `_maybe_confirm`/`_clear_confirm_dialog`, gate the 4 browse/jump surfaces + invalid-input alert
- [ ] `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — gate `_cycle_level` and `_restart_run` via `_apply_*` split
- [ ] `tests/adapters/tkinter/conftest.py` — hoist `FakeSettingsRepository`; `player/conftest.py` imports/re-exports it
- [ ] `tests/app/test_composition_root.py` — widen the stub `mount_home` signatures for the partial
- [ ] `tests/application/test_confirmation_settings.py` — reader/writer matrix (NEW)
- [ ] `tests/application/test_settings_keys.py` — add the 4 names
- [ ] `tests/adapters/tkinter/common/test_confirm_dialog.py` — dialog close/keys/alert-mode coverage (NEW)
- [ ] `tests/adapters/tkinter/common/test_settings_window.py` — repo port + Confirmation category coverage
- [ ] `tests/adapters/tkinter/home/test_home_screen.py` + `builder/test_builder_screen.py` — repo port + AC-3-from-Settings tests
- [ ] `tests/adapters/tkinter/player/test_classic_gallery.py` + `test_gameplay_screen.py` — gating/guard/AC-3 coverage, update the default-ON restart tests
- [ ] `_bmad-output/implementation-artifacts/sprint-status.yaml` — 2-10 → ready-for-dev

**Acceptance Criteria:**
- [ ] AC-1: each of the 4 actions, setting on → a confirm prompt appears before the action applies
- [ ] AC-2: each of the 4 actions, setting off → immediate, no prompt (existing default behavior preserved where the default is off)
- [ ] AC-3: toggling any confirmation setting in the Settings window persists via the game-scoped repo and affects the next action without an app restart

## Design Notes

**Defaults carry the legacy CSV forward.** `Autres/Parametres_defaut.csv` is the source of truth for what the legacy user expected: switch = off (lines 15-16), restart = on (line 17), level-change = off (lines 18-21), invalid-input alert = on (line 7). One deliberate collapse: the legacy had four separate `passage niveau 2/3/4/max` flags (three off, "max" on) — this story unifies them into one `confirm_level_change` toggle with the majority default (off). Faithful-enough for FR-17's intent; documented so the review knows the "max"-was-on nuance was considered and dropped.

**The confirm dialog is non-modal *by design*, with an explicit stacking guard.** `grab_set()` is the one way to make a dialog truly block its source action, but the codebase-wide dialog convention is non-modal (`grab_status() is None` is asserted for `SettingsWindow`; `SaveMazeDialog`/`GenerateRandomDialog` follow the same pattern), and a `grab_set()` under the withdrawn `tk_root` test fixture raises `TclError: grab failed: window not viewable` — it would break the GUI test harness. So each gated action carries `_confirm_dialog is not None → no-op`. This makes a second click while a dialog is open inert rather than stacking a second dialog — closing the "no dedup guard" gap the `review-update-divergence-hunter` flagged for dialog-bearing screens, for these actions. The gameplay keyboard shortcuts already no-op behind the dialog for free via `_toplevel_has_focus()` (the dialog is a separate toplevel). Residual, accepted: a non-modal dialog can't stop the user clicking a *different* gated action behind it — the guard stops stacking, but the first dialog still answers for the first action. A genuinely modal confirmation is the obvious future improvement; it's not worth breaking the no-modal convention and the test harness for in this story.

**The invalid-input "confirm" is an OK-only alert, reusing `ConfirmDialog`.** FR-17's "invalid input" is legacy `alerte mauvaise entree` (`Autres/Outils.py:124`), which was an *informational* prompt, not a yes/no gate — "confirm" there means "prompt me at all". So `ConfirmDialog` supports alert mode (`cancel_label=None`, `confirm_label="OK"`, `on_confirm=None`): a single primary pill, Escape/WM-close dismisses, nothing else happens. The gallery's invalid-jump revert stays immediate; the alert just tells the player. The dialogs' existing *inline* validation (GenerateRandomDialog/SaveMazeDialog) is untouched — this setting governs only the one currently-silent invalid-input surface (the jump field), not a second prompt layered on top of inline errors.

**AC-3 is structural, not a refresh pipeline.** `JsonSettingsRepository.get()` re-reads its per-key file on every call, and every gated method calls `read_confirm_*` at action time (the Story 2.8 HARD-color pattern, the documented exception to the read-once-at-mount rule). Settings writes through the same `settings_repository` instance the screens hold, so the next action observes the new value. No observer/listener, no cache invalidation, no restart — exactly the AC's wording.

**SettingsWindow grows its first real content here — and gets a port it previously lacked.** Home/Builder `mount()` never received `settings_repository`, so their `SettingsWindow` could not read or write any `game`-scope value. Threading it through Home/Builder as a required keyword-only port (partial-bound in `composition_root.py`, exactly the Story 2.1/2.2 Player pattern) is the minimal way to satisfy AC-3 "changed in Settings" from every screen — Settings is reachable from any top bar (EXPERIENCE.md Component Patterns), so the toggles must work from all three. The category nav becomes a real focusable control (NFR6) instead of the placeholder labels.

**Gating `_restart_run` means the timeout-banner Restart pill now prompts by default** — a deliberate behavior change. The banner's Restart pill is the only current restart surface (Story 2.9), and AC-1's "restarting" is unconditional: when `confirm_restart` is on (the default), clicking Restart asks "Restart the run for this maze?" first. The double-prompt feel (you just clicked "Restart") is the price of faithfully matching the AC and the legacy restart-confirmation default; turning the setting off restores the one-click path. The Story 2.9 tests that call `_restart_run()` directly must set the setting off (or drive the dialog) to keep exercising the fresh-run semantics.

**No keybinding table additions.** `<Return>`/`<Escape>` inside `ConfirmDialog` are dialog-level affordances, registered on the dialog's own toplevel — not app shortcuts, so `common/keybindings.py` and `test_keybindings.py` are untouched. The legacy `r`-collision class of bug (Settings vs Restart, `addendum.md:41`) cannot recur here because the restart action stays a click-only pill.

## Previous Story Intelligence

- **Story 2.9** owns the surface this story extends: `_restart_run()` (the fresh-run rebuild, `gameplay_screen.py:790`), the timeout banner's Restart pill (`command=self._restart_run`, line 772), and the mount-time settings-read pattern. Its tests (lines 1972-2185) call `_restart_run()` directly and are the regression surface for gating it — they must be updated to the setting-off (or confirm-through) path.
- **Story 2.1/2.2** established the seam this story widens: `ClassicMazeGallery` already holds `_settings_repository` (line 97) and reads `read_maze_size_bounds` at action time; `mount_player` is partial-bound with `maze_repository` + `settings_repository` in `composition_root.py` (lines 131-142) — Home/Builder adopt the identical pattern. `_on_jump`'s revert semantics (line 224-245) and the gallery's pager clamp behavior are the gate templates.
- **Story 2.8** is the closest persistence template: `hard_mode_settings.py`'s never-raises reader with the strict `isinstance`/value check (`_read_color`, rejecting non-hex) is the direct template for `_read_bool` (rejecting non-bool); the per-sync freshness argument in its Design Notes is the AC-3 argument here.
- **Story 1.8/1.11** own `SettingsWindow`: its non-modal contract (`grab_status() is None`, asserted in home/builder tests), its persistent-container parenting, and its placeholder-category structure — this story's nav/content-split redesign must keep all three. The residual stale-theme-after-toggle gap documented in its module docstring is unchanged by adding content (the Confirmation toggles use the window's own `theme` at construction, same as everything else in it).
- **Regression watchlist:** the `SettingsWindow` non-modality assertions in `test_home_screen.py`/`test_builder_screen.py`/`test_player_screen.py`; every home/builder `mount(...)` call site (new required keyword — 26 call sites across the two test files); `test_composition_root.py`'s 5-arg stub `mount_home`s (the new partial passes a keyword); the Story 2.9 `_restart_run` tests (default-ON gate); `_cycle_level`'s `_toplevel_has_focus()` guard (must stay first); the keybinding-uniqueness test (no new binding); the AD-1/AD-9/AD-11 import-boundary tests (`confirmation_settings.py` and `confirm_dialog.py` must respect them); the `GenerateRandomDialog`/`SaveMazeDialog` tests (untouched). Run a single failing GUI test alone before assuming a regression (flaky focus tests, AGENTS.md).

## Git Intelligence

- Working branch: `epic-2-play-a-maze-game-player` (epic-2 accumulation branch, current HEAD `5ce301d` = Story 2.9 merge). **Never commit directly to it** — create `story-2-10-confirmation-prompts-per-action` from it, merge story → epic via `git merge --no-ff` when done; epic → `rewrite` only via PR once the whole epic is done.
- Mirror the per-story rhythm: `feat(player): ...` (feature) → `test(player): ...` (tests) → `docs(planning): record Story 2.10 ...` (status + spec) → `Merge story-2-10-... into epic-2-... (story 2.10)`. Conventional Commits in English, story number in the subject (`(story 2.10)`).
- `uv.lock` is untracked — leave it alone.

## Latest Technical Information

No new external dependencies: the stack is pinned in `pyproject.toml` (Python ≥3.12, tkinter, pytest ≥8.0, ruff ≥0.6, hatchling). Everything uses stdlib (`dataclasses`, `enum`, `tkinter`) and the existing `domain/`/`application/`/`common/` types. One Tk fact the dev will hit: `tk.Checkbutton` accepts `background`/`foreground`/`activebackground`/`selectcolor`/`font` for full token styling and toggles natively on Space when focused — no custom widget needed for NFR6. One behavioral fact relied on: `Toplevel`-level `<Return>`/`<Escape>` bindings fire when the dialog's widgets hold focus (Tk's bindtags include the toplevel), so the keys work from anywhere in the dialog.

## Verification

**Commands:**
- `ruff check .` — expected: no new lint violations (line-length 100, rules `E, F, I, UP, B, SIM`; no comments unless asked)
- `ruff format --check .` — expected: no formatting diffs
- `pytest` — expected: full suite green, including the new `confirmation_settings`/`ConfirmDialog`/gating tests and the updated restart tests

**Regression watchlist:** `SettingsWindow` non-modality + persistent-container parenting; home/builder `mount` call sites; `test_composition_root.py` stub signatures; Story 2.9 `_restart_run`/timeout-banner tests (default-ON gate changes their path); `_cycle_level` focus-guard ordering; `test_keybindings.py` (untouched); the AD-1/AD-9/AD-11 boundary tests; `GenerateRandomDialog`/`SaveMazeDialog`/`SettingsWindow`-survival tests.

## Project Structure Notes

- All four setting values live in `application/confirmation_settings.py` + four keys in `application/settings_keys.py`; the dialog is a `common/` widget (`common/confirm_dialog.py`); only gating/wiring lands in `adapters/` (`player/classic_gallery.py`, `player/gameplay_screen.py`, the three screens' `mount()`, and `app/composition_root.py`). No domain change, no new port, no new screen.
- Naming is English throughout (NFR4); maze data (`0/1/2/3`) untouched; the new keys use the existing `snake_case` convention; UI strings follow the Voice and Tone register (plain, non-alarmist: "That's not a valid maze number.").
- No `tkinter`/`adapters` import may appear in `confirmation_settings.py` or `settings_keys.py` (AD-1, AD-9); `confirm_dialog.py` may import only `common/` + stdlib (AD-11).

## References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 2.10 ACs (lines 696-714); FR-17 (line 57); AD-11 shared confirmation dialogs (line 107)]
- [Source: `_bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/prd.md` — FR-17 (line 160)]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md` — AD-11 rule, confirmation-prompt dialogs in `common/` (lines 131-132)]
- [Source: `_bmad-output/planning-artifacts/ux-designs/ux-Labyrinthes-2026-08-04/DESIGN.md` — `settings-window` component (line 192), category nav + standard form rows (line 334), `pill-btn` component tokens (lines 178-187)]
- [Source: `_bmad-output/planning-artifacts/ux-designs/ux-Labyrinthes-2026-08-04/EXPERIENCE.md` — entry/exit confirm prompt toggleable off per FR-17 (line 55), Settings window categorized sections (line 62), standard form rows (line 87)]
- [Source: `_bmad-output/implementation-artifacts/epic-2-context.md` — confirmation-prompts paragraph (line 38), game-scoped settings list incl. confirmation toggles (line 50)]
- [Source: `Labyrinthes_copy.py` (legacy, read-only) — `recomencer_lab`/next/prev confirmations (lines 132/140/155), level-change confirmations (lines 2015-2048), Settings checkbuttons (lines 1893-1940)]
- [Source: `Autres/Parametres_defaut.csv` (legacy) — defaults: `lab suivant` 0 / `lab precedent` 0 (lines 15-16), `recomencer lab` 1 (line 17), `passage niveau 2/3/4` 0 + `max` 1 (lines 18-21), `alerte mauvaise entree` 1 (line 7)]
- [Source: `Autres/Outils.py` (legacy) — `alerte mauvaise entree` setting (lines 124, 159)]
- [Source: `src/labyrinthes/application/movement_settings.py`/`hard_mode_settings.py` — never-raises reader/writer templates; `src/labyrinthes/application/settings_keys.py`; `src/labyrinthes/adapters/tkinter/common/settings_window.py` (placeholder + non-modal + Story 1.11 parenting); `src/labyrinthes/adapters/tkinter/player/classic_gallery.py` (`_on_previous`/`_on_next`/`_on_restart`/`_on_jump` lines 206-245, `_settings_repository` line 97); `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` (`_cycle_level` lines 570-579, `_toplevel_has_focus` lines 468-485, `_restart_run` line 790, timeout banner Restart pill line 772); `src/labyrinthes/app/composition_root.py` (partial-binding pattern lines 131-142); `tests/app/test_composition_root.py` (5-arg stub `mount_home`s lines 46-157)]

## Dev Agent Record

### Agent Model Used

opencode/deepseek-v4-flash-free

### Debug Log References

- 2026-08-17: Story 2.10 spec created on branch `epic-2-play-a-maze-game-player` (HEAD `5ce301d`) via the `bmad-create-story` workflow. Full-artifact analysis confirmed no AC is already green — the story is all-new surface: four `game`-scoped bool settings (defaults traced to `Autres/Parametres_defaut.csv`), the first `common/` confirmation-prompt dialog (AD-11), `SettingsWindow`'s first real content + a `settings_repository` port it previously lacked, Home/Builder `mount()` widened with the same required keyword-only port Player already has, and per-action gating in the gallery (switch + invalid-input alert) and gameplay (`_cycle_level`, `_restart_run`). Key decisions: non-modal dialog with an explicit open-dialog stacking guard (a `grab_set()` would break the withdrawn-`tk_root` GUI-test harness); alert-mode reuse of `ConfirmDialog` for the legacy `alerte mauvaise entree`; unified level toggle (legacy per-level flags collapse, majority default off); gating `_restart_run` changes the timeout-banner Restart pill to prompt by default (Story 2.9 restart tests must be updated); AC-3 is structural via per-call disk re-reads + action-time reads.

### Completion Notes List

_(Not implemented yet — this section is filled by the story's Dev Agent Record on implementation.)_

### File List

- This spec: `_bmad-output/implementation-artifacts/spec-2-10-confirmation-prompts-per-action.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — 2-10: backlog → ready-for-dev

## Change Log

- 2026-08-17: Created Story 2.10 spec (status ready-for-dev) on branch `epic-2-play-a-maze-game-player` (baseline `5ce301d`), marking `2-10-confirmation-prompts-per-action` ready-for-dev in `sprint-status.yaml`.