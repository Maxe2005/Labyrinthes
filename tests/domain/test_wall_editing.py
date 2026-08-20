import pytest

from labyrinthes.adapters.storage.csv_maze_format import read_maze_csv, write_maze_csv
from labyrinthes.domain.errors import DomainValidationError
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level_visibility import Wall
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.position import Position
from labyrinthes.domain.wall_editing import (
    break_wall,
    count_broken_walls,
    restore_wall,
    toggle_wall,
    wall_between,
)


def _filled(width: int = 3, height: int = 3) -> Grid:
    return Grid.filled(width, height)


# -- break_wall / restore_wall ------------------------------------------


def test_break_wall_clears_the_top_bit_of_the_owning_cell():
    grid = _filled()

    result = break_wall(grid, Wall(1, 1, "top"))

    assert result.cell_at(Position(1, 1)).value == "2"  # left wall only remains


def test_break_wall_clears_the_left_bit_of_the_owning_cell():
    grid = _filled()

    result = break_wall(grid, Wall(1, 1, "left"))

    assert result.cell_at(Position(1, 1)).value == "1"  # top wall only remains


def test_break_wall_does_not_mutate_the_original_grid():
    grid = _filled()

    break_wall(grid, Wall(1, 1, "top"))

    assert grid.cell_at(Position(1, 1)).value == "3"


def test_break_wall_leaves_every_other_cell_untouched():
    grid = _filled()

    result = break_wall(grid, Wall(1, 1, "top"))

    for row in range(grid.height + 1):
        for col in range(grid.width + 1):
            if (row, col) == (1, 1):
                continue
            assert result.cell_at(Position(row, col)) == grid.cell_at(Position(row, col))


def test_restore_wall_sets_the_bit_back():
    grid = break_wall(_filled(), Wall(1, 1, "top"))

    result = restore_wall(grid, Wall(1, 1, "top"))

    assert result.cell_at(Position(1, 1)).value == "3"


def test_restore_wall_is_a_no_op_value_when_the_wall_is_already_present():
    grid = _filled()

    result = restore_wall(grid, Wall(1, 1, "left"))

    assert result.cell_at(Position(1, 1)).value == "3"


@pytest.mark.parametrize(
    "wall",
    [
        Wall(0, 1, "top"),  # top border row
        Wall(3, 1, "top"),  # bottom border row (row == height)
        Wall(1, 0, "left"),  # left border column
        Wall(1, 3, "left"),  # right border column (col == width)
    ],
)
def test_break_wall_refuses_a_border_wall(wall):
    grid = _filled()

    with pytest.raises(DomainValidationError):
        break_wall(grid, wall)


@pytest.mark.parametrize(
    "wall",
    [
        Wall(0, 1, "top"),
        Wall(3, 1, "top"),
        Wall(1, 0, "left"),
        Wall(1, 3, "left"),
    ],
)
def test_restore_wall_refuses_a_border_wall(wall):
    grid = _filled()

    with pytest.raises(DomainValidationError):
        restore_wall(grid, wall)


def test_break_wall_refusal_leaves_the_grid_unchanged():
    grid = _filled()

    with pytest.raises(DomainValidationError):
        break_wall(grid, Wall(0, 1, "top"))

    assert grid == _filled()


# -- toggle_wall ----------------------------------------------------------


def test_toggle_wall_breaks_a_present_wall():
    grid = _filled()

    result = toggle_wall(grid, Wall(1, 1, "top"))

    assert result.cell_at(Position(1, 1)).value == "2"


def test_toggle_wall_restores_an_absent_wall():
    grid = break_wall(_filled(), Wall(1, 1, "top"))

    result = toggle_wall(grid, Wall(1, 1, "top"))

    assert result.cell_at(Position(1, 1)).value == "3"


def test_toggle_wall_is_its_own_inverse():
    grid = _filled()

    once = toggle_wall(grid, Wall(1, 1, "left"))
    twice = toggle_wall(once, Wall(1, 1, "left"))

    assert twice == grid


def test_toggle_wall_refuses_a_border_wall():
    grid = _filled()

    with pytest.raises(DomainValidationError):
        toggle_wall(grid, Wall(0, 1, "top"))


# -- count_broken_walls -----------------------------------------------


def test_count_broken_walls_is_zero_for_a_freshly_filled_grid():
    assert count_broken_walls(_filled(5, 4)) == 0


def test_count_broken_walls_increments_on_break_and_decrements_on_restore():
    grid = _filled()

    grid = break_wall(grid, Wall(1, 1, "top"))
    assert count_broken_walls(grid) == 1

    grid = break_wall(grid, Wall(1, 1, "left"))
    assert count_broken_walls(grid) == 2

    grid = restore_wall(grid, Wall(1, 1, "top"))
    assert count_broken_walls(grid) == 1


def test_count_broken_walls_never_counts_border_walls():
    # Every border wall is already "present" on a filled grid and can't be
    # broken at all (break_wall refuses it) -- this just pins that the
    # counting loop's own border exclusion matches `is_border_wall`.
    grid = _filled(3, 3)

    assert count_broken_walls(grid) == 0


# -- wall_between -----------------------------------------------------


def test_wall_between_up_is_the_cells_own_top_wall():
    assert wall_between(Position(2, 1), Direction.UP) == Wall(2, 1, "top")


def test_wall_between_down_is_the_neighbors_top_wall():
    assert wall_between(Position(2, 1), Direction.DOWN) == Wall(3, 1, "top")


def test_wall_between_left_is_the_cells_own_left_wall():
    assert wall_between(Position(2, 1), Direction.LEFT) == Wall(2, 1, "left")


def test_wall_between_right_is_the_neighbors_left_wall():
    assert wall_between(Position(2, 1), Direction.RIGHT) == Wall(2, 2, "left")


# -- AC4: save format compatibility ------------------------------------


def test_a_maze_with_broken_walls_round_trips_through_the_csv_format_unchanged(tmp_path):
    grid = break_wall(_filled(4, 3), Wall(1, 1, "top"))
    grid = break_wall(grid, Wall(2, 2, "left"))
    maze = Maze(
        grid=grid,
        entry=Position(0, 0),
        exit=Position(2, 3),
        kind=MazeKind.SKETCH,
        id=None,
    )
    path = tmp_path / "edited.csv"

    write_maze_csv(path, maze)
    reloaded = read_maze_csv(path, MazeKind.SKETCH)

    assert reloaded.grid == grid
    assert reloaded.entry == maze.entry
    assert reloaded.exit == maze.exit
