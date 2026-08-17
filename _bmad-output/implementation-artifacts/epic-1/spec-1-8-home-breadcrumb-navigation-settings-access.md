---
title: 'Story 1.8: Home — breadcrumb navigation & Settings access'
type: 'feature'
created: '2026-08-06'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false # judged after review pass: 7 low-severity, cosmetic/test-infra patches only -- localized, no behavior/API/security/data impact
context: ['_bmad-output/implementation-artifacts/epic-1/epic-1-context.md']
warnings: [oversized]
baseline_revision: 'b171dd57f24932c51803a4ea3964c7d9ddb7766c'
final_revision: '1a10b2adb55c9337f379ba5e0aa68207722f2252'
---

<intent-contract>

## Intent

**Problem:** Home, Builder, and Player (Story 1.7) are static placeholders with no way to navigate between them, no persistent breadcrumb back to Home, and no Settings affordance — every screen's `mount()` only receives `(parent, state)`, giving it no capability to trigger `Router.navigate()` at all.

**Approach:** Give every screen's `mount()` a third `navigate: NavigateFn` parameter (composition root binds each 3-arg screen `mount` to `router.navigate` before registering it with `Router`, which itself stays 2-arg/unchanged); add `common/navigation.py` (`ScreenId` relocated off `app/router.py` so screens can reference it without importing `app/`), `common/breadcrumb.py`, `common/top_bar.py`, and `common/settings_window.py`; wire Home's two entry-point buttons, Builder/Player's "Home / <Screen>" breadcrumb, and all three screens' Settings icon into this new plumbing.

## Boundaries & Constraints

**Always:** Every screen's `mount(parent: tk.Widget, state: Maze | None, navigate: NavigateFn) -> tk.Frame` gains `navigate` (`Callable[[ScreenId, Maze | None], None]`) as a third, required, positional parameter; `Router`, `Router.register`, and `MountFn` stay exactly as Story 1.7 left them (2-arg) — `composition_root.build_app()` closes the gap by wrapping each screen's 3-arg `mount` in a 2-arg adapter bound to `router.navigate` before calling `router.register()`. `ScreenId` moves to `adapters/tkinter/common/navigation.py` and is re-exported unchanged from `app/router.py` (so `from labyrinthes.app.router import ScreenId` keeps working) — this is what lets `home/`, `builder/`, `player/` reference it without importing `app/`, preserving the one-way `app/ → adapters/ → application/ → domain/` dependency direction. On Builder and Player, the top bar renders a `Breadcrumb` reading "Home / Builder" / "Home / Player": the Home segment is always clickable, calling `navigate(ScreenId.HOME, None)`; the trailing segment (the screen's own name) is never clickable. Home renders no breadcrumb of its own (0 navigation depth) — matches the locked `key-home.html` mockup, which shows only the brand mark/wordmark and no `.crumb` element. Every screen's top bar carries a Settings `IconButton`; clicking it opens `SettingsWindow` as its own non-modal `Toplevel` (no `grab_set()`) parented under that screen's frame, without touching the router — the underlying screen stays mounted and interactive behind it. Home renders two `PillButton` entry points, "Open Builder" and "Open Player", calling `navigate(ScreenId.BUILDER, None)` / `navigate(ScreenId.PLAYER, None)` respectively. `SettingsWindow` shows left-hand category navigation with exactly one category, "Appearance", holding a placeholder message. Every new/changed widget takes a construction-time `theme: Theme`; every screen hardcodes `Theme.LIGHT` for now.

**Block If:** None identified — the extended `mount()` signature and `ScreenId`'s relocation both follow directly from the pinned AD-10/AD-11 rules plus the Story 1.7 code already in the repo; nothing here requires a human decision.

**Never:** Do not implement theme toggling, theme persistence, or a theme-toggle icon-btn — Story 1.9's job. Do not add Ball/Difficulty/Shortcuts settings content or wire any setting through `SettingsRepository` — no such settings exist as domain concepts yet. Do not add a third breadcrumb segment (e.g. a maze name) or any screen-owned sub-navigation — Builder/Player have no sub-state until Epics 2/3. Do not make `SettingsWindow` modal (`grab_set()`) or guard against opening it twice — out of this story's declared minimal scope. Do not change `Router`'s own `navigate()`/`register()` behavior or its 2-arg `MountFn` contract — Story 1.7's `tests/app/test_router.py` must keep passing unchanged. Do not build the richer icon+description "nav-card" visual from `key-home.html` — `PillButton` entry points satisfy the AC's "shows navigation entry points" wording without that additional widget investment.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Home cold start | `build_app()` navigates to Home | Home's frame shows no breadcrumb and two entry-point buttons, "Open Builder"/"Open Player" | No error expected |
| Home → Builder | "Open Builder" clicked on Home | `navigate(ScreenId.BUILDER, None)` fires; `Router` swaps the mounted screen to Builder | No error expected |
| Breadcrumb Home click | Breadcrumb's "Home" segment clicked while Builder (or Player) is mounted | `navigate(ScreenId.HOME, None)` fires; `Router` swaps back to Home | No error expected |
| Player receives carried state | `mount(parent, some_maze, navigate)` called on Player | Player's frame renders (placeholder body, `state` otherwise unused) with a "Home / Player" breadcrumb | No error expected |
| Settings from any screen | Settings icon-btn clicked on Home, Builder, or Player | A non-modal `SettingsWindow` `Toplevel` opens showing the "Appearance" category placeholder; the underlying screen's frame stays mounted (`winfo_exists()` true) | No error expected |

</intent-contract>

## Code Map

- `src/labyrinthes/adapters/tkinter/common/navigation.py` -- new; `ScreenId` (relocated from `app/router.py`), `NavigateFn`, `ScreenMountFn` type aliases -- the shared navigation contract `home/`/`builder/`/`player/` and `app/` both depend on without creating an import cycle
- `src/labyrinthes/adapters/tkinter/common/breadcrumb.py` -- new; `BreadcrumbSegment`, `Breadcrumb(tk.Frame)` -- AD-11's shared breadcrumb widget
- `src/labyrinthes/adapters/tkinter/common/top_bar.py` -- new; `TopBar(tk.Frame)` -- brand mark + wordmark, optional `Breadcrumb`, Settings `IconButton`; composed by every screen's `mount()`
- `src/labyrinthes/adapters/tkinter/common/settings_window.py` -- new; `SettingsWindow(tk.Toplevel)` -- minimal categorized settings dialog (Appearance only, placeholder content)
- `src/labyrinthes/adapters/tkinter/common/__init__.py` -- existing; re-export `ScreenId`, `NavigateFn`, `ScreenMountFn`, `BreadcrumbSegment`, `Breadcrumb`, `TopBar`, `SettingsWindow`
- `src/labyrinthes/app/router.py` -- existing; `ScreenId` now imported from `common/navigation.py` and re-exported via `__all__`; `MountFn`/`Router` unchanged
- `src/labyrinthes/app/composition_root.py` -- existing; `build_app()` defines a `navigate()` closure over `router.navigate` and wraps each screen's 3-arg `mount` before `router.register()`
- `src/labyrinthes/adapters/tkinter/home/screen.py` -- existing; `mount()` gains `navigate`, builds a breadcrumb-less `TopBar` plus two `PillButton` entry points
- `src/labyrinthes/adapters/tkinter/builder/screen.py` -- existing; `mount()` gains `navigate`, builds a `TopBar` with a "Home / Builder" breadcrumb
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- existing; `mount()` gains `navigate`, builds a `TopBar` with a "Home / Player" breadcrumb
- `tests/adapters/tkinter/common/test_navigation.py` -- new; `ScreenId` membership, re-export identity with `labyrinthes.app.router.ScreenId`
- `tests/adapters/tkinter/common/test_breadcrumb.py` -- new; segment rendering/separators, a clickable segment invokes its callback, the trailing/current segment does not
- `tests/adapters/tkinter/common/test_top_bar.py` -- new; brand mark present, breadcrumb only rendered when segments are given, Settings icon-btn's command fires
- `tests/adapters/tkinter/common/test_settings_window.py` -- new; is a `Toplevel`, non-modal (`grab_status() == "none"`), shows the Appearance category placeholder
- `tests/app/test_router.py` -- existing, read-only; must keep passing unchanged
- `tests/app/test_composition_root.py` -- existing; `failing_mount_home` stub updated to accept 3 args; new test asserts the `navigate` closure handed to a registered screen actually drives `router.navigate`
- `tests/adapters/tkinter/home/test_home_screen.py` -- existing; `mount()` calls updated to pass a stub `navigate`; new cases for "Open Builder"/"Open Player" clicks and "no breadcrumb on Home"
- `tests/adapters/tkinter/builder/test_builder_screen.py` -- existing; `mount()` calls updated; new case for the breadcrumb's Home-click calling `navigate(ScreenId.HOME, None)`
- `tests/adapters/tkinter/player/test_player_screen.py` -- existing; `mount()` calls updated (including the real-`Maze`-as-`state` case); new case for the breadcrumb's Home-click

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/adapters/tkinter/common/navigation.py` -- add `ScreenId`, `NavigateFn`, `ScreenMountFn` -- the shared contract every screen and `app/` depend on
- [x] `src/labyrinthes/adapters/tkinter/common/breadcrumb.py` -- add `BreadcrumbSegment`, `Breadcrumb` -- clickable "Home"/current-segment rendering per `DESIGN.md`'s `.crumb` markup
- [x] `src/labyrinthes/adapters/tkinter/common/top_bar.py` -- add `TopBar` -- composes brand mark, optional `Breadcrumb`, Settings `IconButton`
- [x] `src/labyrinthes/adapters/tkinter/common/settings_window.py` -- add `SettingsWindow` -- non-modal `Toplevel`, one "Appearance" placeholder category
- [x] `src/labyrinthes/adapters/tkinter/common/__init__.py` -- re-export the four new modules' public symbols
- [x] `src/labyrinthes/app/router.py` -- import `ScreenId` from `common/navigation.py`, re-export via `__all__` -- removes the local definition without breaking existing imports
- [x] `src/labyrinthes/app/composition_root.py` -- add the `navigate()` closure and the 3-arg→2-arg `mount` binding wrapper -- bridges `Router`'s unchanged contract to the new screen contract
- [x] `src/labyrinthes/adapters/tkinter/home/screen.py` -- extend `mount()`, add `TopBar` (no breadcrumb) + "Open Builder"/"Open Player" `PillButton`s -- satisfies AC4
- [x] `src/labyrinthes/adapters/tkinter/builder/screen.py` -- extend `mount()`, add `TopBar` with "Home / Builder" breadcrumb -- satisfies AC1/AC2
- [x] `src/labyrinthes/adapters/tkinter/player/screen.py` -- extend `mount()`, add `TopBar` with "Home / Player" breadcrumb -- satisfies AC1/AC2
- [x] `tests/adapters/tkinter/common/test_navigation.py` -- cover `ScreenId` membership/re-export identity
- [x] `tests/adapters/tkinter/common/test_breadcrumb.py` -- cover the I/O matrix's breadcrumb-click rows
- [x] `tests/adapters/tkinter/common/test_top_bar.py` -- cover conditional breadcrumb rendering + Settings command firing
- [x] `tests/adapters/tkinter/common/test_settings_window.py` -- cover the I/O matrix's Settings row (non-modal, placeholder content)
- [x] `tests/app/test_composition_root.py` -- update `failing_mount_home` to 3 args; add the `navigate`-closure end-to-end test
- [x] `tests/adapters/tkinter/{home,builder,player}/test_*_screen.py` -- update `mount()` calls for the new `navigate` parameter; add per-screen entry-point/breadcrumb/Settings cases

**Acceptance Criteria:**
- Given any screen, when it renders, then a breadcrumb reflecting the actual navigation depth (e.g. "Home / Builder") is shown, with the Home segment always present and clickable
- Given an earlier breadcrumb segment, when clicked, then the router navigates directly to that level
- Given the top-bar Settings icon, when clicked from Home, Builder, or Player, then the settings-window opens as its own window (not routed through Home), and the underlying screen stays mounted behind it
- Given Home at cold start, when the app launches, then Home shows navigation entry points to Builder and Player (even while those screens are still minimal placeholders at this point in the port)

## Spec Change Log

## Review Triage Log

### 2026-08-06 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 7 (low 7)
- defer: 5 (medium 2, low 3)
- reject: 4 (low 4)
- addressed_findings:
  - `[low]` `[patch]` `Breadcrumb`'s clickable segment rested permanently in `colors.accent` with no hover state and used the wrong typography token (`body_secondary` 14px/400 instead of the locked mockups' `.crumb` 13px/600, i.e. `TYPOGRAPHY.body`) — fixed to rest in `colors.ink_soft`, added `<Enter>`/`<Leave>` handlers that swap to/from `colors.accent` (accent is hover-only per `.crumb .seg:hover`), switched the font token to `TYPOGRAPHY.body` for all labels/separators, and fixed `Breadcrumb`'s own background from `colors.panel` to `colors.window` to match the same locked `.topbar`/`.crumb` background it's meant to sit on; `test_breadcrumb.py`'s resting-color assertion (which had locked in the wrong color as "expected") updated, plus a new hover-transition test exercising the exposed `_hover_handlers` pair
  - `[low]` `[patch]` `TopBar`'s own background used `colors.panel` instead of the locked mockups' `.topbar { background: var(--c-window) }` — fixed
  - `[low]` `[patch]` `SettingsWindow`'s "Appearance" category-nav label used `TYPOGRAPHY.body` instead of `DESIGN.md`'s specified `{typography.label}` (10px/700) for category-nav text — fixed
  - `[low]` `[patch]` `_navigate_stub()`/`_find_all()` were copy-pasted verbatim across `test_home_screen.py`/`test_builder_screen.py`/`test_player_screen.py` — hoisted into `tests/adapters/tkinter/conftest.py` as `navigate_stub`/`find_all` fixtures (mirroring Story 1.7's identical `tk_root`-hoisting precedent), all three screen test files updated to consume them
  - `[low]` `[patch]` No test asserted `TopBar`'s brand mark/wordmark ("Labyrinthes") actually renders, despite that being its own docstring's headline behavior — added `test_top_bar_renders_the_brand_mark_and_wordmark` to `test_top_bar.py` and an equivalent assertion in `test_home_screen.py`

Findings routed to `deferred-work.md` (real but out of this story's declared minimal scope, none blocking any stated AC): `TopBar`'s full-perimeter border vs. the mockups' bottom-only rule (cosmetic, needs a small restructure rather than a token swap); `Router.navigate()`'s frame-teardown cascading to silently close an open `SettingsWindow` on breadcrumb-Home-click (no stateful Settings content exists yet to lose, and no AC requires survival across navigation); the breadcrumb's Home segment being mouse-only with no keyboard path (matches every other clickable `common/` widget's identical, Story-1.10-scoped gap); five independent `Theme.LIGHT` hardcodes with no shared source of truth (explicitly this story's declared scope, flagged for Story 1.9's consolidation); `TopBar`'s `breadcrumb_segments=[]` vs `None` distinction (not reachable by any current call site).

Findings rejected as noise: tests reaching into private attributes (`_breadcrumb`, `_segment_handlers`, `_on_click`, etc.) across the new/changed test files — matches this codebase's own established, deliberate testing convention (already used identically in `test_pill_btn.py`/`test_icon_btn.py`/`test_tooltip.py` since Story 1.6, with the same "`tk_root` is withdrawn, real X11 synthesis isn't reliable" rationale), not a defect newly introduced here; `SettingsWindow` allowing repeated gear-clicks to stack multiple overlapping `Toplevel`s (×3, one per screen) — this story's own spec `Never` list explicitly excludes guarding against opening it twice ("out of this story's declared minimal scope"), so this restates an already-made, deliberate scope decision rather than surfacing a missed one.

## Design Notes

- **Why `mount()` gains a `navigate` parameter instead of a `Router` reference:** passing the whole `Router` would let a screen call `register()` or read `current_screen_id`, capabilities it has no business having. A narrow `NavigateFn` callable is the minimum capability Home/Builder/Player actually need (trigger a swap), keeps `Router`'s own Story 1.7 contract/tests untouched, and keeps `adapters/tkinter/{home,builder,player}` from ever importing `app/` at all — `composition_root` is still the only place that wires the two together.
- **Why `ScreenId` moves to `common/navigation.py`:** screens need real, runtime access to `ScreenId` members (e.g. `navigate(ScreenId.HOME, None)` in a button's command, not just a type hint), so it can't stay defined in `app/router.py` without screens importing `app/` — which would invert the epic's pinned one-way dependency direction. `common/` is the one package every screen already imports from and that imports nothing back from them, so it's the natural, cycle-free home for a contract both `app/` and the three screens share. Re-exporting it unchanged from `app/router.py` keeps Story 1.7's own tests (`from labyrinthes.app.router import ScreenId`) passing without modification.
- **Why Home shows no self-breadcrumb:** the locked `key-home.html` mockup has no `.crumb` element at all — only the brand mark/wordmark. Depth-0 (already at the router's root) has nothing meaningful to show; the AC's "any screen" wording is satisfied by Builder/Player (depth 1) always carrying a clickable Home segment, matching every other locked mockup (`key-builder-edit.html`, `key-player-selection.html`, `key-player-gameplay.html`), none of which render a crumb on Home either.
- **Why `SettingsWindow` has exactly one, placeholder-content category:** `EXPERIENCE.md`/`DESIGN.md` name Appearance/Ball/Difficulty/Shortcuts as the eventual category set, but Ball/Difficulty/Shortcuts settings don't exist as domain concepts yet (Epics 2/3, Story 1.10). Stubbing categories with nothing behind them would invite dead UI; the left-hand category-nav *structure* is still built now so later stories add categories without a rework, mirroring how Story 1.7 shipped placeholder screens ahead of their real content.
- **Why `PillButton` for Home's entry points, not a new "nav-card" widget:** `key-home.html`'s icon+description cards aren't in AD-11's enumerated widget-primitive list (`tool-btn`, `hud-chip`, `icon-btn`, `pill-btn`, `kbd-tag`); the AC only requires functional "navigation entry points," which two `PillButton`s satisfy without adding a new primitive this story doesn't otherwise need.
- **Reentrancy stays safe:** `deferred-work.md`'s Story 1.7 note that `Router.navigate()` is not reentrancy-safe if called from inside a `mount()` remains true but still unreached here — `navigate` is only ever invoked from a button's click handler (Home's `PillButton`s, a `Breadcrumb` segment), which fires well after the triggering `mount()` call has already returned control to the Tk event loop, never synchronously during construction.

## Verification

**Commands:**
- `pytest -q` -- expected: full suite passes, including the new `tests/adapters/tkinter/common/` navigation/breadcrumb/top-bar/settings-window tests and the updated `tests/app/` and `tests/adapters/tkinter/{home,builder,player}/` tests
- `ruff check .` -- expected: no findings
- `ruff format --check .` -- expected: no findings

## Auto Run Result

**Summary:** Every screen's `mount()` gained a third `navigate: NavigateFn` parameter, closing the gap Story 1.7 deliberately left open (screens had no way to trigger `Router.navigate()` at all). `Router`/`Router.register`/`MountFn` (Story 1.7) stayed byte-for-byte unchanged; `composition_root.build_app()` bridges the two by binding one `navigate` closure over `router.navigate` into each screen's 3-arg `mount` before registering the resulting 2-arg adapter. `ScreenId` moved from `app/router.py` into a new `adapters/tkinter/common/navigation.py` (re-exported unchanged from `app/router.py`) so screens can reference it at runtime without importing `app/`, preserving the epic's one-way `app/ → adapters/ → application/ → domain/` dependency direction. Four new `common/` primitives were added -- `Breadcrumb`/`BreadcrumbSegment`, `TopBar`, and `SettingsWindow` -- and wired into all three screens: Home shows no self-breadcrumb (matching the locked `key-home.html` mockup) plus two `PillButton` entry points ("Open Builder"/"Open Player"); Builder/Player each show a "Home / <Screen>" breadcrumb with an always-clickable Home segment; every screen's Settings `IconButton` opens a non-modal `SettingsWindow` (`Toplevel`, no `grab_set()`) with a single "Appearance" placeholder category. A review pass then patched 7 low-severity cosmetic/test-infra findings (breadcrumb hover styling, wrong typography/background tokens, duplicated test helpers, a test-coverage gap) and deferred 5 real-but-out-of-scope findings (an open-Settings-gets-destroyed-on-navigate interaction, keyboard-inaccessibility matching every other `common/` widget's Story-1.10-scoped gap, a `Theme.LIGHT` consolidation note for Story 1.9, a `TopBar` border-shape nit, and an unreachable `breadcrumb_segments=[]` edge case), rejecting 4 findings that matched pre-existing project conventions or this story's own declared scope exclusions.

**Files changed:**
- `src/labyrinthes/adapters/tkinter/common/navigation.py` -- new; `ScreenId` (relocated from `app/router.py`), `NavigateFn`, `ScreenMountFn`
- `src/labyrinthes/adapters/tkinter/common/breadcrumb.py` -- new; `BreadcrumbSegment`, `Breadcrumb` (clickable segments rest in `ink_soft`, hover to `accent`; trailing/current segment never clickable)
- `src/labyrinthes/adapters/tkinter/common/top_bar.py` -- new; `TopBar` (brand mark/wordmark, optional `Breadcrumb`, Settings `IconButton`)
- `src/labyrinthes/adapters/tkinter/common/settings_window.py` -- new; `SettingsWindow` (non-modal `Toplevel`, one "Appearance" placeholder category)
- `src/labyrinthes/adapters/tkinter/common/__init__.py` -- re-exports the four new modules' public symbols
- `src/labyrinthes/app/router.py` -- `ScreenId` now imported from `common/navigation.py` and re-exported via `__all__`; `Router`/`MountFn` untouched
- `src/labyrinthes/app/composition_root.py` -- adds the `navigate()` closure and `_bind_navigate()` 3-arg→2-arg adapter
- `src/labyrinthes/adapters/tkinter/{home,builder,player}/screen.py` -- `mount()` extended with `navigate`; Home gets entry-point buttons, Builder/Player get "Home / <Screen>" breadcrumbs; all three get the Settings icon
- `tests/adapters/tkinter/conftest.py` -- new; shared `navigate_stub`/`find_all` fixtures (added during review, replacing three duplicated copies)
- `tests/adapters/tkinter/common/test_navigation.py`, `test_breadcrumb.py`, `test_top_bar.py`, `test_settings_window.py` -- new; cover the I/O matrix's rows for the four new primitives
- `tests/app/test_composition_root.py` -- `failing_mount_home` stub updated to 3 args; new end-to-end test proving the `navigate` closure bound into a screen actually drives the real `Router`
- `tests/adapters/tkinter/{home,builder,player}/test_*_screen.py` -- updated for the new `navigate` parameter; new per-screen entry-point/breadcrumb/Settings/brand-mark cases

**Review findings:** 7 patched (0 high, 0 medium, 7 low), 5 deferred (0 high, 2 medium, 3 low) to `deferred-work.md`, 4 rejected as matching pre-existing project conventions or this story's own declared scope exclusions. See the Review Triage Log above for the full breakdown.

**Verification:** `ruff check .` -- all checks passed. `ruff format --check .` -- all `src/`/`tests/` files format-clean (only the same pre-existing, unrelated documentation-file finding noted in prior stories remains, untouched by this story). `pytest -q` -- 217 passed, including `tests/test_architecture_boundaries.py` unchanged and green (confirming `home/`/`builder/`/`player/` still never import each other or `app/`, and `common/` still never imports the three screens).

**Residual risks:** An open `SettingsWindow` is silently discarded if the user navigates away from its parent screen (e.g. clicking the breadcrumb's Home segment) -- low risk today since Settings holds no real, stateful controls yet, but worth revisiting once a later story gives it persisted content. The breadcrumb's Home segment is mouse-only (no keyboard path), consistent with every other `common/` widget built so far and explicitly Story 1.10's stated scope to close. `Theme.LIGHT` is hardcoded in five independent places pending Story 1.9's real theme-selection wiring.
