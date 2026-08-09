import random
from collections import deque

import pytest

from labyrinthes.domain.errors import DomainValidationError
from labyrinthes.domain.maze import MazeKind
from labyrinthes.domain.maze_generation import generate_random_maze, validate_start_position
from labyrinthes.domain.position import Position


def _open_neighbors(grid, position, width, height):
    """Independent reimplementation of "which neighbors are reachable", used only
    to verify the generator's output from the outside -- not the generator's
    own internal helper."""
    row, col = position.row, position.col
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = row + dr, col + dc
        if not (0 <= nr < height and 0 <= nc < width):
            continue
        if dr == -1:
            open_ = not grid.cell_at(Position(row=row, col=col)).has_top_wall
        elif dr == 1:
            open_ = not grid.cell_at(Position(row=nr, col=nc)).has_top_wall
        elif dc == -1:
            open_ = not grid.cell_at(Position(row=row, col=col)).has_left_wall
        else:
            open_ = not grid.cell_at(Position(row=nr, col=nc)).has_left_wall
        if open_:
            yield Position(row=nr, col=nc)


def _bfs_distances(grid, entry, width, height):
    distances = {entry: 0}
    queue = deque([entry])
    while queue:
        current = queue.popleft()
        for neighbor in _open_neighbors(grid, current, width, height):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)
    return distances


def test_every_real_cell_is_reachable_from_entry():
    maze = generate_random_maze(10, 8, Position(row=0, col=0), random.Random(42))

    distances = _bfs_distances(maze.grid, maze.entry, 10, 8)

    all_real_cells = {Position(row=r, col=c) for r in range(8) for c in range(10)}
    assert set(distances.keys()) == all_real_cells


def test_outer_border_padding_is_never_touched():
    maze = generate_random_maze(6, 5, Position(row=2, col=2), random.Random(7))
    grid = maze.grid

    for col in range(6):
        assert grid.cells[5][col].value == "1"  # padding row
    for row in range(5):
        assert grid.cells[row][6].value == "2"  # padding column
    assert grid.cells[5][6].value == "0"  # corner


def test_kind_is_generated_and_id_is_none():
    maze = generate_random_maze(5, 5, Position(row=0, col=0), random.Random(1))

    assert maze.kind == MazeKind.GENERATED
    assert maze.id is None


def test_maze_dimensions_and_entry_match_input():
    entry = Position(row=1, col=2)
    maze = generate_random_maze(7, 4, entry, random.Random(3))

    assert maze.grid.width == 7
    assert maze.grid.height == 4
    assert maze.entry == entry


def test_exit_is_the_farthest_cell_by_bfs_distance_from_entry():
    maze = generate_random_maze(9, 7, Position(row=0, col=0), random.Random(99))

    distances = _bfs_distances(maze.grid, maze.entry, 9, 7)
    max_distance = max(distances.values())

    assert distances[maze.exit] == max_distance


def test_exit_differs_from_entry_for_a_multi_cell_maze():
    maze = generate_random_maze(10, 8, Position(row=0, col=0), random.Random(5))

    assert maze.exit != maze.entry


@pytest.mark.parametrize(("width", "height"), [(0, 5), (5, 0), (-1, 5), (5, -1)])
def test_rejects_non_positive_dimensions(width, height):
    with pytest.raises(DomainValidationError):
        generate_random_maze(width, height, Position(row=0, col=0), random.Random(0))


@pytest.mark.parametrize(
    "entry",
    [
        Position(row=-1, col=0),
        Position(row=0, col=-1),
        Position(row=5, col=0),
        Position(row=0, col=5),
    ],
)
def test_rejects_entry_outside_the_grid(entry):
    with pytest.raises(DomainValidationError):
        generate_random_maze(5, 5, entry, random.Random(0))


def test_generation_is_deterministic_for_a_given_rng_seed():
    entry = Position(row=0, col=0)
    first = generate_random_maze(10, 8, entry, random.Random(123))
    second = generate_random_maze(10, 8, entry, random.Random(123))

    assert first.grid == second.grid
    assert first.exit == second.exit


def test_generation_differs_across_different_rng_seeds():
    entry = Position(row=0, col=0)
    first = generate_random_maze(10, 8, entry, random.Random(1))
    second = generate_random_maze(10, 8, entry, random.Random(2))

    assert first.grid != second.grid


def test_single_cell_maze_has_entry_equal_to_exit():
    maze = generate_random_maze(1, 1, Position(row=0, col=0), random.Random(0))

    assert maze.entry == maze.exit == Position(row=0, col=0)


# -- validate_start_position ---------------------------------------------------


def test_validate_start_position_returns_no_errors_for_an_in_range_position():
    assert validate_start_position(10, 8, Position(row=0, col=0)) == []
    assert validate_start_position(10, 8, Position(row=7, col=9)) == []


def test_validate_start_position_reports_column_outside_the_entered_grid():
    errors = validate_start_position(10, 8, Position(row=0, col=15))

    assert errors == ["Start column must be between 0 and 9."]


def test_validate_start_position_reports_row_outside_the_entered_grid():
    errors = validate_start_position(10, 8, Position(row=15, col=0))

    assert errors == ["Start row must be between 0 and 7."]


def test_validate_start_position_reports_both_when_both_outside_the_entered_grid():
    errors = validate_start_position(10, 8, Position(row=15, col=15))

    assert errors == [
        "Start column must be between 0 and 9.",
        "Start row must be between 0 and 7.",
    ]
