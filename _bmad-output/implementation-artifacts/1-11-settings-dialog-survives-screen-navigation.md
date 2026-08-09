---
baseline_commit: a757ec25552eaed6d0f257b90450f4d6a92c4728
---

# Story 1.11: Settings dialog survives screen navigation

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->
<!-- Added by the Epic 1 retrospective (_bmad-output/implementation-artifacts/epic-1-retro-2026-08-09.md) -- closes a gap independently deferred three times (Stories 1.8, 1.9, 1.10) without ever being fixed. Not derived from an epics.md FR; a hardening story on Epic 1's own architecture (AD-10). -->

## Story

As a user,
I want the Settings dialog to never disappear as an accidental side effect of navigating away from the screen it was opened on,
so that closing Settings is always something I chose, not something that happened to me.

## Acceptance Criteria

1. **Given** `SettingsWindow` is open over any screen (Home, Builder, or Player), **when** a navigation is triggered (a breadcrumb click, the theme toggle, or a keyboard shortcut that calls `Router.navigate()`), **then** `SettingsWindow`'s lifecycle is no longer an undocumented, untested side effect of the previous screen's frame being torn down -- its fate is a deliberate, explicitly documented and tested outcome.
2. **Given** the documented behavior, **when** `Router.navigate()` is invoked (directly, or via a screen's own frame being destroyed the same way) while `SettingsWindow` is open, **then** an automated test asserts the resulting `SettingsWindow` state matches that documented behavior exactly.
3. **Given** the fix, **when** exercised from Home, Builder, and Player, **then** all three screens exhibit identical behavior -- no per-screen divergence.

## Tasks / Subtasks

- [x] **Task 1 -- Make the close-on-navigate behavior a documented, deliberate decision** (AC: 1)
  - [x] Keep `SettingsWindow` parented to its opening screen's `frame` (unchanged) -- do **not** reparent it to the `Tk` root or otherwise decouple it from the frame's lifecycle. This is a deliberate scope decision, not an oversight: `SettingsWindow`'s only real content today ("Appearance") is still a placeholder (`_APPEARANCE_PLACEHOLDER = "Appearance settings are coming soon."` in `settings_window.py`) -- there is nothing stateful to lose by letting it close, exactly the reasoning the original Story 1.8 deferral already used. Reparenting to survive navigation would be speculative scope creep for content that doesn't exist yet; revisit only once a future story gives `SettingsWindow` real persisted draft state worth protecting.
  - [x] `home/screen.py`'s `open_settings()` already documents this ("`frame` (not `parent`) as the `Toplevel`'s master: closing Home never has to hunt this window down separately, and it never touches the router -- the screen underneath stays mounted"). Add the equivalent comment to `builder/screen.py`'s and `player/screen.py`'s `open_settings()` closures, which currently have none.
  - [x] Add a note to `SettingsWindow`'s module docstring (`src/labyrinthes/adapters/tkinter/common/settings_window.py`) stating explicitly that it is destroyed as a `Toplevel` child when its opening screen's `frame` is torn down by `Router.navigate()`, cross-referencing this story so a future reader doesn't have to rediscover it via `deferred-work.md` a fourth time.
- [x] **Task 2 -- Regression tests pinning the behavior across all three screens** (AC: 2, 3)
  - [x] In each of `tests/adapters/tkinter/home/test_home_screen.py`, `tests/adapters/tkinter/builder/test_builder_screen.py`, `tests/adapters/tkinter/player/test_player_screen.py`, add a test (e.g. `test_destroying_the_screens_frame_closes_an_open_settings_window`) that: mounts the screen, opens `SettingsWindow` via the real `on_settings` path (`top_bar._settings_button._on_click()`, matching `test_settings_icon_click_opens_a_non_modal_settings_window_leaving_home_mounted`'s existing pattern), captures the `SettingsWindow` instance via `frame.winfo_children()` filtered by `isinstance(..., SettingsWindow)`, then calls `frame.destroy()` (the exact operation `Router.navigate()`'s `previous_frame.destroy()` performs) and asserts the captured `SettingsWindow` no longer exists (`winfo_exists() == 0`).
  - [x] Confirm the assertion and its setup are identical in shape across all three screens -- no per-screen divergence in what's being proven (AC 3). If the three tests end up byte-for-byte identical except for `mount`/screen-specific setup, consider whether the existing `tests/adapters/tkinter/conftest.py` hoisting precedent (`navigate_stub`, `find_all`) applies to any shared piece -- but don't force a shared helper if the three call sites differ enough that it would obscure more than it saves.
- [x] **Task 3 -- Close the loop in `deferred-work.md`** (AC: 1)
  - [x] `deferred-work.md` is still in its pre-DW-format (freeform prose bullets), not yet migrated to the canonical `### DW-<seq>` format (`bmad-loop-sweep`'s `deferred-work-format.md` -- that migration is a separate, automated `bmad-loop sweep --migrate` concern, out of scope here). Only two entries in the file describe this exact mechanism (verified by grep -- Story 1.9's own version was never copied into `deferred-work.md` as a separate bullet; `spec-1-9-...md`'s own "Residual risks" section just references the Story 1.8 entry by name). Append a short resolution note, in the same prose style already used in that file, to each:
    - The Story 1.8 entry beginning "`Router.navigate()` destroys the previously-mounted screen's frame, which cascades... to silently close any `SettingsWindow` still open..." (`## Deferred from: code review of spec-1-8-home-breadcrumb-navigation-settings-access (2026-08-06)`, first bullet).
    - The Story 1.10 entry beginning "Pressing 'B'/'P' (Home's canonical shortcuts) while a non-modal `SettingsWindow` is open silently closes it..." (`## Deferred from: code review of spec-1-10-accessibility-floor-keyboard-shortcut-consistency (2026-08-09)`, first bullet).
  - [x] Do not delete or rewrite these entries -- the file is append-only per its own governing convention; add a trailing note such as "Resolved by Story 1.11: this is now a documented, tested, deliberate behavior (see `settings_window.py`'s module docstring and the regression tests in each screen's test file)."

## Dev Notes

### Architecture patterns & constraints

- **AD-10 (single shell, Home-routed screen navigation):** "Settings is not a fourth router screen: per AD-11, it is a `common/`-hosted dialog (its own `Toplevel`) invoked directly by whichever screen's Settings affordance triggered it, so the underlying screen stays mounted (visible/paused) behind it rather than being swapped out." This story does not change that contract -- Settings still isn't router-tracked, and opening it still leaves the underlying screen mounted. It only makes the *closing* half of the lifecycle (what happens when the underlying screen itself gets torn down) explicit instead of accidental. [Source: architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md#AD-10]
- **`Router.navigate()`'s new-before-old ordering** (`src/labyrinthes/app/router.py`): mounts the new frame, packs it, *then* destroys `previous_frame`. `SettingsWindow` is a real Tk child `Toplevel` of that `previous_frame` (constructed as `SettingsWindow(frame, theme=theme)` in each screen's `open_settings()`), so Tk's own parent-child semantics destroy it as a side effect of `previous_frame.destroy()`. This is empirically confirmed (`deferred-work.md`'s Story 1.8/1.10 entries) and is *not* a bug to fix in `Router` itself -- `Router` correctly and intentionally never knows about `SettingsWindow` (it only knows `ScreenId`/`MountFn`, per its own docstring's "never imports a concrete screen module").
- **This story's scope is deliberately narrow: document + test, not restructure.** The same "narrow, mechanical, avoid scope creep" discipline every Story 1.3-1.10 review reinforced applies here -- do not reparent `SettingsWindow`, do not add a `Router`-level Settings-awareness mechanism, do not build a "confirm before closing" prompt. None of that is needed while `SettingsWindow` has no real persisted content.
- **No FR binds this story** -- it originates from the Epic 1 retrospective, not `epics.md`'s original FR list. Treat AC 1-3 above as the complete scope; nothing else is implied.

### Project Structure Notes

- Files this story **updates** (no new modules):
  - `src/labyrinthes/adapters/tkinter/common/settings_window.py` -- docstring only.
  - `src/labyrinthes/adapters/tkinter/home/screen.py`, `.../builder/screen.py`, `.../player/screen.py` -- `open_settings()` comment only, no behavior change. (Home's `open_settings()` already has the comment; only Builder's and Player's need it added.)
  - `tests/adapters/tkinter/home/test_home_screen.py`, `.../builder/test_builder_screen.py`, `.../player/test_player_screen.py` -- one new test each.
  - `_bmad-output/implementation-artifacts/deferred-work.md` -- append-only resolution notes on existing entries.
- No changes to `src/labyrinthes/app/router.py`, `src/labyrinthes/app/composition_root.py`, or any `application/`/`domain/` module -- this is a `common/`- and screen-level docs+tests story only.

### Testing standards summary

- `pytest`, existing per-screen test files under `tests/adapters/tkinter/{home,builder,player}/`, following the established `tk_root`/`navigate_stub`/`toggle_theme_stub`/`find_all` fixture conventions already hoisted into `tests/conftest.py` / `tests/adapters/tkinter/conftest.py` -- reuse them, don't reinvent per-test setup.
- Mirror `test_settings_icon_click_opens_a_non_modal_settings_window_leaving_home_mounted` (`tests/adapters/tkinter/home/test_home_screen.py:84`) for how to open `SettingsWindow` via the real click path and locate it via `frame.winfo_children()` + `isinstance(..., SettingsWindow)`.
- `ruff check .` and `ruff format .` must both pass, per every prior story in this epic.

### References

- [Source: _bmad-output/implementation-artifacts/epic-1-retro-2026-08-09.md#Decisions Made in This Retrospective, #Action Items]
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

- `ruff check .` -- all checks passed.
- `ruff format --check .` -- the 6 files this story touched are formatted; one unrelated pre-existing file (`_bmad-output/implementation-artifacts/1-1-domain-model-foundation.md`) is flagged by the repo-wide format check but is untouched by this story and out of scope.
- `pytest -q` -- 281 passed, 0 failed (includes the 3 new regression tests, one per screen).

### Completion Notes List

- Confirmed the close-on-navigate cascade was already correct behavior (Tk parent-child `Toplevel` semantics via `Router.navigate()`'s `previous_frame.destroy()`); this story only makes it documented and tested, per its deliberately narrow scope -- no changes to `router.py`, `composition_root.py`, or any `application`/`domain` module.
- Added the "`frame` (not `parent`)" master-selection comment to `builder/screen.py`'s and `player/screen.py`'s `open_settings()` closures, matching the one already present in `home/screen.py`.
- Extended `SettingsWindow`'s module docstring with an explicit "Lifecycle (Story 1.11)" paragraph cross-referencing the three prior deferrals (Stories 1.8, 1.9, 1.10) and stating the reparenting-out-of-scope decision.
- Added `test_destroying_the_screens_frame_closes_an_open_settings_window` to all three screen test files, mirroring the existing `test_settings_icon_click_opens_a_non_modal_settings_window_leaving_*_mounted` pattern: opens `SettingsWindow` via the real click path, then calls `frame.destroy()` (the exact operation `Router.navigate()` performs) and asserts `winfo_exists() == 0`. Kept the three tests separate rather than hoisting a shared conftest helper -- the existing, very similar `test_settings_icon_click_opens_...` tests weren't hoisted either, and hoisting across three different per-module `mount` functions would obscure more than it saves for three ~15-line tests.
- Appended "Resolved by Story 1.11" trailing notes to the two `deferred-work.md` entries this story closes (Story 1.8's and Story 1.10's `Router.navigate()`-cascade findings), append-only per that file's governing convention.
- All three acceptance criteria verified: AC1 (documented, deliberate outcome -- docstring + comments), AC2 (automated test per screen asserting the documented `winfo_exists() == 0` outcome), AC3 (identical test shape across Home/Builder/Player, no per-screen divergence).

### File List

- `src/labyrinthes/adapters/tkinter/common/settings_window.py` (modified -- docstring)
- `src/labyrinthes/adapters/tkinter/builder/screen.py` (modified -- comment)
- `src/labyrinthes/adapters/tkinter/player/screen.py` (modified -- comment)
- `tests/adapters/tkinter/home/test_home_screen.py` (modified -- new regression test)
- `tests/adapters/tkinter/builder/test_builder_screen.py` (modified -- new regression test)
- `tests/adapters/tkinter/player/test_player_screen.py` (modified -- new regression test)
- `_bmad-output/implementation-artifacts/deferred-work.md` (modified -- append-only resolution notes)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified -- status tracking)

## Change Log

- 2026-08-09: Documented and pinned the close-on-navigate `SettingsWindow` lifecycle as a deliberate, tested behavior across Home/Builder/Player (Story 1.11); resolved the two matching `deferred-work.md` entries from Stories 1.8 and 1.10. No behavior change.
