"""`MazeSizeBounds` value object -- the FR-4/FR-10 dimension policy bounds.

The one pure policy-bounds source for a maze's columns/rows, shared by this
story's random-generation dialog and (later) the Builder's New Maze dialog --
declaring the 3-50 columns / 3-35 rows defaults once here is what keeps
Builder/Game from drifting into two independently hardcoded copies of the
same bounds.

`validate_dimensions` is pure UI-facing validation, not a domain invariant:
`generate_random_maze` (`maze_generation.py`) does not know about these
bounds at all -- only "structurally invalid" (`width <= 0`/`height <= 0`)
is a domain concern there.
"""

from dataclasses import dataclass

__all__ = ["DEFAULT_MAZE_SIZE_BOUNDS", "MazeSizeBounds", "validate_dimensions"]


@dataclass(frozen=True)
class MazeSizeBounds:
    """Inclusive `[min, max]` bounds for a maze's columns and rows."""

    min_columns: int
    max_columns: int
    min_rows: int
    max_rows: int


DEFAULT_MAZE_SIZE_BOUNDS = MazeSizeBounds(min_columns=3, max_columns=50, min_rows=3, max_rows=35)


def validate_dimensions(bounds: MazeSizeBounds, width: int, height: int) -> list[str]:
    """Human-readable error messages for `width`/`height` outside `bounds`.

    Returns `[]` when both are within bounds. Each message is meant to be
    read directly into an inline validation label -- not just a boolean --
    since `GenerateRandomDialog` shows per-field text, not a generic
    "invalid" flag.
    """
    errors: list[str] = []
    if not (bounds.min_columns <= width <= bounds.max_columns):
        errors.append(f"Columns must be between {bounds.min_columns} and {bounds.max_columns}.")
    if not (bounds.min_rows <= height <= bounds.max_rows):
        errors.append(f"Rows must be between {bounds.min_rows} and {bounds.max_rows}.")
    return errors
