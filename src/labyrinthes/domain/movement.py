"""Movement mechanics: `Direction` + `attempt_move`, pure functions over `Grid`/`Position`.

Mirrors `maze_generation._open_neighbors`'s per-direction wall-bit check
(see that module's docstring): UP/LEFT check the *current* cell's
top/left wall bit, DOWN/RIGHT check the *neighbor*'s -- via
`Grid.cell_at`, which already handles the closed-border padding row/
column so no extra bounds juggling is needed here for the padding side.

No Tkinter, no session/orchestration state -- this only ever answers "is
the one-cell step from `position` in `direction` open", returning either
the new `Position` or `position` unchanged when it's blocked.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from labyrinthes.domain.grid import Grid
from labyrinthes.domain.position import Position

__all__ = ["Direction", "attempt_move"]


@dataclass(frozen=True)
class _DirectionSpec:
    row_delta: int
    col_delta: int


class Direction(enum.Enum):
    """One of the four cardinal one-cell moves, each carrying its row/col delta."""

    UP = _DirectionSpec(row_delta=-1, col_delta=0)
    DOWN = _DirectionSpec(row_delta=1, col_delta=0)
    LEFT = _DirectionSpec(row_delta=0, col_delta=-1)
    RIGHT = _DirectionSpec(row_delta=0, col_delta=1)

    @property
    def row_delta(self) -> int:
        return self.value.row_delta

    @property
    def col_delta(self) -> int:
        return self.value.col_delta


def attempt_move(grid: Grid, position: Position, direction: Direction) -> Position:
    """`position` shifted one cell in `direction`, or `position` unchanged if blocked.

    UP/LEFT check `position`'s own top/left wall bit; DOWN/RIGHT check the
    *neighbor* cell's top/left wall bit -- the same asymmetric convention
    `maze_generation`'s carving already establishes (a wall is only ever
    encoded on one side of a passage, never both). The candidate position
    is also defensively guarded against the playable `[0, width) x
    [0, height)` range: a malformed classic maze (e.g. a missing border
    wall) could otherwise send the ball into the padding row/column.
    """
    candidate = Position(
        row=position.row + direction.row_delta, col=position.col + direction.col_delta
    )

    if direction is Direction.UP:
        blocked = grid.cell_at(position).has_top_wall
    elif direction is Direction.DOWN:
        blocked = grid.cell_at(candidate).has_top_wall
    elif direction is Direction.LEFT:
        blocked = grid.cell_at(position).has_left_wall
    else:  # Direction.RIGHT
        blocked = grid.cell_at(candidate).has_left_wall

    if blocked:
        return position

    if not (0 <= candidate.row < grid.height and 0 <= candidate.col < grid.width):
        return position

    return candidate
