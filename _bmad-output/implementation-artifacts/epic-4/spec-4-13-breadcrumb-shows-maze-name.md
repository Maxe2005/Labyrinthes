---
title: 'Story 4.13: Breadcrumb shows the maze''s own name'
type: 'feature'
created: '2026-09-10'
status: 'done'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-4/epic-4-context.md
baseline_commit: 6c9c4171b8581ada2b15702e37eadad364a7678a
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Player's breadcrumb shows a kind-derived segment ("Classic Maze", "Saved Random Maze", …) but never the maze's own saved name, so two mazes of the same kind are indistinguishable in the breadcrumb (e.g. two Classic mazes both just read "Classic Maze").

**Approach:** Thread the maze's storage-layer name (filename-derived, already known wherever a `Maze` is loaded by name — e.g. the selection gallery) alongside the `Maze` through Player's navigation and screen state, and append it as a trailing breadcrumb segment after the kind segment. `Maze` (domain) gains no `name` field.

## Boundaries & Constraints

**Always:**
- Player gameplay view only. Home has no breadcrumb; Builder's breadcrumb has no kind-derived segment at all today (pre-existing gap) and is out of scope.
- Name segment has no click handler, same as the existing kind segment.
- Name segment exists only when the maze is already named: loaded via a gallery card (Classic/Creation/Saved-Random, name known at mount), or a `generated` maze saved mid-session via the existing Save Maze flow (name becomes known at that moment).
- An unsaved `generated` maze: no name segment — breadcrumb stays at 3 segments (Home/Player/kind) until saved.
- A `BuilderTestLaunch`-originated maze (Test-in-Player from Builder): no name segment — Builder never tracks a name today.
- Growing the breadcrumb from 3 to 4 segments mid-session is additive only — existing segments/handlers/tests must not be rebuilt or re-created.

**Ask First:** None — fully determined by epic context + existing code investigation.

**Never:** Extend `NavigateFn` beyond one new sibling type to `BuilderTestLaunch`. Touch Builder's breadcrumb. Add a `name` field to `Maze` (domain). Change Home's screen.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Classic/Creation/Saved-Random card clicked in gallery | `MazeSelectionGallery` card for name "10x10edf" | Player mounts with 4-segment breadcrumb: Home / Player / \<kind label\> / "10x10edf" | N/A |
| Generate Random → Play | Fresh `generated` maze, never saved | Breadcrumb has 3 segments only (Home / Player / Random Maze), no name segment | N/A |
| Mid-session Save Maze on a `generated` maze | User types "foo", confirms save | Breadcrumb grows to 4 segments; kind segment updates to "Saved Random Maze" (existing behavior) and a new trailing "foo" segment appears | N/A |
| Test-in-Player launch from Builder | `BuilderTestLaunch` state | Breadcrumb unchanged — no name segment (as today) | N/A |

</frozen-after-approval>

## Code Map

- `src/labyrinthes/adapters/tkinter/common/navigation.py` -- `NavigateFn` type alias, `BuilderTestLaunch` (L35-51); add a sibling `MazeWithName(maze: Maze, name: str)` dataclass and extend the union
- `src/labyrinthes/adapters/tkinter/common/breadcrumb.py` -- `BreadcrumbSegment` (L28-37), `Breadcrumb.set_label()` (L127-136) overwrites an existing index only; add `append_segment(segment: BreadcrumbSegment) -> int` that packs one more label+separator without touching existing ones
- `src/labyrinthes/adapters/tkinter/common/top_bar.py` -- `TopBar.set_breadcrumb_label()` (L95-104) passthrough pattern; add `append_breadcrumb_segment(segment) -> int` passthrough to the new `Breadcrumb` method
- `src/labyrinthes/adapters/tkinter/player/maze_selection_gallery.py` -- `_build_section` (L127-174) already has `(name, maze)` together at L155-162; `_on_card_activated` (L179-180) currently calls `navigate(ScreenId.PLAYER, maze)`, drops `name` -- wrap as `navigate(ScreenId.PLAYER, MazeWithName(maze, name))`
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- `_KIND_LABELS` (L60-66), breadcrumb construction (L121-138), `on_kind_changed` wiring (L186); unwrap `MazeWithName` in `mount()`, include a 4th segment at construction when name is known, pass `initial_name` + a new `on_name_saved` callback into `GameplayScreen`
- `src/labyrinthes/adapters/tkinter/player/gameplay/screen.py` -- `self._maze = maze` (L266), `on_kind_changed` param (L263), save flow `_on_save_confirmed` (L924-940); add `initial_name: str | None` param, store `self._maze_name`, invoke new `on_name_saved(name)` callback alongside the existing `on_kind_changed` call at the point a `generated` maze is first saved
- `tests/adapters/tkinter/common/test_breadcrumb.py` -- add `append_segment` coverage
- `tests/adapters/tkinter/player/test_player_screen.py` -- existing kind-segment tests (L64, L151, L181, L239) are the pattern to mirror for the name segment

## Tasks & Acceptance

**Execution:**
- [x] `navigation.py` -- add `MazeWithName` dataclass, extend `NavigateFn` union -- carries the name from gallery to Player
- [x] `breadcrumb.py` -- add `append_segment()` -- grows the breadcrumb without disturbing existing segments
- [x] `top_bar.py` -- add `append_breadcrumb_segment()` passthrough
- [x] `maze_selection_gallery.py` -- `_on_card_activated` navigates with `MazeWithName(maze, name)`
- [x] `player/screen.py` -- unwrap `MazeWithName`; build the 4th segment at construction when name known; wire `initial_name`/`on_name_saved` into `GameplayScreen`
- [x] `gameplay/screen.py` -- accept `initial_name`, track `self._maze_name`, fire `on_name_saved` on first successful save of a `generated` maze
- [x] `test_breadcrumb.py` -- `append_segment` adds one label+separator, existing segments/handlers untouched
- [x] `test_player_screen.py` -- name segment present (named kinds via gallery), absent (fresh `generated`), grows mid-session after save, absent for `BuilderTestLaunch`
- [x] Run `ruff check .`, `ruff format --check .`, `pytest -q` -- all green

**Acceptance Criteria:**
- Given a Classic/Creation/Saved-Random maze opened from the gallery, when Player mounts, then the breadcrumb has 4 segments ending with the maze's saved name, and that segment has no click handler.
- Given a freshly generated (unsaved) maze, when Player mounts, then the breadcrumb has exactly 3 segments.
- Given that generated maze is saved mid-session with a typed name, when the save succeeds, then the breadcrumb grows to 4 segments with the typed name trailing, and the first 3 segments' widgets are unchanged.
- Given a Builder Test-in-Player launch, when Player mounts, then breadcrumb behavior is unchanged from today (no name segment).

## Design Notes

`MazeWithName` is a thin sibling to `BuilderTestLaunch` in the same module, not a `Maze` field — keeps the "no `name` on domain `Maze`" constraint mechanical rather than a discipline to remember. `append_segment()` is additive-only by design: existing tests assert on `_labels`/`_segment_handlers` by index, and a full rebuild would risk invalidating those indices for no benefit, since the first 3 segments never change shape once mounted.

## Verification

**Commands:**
- `ruff check .` -- expected: no errors
- `ruff format --check .` -- expected: no reformatting needed
- `pytest -q` -- expected: all tests pass, including new `append_segment` and Player breadcrumb name-segment tests

**Manual checks (if no CLI):**
- Launch Player, open the gallery, click a Classic maze card — breadcrumb reads "Home / Player / Classic Maze / \<its saved name\>".
- Generate a random maze, click Play — breadcrumb reads "Home / Player / Random Maze" (3 segments). Save it mid-session with a typed name — breadcrumb grows to 4 segments ending with that name.

## Suggested Review Order

**Carrying the name from gallery to Player**

- Entry point: the payload that lets Player know a maze's own name without adding one to the domain `Maze`.
  [`navigation.py:62`](../../../src/labyrinthes/adapters/tkinter/common/navigation.py#L62)

- The gallery already pairs `(name, maze)` per card; this is the one line that used to drop `name` on the floor.
  [`maze_selection_gallery.py:181`](../../../src/labyrinthes/adapters/tkinter/player/maze_selection_gallery.py#L181)

**Player screen — unwrapping state into a 3-or-4-segment breadcrumb**

- Every `state` shape (`None`/`BuilderTestLaunch`/`MazeWithName`/bare `Maze`) collapses to one `(maze, maze_name)` pair here.
  [`player/screen.py:132`](../../../src/labyrinthes/adapters/tkinter/player/screen.py#L132)

- The 4th segment is appended at construction only when a name is already known — never a placeholder.
  [`player/screen.py:173`](../../../src/labyrinthes/adapters/tkinter/player/screen.py#L173)

- Mid-session growth: fires once, the moment a `generated` maze is first named via Save Maze.
  [`player/screen.py:209`](../../../src/labyrinthes/adapters/tkinter/player/screen.py#L209)

**Gameplay screen — tracking the name across a save**

- `initial_name`/`on_name_saved` let this screen report a newly-typed name without knowing anything about breadcrumbs.
  [`gameplay/screen.py:271`](../../../src/labyrinthes/adapters/tkinter/player/gameplay/screen.py#L271)

- Fired alongside the existing `on_kind_changed` call, at the exact point a `generated` maze becomes named.
  [`gameplay/screen.py:970`](../../../src/labyrinthes/adapters/tkinter/player/gameplay/screen.py#L970)

**Breadcrumb widget — growing after construction**

- `append_segment()` reuses the same per-segment wiring as `__init__`'s loop, indexed identically — additive, never a rebuild.
  [`breadcrumb.py:148`](../../../src/labyrinthes/adapters/tkinter/common/breadcrumb.py#L148)

- `TopBar`'s passthrough — a graceful `-1` no-op when there's no breadcrumb, matching `set_breadcrumb_label()`'s own precedent.
  [`top_bar.py:106`](../../../src/labyrinthes/adapters/tkinter/common/top_bar.py#L106)

**Peripherals — type consistency & tests**

- `MountFn`/`Router.navigate()` widened to match `NavigateFn`, since `mount()` is bound to both.
  [`router.py:31`](../../../src/labyrinthes/app/router.py#L31)

- The 4 I/O-matrix scenarios: named-via-gallery, no-name-when-unsaved, grows-after-save, no-name-for-test-launch.
  [`test_player_screen.py:216`](../../../tests/adapters/tkinter/player/test_player_screen.py#L216)

- Growth mechanics in isolation: existing segments/handlers survive `append_segment()` byte-for-byte.
  [`test_breadcrumb.py:20`](../../../tests/adapters/tkinter/common/test_breadcrumb.py#L20)

- The no-op path added by review: `append_breadcrumb_segment()` returns `-1` rather than asserting.
  [`test_top_bar.py:71`](../../../tests/adapters/tkinter/common/test_top_bar.py#L71)

- Gallery activation now hands off `MazeWithName`, not a bare `Maze`.
  [`test_maze_selection_gallery.py:160`](../../../tests/adapters/tkinter/player/test_maze_selection_gallery.py#L160)
