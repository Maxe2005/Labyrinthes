---
title: 'Story 2.3: Random maze saving, reappears after restart'
type: 'feature'
created: '2026-08-10'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-2-context.md']
warnings: [oversized]
baseline_revision: '2031f36c600c07c6af7f64e8e8ab7266df174d2b'
final_revision: 'ffdfa0fbf4b26b7ebacc31d8d4971ee313c4498c'
---

<intent-contract>

## Intent

**Problem:** A `generated` maze reaching Player's gameplay placeholder has no way to be saved — `MazeRepository.save()` already supports `SAVED_RANDOM` (Story 1.4), but nothing calls it from the UI — and `ClassicMazeGallery` only ever lists `MazeKind.CLASSIC`, so even a maze saved by hand-editing storage would never resurface in the selector, reproducing the exact legacy dead end this story exists to fix.

**Approach:** Add a minimal "Save" action to Player's gameplay placeholder (Story 2.4 owns the real gameplay screen; this story only needs an entry point ahead of it), shown when the mounted `Maze.kind` is `GENERATED`, opening a new `SaveMazeDialog` (modeled on `GenerateRandomDialog`) that takes a name, live-validates it, and arms/confirms an explicit overwrite on a collision against `MazeRepository.list_names(MazeKind.SAVED_RANDOM)`. On confirm, transition the maze to `kind=SAVED_RANDOM` via `dataclasses.replace` and call `MazeRepository.save()`, which mints the fresh `MazeId`. Extend `ClassicMazeGallery` to browse `SAVED_RANDOM` mazes appended after the classic ones in the same pager, so a restart-then-reopen finds them.

## Boundaries & Constraints

**Always:** `adapters/tkinter/player/` never imports `adapters/storage/` directly (AD-9) — the dialog's own name-shape validation (empty / contains `/` or `\`) duplicates `maze_file_path`'s two rules rather than importing them. The Save button only ever appears for `kind is MazeKind.GENERATED`; an already-`SAVED_RANDOM`/`CLASSIC` maze reaching the placeholder shows no Save affordance. Kind transition happens via `dataclasses.replace(maze, kind=MazeKind.SAVED_RANDOM, id=None)` before calling `save()` — never in-place mutation, never done by the repository itself (its contract explicitly leaves `kind` alone). The new `save_maze` shortcut ("s") registers in `KEYBINDINGS` (Story 1.10) and binds/unbinds scoped to the Save button's own lifetime (not the placeholder frame's), since the button is conditionally destroyed on save while the frame persists.

**Block If:** Nothing here requires human input — the FR-5 "consistent with the Builder's save behavior" reference points at Story 3.6, which is not yet implemented (confirmed: no duplicate-name pattern exists anywhere in `adapters/tkinter/` today), so this story establishes that pattern rather than reusing one; that is a resolvable design decision, not a blocking gap (see Design Notes).

**Never:** No real gameplay rendering, HUD, or movement (Story 2.4). No Builder-side save/duplicate-name work (Story 3.6). No renaming/deleting saved mazes. No change to `MazeRepository`, `CsvMazeRepository`, or the domain `Maze`/`MazeKind` types — all already support `SAVED_RANDOM` end-to-end (Story 1.4).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Save a fresh generated maze | Gameplay placeholder holds a `GENERATED` maze; dialog opened, name "forest" typed (no collision) | `save()` called once with `kind=SAVED_RANDOM`, `id=None`; placeholder now shows the returned maze (`kind=SAVED_RANDOM`, fresh `MazeId`), Save button gone, dialog closed | No error |
| Empty name | Dialog open, name field cleared | Inline "Name is required." error shown; clicking Save/pressing Return is a no-op, dialog stays open | Inline error, no `save()` call |
| Name with a path separator | Name field = `"a/b"` | Inline "Name must not contain a path separator." error shown; Save is a no-op | Inline error, no `save()` call |
| Name collides with an existing saved-random maze, first Save click | Name = an entry already in `list_names(MazeKind.SAVED_RANDOM)` | No save yet; inline warning "A maze named '{name}' already exists — Save again to overwrite it." shown, button label switches to "Overwrite" | No error, dialog stays open, armed |
| Same colliding name, second click (armed, unchanged) | Click "Overwrite" | `save()` called once with the same name, overwriting; placeholder updates as in the happy path | No error |
| Name edited after arming | Armed state, then any `<KeyRelease>` changes the text | Arming resets: button reverts to "Save", a fresh collision check re-runs against the new text | No error |
| Cancel / Escape | Dialog open, Cancel clicked or `<Escape>` pressed | Dialog destroyed, no `save()` call, placeholder unchanged | No error |
| Selector after restart | App restarted with a previously `SAVED_RANDOM`-persisted maze on disk; selection screen opens | `ClassicMazeGallery` lists it after the classics in the same pager; position label reads `"Saved Random Maze {i} of {n}"` (overall index/total, matching the jump-entry's own numbering) | No error |
| No classics, only saved-random mazes exist | `list_names(CLASSIC) == []`, `list_names(SAVED_RANDOM)` non-empty | Populated (pager) state shown, not the empty state | No error |
| Neither classics nor saved-random mazes exist | Both `list_names()` calls return `[]` | Empty-state message shown, no pager/Play | No error |

</intent-contract>

## Code Map

- `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- add `Keybinding("save_maze", "Save", "s")` to `KEYBINDINGS`
- `src/labyrinthes/adapters/tkinter/player/save_maze_dialog.py` -- new; `SaveMazeDialog(tk.Toplevel)` -- name entry, live validation, arm/confirm overwrite, Cancel/Save `PillButton`s, modeled on `generate_random_dialog.py`
- `src/labyrinthes/adapters/tkinter/player/gameplay_placeholder.py` -- new; `GameplayPlaceholder(tk.Frame)` replacing `screen.py`'s current free-function placeholder -- holds mutable `self._maze`, shows/hides a Save `PillButton` based on `kind`, opens `SaveMazeDialog`, performs the kind-transition + `save()` on confirm, re-renders
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- remove `_mount_gameplay_placeholder`; `mount()`'s `state is not None` branch constructs `GameplayPlaceholder(frame, state, theme, maze_repository=maze_repository)` instead
- `src/labyrinthes/adapters/tkinter/player/classic_gallery.py` -- `self._names` becomes `self._entries: list[tuple[MazeKind, str]]` = classics (existing sort) then `list_names(MazeKind.SAVED_RANDOM)` (same sort); `_position_text()`/`_current_maze()` become kind-aware; empty-state check and message updated to cover both kinds
- `tests/adapters/tkinter/player/test_save_maze_dialog.py` -- new; the I/O matrix's dialog rows (empty/separator/collision-arm/re-arm-reset/cancel/escape) directly against `SaveMazeDialog`
- `tests/adapters/tkinter/player/test_gameplay_placeholder.py` -- new; Save button visibility per `kind`, save happy path, repository untouched until Save is clicked, shortcut scoped to the button's lifetime
- `tests/adapters/tkinter/player/test_player_screen.py` -- update `_maze()`-based assertions only if the placeholder's public shape changed (breadcrumb/frame-type tests); no behavior change expected for the existing `test_state_not_none_never_reads_the_maze_repository` case (a `CLASSIC` maze never shows Save, so it still never touches the repository at mount time)
- `tests/adapters/tkinter/player/test_classic_gallery.py` -- existing classic-only tests keep their `"Classic Maze N of M"` assertions unchanged (backward-compatible numbering, see Design Notes); add new tests seeding `SAVED_RANDOM` mazes for combined-listing/position-label/empty-state coverage
- `tests/adapters/tkinter/player/conftest.py` -- add a `saved_random_maze(name, width, height)` helper and/or a fixture seeding both kinds, alongside the existing `classic_maze()`/`seeded_maze_repository`
- `tests/adapters/storage/test_csv_maze_repository.py` -- no change expected (SAVED_RANDOM save/load/list already covered per Story 1.4); read to confirm before assuming

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- register `save_maze` ("s") -- the one canonical shortcut table (Story 1.10), no ad hoc binding
- [x] `src/labyrinthes/adapters/tkinter/player/save_maze_dialog.py` -- add `SaveMazeDialog` -- name entry + live validation + arm/confirm overwrite UI, reporting via an `on_confirm: Callable[[str], None]` callback like `GenerateRandomDialog`
- [x] `tests/adapters/tkinter/player/test_save_maze_dialog.py` -- unit-test the dialog against the I/O matrix rows
- [x] `src/labyrinthes/adapters/tkinter/player/gameplay_placeholder.py` -- add `GameplayPlaceholder` -- Save button gated on `kind is GENERATED`, dialog wiring, kind-transition + `save()` on confirm, re-render
- [x] `src/labyrinthes/adapters/tkinter/player/screen.py` -- swap `_mount_gameplay_placeholder` for `GameplayPlaceholder`
- [x] `tests/adapters/tkinter/player/test_gameplay_placeholder.py` -- unit-test Save visibility/happy-path/repository-untouched-until-click/shortcut-scoping
- [x] `tests/adapters/tkinter/player/test_player_screen.py` -- re-run/adjust existing placeholder-shape assertions against the new class
- [x] `src/labyrinthes/adapters/tkinter/player/classic_gallery.py` -- combine classic + saved-random listing into `self._entries`, kind-aware position/current-maze/empty-state
- [x] `tests/adapters/tkinter/player/conftest.py` -- add saved-random seeding helper/fixture
- [x] `tests/adapters/tkinter/player/test_classic_gallery.py` -- add combined-listing tests; confirm existing classic-only tests still pass unmodified

**Acceptance Criteria:**
- Given a `GENERATED` maze in the gameplay placeholder, when the player saves it with a non-colliding name, then `MazeRepository.save()` is called exactly once and the returned `Maze` carries `kind=SAVED_RANDOM` and a freshly minted `MazeId`
- Given a previously saved random maze on disk, when the app restarts and the selection screen opens, then it appears in `ClassicMazeGallery`'s pager alongside classic mazes
- Given a save-name collision, when the player saves, then no overwrite happens on the first click (an inline warning appears and the action must be explicitly re-confirmed) — the two-step arm/confirm pattern this story establishes, since no prior Builder (FR-5) implementation exists yet to match

## Spec Change Log

## Review Triage Log

### 2026-08-10 — Review pass

- intent_gap: 0
- bad_spec: 0
- patch: 7 (high 1, medium 2, low 4)
- defer: 2
- reject: 2
- addressed_findings:
  - `[high]` `[patch]` `SaveMazeDialog._name_entry` had no `<KeyPress-s>`/`<KeyPress-S>` guard, so typing a name containing "s" (empirically confirmed against a live Tk instance) both inserted the character and fired the global `save_maze` `bind_all()` shortcut, stacking a second `SaveMazeDialog` on top mid-typing. Fixed by binding both case variants to return `"break"` on the name entry, mirroring `ClassicMazeGallery`'s existing identical guard for "n"/"N" on its jump entry.
  - `[medium]` `[patch]` `GameplayPlaceholder._on_save_confirmed`'s `_build()` cleanup loop (`for child in self.winfo_children(): child.destroy()`) destroyed the still-executing `SaveMazeDialog` as an incidental side effect, since a `Toplevel` is a child of its parent for `winfo_children()` purposes (empirically confirmed) -- relying on Tk's double-`destroy()`-is-a-no-op behavior rather than a controlled close. Fixed by reordering `SaveMazeDialog._on_save_clicked` to call `self.destroy()` before invoking `on_confirm`, so the dialog is already gone via its own path before the parent's rebuild runs.
  - `[medium]` `[patch]` `SaveMazeDialog` reached into `PillButton`'s private `_label` attribute (`self._save_button._label.configure(text=...)`) to relabel the button for the arm/confirm flow -- no other file in the codebase reaches into another widget's underscore-prefixed internals from outside its own class. Fixed by adding a public `PillButton.set_text(text: str)` method and using it instead.
  - `[low]` `[patch]` `_on_name_changed` reset the arm/confirm state on *every* `<KeyRelease>`, including non-content keys (arrow keys, Home/End) that leave the field's text unchanged -- a user who got the overwrite warning and merely repositioned the cursor lost the arming and needed a third click. Fixed by only resetting when the field's raw text actually differs from the text captured at arm time.
  - `[low]` `[patch]` Neither `_validate_name` nor the collision check stripped the entered name, so a whitespace-only name (e.g. `"   "`) passed validation and got persisted, and a name differing from an existing one only by trailing whitespace (e.g. `"alpha "` vs. `"alpha"`) silently created a visually-indistinguishable near-duplicate instead of surfacing the overwrite warning. Fixed by `.strip()`-ping the name once in `_on_save_clicked`/`_on_name_changed` before validating, collision-checking, arming, or confirming.
  - `[low]` `[patch]` `_EMPTY_STATE_MESSAGE` still read "No classic mazes were found," even though the empty branch now depends on both classics and saved-random mazes being absent (the spec's own Code Map called for the message to be "updated to cover both kinds," which the implementation pass missed). Fixed the wording and the two tests asserting on it.
  - `[low]` `[patch]` The pager's Previous/Next/Restart `IconButton` tooltips still hardcoded "classic maze" wording (e.g. "Previous classic maze."), misleading once a browsed entry is a saved-random maze. Fixed by generalizing to kind-neutral wording ("Previous maze.", "Next maze.", "Restart at the first maze.").

Deferred (see `deferred-work.md`): `SaveMazeDialog` never calls `grab_set()`/`transient()` and has no dedup guard against a second instance opening while one is already open -- the same already-deferred `SettingsWindow`/`GenerateRandomDialog` non-modal-dialog pattern, not a new failure class; `_on_save_clicked` doesn't catch an exception from `on_confirm` (e.g. a `maze_repository.save()` I/O error) -- consistent with this codebase's existing no-try/except-at-the-UI-layer posture for domain/storage errors, not a regression introduced here.

Rejected as noise or as already-deliberate: `_position_text`'s `if kind is MazeKind.CLASSIC else "Saved Random Maze"` flagged as non-exhaustive over `MazeKind` -- on inspection, `self._entries` can only ever contain `CLASSIC`/`SAVED_RANDOM` tuples (the two `list_names()` calls that build it), so a third kind reaching this branch is unreachable with the current code, not a latent bug. No explicit "Saved!" success banner after a save flagged as missing feedback -- already deliberate per this spec's own I/O matrix (the placeholder's summary text visibly updates its `kind=...` field on save), and richer save feedback belongs to Story 2.4's real gameplay screen, not this placeholder.

### 2026-08-10 — Review pass (follow-up)

- intent_gap: 0
- bad_spec: 0
- patch: 4 (high 0, medium 1, low 3)
- defer: 5
- reject: 3
- addressed_findings:
  - `[medium]` `[patch]` `SaveMazeDialog._on_name_changed` unconditionally overwrote `_message_label`'s text on *every* `<KeyRelease>`, including the cursor-only keys (arrow keys, Home/End) that the same handler's own arming-reset logic already treats as a no-op -- so a cursor-only key release while armed cleared the "already exists -- Save again to overwrite it." warning even though the button still read "Overwrite," leaving the button with no visible explanation of what it was about to do. Fixed by skipping the message update whenever `_armed_name` is still set after the reset check, mirroring the button-label guard added in the prior review pass; extended `test_cursor_only_key_release_while_armed_does_not_reset_arming` to assert the message text too, closing the gap that let this regression through undetected.
  - `[low]` `[patch]` The AC "the returned `Maze` carries ... a freshly minted `MazeId`" had no test able to verify it -- `FakeMazeRepository.save()` (`tests/adapters/tkinter/player/conftest.py`) stored the maze as-is and never minted an id, unlike the real `CsvMazeRepository.save()` it stands in for. Fixed by mirroring `CsvMazeRepository`'s own id-eligible-kind-and-`id is None` minting contract in the fake, and added `saved.id is not None`/`placeholder._maze.id is not None` assertions to the two happy-path tests that were silently unable to check this before.
  - `[low]` `[patch]` No test drove the collision/overwrite I/O-matrix rows end-to-end through `GameplayPlaceholder`'s real Save button and `SaveMazeDialog` together -- `test_gameplay_placeholder.py` only covered the non-colliding happy path, and `test_save_maze_dialog.py`'s arm/confirm tests only exercised the dialog in isolation against an `on_confirm` stub, so "Save -> collision -> Overwrite -> repository.save()" as one full cycle was unverified. Fixed by adding `test_confirming_an_overwrite_through_the_full_dialog_flow_saves_once`.
  - `[low]` `[patch]` The Design Notes section (outside `<intent-contract>`) referred to the Save button's re-render as `_refresh()`, but the actual method is `_build()` -- a small naming drift between the narrative and the code (the module docstring itself already said `_build()`). Fixed the Design Notes reference.

Deferred (see `deferred-work.md`): the "s"/"S" guard only intercepts the keystroke while the name field has focus, so tabbing away and pressing "s" still stacks a second dialog (same root cause as the already-deferred no-modality/no-dedup gap, a more specific trigger path); the collision check is case-sensitive with a snapshot taken once at dialog-open, never re-checked at confirm; no upper length ceiling on the entered name before it reaches the storage layer; `ClassicMazeGallery._current_maze()`'s pre-existing unguarded `load()` now also covers user-authored `SAVED_RANDOM` entries.

Rejected as noise or as already-deliberate: the maze always getting a brand-new `MazeId` on overwrite (rather than preserving the old one) flagged as surprising -- this is exactly what the intent contract's own "Always" clause mandates (`dataclasses.replace(maze, kind=MazeKind.SAVED_RANDOM, id=None)` unconditionally, before every `save()`), not a bug. An unhandled exception from `on_confirm`/`maze_repository.save()` flagged again -- already captured verbatim by this story's own prior-pass deferred-work entry, no new information. General commentary that the placeholder "reproduces silent-failure characteristics of the legacy app" -- covered by the specific, already-deferred/newly-deferred items above; not independently actionable.

## Design Notes

**Story 2.3 establishes the duplicate-name pattern; it does not "match" one.** The epic's AC references "the Builder's save behavior (FR-5)", but that behavior belongs to Story 3.6, not yet implemented anywhere in `adapters/tkinter/` (confirmed by exhaustive grep). Rather than block on a nonexistent precedent, this story defines a minimal, non-modal, two-click arm/confirm inside `SaveMazeDialog` itself (first click on a colliding name warns and relabels the button "Overwrite"; a second click on the same name performs it; any edit resets the arming). Story 3.6 should later match *this* pattern for consistency, not the reverse.

**Position-label numbering is deliberately unified, not per-kind.** `ClassicMazeGallery`'s pager uses one flat `self._entries` list (classics first, then saved-random) with one 1-based index shared by the position label, the jump-entry, and Previous/Next/Restart — e.g. `"Saved Random Maze 4 of 5"` where 4/5 are the *overall* combined position, not "1 of 2 within saved-random". This keeps the jump-entry's typed number always matching the label's own number (no per-kind/overall mismatch), and — since classics are listed first and contiguous — every existing classic-only test's `"Classic Maze N of M"` assertion stays byte-for-byte unchanged when no saved-random mazes are seeded.

**The "s" shortcut binds to the Save button's own widget, not the placeholder frame.** `ClassicMazeGallery`'s precedent (`bind_shortcut(self, generate_kb, ...)`) binds to a widget that outlives the whole screen. `GameplayPlaceholder`'s Save button is conditionally destroyed and rebuilt on `_build()` once the maze becomes `SAVED_RANDOM` — binding to the button itself lets `bind_shortcut`'s existing per-sequence token/`<Destroy>` cleanup (see that module's docstring) unregister "s" automatically when the button disappears, rather than leaving a stale binding that could re-open the dialog and re-mint an id for an already-saved maze.

## Verification

**Commands:**
- `ruff check .` -- expected: no new lint violations
- `ruff format --check .` -- expected: no formatting diffs
- `pytest` -- expected: full suite green, including new `SaveMazeDialog`/`GameplayPlaceholder` tests and the updated `ClassicMazeGallery`/player-screen tests

## Auto Run Result

**Summary:** This is a follow-up review pass over the already-implemented Story 2.3 (Player's gameplay placeholder can Save a `GENERATED` maze via `SaveMazeDialog`'s two-click arm/confirm overwrite, and `ClassicMazeGallery` browses `SAVED_RANDOM` mazes alongside classics). No behavior changed for the feature's happy paths; this pass fixed one real UX regression left by the prior pass's own arming fix, closed two test-coverage gaps that left parts of the story's own acceptance criteria unverifiable, corrected a small doc/code naming drift, and logged five new pre-existing/adjacent gaps to `deferred-work.md` (none blocking, none a regression introduced by this story).

**Files changed:**
- `src/labyrinthes/adapters/tkinter/player/save_maze_dialog.py` — fixed `_on_name_changed` clearing the "already exists" overwrite warning on a cursor-only key release while still armed (the button label already survived this per the prior review pass; the message text did not)
- `tests/adapters/tkinter/player/test_save_maze_dialog.py` — extended the cursor-only key-release regression test to also assert the message text survives, not just the button label
- `tests/adapters/tkinter/player/conftest.py` — `FakeMazeRepository.save()` now mirrors `CsvMazeRepository`'s id-eligible-kind-and-`id is None` minting contract, so tests can actually verify the "freshly minted `MazeId`" acceptance criterion
- `tests/adapters/tkinter/player/test_gameplay_placeholder.py` — added `saved.id is not None`/`placeholder._maze.id is not None` assertions to the two happy-path tests; added a new end-to-end test driving Save → collision → Overwrite → `repository.save()` through the real `GameplayPlaceholder`/`SaveMazeDialog` pair, not just each in isolation
- `_bmad-output/implementation-artifacts/spec-2-3-random-maze-saving-reappears-after-restart.md` — fixed a Design Notes reference to a nonexistent `_refresh()` method (the actual method is `_build()`); this Review Triage Log entry
- `_bmad-output/implementation-artifacts/deferred-work.md` — five new entries logged (see below)

**Review findings breakdown:** 4 patches applied (0 high, 1 medium, 3 low), 5 deferred to `deferred-work.md` (a more specific, focus-tab-triggered variant of the already-deferred no-modality/dedup gap; case-sensitive collision detection with a stale open-time snapshot; no name-length ceiling before reaching the storage layer; `ClassicMazeGallery`'s pre-existing unguarded `load()` now also reachable via user-authored `SAVED_RANDOM` entries), 3 rejected as noise or already-deliberate (the intent contract's own mandatory `id=None`-on-every-save rule misread as a bug; an unhandled-`on_confirm`-exception finding that duplicated the prior pass's own deferred-work entry verbatim; general non-actionable commentary already covered by the specific items above).

**Verification performed:** `ruff check .` (all checks passed), `ruff format --check .` (156 files unchanged), `pytest` (417 passed, full suite, up from 416 — the two new/extended tests) — all re-run after this pass's patches.

**Follow-up review recommendation:** `false`. This pass's changes are localized (one UI callback's message-clearing bug, two test files gaining assertions/a test, one doc-string correction) and low-consequence (a warning-message cosmetic regression, not data loss or a save-path change); none of the newly deferred items are regressions this story introduced outright, and the two headline structural fixes from the *prior* pass (keystroke-stacking guard, destroy-before-confirm ordering) were not touched here.

**Residual risks:** The five newly deferred items are real but non-blocking, consistent with this story's already-established pattern of deferring dialog-modality and storage-layer-adjacent gaps rather than solving them piecemeal per widget. The most consequential of the five (focus-tab bypass of the "s" guard, stacking a second dialog that can be silently destroyed) shares its fix with the already-deferred `SettingsWindow`/`GenerateRandomDialog`/`SaveMazeDialog` non-modal-dialog pattern and should be solved once, holistically, not per-dialog.

