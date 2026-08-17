---
baseline_commit: a757ec25552eaed6d0f257b90450f4d6a92c4728
---

# Story 1.11: Settings dialog survives screen navigation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->
<!-- Added by the Epic 1 retrospective (_bmad-output/implementation-artifacts/epic-1/epic-1-retro-2026-08-09.md) -- closes a gap independently deferred three times (Stories 1.8, 1.9, 1.10) without ever being fixed. Not derived from an epics.md FR; a hardening story on Epic 1's own architecture (AD-10). -->

## Story

As a user,
I want the Settings dialog to never disappear as an accidental side effect of navigating away from the screen it was opened on,
so that closing Settings is always something I chose, not something that happened to me.

## Acceptance Criteria

1. **Given** `SettingsWindow` is open over any screen (Home, Builder, or Player), **when** a navigation is triggered (a breadcrumb click, the theme toggle, or a keyboard shortcut that calls `Router.navigate()`), **then** `SettingsWindow`'s lifecycle is no longer an undocumented, untested side effect of the previous screen's frame being torn down -- its fate is a deliberate, explicitly documented and tested outcome.
2. **Given** the documented behavior, **when** `Router.navigate()` is invoked (directly, or via a screen's own frame being destroyed the same way) while `SettingsWindow` is open, **then** an automated test asserts the resulting `SettingsWindow` state matches that documented behavior exactly.
3. **Given** the fix, **when** exercised from Home, Builder, and Player, **then** all three screens exhibit identical behavior -- no per-screen divergence.

## Tasks / Subtasks

> **Revised after code review (2026-08-09).** The original implementation below (Task 1 as first written) chose to document the close-on-navigate cascade as intentional rather than fix it, reasoning that "nothing stateful to lose" carried the decision the same way it had for Stories 1.8-1.10. Code review flagged that this contradicted the Epic 1 retrospective's own Decision #1 / Action Item #1 ("**Fix** `Router.navigate()` silently closing an open `SettingsWindow`," filed critical-path specifically because the "nothing to lose yet" reasoning stops holding once Epic 2 lands real stateful UI). Max's call: honor the retro's original fix intent. Task 1 below reflects what was actually implemented as a result -- real survival, not documentation of non-survival. Struck-through bullets are kept for audit trail (what the first pass did and why it was insufficient), not deleted, matching this project's append-only ethos elsewhere (`deferred-work.md`).

- [x] **Task 1 -- Make `SettingsWindow` actually survive `Router.navigate()`** (AC: 1)
  - [x] Reparent `SettingsWindow` from its opening screen's `frame` to `parent` -- the app's persistent container that `Router` passes into every screen's `mount()` and that `Router.navigate()` never destroys. Each screen's `open_settings()` now constructs `SettingsWindow(parent, theme=theme)` instead of `SettingsWindow(frame, theme=theme)`, so Tk's parent-child `Toplevel` destroy-cascade no longer reaches it when `previous_frame.destroy()` runs.
  - [x] Update the `open_settings()` comment in all three screens (`home/screen.py`, `builder/screen.py`, `player/screen.py`) to explain the new `parent`-not-`frame` parenting and why it makes `SettingsWindow` survive navigation.
  - [x] Rewrite `SettingsWindow`'s module docstring (`src/labyrinthes/adapters/tkinter/common/settings_window.py`) to describe the real lifecycle: survives `Router.navigate()`, why the old `frame`-parented behavior broke that across Stories 1.8-1.10, and why the retro judged it unsafe to defer a 4th time. Also documents a residual, deliberately-unfixed gap: a surviving `SettingsWindow` doesn't re-theme itself live if the theme is toggled while it's open (not reachable in a way that matters yet -- `_APPEARANCE_PLACEHOLDER` is still the only content).
  - ~~[x] Keep `SettingsWindow` parented to its opening screen's `frame` (unchanged) -- do not reparent it to the `Tk` root or otherwise decouple it from the frame's lifecycle. ... Reparenting to survive navigation would be speculative scope creep for content that doesn't exist yet.~~ (superseded -- see note above)
- [x] **Task 2 -- Regression tests pinning the behavior across all three screens** (AC: 2, 3)
  - [x] In each of `tests/adapters/tkinter/home/test_home_screen.py`, `tests/adapters/tkinter/builder/test_builder_screen.py`, `tests/adapters/tkinter/player/test_player_screen.py`, renamed the new test to `test_destroying_the_screens_frame_leaves_an_open_settings_window_open`: mounts the screen, opens `SettingsWindow` via the real `on_settings` path (`top_bar._settings_button._on_click()`), captures the `SettingsWindow` instance via `tk_root.winfo_children()` (its new master) filtered by `isinstance(..., SettingsWindow)`, then calls `frame.destroy()` (the exact operation `Router.navigate()`'s `previous_frame.destroy()` performs) and asserts the captured `SettingsWindow` **still exists** (`winfo_exists() == 1`). Also updated the pre-existing `test_settings_icon_click_opens_a_non_modal_settings_window_leaving_*_mounted` test in each file, which was filtering `frame.winfo_children()` and would otherwise have started silently finding zero `SettingsWindow`s once the reparenting landed.
  - [x] Added one true end-to-end regression, `test_settings_window_opened_on_home_survives_a_real_navigate_to_builder` (`tests/app/test_composition_root.py`), using the real `build_app()`/`Router.navigate()` (not `navigate_stub`) to prove survival through the actual mechanism, not just an isolated `frame.destroy()` call mirroring it.
  - [x] Confirmed the assertion and its setup are identical in shape across all three per-screen tests -- no per-screen divergence in what's being proven (AC 3).
- [x] **Task 3 -- Close the loop in `deferred-work.md`** (AC: 1)
  - [x] Appended a resolution note to the two matching entries (Story 1.8's breadcrumb-click finding, Story 1.10's keyboard-shortcut finding) describing the actual fix (`parent`-not-`frame` reparenting), not just "documented as intentional."

### Review Findings

- [x] [Review][Decision] Story reinterprets the retro's "fix" mandate as "document as intentional," leaving the underlying risk carried unresolved into Epic 2 — `epic-1-retro-2026-08-09.md`'s Decision #1 and Action Item #1 both say "**Fix** `Router.navigate()` silently closing an open `SettingsWindow` on frame-teardown," filed "critical path," explicitly because "the 'nothing to lose yet' justification that carried this deferral through three stories no longer holds once Epic 2 lands." — **Resolved: reopened and implemented.** Max chose to honor the retro's original fix intent rather than accept the "document as intentional" outcome. `SettingsWindow` is now reparented to `parent` (the persistent container) instead of `frame`, so it genuinely survives `Router.navigate()`; the three per-screen tests and the new end-to-end `test_composition_root.py` test assert survival, not closure; `deferred-work.md`'s two resolution notes now describe the real fix; `sprint-status.yaml`'s action item 1 is updated to `done`.
- [x] [Review][Patch] `SettingsWindow` docstring overstates its `deferred-work.md` evidence trail -- claims closing was "explicitly accepted three times... (Stories 1.8, 1.9, 1.10; see `deferred-work.md`'s matching entries)," but only two entries in that file describe this mechanism (1.8, 1.10). — **Fixed:** superseded by the Task 1 docstring rewrite (describes the real survival fix, not the old three-times-deferred closing behavior), so the overstated claim no longer exists.
- [x] [Review][Defer] `open_settings()` has no guard against opening multiple `SettingsWindow` instances -- repeated settings-icon clicks stack independent `Toplevel`s with no dedup, across all three screens [src/labyrinthes/adapters/tkinter/home/screen.py:51, src/labyrinthes/adapters/tkinter/builder/screen.py:41, src/labyrinthes/adapters/tkinter/player/screen.py:41] -- deferred, pre-existing: the `SettingsWindow(...)` construction call itself predates this diff (only its argument and surrounding comment changed), and this story's scope is real-survival + tests for the close-on-navigate behavior, not general instance management. Now arguably more worth revisiting sooner than before, since a surviving `SettingsWindow` can accumulate across more navigations than a closing one ever could -- noted in `deferred-work.md`.

## Dev Notes

### Architecture patterns & constraints

- **AD-10 (single shell, Home-routed screen navigation):** "Settings is not a fourth router screen: per AD-11, it is a `common/`-hosted dialog (its own `Toplevel`) invoked directly by whichever screen's Settings affordance triggered it, so the underlying screen stays mounted (visible/paused) behind it rather than being swapped out." This story does not change that contract -- Settings still isn't router-tracked, and opening it still leaves the underlying screen mounted. It now also makes the dialog outlive the screen that opened it, rather than being torn down as an accidental side effect. [Source: architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md#AD-10]
- **`Router.navigate()`'s new-before-old ordering** (`src/labyrinthes/app/router.py`): mounts the new frame, packs it, *then* destroys `previous_frame`. `SettingsWindow` is now a real Tk child `Toplevel` of `parent` (the persistent container `Router` passes into every screen's `mount()`), constructed as `SettingsWindow(parent, theme=theme)` in each screen's `open_settings()` -- not of `previous_frame` -- so `previous_frame.destroy()` no longer cascades into destroying it. `Router` itself is untouched: it still correctly and intentionally never knows about `SettingsWindow` (it only knows `ScreenId`/`MountFn`, per its own docstring's "never imports a concrete screen module"); the fix lives entirely in which widget each screen passes as `SettingsWindow`'s master.
- **Reparenting was reconsidered mid-story (see Review Findings above).** The first implementation pass kept the original "narrow, mechanical, avoid scope creep" framing -- document + test the existing close-on-navigate cascade rather than fix it -- reasoning `SettingsWindow` has nothing stateful to lose yet. Code review found that this contradicted the Epic 1 retrospective's own critical-path Action Item #1 ("Fix ... closing"), filed explicitly because that "nothing to lose" reasoning stops holding once Epic 2 lands. Max's call: implement the real fix now. The `Router`-level scope boundary (no `Router`-level Settings-awareness mechanism, no "confirm before closing" prompt) still holds -- the fix needed only a one-argument change in each screen's `open_settings()`, not a `Router` redesign.
- **No FR binds this story** -- it originates from the Epic 1 retrospective, not `epics.md`'s original FR list. Treat AC 1-3 above as the complete scope; nothing else is implied.

### Project Structure Notes

- Files this story **updates** (no new modules):
  - `src/labyrinthes/adapters/tkinter/common/settings_window.py` -- docstring, describing the real survival fix and its one residual documented gap (no live re-theming while open across a theme toggle).
  - `src/labyrinthes/adapters/tkinter/home/screen.py`, `.../builder/screen.py`, `.../player/screen.py` -- `open_settings()`: `SettingsWindow(frame, theme=theme)` -> `SettingsWindow(parent, theme=theme)`, plus updated comment. This is the actual behavior change.
  - `tests/adapters/tkinter/home/test_home_screen.py`, `.../builder/test_builder_screen.py`, `.../player/test_player_screen.py` -- the pre-existing "opens settings" test's lookup moved from `frame.winfo_children()` to `tk_root.winfo_children()`; the new regression test renamed and flipped to assert survival.
  - `tests/app/test_composition_root.py` -- new end-to-end survival test exercising the real `Router`/`build_app()`, not `navigate_stub`.
  - `_bmad-output/implementation-artifacts/deferred-work.md` -- append-only resolution notes on existing entries.
- No changes to `src/labyrinthes/app/router.py`, `src/labyrinthes/app/composition_root.py`, or any `application/`/`domain/` module -- this is a `common/`- and screen-level docs+tests story only.

### Testing standards summary

- `pytest`, existing per-screen test files under `tests/adapters/tkinter/{home,builder,player}/`, following the established `tk_root`/`navigate_stub`/`toggle_theme_stub`/`find_all` fixture conventions already hoisted into `tests/conftest.py` / `tests/adapters/tkinter/conftest.py` -- reuse them, don't reinvent per-test setup.
- Mirror `test_settings_icon_click_opens_a_non_modal_settings_window_leaving_home_mounted` (`tests/adapters/tkinter/home/test_home_screen.py:84`) for how to open `SettingsWindow` via the real click path and locate it via `frame.winfo_children()` + `isinstance(..., SettingsWindow)`.
- `ruff check .` and `ruff format .` must both pass, per every prior story in this epic.

### References

- [Source: _bmad-output/implementation-artifacts/epic-1/epic-1-retro-2026-08-09.md#Decisions Made in This Retrospective, #Action Items]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md#Deferred from: code review of spec-1-8-home-breadcrumb-navigation-settings-access (2026-08-06)]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md#Deferred from: code review of spec-1-10-accessibility-floor-keyboard-shortcut-consistency (2026-08-09)]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.11: Settings dialog survives screen navigation]
- [Source: architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md#AD-10, AD-11]
- [Source: src/labyrinthes/app/router.py, src/labyrinthes/adapters/tkinter/common/settings_window.py, src/labyrinthes/adapters/tkinter/home/screen.py]
- [Source: tests/adapters/tkinter/home/test_home_screen.py:84 (existing settings-open test pattern to mirror)]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5)

### Debug Log References

- First pass: `ruff check .` all checks passed; `ruff format --check .` clean on the 6 touched files (same one unrelated pre-existing flag on `1-1-domain-model-foundation.md`); `pytest -q` -- 281 passed.
- Post-review pass (real survival fix): `ruff check .` -- all checks passed. `ruff format --check .` -- the files this story touches remain formatted; the same unrelated pre-existing `1-1-domain-model-foundation.md` flag persists, still out of scope. `pytest -q` -- 282 passed, 0 failed (281 plus the new end-to-end `test_composition_root.py` regression).

### Completion Notes List

- **Post-review revision (see Review Findings):** the first pass below documented the close-on-navigate cascade as intentional; code review found that contradicted the retro's critical-path "fix" mandate, and Max chose to implement the real fix. `SettingsWindow` is now constructed as `SettingsWindow(parent, theme=theme)` (the persistent container) instead of `SettingsWindow(frame, theme=theme)` (the screen's own frame) in all three screens' `open_settings()` -- one argument change per screen, no `Router`/`composition_root` changes needed, since `Router.navigate()` was already passing that persistent container in as `parent` to every screen's `mount()`.
- `SettingsWindow`'s module docstring now documents the real survival lifecycle plus one residual, deliberately-unfixed gap: it doesn't live-re-theme if the theme is toggled while it's open (unreachable in a way that matters yet -- placeholder content only).
- Renamed and flipped all three per-screen regression tests to `test_destroying_the_screens_frame_leaves_an_open_settings_window_open`, asserting `winfo_exists() == 1` after `frame.destroy()`; also fixed the pre-existing `test_settings_icon_click_opens_...` test in each file, which was filtering `frame.winfo_children()` and would have silently found zero `SettingsWindow`s once its master changed to `tk_root`/`parent`.
- Added a genuine end-to-end regression (`tests/app/test_composition_root.py`) driving the real `build_app()` + `Router.navigate()` (not `navigate_stub`), so survival is proven through the actual mechanism at least once, not only via the per-screen `frame.destroy()` mirror.
- Updated the two `deferred-work.md` "Resolved by Story 1.11" notes to describe the real fix (reparenting) rather than "documented as intentional."
- Updated `sprint-status.yaml`'s action item 1 (`Fix Router.navigate() silently closing an open SettingsWindow on frame-teardown`) to `status: done`.
- All three acceptance criteria verified against the real fix: AC1 (`SettingsWindow`'s fate -- now staying open -- is deliberate, documented, and tested, not accidental), AC2 (automated test per screen plus one end-to-end test asserting the documented survival outcome), AC3 (identical test shape across Home/Builder/Player, no per-screen divergence).

### File List

- `src/labyrinthes/adapters/tkinter/common/settings_window.py` (modified -- docstring + real lifecycle description)
- `src/labyrinthes/adapters/tkinter/home/screen.py` (modified -- `SettingsWindow(frame, ...)` -> `SettingsWindow(parent, ...)`, comment)
- `src/labyrinthes/adapters/tkinter/builder/screen.py` (modified -- same)
- `src/labyrinthes/adapters/tkinter/player/screen.py` (modified -- same)
- `tests/adapters/tkinter/home/test_home_screen.py` (modified -- fixed existing test's lookup + renamed/flipped regression test)
- `tests/adapters/tkinter/builder/test_builder_screen.py` (modified -- same)
- `tests/adapters/tkinter/player/test_player_screen.py` (modified -- same)
- `tests/app/test_composition_root.py` (modified -- new end-to-end survival regression)
- `_bmad-output/implementation-artifacts/deferred-work.md` (modified -- resolution notes, updated to describe the real fix; one new deferred entry from this story's own review)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified -- status tracking; action item 1 -> done)

## Change Log

- 2026-08-09: First pass -- documented and pinned the close-on-navigate `SettingsWindow` lifecycle as a deliberate, tested (non-survival) behavior across Home/Builder/Player. No behavior change.
- 2026-08-09: Code review found the first pass contradicted the Epic 1 retrospective's critical-path fix mandate (Action Item #1). Reopened and implemented the real fix: `SettingsWindow` is reparented from its opening screen's `frame` to the persistent `parent` container, so it now genuinely survives `Router.navigate()` across Home, Builder, and Player. Regression tests updated to match; `deferred-work.md` and `sprint-status.yaml` updated to reflect the real outcome.
