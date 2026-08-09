from labyrinthes.domain.maze_size_bounds import (
    DEFAULT_MAZE_SIZE_BOUNDS,
    MazeSizeBounds,
    validate_dimensions,
)


def test_default_maze_size_bounds_are_3_to_50_columns_and_3_to_35_rows():
    assert DEFAULT_MAZE_SIZE_BOUNDS.min_columns == 3
    assert DEFAULT_MAZE_SIZE_BOUNDS.max_columns == 50
    assert DEFAULT_MAZE_SIZE_BOUNDS.min_rows == 3
    assert DEFAULT_MAZE_SIZE_BOUNDS.max_rows == 35


def test_validate_dimensions_returns_no_errors_for_values_within_bounds():
    bounds = MazeSizeBounds(min_columns=3, max_columns=50, min_rows=3, max_rows=35)

    assert validate_dimensions(bounds, width=10, height=8) == []


def test_validate_dimensions_returns_no_errors_at_the_exact_bounds():
    bounds = MazeSizeBounds(min_columns=3, max_columns=50, min_rows=3, max_rows=35)

    assert validate_dimensions(bounds, width=3, height=3) == []
    assert validate_dimensions(bounds, width=50, height=35) == []


def test_validate_dimensions_reports_columns_below_the_minimum():
    bounds = MazeSizeBounds(min_columns=3, max_columns=50, min_rows=3, max_rows=35)

    errors = validate_dimensions(bounds, width=2, height=10)

    assert errors == ["Columns must be between 3 and 50."]


def test_validate_dimensions_reports_columns_above_the_maximum():
    bounds = MazeSizeBounds(min_columns=3, max_columns=50, min_rows=3, max_rows=35)

    errors = validate_dimensions(bounds, width=99, height=10)

    assert errors == ["Columns must be between 3 and 50."]


def test_validate_dimensions_reports_rows_out_of_bounds():
    bounds = MazeSizeBounds(min_columns=3, max_columns=50, min_rows=3, max_rows=35)

    errors = validate_dimensions(bounds, width=10, height=99)

    assert errors == ["Rows must be between 3 and 35."]


def test_validate_dimensions_reports_both_when_both_out_of_bounds():
    bounds = MazeSizeBounds(min_columns=3, max_columns=50, min_rows=3, max_rows=35)

    errors = validate_dimensions(bounds, width=1, height=1)

    assert errors == ["Columns must be between 3 and 50.", "Rows must be between 3 and 35."]
