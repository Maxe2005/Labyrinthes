import pytest

from labyrinthes.domain.difficulty import Difficulty
from labyrinthes.domain.errors import DomainValidationError
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level import Level
from labyrinthes.domain.level_visibility import (
    Partition,
    Wall,
    advance_visibility,
    initial_level_visibility,
    is_border_wall,
    note_collision,
    partition_grid,
    partition_size_for_difficulty,
    reveal_threshold,
    show_contour,
    total_interior_walls,
    visible_walls,
)
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.position import Position


def _filled_maze(width: int, height: int) -> Maze:
    return Maze(
        grid=Grid.filled(width=width, height=height),
        entry=Position(row=0, col=0),
        exit=Position(row=height - 1, col=width - 1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


# -- partition sizing & grid ------------------------------------------


def test_partition_size_for_difficulty_matches_the_legacy_formula():
    # The spec's worked example: 8x6, D1 -> 3x3 partitions, 3x2 = 6 partitions.
    assert partition_size_for_difficulty(8, 6, Difficulty.ONE) == (3, 3)
    assert partition_size_for_difficulty(8, 6, Difficulty.TWO) == (2, 2)
    assert partition_size_for_difficulty(8, 6, Difficulty.THREE) == (2, 2)


def test_partition_size_is_clamped_to_a_minimum_of_two():
    # 3//8 == 0, clamped up to the 2-cell floor on each axis.
    assert partition_size_for_difficulty(3, 3, Difficulty.THREE) == (2, 2)
    assert partition_size_for_difficulty(2, 2, Difficulty.ONE) == (2, 2)


def test_partition_grid_no_remainder_is_a_clean_row_major_tiling():
    partitions = partition_grid(8, 6, 3, 3)

    assert len(partitions) == 6
    assert partitions[0] == Partition(Position(0, 0), Position(3, 3))
    assert partitions[1] == Partition(Position(0, 3), Position(3, 6))
    assert partitions[2] == Partition(Position(0, 6), Position(3, 8))
    assert partitions[3] == Partition(Position(3, 0), Position(6, 3))
    assert partitions[4] == Partition(Position(3, 3), Position(6, 6))
    assert partitions[5] == Partition(Position(3, 6), Position(6, 8))


def test_partition_grid_folds_remainder_rows_and_columns_into_the_last_partition():
    partitions = partition_grid(3, 3, 2, 2)

    assert len(partitions) == 4
    assert Partition(Position(0, 0), Position(2, 2)) in partitions
    assert Partition(Position(0, 2), Position(2, 3)) in partitions
    assert Partition(Position(2, 0), Position(3, 2)) in partitions
    assert Partition(Position(2, 2), Position(3, 3)) in partitions


def test_reveal_threshold_uses_the_shared_division_formula():
    assert reveal_threshold((3, 2), Difficulty.ONE) == 3
    assert reveal_threshold((3, 2), Difficulty.TWO) == 2
    assert reveal_threshold((2, 2), Difficulty.ONE) == 2


# -- initial state -----------------------------------------------------


def test_initial_level_visibility_seeds_the_current_partition_and_defaults():
    maze = _filled_maze(width=8, height=6)
    vis = initial_level_visibility(maze, Level.TWO, Difficulty.ONE, Position(0, 0))

    assert vis.level is Level.TWO
    assert vis.difficulty is Difficulty.ONE
    assert vis.partition_size == (3, 3)
    assert len(vis.partitions) == 6
    assert vis.current_partition == 0
    assert vis.visited == frozenset({0})
    assert vis.discovered_walls == frozenset()
    assert vis.contour_shown is False


def test_initial_level_visibility_for_max_sets_contour_shown():
    maze = _filled_maze(width=3, height=3)
    vis = initial_level_visibility(maze, Level.MAX, Difficulty.ONE, Position(0, 0))

    assert vis.contour_shown is True


# -- Level 1 -----------------------------------------------------------


def test_level_one_visible_walls_are_every_grid_wall_and_no_contour():
    maze = _filled_maze(width=4, height=4)
    vis = initial_level_visibility(maze, Level.ONE, Difficulty.ONE, maze.entry)

    assert len(visible_walls(vis, maze.grid)) == 40
    assert show_contour(vis) is False
    assert advance_visibility(vis, maze, Position(1, 1)) is vis
    assert note_collision(vis, maze, Position(1, 1), Direction.UP) is vis


# -- Level 2 -----------------------------------------------------------


def test_level_two_accumulates_visited_partitions_then_resets_past_the_threshold():
    maze = _filled_maze(width=8, height=6)  # 3x3 partitions, threshold = round(6/2) = 3
    vis = initial_level_visibility(maze, Level.TWO, Difficulty.ONE, Position(0, 0))
    assert vis.visited == frozenset({0})

    vis = advance_visibility(vis, maze, Position(0, 3))
    assert vis.visited == frozenset({0, 1})

    vis = advance_visibility(vis, maze, Position(3, 3))
    assert vis.visited == frozenset({0, 1, 4})
    assert len(vis.visited) == 3  # at the threshold, not past it -- no reset yet

    same = advance_visibility(vis, maze, Position(3, 5))
    assert same is vis  # no partition boundary crossed -> no state churn

    vis = advance_visibility(vis, maze, Position(0, 6))
    assert vis.visited == frozenset({2})  # 4th partition: reset, keep only the current


def test_level_two_visible_walls_cover_every_visited_partition():
    maze = _filled_maze(width=4, height=4)  # 2x2 partitions
    vis = initial_level_visibility(maze, Level.TWO, Difficulty.ONE, Position(0, 0))
    one_partition = visible_walls(vis, maze.grid)

    vis = advance_visibility(vis, maze, Position(0, 2))
    both_partitions = visible_walls(vis, maze.grid)

    assert len(vis.visited) == 2
    assert len(both_partitions) > len(one_partition)


def test_level_two_reentering_a_visited_partition_updates_current_partition():
    maze = _filled_maze(width=8, height=6)  # 3x3 partitions
    vis = initial_level_visibility(maze, Level.TWO, Difficulty.ONE, Position(0, 0))
    vis = advance_visibility(vis, maze, Position(0, 3))  # 0 -> 1
    assert vis.current_partition == 1

    vis = advance_visibility(vis, maze, Position(0, 0))  # back into 0
    assert vis.current_partition == 0
    assert vis.visited == frozenset({0, 1})


def test_level_two_staying_within_the_current_partition_is_a_no_op():
    maze = _filled_maze(width=8, height=6)
    vis = initial_level_visibility(maze, Level.TWO, Difficulty.ONE, Position(0, 0))

    assert advance_visibility(vis, maze, Position(0, 2)) is vis


def test_level_two_show_contour_is_always_true():
    maze = _filled_maze(width=4, height=4)
    vis = initial_level_visibility(maze, Level.TWO, Difficulty.ONE, maze.entry)

    assert show_contour(vis) is True


# -- Level 3 -----------------------------------------------------------


def test_level_three_shows_only_the_current_partition():
    maze = _filled_maze(width=8, height=6)
    vis = initial_level_visibility(maze, Level.THREE, Difficulty.ONE, Position(0, 0))
    assert vis.current_partition == 0
    assert vis.visited == frozenset({0})

    vis = advance_visibility(vis, maze, Position(0, 3))
    assert vis.current_partition == 1
    assert vis.visited == frozenset({1})

    vis = advance_visibility(vis, maze, Position(3, 6))
    assert vis.current_partition == 5
    assert vis.visited == frozenset({5})


def test_level_three_visible_walls_show_only_the_current_partition():
    maze = _filled_maze(width=4, height=4)
    vis = initial_level_visibility(maze, Level.THREE, Difficulty.ONE, Position(0, 0))
    assert len(visible_walls(vis, maze.grid)) == 18

    vis = advance_visibility(vis, maze, Position(2, 2))
    assert vis.current_partition == 3
    # The bottom-right partition borders the padding row/column, so its raw
    # cell walls (12) differ from the top-left partition's (18) -- the point
    # is exactly one partition is shown either way.
    assert len(visible_walls(vis, maze.grid)) == 12


def test_level_three_reentering_the_current_partition_is_a_no_op():
    maze = _filled_maze(width=8, height=6)
    vis = initial_level_visibility(maze, Level.THREE, Difficulty.ONE, Position(0, 0))

    assert advance_visibility(vis, maze, Position(0, 2)) is vis


# -- Level 4 -----------------------------------------------------------


def test_level_four_blocked_move_maps_direction_to_the_right_wall():
    maze = _filled_maze(width=3, height=3)
    vis = initial_level_visibility(maze, Level.FOUR, Difficulty.ONE, Position(1, 1))
    assert vis.discovered_walls == frozenset()

    vis = note_collision(vis, maze, Position(1, 0), Direction.UP)
    assert vis.discovered_walls == frozenset({Wall(1, 0, "top")})

    vis = note_collision(vis, maze, Position(1, 0), Direction.DOWN)
    assert vis.discovered_walls == frozenset({Wall(1, 0, "top"), Wall(2, 0, "top")})

    vis = note_collision(vis, maze, Position(1, 1), Direction.LEFT)
    assert Wall(1, 1, "left") in vis.discovered_walls

    vis = note_collision(vis, maze, Position(1, 1), Direction.RIGHT)
    assert Wall(1, 2, "left") in vis.discovered_walls


def test_level_four_border_wall_discovery_is_a_no_op():
    maze = _filled_maze(width=3, height=3)
    vis = initial_level_visibility(maze, Level.FOUR, Difficulty.ONE, Position(0, 0))

    assert note_collision(vis, maze, Position(0, 0), Direction.UP) is vis
    assert note_collision(vis, maze, Position(0, 2), Direction.RIGHT) is vis
    assert note_collision(vis, maze, Position(2, 0), Direction.DOWN) is vis
    assert vis.discovered_walls == frozenset()


def test_level_four_already_discovered_wall_is_idempotent():
    maze = _filled_maze(width=3, height=3)
    vis = initial_level_visibility(maze, Level.FOUR, Difficulty.ONE, Position(1, 0))
    vis = note_collision(vis, maze, Position(1, 0), Direction.UP)

    assert note_collision(vis, maze, Position(1, 0), Direction.UP) is vis


def test_level_four_threshold_reset_hides_all_but_the_last_discovered_wall():
    maze = _filled_maze(width=2, height=2)  # 4 interior walls, threshold = round(4/2) = 2
    vis = initial_level_visibility(maze, Level.FOUR, Difficulty.ONE, Position(1, 1))
    assert vis.total_interior_walls == 4

    vis = note_collision(vis, maze, Position(1, 0), Direction.UP)
    vis = note_collision(vis, maze, Position(1, 1), Direction.UP)
    assert len(vis.discovered_walls) == 2  # at the threshold, not past it

    vis = note_collision(vis, maze, Position(0, 1), Direction.LEFT)
    assert vis.discovered_walls == frozenset({Wall(0, 1, "left")})


def test_level_four_show_contour_is_always_true():
    maze = _filled_maze(width=3, height=3)
    vis = initial_level_visibility(maze, Level.FOUR, Difficulty.ONE, maze.entry)

    assert show_contour(vis) is True


# -- Level Max ---------------------------------------------------------


def test_level_max_has_no_interior_walls_and_contour_toggles_on_collision_then_hides_on_move():
    maze = _filled_maze(width=3, height=3)
    vis = initial_level_visibility(maze, Level.MAX, Difficulty.ONE, Position(0, 0))

    assert vis.contour_shown is True
    assert visible_walls(vis, maze.grid) == frozenset()
    assert show_contour(vis) is True

    vis = advance_visibility(vis, maze, Position(0, 1))
    assert vis.contour_shown is False
    assert show_contour(vis) is False

    vis = note_collision(vis, maze, Position(0, 1), Direction.UP)
    assert vis.contour_shown is True
    assert show_contour(vis) is True


def test_level_max_collision_when_the_contour_is_already_shown_is_a_no_op():
    maze = _filled_maze(width=3, height=3)
    vis = initial_level_visibility(maze, Level.MAX, Difficulty.ONE, Position(0, 0))

    assert note_collision(vis, maze, Position(0, 0), Direction.UP) is vis


# -- helpers -----------------------------------------------------------


def test_is_border_wall_identifies_border_segments():
    grid = Grid.filled(width=3, height=3)

    assert is_border_wall(grid, Wall(0, 1, "top")) is True
    assert is_border_wall(grid, Wall(3, 1, "top")) is True
    assert is_border_wall(grid, Wall(1, 0, "left")) is True
    assert is_border_wall(grid, Wall(1, 3, "left")) is True
    assert is_border_wall(grid, Wall(1, 1, "top")) is False
    assert is_border_wall(grid, Wall(1, 1, "left")) is False


def test_total_interior_walls_counts_only_non_border_segments():
    assert total_interior_walls(Grid.filled(width=2, height=2)) == 4
    assert total_interior_walls(Grid.filled(width=3, height=3)) == 12


# -- value-object validation -------------------------------------------


def test_wall_rejects_an_invalid_side():
    with pytest.raises(DomainValidationError):
        Wall(row=0, col=0, side="bottom")


def test_wall_accepts_the_two_valid_sides():
    assert Wall(row=0, col=0, side="top") is not None
    assert Wall(row=0, col=0, side="left") is not None


def test_partition_rejects_a_degenerate_rectangle():
    with pytest.raises(DomainValidationError):
        Partition(Position(0, 0), Position(0, 3))
    with pytest.raises(DomainValidationError):
        Partition(Position(0, 0), Position(3, 0))
    with pytest.raises(DomainValidationError):
        Partition(Position(2, 2), Position(1, 3))
