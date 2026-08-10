import pytest

from labyrinthes.domain.cell import Cell
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.movement import Direction, attempt_move
from labyrinthes.domain.position import Position


def _passage_grid() -> Grid:
    """A mostly-filled 3x3 grid with one vertical and one horizontal passage.

    `(1, 1)` has its top wall cleared -- a passage between `(0, 1)` and
    `(1, 1)`. `(1, 2)` has its left wall cleared -- a passage between
    `(1, 1)` and `(1, 2)`. Every other real cell stays fully walled.
    """
    rows = []
    for row in range(3):
        real_cells = []
        for col in range(3):
            if (row, col) == (1, 1):
                real_cells.append(Cell("2"))  # left wall only: top clear
            elif (row, col) == (1, 2):
                real_cells.append(Cell("1"))  # top wall only: left clear
            else:
                real_cells.append(Cell("3"))
        rows.append(tuple(real_cells) + (Cell("2"),))
    rows.append(tuple(Cell("1") for _ in range(3)) + (Cell("0"),))
    return Grid(cells=tuple(rows))


def test_up_moves_through_an_open_top_wall():
    grid = _passage_grid()

    result = attempt_move(grid, Position(row=1, col=1), Direction.UP)

    assert result == Position(row=0, col=1)


def test_down_moves_through_the_neighbors_open_top_wall():
    grid = _passage_grid()

    result = attempt_move(grid, Position(row=0, col=1), Direction.DOWN)

    assert result == Position(row=1, col=1)


def test_left_moves_through_an_open_left_wall():
    grid = _passage_grid()

    result = attempt_move(grid, Position(row=1, col=2), Direction.LEFT)

    assert result == Position(row=1, col=1)


def test_right_moves_through_the_neighbors_open_left_wall():
    grid = _passage_grid()

    result = attempt_move(grid, Position(row=1, col=1), Direction.RIGHT)

    assert result == Position(row=1, col=2)


def test_up_is_blocked_by_a_closed_top_wall():
    grid = _passage_grid()

    result = attempt_move(grid, Position(row=2, col=2), Direction.UP)

    assert result == Position(row=2, col=2)


def test_down_is_blocked_by_the_neighbors_closed_top_wall():
    grid = _passage_grid()

    result = attempt_move(grid, Position(row=0, col=0), Direction.DOWN)

    assert result == Position(row=0, col=0)


def test_left_is_blocked_by_a_closed_left_wall():
    grid = _passage_grid()

    result = attempt_move(grid, Position(row=0, col=0), Direction.LEFT)

    assert result == Position(row=0, col=0)


def test_right_is_blocked_by_the_neighbors_closed_left_wall():
    grid = _passage_grid()

    result = attempt_move(grid, Position(row=0, col=0), Direction.RIGHT)

    assert result == Position(row=0, col=0)


@pytest.mark.parametrize(
    ("position", "direction"),
    [
        (Position(row=0, col=0), Direction.UP),
        (Position(row=0, col=0), Direction.LEFT),
        (Position(row=2, col=0), Direction.DOWN),
        (Position(row=0, col=2), Direction.RIGHT),
    ],
)
def test_border_moves_are_blocked_by_the_closed_outer_wall(position, direction):
    grid = _passage_grid()

    result = attempt_move(grid, position, direction)

    assert result == position


@pytest.mark.parametrize(
    "direction", [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]
)
def test_defensively_guards_against_a_malformed_maze_missing_its_border_wall(direction):
    # A structurally valid but semantically malformed 1x1 maze: every
    # cell -- including the padding row/column that would normally carry
    # the closed-border wall bits (see `Grid.filled`'s own convention) --
    # has *no* walls at all. `attempt_move` must not raise or step outside
    # the playable range just because the wall-bit check alone says
    # "open", for every direction: UP/LEFT check `position`'s own cell,
    # DOWN/RIGHT check the *neighbor* -- here, the malformed padding cell.
    grid = Grid(cells=((Cell("0"), Cell("0")), (Cell("0"), Cell("0"))))

    result = attempt_move(grid, Position(row=0, col=0), direction)

    assert result == Position(row=0, col=0)


def test_direction_row_col_deltas():
    assert (Direction.UP.row_delta, Direction.UP.col_delta) == (-1, 0)
    assert (Direction.DOWN.row_delta, Direction.DOWN.col_delta) == (1, 0)
    assert (Direction.LEFT.row_delta, Direction.LEFT.col_delta) == (0, -1)
    assert (Direction.RIGHT.row_delta, Direction.RIGHT.col_delta) == (0, 1)
