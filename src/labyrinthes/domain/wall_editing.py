"""Pure wall editing operations over `Grid`/`Cell`/`Wall` (Story 3.2).

Return new immutable `Grid` values -- never mutate in place. Wall encoding
follows the same 0/1/2/3 contract as `Cell`/`Grid` (bit 0 = top wall, bit 1
= left wall), preserving the CSV save format from Story 1.4's
`MazeRepository` (NFR2/AD-6): a break/restore only ever flips one of those
two bits on the one cell that owns the segment, so `CsvMazeRepository`
reads/writes the resulting `Cell.value` exactly as it always has.

`Wall` coordinates are raw grid indices (`row` in `0..grid.height`, `col`
in `0..grid.width`), identified by `side` (`"top"` or `"left"`). Border
walls (the playable-area outer contour, `level_visibility.is_border_wall`)
are refused by every mutator here -- the closed-border invariant (FR-2)
always wins, so `break_wall`/`restore_wall`/`toggle_wall` raise
`DomainValidationError` rather than silently no-op.

`wall_between` reuses `level_visibility._blocked_wall`'s move -> `Wall`
mapping so a cursor crossing a wall (Pass-through mode,
`application.builder_session.move_cursor`) breaks exactly the same segment
the legacy `fleches`/`modifier_un_mur` convention would.
"""

from __future__ import annotations

from labyrinthes.domain.cell import Cell
from labyrinthes.domain.errors import DomainValidationError
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level_visibility import Wall, _blocked_wall, is_border_wall
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.position import Position

__all__ = [
    "break_wall",
    "count_broken_walls",
    "restore_wall",
    "toggle_wall",
    "wall_between",
]

_WALL_BIT = {"top": 1, "left": 2}


def _with_wall_bit(grid: Grid, wall: Wall, *, present: bool) -> Grid:
    """Return a new `Grid` with `wall`'s bit set (`present=True`) or cleared.

    Raises `DomainValidationError` for a border `wall` -- shared by every
    mutator below so the refusal message/behavior never drifts between
    `break_wall`/`restore_wall`/`toggle_wall`.
    """
    if is_border_wall(grid, wall):
        raise DomainValidationError(
            f"Cannot edit border wall {wall!r}; the maze's outer contour must stay closed"
        )
    bit = _WALL_BIT[wall.side]
    cell = grid.cell_at(Position(wall.row, wall.col))
    value = int(cell.value)
    new_value = (value | bit) if present else (value & ~bit)
    new_cell = Cell(str(new_value))

    rows = list(grid.cells)
    row = list(rows[wall.row])
    row[wall.col] = new_cell
    rows[wall.row] = tuple(row)
    return Grid(cells=tuple(rows))


def break_wall(grid: Grid, wall: Wall) -> Grid:
    """Clear `wall`'s bit, opening a passage between its two adjacent cells.

    Only the one cell that owns the bit (`wall.row`/`wall.col`) has its
    encoding changed -- walls are single-encoded, never stored on both
    sides of a passage, so the passage opens consistently for both
    adjacent cells even though only one digit changes (FR-1's "both cells'
    encoding update symmetrically" is this behavioral symmetry, not a
    literal two-digit change).

    Raises `DomainValidationError` for a border `wall`.
    """
    return _with_wall_bit(grid, wall, present=False)


def restore_wall(grid: Grid, wall: Wall) -> Grid:
    """Set `wall`'s bit, closing the passage back up.

    The mirror of `break_wall` -- same single-cell encoding, same border
    refusal.
    """
    return _with_wall_bit(grid, wall, present=True)


def toggle_wall(grid: Grid, wall: Wall) -> Grid:
    """Break `wall` if it's currently present, restore it if currently absent.

    Raises `DomainValidationError` for a border `wall` (via `break_wall`/
    `restore_wall`).
    """
    cell = grid.cell_at(Position(wall.row, wall.col))
    currently_present = cell.has_top_wall if wall.side == "top" else cell.has_left_wall
    return _with_wall_bit(grid, wall, present=not currently_present)


def count_broken_walls(grid: Grid) -> int:
    """The number of interior (non-border) wall segments currently broken.

    A fresh `Grid.filled` grid has every interior wall present, so this
    starts at 0 and moves by exactly ±1 per `break_wall`/`restore_wall`
    call -- the HUD "Walls broken" chip's live value.

    Unlike `level_visibility.total_interior_walls` (which counts *present*
    bits and so never trips over the padding row/column's unused bits --
    those are always absent by construction), this counts *absent* bits,
    so it must not walk the padding column's top bit or the padding row's
    left bit -- both are dead encoding space, never a real wall, always
    absent. A "top" bit is only meaningful for a real column (`col <
    width`); a "left" bit only for a real row (`row < height`).
    """
    count = 0
    for row in range(grid.height + 1):
        for col in range(grid.width):
            top_wall = Wall(row, col, "top")
            if is_border_wall(grid, top_wall):
                continue
            if not grid.cell_at(Position(row=row, col=col)).has_top_wall:
                count += 1
    for row in range(grid.height):
        for col in range(grid.width + 1):
            left_wall = Wall(row, col, "left")
            if is_border_wall(grid, left_wall):
                continue
            if not grid.cell_at(Position(row=row, col=col)).has_left_wall:
                count += 1
    return count


def wall_between(position: Position, direction: Direction) -> Wall:
    """The raw-coordinate `Wall` a move from `position` in `direction` crosses.

    Delegates to `level_visibility._blocked_wall`, the same mapping
    `note_collision` uses, so Break/Pass-through editing and gameplay
    collision detection always agree on which segment a given move
    touches. The returned `Wall` may be a border wall; callers (e.g.
    `application.builder_session.move_cursor`) check `is_border_wall`
    before attempting to break it.
    """
    return _blocked_wall(position, direction)
