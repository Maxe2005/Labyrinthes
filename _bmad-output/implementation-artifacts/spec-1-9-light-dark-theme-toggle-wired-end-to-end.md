---
title: 'Story 1.9: Light/dark theme toggle, wired end-to-end'
type: 'feature'
created: '2026-08-06'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-1-context.md']
warnings: [oversized]
baseline_revision: 'bf9402254a8a6c7d14b81ce24a7d8b1adec5b51a'
final_revision: '9a6e5ca9e149f6435f7e577be81d9f2c4cb67449'
---

<intent-contract>

## Intent

**Problem:** `Theme.LIGHT` is hardcoded independently in five places across `home/`, `builder/`, `player/` (Story 1.8's deliberate placeholder), there is no way for a user to switch it, and `SettingsRepository`'s `shared` scope is defined but never actually wired into the composition root.

**Approach:** Add a `ThemeController` in `app/` that owns the current `Theme`, loads/persists it through `JsonSettingsRepository`'s `shared` scope (Story 1.5), and notifies subscribers on toggle; wire a theme-toggle `icon-btn` into `TopBar` (next to Settings, per the locked mockups); extend the screen `mount()` contract (already extended once in Story 1.8 for `navigate`) with `theme`/`toggle_theme`, replacing every hardcoded `Theme.LIGHT`; `composition_root.build_app()` re-navigates the currently-mounted screen on toggle so it rebuilds with the new theme's tokens.

## Boundaries & Constraints

**Always:** `application/settings_keys.py` gains `THEME = "theme"`. `app/theme_controller.py`'s `ThemeController(settings: SettingsRepository)` loads the persisted `shared`/`THEME` value at construction (defaulting to `Theme.LIGHT` via caught `SettingNotFoundError`, never letting that propagate), exposes a read-only `.theme` property, `subscribe(listener: Callable[[Theme], None])`, and `toggle()` (flips the theme, `settings.set(SettingsScope.SHARED, THEME, ...)` immediately, then calls every subscriber with the new `Theme`). `adapters/tkinter/common/navigation.py` gains `ToggleThemeFn = Callable[[], None]`, and `ScreenMountFn` becomes `Callable[[tk.Widget, Maze | None, NavigateFn, Theme, ToggleThemeFn], tk.Frame]` — `Router`/`Router.register`/`MountFn` (Story 1.7) stay exactly as they are; `composition_root.build_app()` is what still bridges the two, same pattern as Story 1.8's `navigate` bridging. Every one of `home/screen.py`/`builder/screen.py`/`player/screen.py`'s `mount()` gains `theme: Theme` and `toggle_theme: ToggleThemeFn` as two more required positional parameters (after `navigate`), replaces its local `theme = Theme.LIGHT` with the received `theme`, and passes `on_theme_toggle=toggle_theme` into its `TopBar(...)` call. `TopBar` gains an `on_theme_toggle: Callable[[], None] | None = None` parameter and renders a second `icon-btn` (glyph `"🌙"`, tooltip `"Toggle theme."`, matching every locked mockup's identical moon glyph regardless of theme) to the **right of** the existing Settings icon-btn — pack the theme-toggle button before the Settings button so it lands at the outer-right edge (`side="right"` packing places the first-packed widget nearest the edge). `composition_root.build_app()` constructs one `JsonSettingsRepository()` (default root) and one `ThemeController` from it, tracks the `state` most recently passed to `navigate()` in a closure variable, subscribes a listener that re-navigates the router's `current_screen_id` (skipped if `None`, i.e. before the first `navigate()`) with that tracked state whenever the theme changes, and binds `theme_controller.theme`/`theme_controller.toggle` (read/called fresh on every mount, not captured once) into each registered screen's `mount()` alongside the existing `navigate` closure. `build_app()` gains an optional `settings_repository: SettingsRepository | None = None` parameter (defaults to a real `JsonSettingsRepository()`) so tests can inject a `tmp_path`-rooted or in-memory instance instead of touching the real, relative `./settings/` directory on disk.

**Block If:** None identified — this is a direct, mechanical extension of Story 1.8's own `navigate`-threading precedent plus Story 1.5's already-built, already-tested `SettingsRepository` port; nothing here requires a human decision.

**Never:** Do not add real Appearance-category content to `SettingsWindow` (logo picker, etc.) — the theme toggle lives in `TopBar` per `EXPERIENCE.md`'s Component Patterns table ("icon-btn | Top bar | Settings and theme-toggle live here"), not inside the Settings dialog; `SettingsWindow`'s "Appearance settings are coming soon." placeholder is untouched (Story 2.11/FR-18 owns the logo picker). Do not modify `Router`, `Router.register`, or `MountFn`'s 2-arg contract, or `tests/app/test_router.py`. Do not add a `TYPE_CHECKING`-only or lazy fix for `Router.navigate()` destroying an open `SettingsWindow` on re-navigate (already an accepted, documented Story 1.8 tradeoff in `deferred-work.md`; toggling theme while Settings is open closing it is the same class of behavior, not a new regression to fix here). Do not change the wall/corridor dark-mode-is-not-an-inversion behavior or its tokens — Story 1.6 already implemented and tested this (`test_wall_and_corridor_are_locked_per_theme_hexes_not_a_mechanical_inversion`); this story only needs to prove it's reachable end-to-end via the toggle, not re-implement it.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| First launch, no persisted theme | `ThemeController(settings)` constructed, `shared/theme` never set | `.theme == Theme.LIGHT` | `SettingNotFoundError` caught internally, never propagates |
| Toggle from Home | Theme-toggle icon-btn clicked while Home is mounted | `ThemeController.toggle()` flips theme, persists it via `SettingsRepository.set(SHARED, THEME, ...)`, Home's frame is destroyed and rebuilt with the new theme's tokens (new `TopBar`/`PillButton` colors) | No error expected |
| Toggle from Builder/Player | Theme-toggle icon-btn clicked while Builder (or Player) is mounted | Same rebuild-in-place behavior, breadcrumb and all `TopBar` elements re-render with the new theme | No error expected |
| Restart after a toggle | New `ThemeController(settings)` built against the same persisted store | `.theme` equals whatever was last toggled to, not `Theme.LIGHT` | No error expected |
| Toggle before any `navigate()` | (Not reachable in practice — `build_app()` always calls `router.navigate(HOME)` before returning) | N/A | `router.current_screen_id is None` guard prevents a crash if ever reached |

</intent-contract>

## Code Map

- `src/labyrinthes/application/settings_keys.py` -- add `THEME = "theme"`
- `src/labyrinthes/app/theme_controller.py` -- new; `ThemeController` (load/persist/toggle/subscribe)
- `src/labyrinthes/adapters/tkinter/common/navigation.py` -- add `ToggleThemeFn`; extend `ScreenMountFn` to 5-arg
- `src/labyrinthes/adapters/tkinter/common/top_bar.py` -- add `on_theme_toggle` param + second `icon-btn`
- `src/labyrinthes/adapters/tkinter/common/__init__.py` -- re-export `ToggleThemeFn`
- `src/labyrinthes/app/composition_root.py` -- construct `JsonSettingsRepository`/`ThemeController`, track last `state`, subscribe re-render, bind `theme`/`toggle_theme` into each screen's `mount()`, add `settings_repository` param
- `src/labyrinthes/adapters/tkinter/home/screen.py` -- `mount()` gains `theme`/`toggle_theme`, drops the hardcode, wires `on_theme_toggle`
- `src/labyrinthes/adapters/tkinter/builder/screen.py` -- same as above
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- same as above
- `tests/app/test_theme_controller.py` -- new; covers the I/O matrix's `ThemeController` rows
- `tests/application/test_settings_keys.py` -- add `THEME` to the covered key list
- `tests/adapters/tkinter/common/test_top_bar.py` -- new theme-toggle button cases (present, command fires, positioned right of Settings)
- `tests/adapters/tkinter/conftest.py` -- add a `toggle_theme_stub` fixture (mirrors `navigate_stub`)
- `tests/adapters/tkinter/{home,builder,player}/test_*_screen.py` -- update `mount()` calls for the two new params; assert `on_theme_toggle` reaches `TopBar`
- `tests/app/test_composition_root.py` -- add `settings_repository` (tmp_path-rooted) to every `build_app()` call; update `failing_mount_home`/`capturing_mount_home` stubs to 5 args; new tests for toggle-triggers-rerender and persistence-across-a-fresh-`ThemeController`

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/application/settings_keys.py` -- add `THEME` -- the one shared key name every consumer imports instead of hardcoding
- [x] `src/labyrinthes/app/theme_controller.py` -- add `ThemeController` -- the shell-wide theme mechanism Story 2.11/3.7 reuse
- [x] `src/labyrinthes/adapters/tkinter/common/navigation.py` -- add `ToggleThemeFn`, extend `ScreenMountFn` -- the updated screen contract
- [x] `src/labyrinthes/adapters/tkinter/common/top_bar.py` -- add the theme-toggle `icon-btn` -- satisfies the AC1 toggle affordance
- [x] `src/labyrinthes/adapters/tkinter/common/__init__.py` -- re-export `ToggleThemeFn`
- [x] `src/labyrinthes/app/composition_root.py` -- wire `JsonSettingsRepository`/`ThemeController`, re-render-on-toggle, `settings_repository` param
- [x] `src/labyrinthes/adapters/tkinter/{home,builder,player}/screen.py` -- extend `mount()`, drop hardcodes, wire `on_theme_toggle`
- [x] `tests/app/test_theme_controller.py` -- cover default/persist/toggle/reload
- [x] `tests/application/test_settings_keys.py` -- cover `THEME`
- [x] `tests/adapters/tkinter/common/test_top_bar.py` -- cover the new icon-btn
- [x] `tests/adapters/tkinter/conftest.py` -- add `toggle_theme_stub`
- [x] `tests/adapters/tkinter/{home,builder,player}/test_*_screen.py` -- update calls, add theme-toggle wiring cases
- [x] `tests/app/test_composition_root.py` -- update stubs/calls, add rerender + persistence-across-restart tests

**Acceptance Criteria:**
- Given the theme is toggled from any mounted screen's `TopBar`, when that screen re-renders, then every token-driven surface (brand mark, breadcrumb, buttons, icon-btns) switches to the paired dark/light `ColorTokens` value
- Given dark mode, when wall/corridor colors are read via `colors_for(Theme.DARK)`, then they are the dedicated dark-mode hexes, not a mechanical inversion of light mode (already proven by Story 1.6's `test_tokens.py`; this story only needs the toggle path reachable, not new dark-mode color logic)
- Given the theme has been toggled, when the app restarts (a fresh `ThemeController` built against the same settings store), then the previously chosen theme persists via `SettingsRepository`'s `shared` scope

## Spec Change Log

## Review Triage Log

### 2026-08-06 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 3 (medium 1, low 2)
- defer: 7 (medium 3, low 4)
- reject: 4 (low 4)
- addressed_findings:
  - `[medium]` `[patch]` `ThemeController._load_theme()` only caught `SettingNotFoundError`; a persisted `shared/theme` value that isn't `"light"`/`"dark"` (corrupted/hand-edited/future-format file) raised an uncaught `ValueError` from `Theme(value)`, crashing the entire app before its window ever showed, since `ThemeController` is now built unconditionally on every real launch via `composition_root.build_app()` — fixed by also catching `ValueError` and defaulting to `Theme.LIGHT`; added `test_default_theme_is_light_when_the_persisted_value_is_not_a_recognized_theme`
  - `[low]` `[patch]` `build_app()`'s initial screen mount called `router.navigate(ScreenId.HOME)` directly instead of through the `navigate` closure, so `last_state` tracking was only coincidentally correct (Home happens to take no state) rather than structurally guaranteed from the first screen onward — fixed to call `navigate(ScreenId.HOME)`
  - `[low]` `[patch]` `test_toggling_theme_bound_into_a_screens_mount_rerenders_the_current_screen` asserted the new frame differs from the old one but never that the old one was actually torn down — a regression leaving two overlapping `TopBar`s mounted side by side would have passed undetected — added `assert not first_call["frame"].winfo_exists()`

Findings routed to `deferred-work.md` (real but pre-existing patterns, cross-cutting repository-layer gaps, or not reachable through any current call path — none blocking any stated AC): `ThemeController` is the first unconditional, every-launch consumer of `SettingsRepository.get()`, escalating (but not newly causing) the already-deferred Story 1.5 finding that malformed JSON raises an uncaught `json.JSONDecodeError` — a repository-level fix, out of this story's scope; `ThemeController.toggle()` has no error handling around `settings.set()` persistence failures, same class as the already-deferred Story 1.4/1.5 non-atomic-write findings; the default `JsonSettingsRepository()` root is CWD-relative with no XDG anchoring (Story 1.5's pre-existing default, newly load-bearing now that this story activates it from a live path); `ThemeController.toggle()`'s listener loop has no per-listener isolation (not reachable today, exactly one listener is ever registered); `navigate()`'s `last_state` is set before `router.navigate()` confirms success, and a theme-triggered re-navigate that raises escapes `build_app()`'s own exception guard (both share the same "not reachable today" precondition as the already-deferred Story 1.7 `Router.navigate()` exception-safety findings — no screen's `mount()` raises); no test exercises the `on_theme_change` "toggle before any navigate()" guard, which isn't independently reachable through `build_app()`'s public surface today.

Findings rejected as noise: `test_theme_toggle_button_is_visually_right_of_the_settings_button` asserting `pack_slaves()` order rather than real on-screen geometry — this was the explicitly sanctioned fallback for this codebase's withdrawn-`tk_root` test convention (real `winfo_x()` geometry is unavailable under it, same limitation already documented in other `common/` widget tests), not an oversight; the toggle-closes-an-open-`SettingsWindow` interaction being untested — the spec's own `Never` list explicitly declines to fix or test this, and it restates the already-recorded Story 1.8 deferred-work entry for the identical class of behavior rather than surfacing new information; the Problem statement's "hardcoded independently in five places" phrasing counting each screen's `SettingsWindow`-opening closure as an independent hardcode (they close over the same already-declared local `theme`, not a separate literal) — cosmetic prose inherited verbatim from the pre-existing Story 1.8 deferred-work entry, no functional impact, all three real hardcode sites were correctly identified and removed; `ThemeController` lacking an `unsubscribe()` API and a multi-subscriber test — speculative and forward-looking, no current call site needs either, matching this codebase's existing precedent of not building unregister/unsubscribe APIs ahead of actual need (e.g. `Router.register()`).

## Design Notes

- **Why `ThemeController` lives in `app/`, not `common/`:** the epic's Technical Decisions pin `SettingsRepository` as accessed only through the composition root, never directly by a screen; `app/` already constructs concrete adapters (composition_root is the sole place allowed to import concrete screens, AD-10) and is the natural, already-established layer for wiring a port to UI callbacks, mirroring how `navigate` was bridged in Story 1.8 rather than handing screens a raw `Router`.
- **Why re-navigate instead of live-restyling widgets in place:** Tk widgets have no reactive re-theming primitive — every `common/` primitive resolves its colors once, at construction, from `colors_for(theme)`. Story 1.7/1.8 already established that `Router.navigate()` fully tears down and rebuilds a screen's frame; reusing that exact mechanism for "the same screen, new theme" is the smallest correct change, and it's the same code path already covered by `tests/app/test_router.py`'s new-before-old ordering tests.
- **Why `toggle_theme` is a narrow `ToggleThemeFn`, not the whole `ThemeController`:** mirrors Story 1.8's `NavigateFn` reasoning exactly — a screen only ever needs to trigger a toggle, never to `subscribe()` another listener or read `.theme` outside of what `mount()` already handed it.
- **Settings-window-closes-on-toggle is an accepted, pre-existing tradeoff:** identical in kind to the already-deferred "breadcrumb Home click closes an open Settings window" finding from Story 1.8 — not a new regression, not addressed here.

## Verification

**Commands:**
- `pytest -q` -- expected: full suite passes, including new `tests/app/test_theme_controller.py` and updated `tests/app/test_composition_root.py`/`tests/adapters/tkinter/**`
- `ruff check .` -- expected: no findings
- `ruff format --check .` -- expected: no findings

## Auto Run Result

**Summary:** Added a shell-wide `ThemeController` (`app/theme_controller.py`) that owns the current `Theme`, loads/persists it through `JsonSettingsRepository`'s `shared` scope, and notifies subscribers on `toggle()`. Wired a theme-toggle `icon-btn` (🌙, "Toggle theme.") into `TopBar`, to the right of the existing Settings icon-btn per the locked mockups. Extended every screen's `mount()` (Home/Builder/Player) with two more required parameters, `theme: Theme` and `toggle_theme: ToggleThemeFn`, removing the five Story-1.8-flagged independent `Theme.LIGHT` hardcodes in favor of the passed-in value. `composition_root.build_app()` now constructs one `JsonSettingsRepository`/`ThemeController` pair, tracks the state most recently passed to `navigate()`, and subscribes a listener that re-navigates the currently-mounted screen (rebuilding it with the new theme's tokens) whenever the theme changes — the same `Router.navigate()` teardown-and-rebuild mechanism Story 1.7/1.8 already established, since Tk widgets have no reactive re-theming primitive. `build_app()` gained an optional `settings_repository` parameter so tests never touch the real, relative `./settings/` directory.

**Files changed:**
- `src/labyrinthes/app/theme_controller.py` -- new; `ThemeController` (load/persist/toggle/subscribe), hardened during review to also default to `Theme.LIGHT` on an unrecognized persisted value
- `src/labyrinthes/application/settings_keys.py` -- adds `THEME = "theme"`
- `src/labyrinthes/adapters/tkinter/common/navigation.py` -- adds `ToggleThemeFn`; extends `ScreenMountFn` to the 5-arg shape
- `src/labyrinthes/adapters/tkinter/common/top_bar.py` -- adds `on_theme_toggle` param + the theme-toggle `icon-btn`, positioned right of Settings via pack order
- `src/labyrinthes/adapters/tkinter/common/__init__.py` -- re-exports `ToggleThemeFn`
- `src/labyrinthes/app/composition_root.py` -- wires `JsonSettingsRepository`/`ThemeController`, tracks `last_state`, subscribes the re-render-on-toggle listener, adds the `settings_repository` param; renamed `_bind_navigate`→`_bind_screen`; initial Home navigation now goes through the `navigate` closure (review fix)
- `src/labyrinthes/adapters/tkinter/{home,builder,player}/screen.py` -- `mount()` extended with `theme`/`toggle_theme`; drops the hardcode; wires `on_theme_toggle`
- `tests/app/test_theme_controller.py` -- new; default/toggle/persist/subscribe/reload coverage, plus a review-added malformed-value fallback case
- `tests/application/test_settings_keys.py` -- covers `THEME`
- `tests/adapters/tkinter/common/test_top_bar.py` -- covers the new icon-btn (click, no-op, right-of-Settings ordering)
- `tests/adapters/tkinter/conftest.py` -- adds `toggle_theme_stub`
- `tests/adapters/tkinter/{home,builder,player}/test_*_screen.py` -- updated `mount()` calls; new theme-toggle wiring cases
- `tests/app/test_composition_root.py` -- all `build_app()` calls now inject a `tmp_path`-rooted repository; new rerender-on-toggle and persistence-across-two-`App`-builds tests, the former hardened during review to also assert the old frame is torn down (`winfo_exists()`)

**Review findings:** 14 unique findings from two parallel reviews (Blind Hunter adversarial + Edge Case Hunter). 3 patched (0 high, 1 medium, 2 low): a persisted settings value that isn't `"light"`/`"dark"` crashing the app on every future launch (now defaults to `Theme.LIGHT`); the initial Home navigation bypassing `last_state` tracking; a rerender test not confirming the old frame was actually torn down. 7 deferred to `deferred-work.md` (0 high, 3 medium, 4 low): the same malformed-settings-file risk in its broader, repository-level form (raw `json.JSONDecodeError`, a pre-existing Story 1.5 gap this story is the first to make reachable); no error handling around a failed settings write; the CWD-relative default settings root now being live; a listener-isolation gap in `toggle()`'s notification loop; two `Router.navigate()`-exception-safety gaps sharing the same "not reachable today" precondition as existing Story 1.7 deferred entries; a test-coverage gap for an already-declared-unreachable guard branch. 4 rejected as noise: a test-fallback limitation explicitly sanctioned in advance; the Settings-closes-on-toggle interaction, already covered by an existing Story 1.8 deferred-work entry and explicitly out of this story's declared scope; a cosmetic phrasing imprecision in the spec's own Problem statement; a speculative `unsubscribe()`/multi-subscriber request with no current call site.

**Verification:** `ruff check .` -- all checks passed. `ruff format --check .` -- all `src/`/`tests/` files format-clean (the pre-existing, unrelated `_bmad-output/implementation-artifacts/1-1-domain-model-foundation.md` formatting finding, present before this story, remains untouched and out of scope). `pytest -q` -- 232 passed. `pytest tests/test_architecture_boundaries.py -q` -- 4 passed, confirming `home/`/`builder/`/`player/` still never import each other or `app/`, `common/` still never imports the three screens or `adapters/storage/` directly, and `domain/`/`application/` still import nothing from `adapters/`/`tkinter`.

**Residual risks:** Toggling the theme while a `SettingsWindow` is open silently closes it (accepted, pre-existing tradeoff, identical in kind to Story 1.8's breadcrumb-Home-click finding — no stateful Settings content exists yet to lose). A malformed `settings/shared/theme.json` file (e.g. from a crash mid non-atomic-write, an already-deferred Story 1.5 risk) still crashes the app on launch via a raw `json.JSONDecodeError` — this story closed the narrower "recognized-but-wrong value" half of that gap, not the broader "corrupted JSON" half, which needs a repository-level fix. The default settings root is CWD-relative with no XDG anchoring, now live for the first time via theme persistence. Several `Router.navigate()`/`ThemeController` exception-safety and reentrancy gaps remain theoretical (no current `mount()` implementation or listener ever raises), consistent with equivalent, already-accepted gaps from Story 1.7.
