---
title: 'Story 2.1: Player maze-selection screen — classic maze browsing'
type: 'feature'
created: '2026-08-09'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-2-context.md']
warnings: [oversized]
baseline_revision: '08928b98f85a6891cd932f097922d2d7874456cd'
final_revision: 'bcc2c3244d996e7563a307b3a08d29647e8d30f8'
---

<intent-contract>

## Intent

**Problem:** Player's `mount()` is still Story 1.7's placeholder (`state` accepted but unused, body is a bare "Player" label) — there is no way to browse the classic maze library, no way to pick one, and no `MazeRepository` capability to enumerate what classic mazes even exist.

**Approach:** Add `MazeRepository.list_names(kind)` (plus the `CsvMazeRepository` implementation) so a screen can enumerate persisted mazes of a kind; build a local `ClassicMazeGallery` widget (previous/next/restart/jump-to-number over one browsed classic maze at a time, a "Generate random" entry point, and an inline empty-state) that Player's `mount()` shows when `state is None`; wire its confirm action to call the existing `navigate(ScreenId.PLAYER, maze)` closure, which Player's `mount()` now dispatches on `state is not None` to a gameplay-placeholder view (real rendering is Story 2.4's job). `composition_root.py` constructs one `CsvMazeRepository` and binds it into Player's registration via `functools.partial`, without widening the shared `ScreenMountFn` signature Home/Builder also use.

## Boundaries & Constraints

**Always:** `MazeRepository` gains an abstract `list_names(self, kind: MazeKind) -> list[str]` returning persisted names for `kind`, sorted (lexicographic — no numeric-aware ordering), `[]` when the kind's folder doesn't exist yet; `CsvMazeRepository.list_names()` implements it via the same `MAZE_FILE_SUFFIX` glob `find_by_id` already uses. `player/screen.py`'s `mount()` keeps the exact 5-positional-arg `ScreenMountFn` shape (`parent, state, navigate, theme, toggle_theme`) but adds one **required, keyword-only** `maze_repository: MazeRepository` param; `composition_root.build_app()` supplies it by wrapping `mount_player` in `functools.partial(mount_player, maze_repository=...)` before passing it to the existing `_bind_screen()` — Home/Builder/`ScreenMountFn`/`_bind_screen()` itself stay untouched. `build_app()` gains an optional `maze_repository: MazeRepository | None = None` param (mirrors `settings_repository`), defaulting to `CsvMazeRepository()`. `mount()` dispatches purely on `state`: `state is None` → mount `ClassicMazeGallery` (browsing); `state is not None` → mount the gameplay-placeholder view for that `Maze` (a text summary only, no wall/HUD rendering — Story 2.4's job). `ClassicMazeGallery` browses one maze at a time (not the mockup's 4-card thumbnail grid — no wall-bar rendering component exists yet to draw thumbnails from): a position label ("Classic Maze {i+1} of {n}"), Previous/Next `IconButton`s that clamp at the bounds (no wraparound, no-op past either end — satisfies "no crash, no out-of-range index"), a Restart `IconButton` that jumps back to index 0, a jump-to-number `tk.Entry` bound to `<Return>` that jumps to a valid 1-based number and otherwise reverts its displayed text without changing the browsed index, and a primary "Play" `PillButton` whose command loads the currently-browsed name and calls `navigate(ScreenId.PLAYER, maze)`. Both the populated and empty-state views show a "Generate random" primary `PillButton` (kbd "N", added to `KEYBINDINGS` as `generate_random`) wired to a documented no-op placeholder callback (Story 2.2 wires real generation, same "placeholder for a later story to complete" pattern Story 1.7 already established for whole screens). The gameplay-placeholder view keeps the same "Home / Player" 2-segment breadcrumb as the selection view (no 3-segment dynamic label yet — deferred, see Never).

**Block If:** None — every open question below (restart semantics, single- vs multi-card browsing, the generate-random stub, breadcrumb depth) is resolved by the choices above; nothing here requires a human decision.

**Never:** Do not render maze thumbnails (mini wall/entry/exit previews) in the gallery — deferred until Story 2.4's wall-bar rendering exists. Do not implement random-maze generation or a generation dialog — Story 2.2. Do not implement real gameplay rendering (walls, ball, HUD) for the post-confirm view — Story 2.4; it stays a plain summary label. Do not add a dynamic 3-segment breadcrumb label (e.g. "Classic Maze 4") for the gameplay-placeholder view — the bare `Maze` a top-level `navigate()` call carries has no name/position to derive one from without new state-shape work; leave this to Story 2.4. Do not add resilience for a classic maze file deleted between `list_names()` and `load()` (mid-session external deletion) — matches the existing error floor, out of scope. Do not change `Router`, `MountFn`, `ScreenMountFn`, or `_bind_screen()`'s own signatures, and do not touch Home's or Builder's `mount()` signatures.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Cold open, classics exist | `mount(parent, None, navigate, theme, toggle, maze_repository=repo)`, repo has 3 classics | First classic (index 0) shown with position label "Classic Maze 1 of 3", size, pager controls, Play button | No error expected |
| Next at last index | Browsing index 2 of 3 (0-based), Next clicked | Index stays 2, display unchanged | No error expected (no-op, no crash) |
| Previous at first index | Browsing index 0, Previous clicked | Index stays 0, display unchanged | No error expected (no-op, no crash) |
| Restart mid-browse | Browsing index 2, Restart clicked | Index resets to 0, display shows maze 1 | No error expected |
| Valid jump | Jump entry set to "3" of 3, `<Return>` pressed | Index becomes 2 (0-based), display shows maze 3 | No error expected |
| Invalid jump (out of range / non-numeric) | Jump entry set to "9" or "abc", `<Return>` pressed | Index unchanged; entry text reverts to the current index | No error raised, no state change |
| Cold open, no classics | `repo.list_names(MazeKind.CLASSIC) == []` | Inline empty-state message shown, no pager/Play controls, "Generate random" button present | No error expected |
| Confirm a pick | Play clicked while browsing index 1 | `navigate(ScreenId.PLAYER, loaded_maze)` called exactly once with that maze | No error expected |
| Re-navigate with state | `mount(parent, some_maze, navigate, theme, toggle, maze_repository=repo)` | Gameplay-placeholder Frame returned (no gallery, no repository read) | No error expected |

</intent-contract>

## Code Map

- `src/labyrinthes/application/maze_repository.py` -- add abstract `list_names(self, kind: MazeKind) -> list[str]`
- `src/labyrinthes/adapters/storage/csv_maze_repository.py` -- implement `list_names()` via the same glob pattern `find_by_id` uses
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- add `Keybinding("generate_random", "Generate random", "n")` to `KEYBINDINGS`
- `src/labyrinthes/adapters/tkinter/player/classic_gallery.py` -- new; `ClassicMazeGallery(tk.Frame)` -- pager/jump/restart/play/generate-random widget, populated + empty-state branches
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- rewrite `mount()`: keyword-only `maze_repository` param, dispatch on `state` between `ClassicMazeGallery` and a new small `_mount_gameplay_placeholder()` helper
- `src/labyrinthes/adapters/tkinter/player/__init__.py` -- update stale "real content in Epic 3" docstring (this story is Epic 2's real content landing)
- `src/labyrinthes/app/composition_root.py` -- import `CsvMazeRepository`; `build_app()` gains `maze_repository` param; Player's registration wraps `mount_player` with `functools.partial(..., maze_repository=...)`
- `tests/application/test_maze_repository.py` -- add `list_names` to `_CompleteMazeRepository`; add a case for a subclass missing only `list_names`
- `tests/adapters/storage/test_csv_maze_repository.py` -- `list_names()`: empty when folder absent, sorted names, only the requested kind's folder
- `tests/adapters/tkinter/common/test_keybindings.py` -- existing collision/uniqueness test covers the new entry automatically; no new test needed beyond the table addition
- `tests/adapters/tkinter/player/conftest.py` -- new; `_FakeMazeRepository` test double (in-memory, implements the 4-method port) + a fixture seeding a couple of classic mazes
- `tests/adapters/tkinter/player/test_classic_gallery.py` -- new; covers the I/O matrix's gallery rows directly against `ClassicMazeGallery`
- `tests/adapters/tkinter/player/test_player_screen.py` -- rewrite: all existing `mount()` calls gain `maze_repository=`; new cases for the `state`-based dispatch and the confirm→`navigate()` hand-off
- `tests/app/test_composition_root.py` -- existing `mount_home`-only tests are unaffected; add one case asserting Player's registration is reachable/callable with a `tmp_path`-rooted `maze_repository`

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/application/maze_repository.py` -- add `list_names()` abstract method -- the port capability every consumer (this story, later Story 2.3) needs to enumerate persisted mazes
- [x] `src/labyrinthes/adapters/storage/csv_maze_repository.py` -- implement `list_names()` -- concrete enumeration backing the port
- [x] `tests/application/test_maze_repository.py` -- extend the ABC-completeness tests for the new method
- [x] `tests/adapters/storage/test_csv_maze_repository.py` -- unit-test `list_names()`'s I/O matrix rows
- [x] `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- add the `generate_random` entry
- [x] `src/labyrinthes/adapters/tkinter/player/classic_gallery.py` -- add `ClassicMazeGallery` -- the pager/jump/restart/play/empty-state widget
- [x] `tests/adapters/tkinter/player/conftest.py` -- add the fake repository double + seeding fixture
- [x] `tests/adapters/tkinter/player/test_classic_gallery.py` -- unit-test `ClassicMazeGallery` against the I/O matrix
- [x] `src/labyrinthes/adapters/tkinter/player/screen.py` -- rewrite `mount()` to accept `maze_repository` and dispatch on `state`
- [x] `src/labyrinthes/adapters/tkinter/player/__init__.py` -- fix the stale placeholder docstring
- [x] `src/labyrinthes/app/composition_root.py` -- wire `CsvMazeRepository` into Player's registration
- [x] `tests/adapters/tkinter/player/test_player_screen.py` -- update existing calls, add dispatch/hand-off coverage
- [x] `tests/app/test_composition_root.py` -- add Player-registration wiring coverage

**Acceptance Criteria:**
- Given the classic maze library loaded via `MazeRepository`, when the selection screen opens, then the first classic maze is shown with previous/next/restart controls and a jump-to-number field
- Given the previous/next controls, when used at the first/last maze, then navigation stays within bounds (no crash, no out-of-range index)
- Given no classic mazes exist yet, when the screen opens, then an inline empty-state message is shown with a way to generate a random maze instead
- Given a classic maze is picked, when confirmed, then `navigate(ScreenId.PLAYER, maze)` is called with that `Maze`, and Player's `mount()` responds by rendering the gameplay-placeholder view for it

## Spec Change Log

## Review Triage Log

### 2026-08-09 — Review pass

- intent_gap: 0
- bad_spec: 0
- patch: 3 (medium 1, low 2)
- defer: 1 (medium 1)
- reject: 10
- addressed_findings:
  - `[medium]` `[patch]` The global "n" (generate-random) shortcut fired via `bind_all()` even while the jump-to-number `Entry` had keyboard focus, both inserting the character and triggering the placeholder action — fixed by binding `<KeyPress-n>`/`<KeyPress-N>` locally on the `Entry` to consume the event (`"break"`) before Tk's binding order reaches the global `bind_all()` handler.
  - `[low]` `[patch]` `CsvMazeRepository.list_names()` globbed `*.csv` without checking `path.is_file()`, so a same-named directory would be listed but fail on a later `load()` — fixed by filtering to `path.is_file()`.
  - `[low]` `[patch]` The new composition-root Player-wiring tests only asserted `current_screen_id == ScreenId.PLAYER`, not that `ClassicMazeGallery` (or its empty state) actually mounted — strengthened `test_player_registration_is_reachable_and_uses_the_injected_maze_repository` to assert the gallery's empty-state message is present (the `tmp_path`-rooted repository has no classics).

Deferred (see `deferred-work.md`): toggling the theme mid-browse re-navigates Player via the pre-existing Story 1.9 "re-navigate to re-theme" mechanism, which loses `ClassicMazeGallery`'s internal `_index` (browse position resets to the first maze) since browse position isn't part of the `Maze | None` `state` channel. Real, reproducible, medium severity — but the clean fix is architectural (a way to preserve per-screen internal state across a theme-driven remount) and will recur for every future stateful Player view (Story 2.4's gameplay screen has far more such state: position, elapsed time, Level/Difficulty selection), so it's deferred for a holistic fix rather than a one-off patch scoped to this widget alone.

Rejected as noise or as already-deliberate, already-documented decisions (not gaps): a classic maze deleted/corrupted between `list_names()` and `load()` raising uncaught (spec's `Never` clause explicitly descopes this); repeated `MazeRepository.load()` calls per pager click for the size label (matches the existing "tens, not thousands" performance floor already accepted by `find_by_id`'s docstring); an invalid jump reverting with no visible error feedback (matches the I/O matrix's own "no error raised, no state change" wording exactly); the empty-state message's "Build one in the Builder" phrasing not being a clickable link (verbatim from the locked `key-player-selection.html` mockup); the jump-to-number `<Return>` binding being exercised in tests by calling `_on_jump()` directly rather than a synthesized key event (matches the project-wide, documented "real X11 event synthesis isn't reliable against a withdrawn `tk_root`" testing convention used by every other widget); the lexicographic (non-numeric-aware) name sort (already explicitly documented and justified in `list_names()`'s own docstring and the spec); Play acting on the browsed index rather than an unconfirmed jump-entry value (matches the spec's deliberate commit-on-`<Return>` design); `list_names()` letting non-`is_dir()`-related `OSError`s (permissions, I/O) propagate (matches the existing repository-wide error-handling floor -- Story 1.12 scoped typed errors to malformed *content*, not filesystem I/O failures); the glob's case-sensitive `.csv` suffix match (identical to `find_by_id`'s pre-existing glob, not a new inconsistency).

## Design Notes

**Confirm hand-off reuses the existing `navigate()` closure, not a new sub-router.** The epic context frames the selection→gameplay transition as "sub-navigation the Player screen manages internally", which could be read as "build a second, local Router-like mechanism". It isn't: `mount()` already receives `state: Maze | None` and the same `navigate: NavigateFn` every screen gets. Calling `navigate(ScreenId.PLAYER, maze)` from inside the currently-mounted selection view re-invokes `Router.navigate(PLAYER, maze)`, which re-runs Player's own `_bind_screen`-bound `mount()` — now with `state=maze` — and destroys the old (selection) frame after the new (gameplay-placeholder) one is packed. This is the exact same "re-navigate to the screen you're already on" pattern `composition_root.py`'s theme-toggle listener already exercises, already proven safe (a click handler destroying the frame that contains the very button clicked). No new navigation primitive, no `ScreenId.PLAYER_SELECTION`/`ScreenId.PLAYER_GAMEPLAY` split.

**`maze_repository` injection via `functools.partial`, not a widened `ScreenMountFn`.** Widening the shared 5-arg signature to 6 args would force Home/Builder to accept-but-ignore a `MazeRepository` they don't need (precedent exists for that with `state`, but it's not free — every existing Home/Builder test and `_bind_screen()` call site would need touching). Binding `maze_repository` into `mount_player` specifically, before it reaches the untouched `_bind_screen(mount, navigate, theme_controller)`, keeps the blast radius to Player + composition_root only:

```python
router.register(
    ScreenId.PLAYER,
    _bind_screen(
        partial(mount_player, maze_repository=maze_repository), navigate, theme_controller
    ),
)
```

**Gallery labels are position-based, not filename-based.** `Maze` carries no name/label field, so "Classic Maze {i+1} of {n}" is derived purely from the browsed index within `list_names()`'s returned order — never from the underlying storage name. This sidesteps needing numeric-aware sorting of filenames (Epic 4's migration hasn't defined a naming convention yet) and keeps the label meaningful regardless of what a classic maze happens to be named on disk.

## Verification

**Commands:**
- `ruff check .` -- expected: no new lint violations
- `ruff format --check .` -- expected: no formatting diffs
- `pytest` -- expected: full suite green, including the new/updated `list_names`, `ClassicMazeGallery`, and Player-screen tests

## Auto Run Result

**Summary:** Implemented Story 2.1's classic-maze selection screen for the Player: `MazeRepository.list_names(kind)` (plus `CsvMazeRepository`'s implementation) to enumerate persisted mazes; a new `ClassicMazeGallery` widget browsing one classic maze at a time (previous/next/restart, jump-to-number, an inline empty-state, and a "Generate random" entry point wired to a documented Story-2.2 placeholder); Player's `mount()` now dispatches on `state` between that gallery and a minimal gameplay-placeholder view; `composition_root.py` wires a `CsvMazeRepository` into Player's registration via `functools.partial` without touching Home/Builder or the shared `ScreenMountFn` contract. A code-review pass then patched three findings (keyboard-shortcut focus collision, a `list_names()` robustness gap, a weak integration test) and deferred one (theme-toggle mid-browse losing the gallery's position) to `deferred-work.md`.

**Files changed:**
- `src/labyrinthes/application/maze_repository.py` -- new `list_names(kind)` abstract method on the `MazeRepository` port
- `src/labyrinthes/adapters/storage/csv_maze_repository.py` -- `list_names()` implementation, filtered to real files (review patch)
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- new `generate_random` ("n") canonical keybinding
- `src/labyrinthes/adapters/tkinter/player/classic_gallery.py` -- new `ClassicMazeGallery` widget, including the local `<KeyPress-n>`/`<KeyPress-N>` focus-collision fix (review patch)
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- `mount()` gains keyword-only `maze_repository`, dispatches on `state` between the gallery and a new `_mount_gameplay_placeholder()`
- `src/labyrinthes/adapters/tkinter/player/__init__.py` -- stale placeholder docstring fixed
- `src/labyrinthes/app/composition_root.py` -- `build_app()` gains an optional `maze_repository` param; Player's registration wraps `mount_player` via `functools.partial`
- `_bmad-output/implementation-artifacts/epic-2-context.md` -- compiled epic context (missing, so generated during step-01)
- `_bmad-output/implementation-artifacts/deferred-work.md` -- one new entry (theme-toggle-resets-browse-position)
- Tests: `tests/application/test_maze_repository.py`, `tests/adapters/storage/test_csv_maze_repository.py` (+ review patch coverage), `tests/adapters/tkinter/player/conftest.py` (new), `tests/adapters/tkinter/player/test_classic_gallery.py` (new, + review patch coverage), `tests/adapters/tkinter/player/test_player_screen.py` (rewritten), `tests/app/test_composition_root.py` (+ review patch coverage)

**Review findings breakdown:** 14 distinct findings across the two parallel reviewers (Blind Hunter, Edge Case Hunter), 3 overlapping/deduplicated. 3 patched (1 medium: shortcut/focus collision; 2 low: `list_names()` robustness, test strength), 1 deferred (medium: theme-toggle browse-position loss, architectural), 10 rejected (matched explicit spec `Never` clauses, the I/O matrix's own wording, the locked UX mockup verbatim, or pre-existing project-wide conventions already established in earlier stories). Full breakdown in the Review Triage Log above.

**Verification performed:** `ruff check .` clean, `ruff format --check .` clean, `pytest` -- 324 passed (322 before the review-patch pass, +2 new regression tests for the two code-level patches).

**Residual risk:** The deferred theme-toggle/browse-position issue is real but low-consequence (one click restores the browsed maze) and self-contained to this screen; no other residual risks identified. The classic-maze library is empty in this repo today (`mazes/classic/` doesn't exist -- Epic 4's migration hasn't run), so the populated-gallery path is currently exercised only by tests, not by a real run of the app; this is expected and unblocks on Epic 4, not this story.
