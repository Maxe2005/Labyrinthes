from labyrinthes.domain.grid import Grid
from labyrinthes.domain.position import Position
from labyrinthes.domain.wall_editing import count_broken_walls
from labyrinthes.domain.zone_editing import destroy_zone, restore_zone


def _filled(width: int = 5, height: int = 5) -> Grid:
    return Grid.filled(width, height)


def _top_walls(grid: Grid, rows: range, cols: range) -> set[bool]:
    return {grid.cell_at(Position(row, col)).has_top_wall for row in rows for col in cols}


def _left_walls(grid: Grid, rows: range, cols: range) -> set[bool]:
    return {grid.cell_at(Position(row, col)).has_left_wall for row in rows for col in cols}


# -- destroy_zone / restore_zone -----------------------------------------


def test_destroy_zone_breaks_every_interior_wall_in_the_spanned_rectangle():
    grid = _filled()

    result = destroy_zone(grid, Position(1, 1), Position(3, 3))

    # top walls: row in [1, 4], col in [1, 3]; left walls: row in [1, 3], col in [1, 4]
    assert _top_walls(result, range(1, 5), range(1, 4)) == {False}
    assert _left_walls(result, range(1, 4), range(1, 5)) == {False}


def test_destroy_zone_leaves_walls_outside_the_span_untouched():
    grid = _filled()

    result = destroy_zone(grid, Position(1, 1), Position(3, 3))

    # A wall clearly outside the spanned rectangle, e.g. the top-left cell.
    assert result.cell_at(Position(0, 0)).has_top_wall is True
    assert result.cell_at(Position(0, 0)).has_left_wall is True


def test_destroy_zone_does_not_mutate_the_original_grid():
    grid = _filled()

    destroy_zone(grid, Position(1, 1), Position(3, 3))

    assert grid == _filled()


def test_destroy_zone_skips_border_walls_touching_the_grid_edge_instead_of_raising():
    grid = _filled()

    # Span includes row 0 and col 0 -- the grid's outer edge.
    result = destroy_zone(grid, Position(0, 0), Position(2, 2))  # must not raise

    # The outer contour stays closed (AC3): border walls untouched.
    assert result.cell_at(Position(0, 0)).has_top_wall is True  # top border row
    assert result.cell_at(Position(0, 0)).has_left_wall is True  # left border column
    # But interior walls within the span are broken.
    assert result.cell_at(Position(1, 1)).has_top_wall is False
    assert result.cell_at(Position(1, 1)).has_left_wall is False


def test_destroy_zone_at_the_bottom_right_edge_skips_border_walls_too():
    grid = _filled(width=5, height=5)

    result = destroy_zone(grid, Position(2, 2), Position(4, 4))  # touches height/width edge

    # The padding row/column carries the bottom/right border bits.
    assert result.cell_at(Position(5, 4)).has_top_wall is True  # bottom border row
    assert result.cell_at(Position(4, 5)).has_left_wall is True  # right border column
    assert result.cell_at(Position(3, 3)).has_top_wall is False
    assert result.cell_at(Position(3, 3)).has_left_wall is False


def test_restore_zone_sets_every_interior_wall_in_the_span_back_to_present():
    grid = destroy_zone(_filled(), Position(1, 1), Position(3, 3))

    result = restore_zone(grid, Position(1, 1), Position(3, 3))

    assert _top_walls(result, range(1, 5), range(1, 4)) == {True}
    assert _left_walls(result, range(1, 4), range(1, 5)) == {True}


def test_destroy_then_restore_the_same_zone_returns_the_grid_to_its_initial_state():
    grid = _filled()

    destroyed = destroy_zone(grid, Position(1, 1), Position(3, 3))
    restored = restore_zone(destroyed, Position(1, 1), Position(3, 3))

    assert restored == grid


def test_destroy_zone_is_order_independent_between_the_two_corners():
    grid = _filled()

    forward = destroy_zone(grid, Position(1, 1), Position(3, 3))
    backward = destroy_zone(grid, Position(3, 3), Position(1, 1))

    assert forward == backward


def test_destroy_zone_is_order_independent_for_diagonally_flipped_corners():
    grid = _filled()

    forward = destroy_zone(grid, Position(1, 3), Position(3, 1))
    backward = destroy_zone(grid, Position(3, 1), Position(1, 3))

    assert forward == backward


def test_destroy_zone_on_a_single_cell_breaks_all_four_of_its_walls():
    grid = _filled()

    result = destroy_zone(grid, Position(2, 2), Position(2, 2))

    assert result.cell_at(Position(2, 2)).has_top_wall is False
    assert result.cell_at(Position(2, 2)).has_left_wall is False
    assert result.cell_at(Position(3, 2)).has_top_wall is False  # bottom edge of cell (2,2)
    assert result.cell_at(Position(2, 3)).has_left_wall is False  # right edge of cell (2,2)


def test_destroy_zone_updates_the_broken_wall_count_for_a_fully_interior_span():
    grid = _filled()

    result = destroy_zone(grid, Position(1, 1), Position(3, 3))

    # top: 4 rows x 3 cols = 12; left: 3 rows x 4 cols = 12
    assert count_broken_walls(result) == 24
