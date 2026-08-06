# Deferred Work

## Deferred from: code review of 1-1-domain-model-foundation (2026-08-05)

- `Grid.filled` has no type validation; a non-`int` width/height raises a raw `TypeError` instead of `DomainValidationError` [src/labyrinthes/domain/grid.py:54] — deferred, pre-existing pattern across the whole diff (no value object in this story validates argument *types*, only business-domain invariants; consistent with the codebase having no static type-checker configured yet).
- `MazeId` performs zero validation — an empty/whitespace string is accepted as a valid opaque id [src/labyrinthes/domain/maze_id.py:11] — deferred, the story explicitly scopes `MazeId` to "an opaque identifier only, no minting scheme here"; a validation rule is better decided alongside Story 1.4's minting function.

## Deferred from: code review of spec-1-2-automated-domain-ui-boundary-test (2026-08-06)

- `TYPE_CHECKING`-guarded imports are not excluded from the AST scan and would false-positive once `domain/`/`application/` first use type-only imports [tests/test_architecture_boundaries.py] — deferred, pre-existing scope boundary; revisit when a story first needs a `TYPE_CHECKING` import in `domain/`/`application/`.
- Minor untested/low-probability edge branches in the scanner: bare `from . import x` (logic re-read, correct), a relative import climbing above the top-level package (Python itself would crash on this at runtime), a directory shadowed by a same-named file [tests/test_architecture_boundaries.py] — deferred, no reachable consequence today.
- `_format_violations` reports no line number, only file + module [tests/test_architecture_boundaries.py:117] — deferred, optional debuggability improvement, not required by any AC.
- A future `adapters/tkinter/__init__.py` barrel re-export would bypass the screen-isolation check [tests/test_architecture_boundaries.py] — deferred, speculative/forward-looking, no such file exists yet.
