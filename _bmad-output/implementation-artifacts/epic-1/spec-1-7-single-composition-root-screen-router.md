---
title: 'Story 1.7: Single composition root & screen router'
type: 'feature'
created: '2026-08-06'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-1/epic-1-context.md']
warnings: [oversized]
baseline_revision: 'd4d94d00674a5b727f4bd72161df1216cbe2a4b5'
final_revision: '9aacb888e4bf8b5ff2f43e4a69e0824e0d40ff00'
---

<intent-contract>

## Intent

**Problem:** `adapters/tkinter/` has only `common/` so far (Story 1.6) — there is no `app/` package, no single `Tk()` root, and no router, so Home/Builder/Player have nowhere to register as screens and nothing yet forbids them from importing each other directly.

**Approach:** Add `app/router.py` (`ScreenId` enum + `Router` swapping screens via each screen's `mount(parent, state)`), `app/composition_root.py` (builds the one `Tk()` root, registers the three screens, navigates to Home), and one minimal placeholder screen module per `home/`/`builder/`/`player/` exposing `mount()` — just enough for the router to prove itself; real screen content is later stories' job.

## Boundaries & Constraints

**Always:** `app/composition_root.py` calls `tk.Tk()` exactly once and is the only module that imports concrete screen modules (`adapters.tkinter.home.screen`, `.builder.screen`, `.player.screen`) to build the router's registry — `Router` itself never imports a screen module. `ScreenId` is an enum (`HOME`, `BUILDER`, `PLAYER`), never a bare string, used as the sole registration/navigation key. `Router.register(screen_id, mount)` stores a screen's `mount` callable; `Router.navigate(screen_id, state=None)` calls the target's `mount(container, state)`, packs the returned `Frame` into the router's container, then destroys the previously-mounted frame (new-before-old, so there's never a visible gap) and updates `current_screen_id`. Each screen module exposes a module-level `mount(parent: tk.Widget, state: Maze | None) -> tk.Frame` (AD-10's exact signature) that only constructs and returns a `Frame` parented under `parent` — no navigation, no state mutation beyond accepting the parameter. Composition root builds `Router`, registers all three screens, then calls `navigate(ScreenId.HOME)` before `mainloop()`, so Home is always the first mounted screen. `Router.navigate()` on an unregistered `ScreenId` raises a typed `UnregisteredScreenError` (subclasses `LabyrinthesError`), never a bare `KeyError`.

**Block If:** None identified — AD-10 fully pins the composition root/router contract this story implements; nothing here requires a human decision.

**Never:** Do not build the breadcrumb, real Home navigation entry points, the Settings dialog, theme wiring, or the canonical keybinding table — Stories 1.8/1.9/1.10. Do not give Builder/Player screens real maze-canvas content, HUD, or any domain-service wiring — Epics 2/3. Do not implement the Test-in-Player/Edit-in-Builder state-carrying transitions (later stories reuse this story's `Router.navigate(screen_id, state)` for that, but wiring the actual triggers is not this story's job). Do not add a second `Tk()` instance anywhere, including in tests — reuse the existing `tk_root`-style pattern (create, `withdraw()`, `destroy()` at teardown). Do not have `app/` or a screen module import `adapters/storage/` directly.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Cold start | `build_app()` called | Exactly one `tk.Tk()` created; `router.current_screen_id == ScreenId.HOME`; the mounted frame came from `home.screen.mount` | No error expected |
| Screen swap | `router.navigate(ScreenId.BUILDER, state=None)` after Home is mounted | Builder's `mount(container, None)` is called, its frame is packed, Home's prior frame is destroyed, `current_screen_id == ScreenId.BUILDER` | No error expected |
| State hand-off | `router.navigate(ScreenId.PLAYER, state=some_maze)` | Player's `mount(container, some_maze)` receives that exact `Maze` instance | No error expected |
| Unregistered screen | `router.navigate(ScreenId.PLAYER)` before `register(ScreenId.PLAYER, ...)` | Nothing is mounted, prior screen stays as-is | Raises `UnregisteredScreenError` |
| First navigate | `router.navigate(...)` called when no screen has been mounted yet | New frame is mounted; no teardown attempted (nothing to destroy) | No error expected |

</intent-contract>

## Code Map

- `src/labyrinthes/app/__init__.py` -- new; package docstring naming this as the shell/composition root (AD-10)
- `src/labyrinthes/app/errors.py` -- new; `UnregisteredScreenError(LabyrinthesError)`, mirroring `adapters/storage/errors.py`'s convention
- `src/labyrinthes/app/router.py` -- new; `ScreenId` enum, `MountFn` type alias, `Router` (`register`, `navigate`, `current_screen_id`)
- `src/labyrinthes/app/composition_root.py` -- new; `App` (frozen dataclass: `root`, `router`), `build_app() -> App`, `main() -> None`
- `src/labyrinthes/app/__main__.py` -- new; `python -m labyrinthes.app` entry point, calls `composition_root.main()`
- `src/labyrinthes/adapters/tkinter/home/__init__.py` -- new; re-exports `mount`
- `src/labyrinthes/adapters/tkinter/home/screen.py` -- new; placeholder `mount(parent, state) -> tk.Frame`
- `src/labyrinthes/adapters/tkinter/builder/__init__.py` -- new; re-exports `mount`
- `src/labyrinthes/adapters/tkinter/builder/screen.py` -- new; placeholder `mount(parent, state) -> tk.Frame`
- `src/labyrinthes/adapters/tkinter/player/__init__.py` -- new; re-exports `mount`
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- new; placeholder `mount(parent, state) -> tk.Frame`
- `src/labyrinthes/domain/maze.py` -- existing, read-only; `Maze`/`MazeKind` used for the `state` type hint and tests
- `tests/test_architecture_boundaries.py` -- existing, read-only; already scans `home/`/`builder/`/`player/`/`common/`/`adapters.storage` for lateral imports and must keep passing unchanged against this story's new files
- `tests/app/test_router.py` -- new; covers the I/O matrix's swap/state-handoff/unregistered/first-navigate rows
- `tests/app/test_composition_root.py` -- new; covers the cold-start row (single `Tk()`, Home mounted first) and `main()` wiring `build_app()` to `mainloop()`
- `tests/adapters/tkinter/home/test_home_screen.py` -- new; `mount()` returns a `Frame` parented under the given parent (renamed from `test_screen.py` during review to give each screen's test file a unique basename, avoiding a pytest same-basename collision without a global `--import-mode` change)
- `tests/adapters/tkinter/builder/test_builder_screen.py` -- new; same, for Builder
- `tests/adapters/tkinter/player/test_player_screen.py` -- new; same, for Player, plus a case passing a real `Maze` as `state`
- `tests/conftest.py` -- new; the shared `tk_root` fixture, hoisted here during review to replace four identical per-directory copies

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/app/__init__.py` -- add package docstring, no imports -- establishes the package before submodules need it
- [x] `src/labyrinthes/app/errors.py` -- add `UnregisteredScreenError(LabyrinthesError)` -- typed error for `Router.navigate()` on an unregistered `ScreenId`
- [x] `src/labyrinthes/app/router.py` -- add `ScreenId`, `MountFn`, `Router` -- the screen-swap mechanism every later story navigates through
- [x] `src/labyrinthes/adapters/tkinter/home/screen.py` + `__init__.py` -- add placeholder `mount()` -- the AC's "Home is the initial screen" target
- [x] `src/labyrinthes/adapters/tkinter/builder/screen.py` + `__init__.py` -- add placeholder `mount()` -- registers Builder with the router ahead of Epic 3's real content
- [x] `src/labyrinthes/adapters/tkinter/player/screen.py` + `__init__.py` -- add placeholder `mount()` -- registers Player with the router ahead of Epic 2's real content
- [x] `src/labyrinthes/app/composition_root.py` -- add `App`, `build_app()`, `main()` -- wires the single `Tk()` root, registers all three screens, navigates to Home
- [x] `src/labyrinthes/app/__main__.py` -- add `python -m labyrinthes.app` entry point
- [x] `tests/app/test_router.py` -- cover register/navigate, teardown-after-mount ordering, state hand-off, `UnregisteredScreenError`, first-navigate-with-nothing-to-destroy
- [x] `tests/app/test_composition_root.py` -- cover single `Tk()` + Home-mounted-first, and `main()` calling `mainloop()` on the built root
- [x] `tests/adapters/tkinter/{home,builder,player}/test_screen.py` -- cover each placeholder's `mount()` contract

**Acceptance Criteria:**
- Given the shell starts, when it launches, then exactly one `Tk()` root exists and Home is the initial screen
- Given a screen enum member and a `Maze | None` state, when the router swaps screens, then the target screen's `mount(parent, state)` is called and the previous screen is torn down
- Given Home, Builder, and Player, when their imports are inspected, then none imports another directly — all navigation goes through `app/`'s router (verified by the existing `tests/test_architecture_boundaries.py` passing unchanged)

## Spec Change Log

## Review Triage Log

### 2026-08-06 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 3 (medium 1, low 2)
- defer: 7 (medium 2, low 5)
- reject: 2 (low 2)
- addressed_findings:
  - `[low]` `[patch]` Four identical `tk_root` conftest.py fixtures were duplicated across `tests/app/`, `tests/adapters/tkinter/{home,builder,player}/` -- hoisted into one `tests/conftest.py`; pytest's ancestor-directory conftest discovery makes it visible to every test unchanged, and the pre-existing `tests/adapters/tkinter/common/conftest.py` copy was left alone (out of this story's diff, no functional issue from leaving it)
  - `[low]` `[patch]` The three new `test_screen.py` files shared a basename across `home/`/`builder/`/`player/` with no `__init__.py` in `tests/` (matching the rest of the suite), which the initial implementation had "fixed" with a suite-wide `addopts = "--import-mode=importlib"` in `pyproject.toml` -- verified the collision is real (`pytest` fails with "import file mismatch" without it) but replaced the global config change with the narrower fix of renaming each file uniquely (`test_home_screen.py`/`test_builder_screen.py`/`test_player_screen.py`) and reverted the `pyproject.toml` edit, since a suite-wide collection-mode change has broader semantic reach (conftest resolution, sys.path handling) than this story's own scope warrants
  - `[medium]` `[patch]` `build_app()` leaked its just-created `tk.Tk()` root if wiring failed partway through (e.g. a screen's `mount()` raising during `router.navigate(ScreenId.HOME)`) -- wrapped the wiring in `try`/`except Exception: root.destroy(); raise`, so a startup failure no longer leaves an orphaned, never-shown Tk window; added `test_build_app_destroys_the_root_if_wiring_fails_partway_through` as a regression test

Findings routed to `deferred-work.md` (real but out of this story's declared minimal scope, none blocking any stated AC): `Router.navigate()` has no exception-safety if a registered `mount()` callable raises mid-construction -- any widgets it already created are orphaned and the exception propagates raw, with no test exercising "a screen's own `mount()` blows up"; `Router.navigate()`'s returned frame from `mount()` is never validated as a `tk.Frame` before `.pack()` is called on it, so a misbehaving screen surfaces as a bare `AttributeError` instead of a clear error; `Router.navigate()` is not reentrancy-safe -- a `mount()` callback that itself calls `navigate()` would corrupt `_current_frame`/`_current_screen_id` bookkeeping; `previous_frame.destroy()` isn't guarded -- if it raises, the frame-swap's bookkeeping update never runs, leaving `current_screen_id`/`_current_frame` pointing at the torn-down screen while the new one is already visible; `Router.register()` silently overwrites an existing `ScreenId` registration and `navigate()` always tears down and rebuilds even when re-navigating to the already-current screen -- neither is tested or specified as intentional; `test_navigate_to_unregistered_screen_raises_and_leaves_current_screen_mounted`'s "leaves current screen mounted" claim is only checked via `winfo_exists()`, not `winfo_ismapped()` -- verified empirically that `winfo_ismapped()` returns `False` for any packed widget under this suite's convention of an immediately-`withdraw()`-ed root, so the seemingly-obvious stronger assertion would false-fail here and needs a different verification approach, not a one-line fix.

Findings rejected as noise: `home/screen.py`/`builder/screen.py`/`player/screen.py` importing `Maze` at module scope purely for the `state: Maze | None` annotation (under `from __future__ import annotations`) -- matches the exact same pattern already established in `application/maze_repository.py` (no `TYPE_CHECKING` guard there either), consistent with the project's no-static-type-checker, hints-as-documentation convention; the three screens' `__init__.py` re-exporting `mount` with no current consumer of the package-level import (only `screen.py`-qualified imports are used today) -- mirrors every other package's `__init__.py` convention in this codebase (`adapters/storage/`, `adapters/tkinter/common/`) and was explicitly called for in this story's own Code Map; the screen docstrings' "(AD-1, AD-9)" citation for the "never import sibling screens / never import `adapters/storage/`" claim technically omits AD-10 (the actual lateral-import rule; AD-9 is its enforcement) -- but this exact citation pattern is copied verbatim from `adapters/tkinter/common/__init__.py` (Story 1.6, already reviewed and merged), so it's pre-existing convention, not a defect newly introduced here.

## Design Notes

- **New-before-old teardown:** `Router.navigate()` mounts the target screen and packs it before destroying the previous frame, so there's never a frame-less gap mid-swap. The AC only requires the previous screen to end up "torn down" — the ordering is this story's implementation choice, not a spec requirement, and is called out here so a reviewer doesn't mistake it for an oversight.
- **`App` is a plain frozen dataclass, not an attribute bolted onto `tk.Tk`:** keeps `build_app()` testable (assert on `app.router.current_screen_id` etc.) without monkey-patching a stdlib widget instance.
- **Screens don't need `ScreenId`:** only `composition_root.py` imports both the concrete screen modules and `ScreenId` to build the registry; `Router` and the screen modules themselves never need to know about each other, keeping the "screens never import each other" boundary trivially true rather than merely tested.

## Verification

**Commands:**
- `pytest -q` -- expected: full suite passes, including the new `tests/app/` and `tests/adapters/tkinter/{home,builder,player}/` tests
- `ruff check .` -- expected: no findings
- `ruff format --check .` -- expected: no findings

## Auto Run Result

**Summary:** Added `src/labyrinthes/app/` -- the project's single composition root and screen router (`ScreenId`, `MountFn`, `Router`, `UnregisteredScreenError`, `App`, `build_app()`, `main()`, and a `python -m labyrinthes.app` entry point) -- plus minimal placeholder `mount(parent, state)` screens for `home/`, `builder/`, `player/`. `composition_root.py` is the sole module that imports concrete screen modules; `Router` only ever calls the `MountFn` callables it was `register()`-ed with, keeping the "screens never import each other" boundary trivially true. This closes the gap Story 1.8+ needs: Home/Builder/Player now have somewhere to register, and later stories can reuse `Router.navigate(screen_id, state)` for the Test-in-Player/Edit-in-Builder hand-offs. A review pass then patched one real robustness gap (a leaked `Tk()` root on startup failure) and two test-hygiene issues (duplicated fixtures, an over-broad global pytest config change), deferring six lower-priority `Router` edge cases and rejecting three findings that matched pre-existing project conventions.

**Files changed:**
- `src/labyrinthes/app/__init__.py` -- new; package docstring for the composition-root/router shell (AD-10)
- `src/labyrinthes/app/errors.py` -- new; `UnregisteredScreenError(LabyrinthesError)`
- `src/labyrinthes/app/router.py` -- new; `ScreenId` enum, `MountFn` type alias, `Router` (`register`, `navigate`, `current_screen_id`)
- `src/labyrinthes/app/composition_root.py` -- new; `App` (frozen dataclass: `root`, `router`), `build_app() -> App` (wraps its wiring in `try`/`except Exception: root.destroy(); raise`, added during review so a startup failure can't leak an orphaned `Tk()` window), `main() -> None`
- `src/labyrinthes/app/__main__.py` -- new; `python -m labyrinthes.app` entry point, calls `composition_root.main()`
- `src/labyrinthes/adapters/tkinter/home/screen.py` + `__init__.py` -- new; placeholder `mount(parent, state) -> tk.Frame` labeled "Home", re-exported
- `src/labyrinthes/adapters/tkinter/builder/screen.py` + `__init__.py` -- new; placeholder `mount(parent, state) -> tk.Frame` labeled "Builder", re-exported
- `src/labyrinthes/adapters/tkinter/player/screen.py` + `__init__.py` -- new; placeholder `mount(parent, state) -> tk.Frame` labeled "Player", re-exported
- `tests/conftest.py` -- new; the shared `tk_root` fixture, hoisted here during review to replace four identical per-directory copies
- `tests/app/test_router.py` -- new; register+navigate, new-before-old teardown ordering, state hand-off with a real `Maze`, `UnregisteredScreenError` on an unregistered screen (current screen stays mounted), first-navigate-with-nothing-to-destroy
- `tests/app/test_composition_root.py` -- new; `build_app()` produces exactly one `tk.Tk` with Home mounted first, `main()` invokes `mainloop()` on a monkeypatched `build_app()`'s fake root, and (added during review) `build_app()` destroys its root if a screen's `mount()` raises partway through wiring
- `tests/adapters/tkinter/home/test_home_screen.py`, `.../builder/test_builder_screen.py`, `.../player/test_player_screen.py` -- new (renamed from `test_screen.py` during review for a unique basename per file); `mount(tk_root, None)` returns a `Frame` parented under `tk_root`; Player's also covers `mount(tk_root, a_real_maze)` not raising

**Review findings:** 3 patched (1 medium, 2 low), 7 deferred (2 medium, 5 low) to `deferred-work.md`, 3 rejected as matching pre-existing project conventions. See the Review Triage Log above for the full breakdown and reasoning.

**Verification:** `ruff check .` -- all checks passed. `ruff format --check .` -- only a pre-existing, unrelated finding in `_bmad-output/implementation-artifacts/1-1-domain-model-foundation.md` (a documentation code-block comment-alignment nit, untouched by this story); all `src/`/`tests/`/`pyproject.toml` files format-clean. `pytest -q` -- 186 passed, including `tests/test_architecture_boundaries.py` and `tests/test_architecture_boundaries_scanner.py` unchanged and green.

**Residual risks:** `Router` has no exception-safety, reentrancy guard, or return-type validation around a screen's own `mount()` call (deferred above) -- low risk today since all three registered screens are static placeholders that never raise or misbehave, but worth revisiting once Stories 1.8+/Epics 2-3 give screens real logic that could fail mid-mount.
