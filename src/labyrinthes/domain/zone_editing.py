"""Pure zone editing operations over `Grid`/`Position` (Story 3.3).

Return new immutable `Grid` values -- never mutate in place, matching
`wall_editing.py`'s pattern. `destroy_zone`/`restore_zone` batch
`wall_editing.break_wall`/`restore_wall` over every interior wall spanned
by two corner cells (a click-and-drag rectangle), reusing those single-wall
mutators per non-border wall rather than duplicating the bit-twiddle.

Unlike the single-wall mutators they wrap, `destroy_zone`/`restore_zone`
never raise `DomainValidationError` for a border wall inside their span --
`_walls_in_zone` checks `level_visibility.is_border_wall` and silently
skips it instead, so a zone touching the grid's outer edge (the common
case) still processes every interior wall in one pass instead of aborting
the whole operation (FR-2's closed-border invariant always wins, but never
by refusing the batch).
"""

from __future__ import annotations

from collections.abc import Iterator

from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level_visibility import Wall, is_border_wall
from labyrinthes.domain.position import Position
from labyrinthes.domain.wall_editing import break_wall, restore_wall

__all__ = ["destroy_zone", "restore_zone"]


def _walls_in_zone(grid: Grid, corner_a: Position, corner_b: Position) -> Iterator[Wall]:
    """Every non-border `Wall` in the rectangle spanned by `corner_a`/`corner_b`.

    The two corners are normalized order-independently to `(r0, c0)` <=
    `(r1, c1)` (inclusive cell range). Following `count_broken_walls`'s
    indexing convention, bounded to the span instead of the whole grid:
    "top" walls run `row in [r0, r1+1]`, `col in [c0, c1]`; "left" walls
    run `row in [r0, r1]`, `col in [c0, c1+1]`. Border walls are skipped,
    never yielded.
    """
    r0, r1 = sorted((corner_a.row, corner_b.row))
    c0, c1 = sorted((corner_a.col, corner_b.col))

    for row in range(r0, r1 + 2):
        for col in range(c0, c1 + 1):
            wall = Wall(row, col, "top")
            if not is_border_wall(grid, wall):
                yield wall

    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 2):
            wall = Wall(row, col, "left")
            if not is_border_wall(grid, wall):
                yield wall


def destroy_zone(grid: Grid, corner_a: Position, corner_b: Position) -> Grid:
    """Break every interior wall in the rectangle spanned by `corner_a`/`corner_b`.

    Border walls within the span are silently skipped (never raised) --
    see the module docstring. Returns a new `Grid`; `grid` is untouched.
    """
    for wall in _walls_in_zone(grid, corner_a, corner_b):
        grid = break_wall(grid, wall)
    return grid


def restore_zone(grid: Grid, corner_a: Position, corner_b: Position) -> Grid:
    """Restore every interior wall in the rectangle spanned by `corner_a`/`corner_b`.

    The mirror of `destroy_zone` -- same span, same border-skip. Restoring
    the identical corners immediately after a `destroy_zone` call sets
    every wall in the span back to present, satisfying AC2.
    """
    for wall in _walls_in_zone(grid, corner_a, corner_b):
        grid = restore_wall(grid, wall)
    return grid
