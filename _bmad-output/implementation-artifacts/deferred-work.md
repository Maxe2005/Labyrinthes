# Deferred Work

## Deferred from: code review of 1-1-domain-model-foundation (2026-08-05)

- `Grid.filled` has no type validation; a non-`int` width/height raises a raw `TypeError` instead of `DomainValidationError` [src/labyrinthes/domain/grid.py:54] — deferred, pre-existing pattern across the whole diff (no value object in this story validates argument *types*, only business-domain invariants; consistent with the codebase having no static type-checker configured yet).
- `MazeId` performs zero validation — an empty/whitespace string is accepted as a valid opaque id [src/labyrinthes/domain/maze_id.py:11] — deferred, the story explicitly scopes `MazeId` to "an opaque identifier only, no minting scheme here"; a validation rule is better decided alongside Story 1.4's minting function.
