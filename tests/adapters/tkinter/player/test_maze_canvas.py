import pytest

from labyrinthes.adapters.tkinter.common.tokens import Theme, colors_for
from labyrinthes.adapters.tkinter.player.maze_canvas import MazeCanvas
from labyrinthes.domain.difficulty import Difficulty
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level import Level
from labyrinthes.domain.level_visibility import advance_visibility, initial_level_visibility
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.position import Position


def _maze(width=2, height=2) -> Maze:
    return Maze(
        grid=Grid.filled(width=width, height=height),
        entry=Position(row=0, col=0),
        exit=Position(row=height - 1, col=width - 1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def _expected_cell_size(width: int, height: int) -> int:
    raw = min(480 // width, 480 // height)
    return max(16, min(40, raw))


def test_wall_bar_count_matches_the_grids_set_wall_bits(tk_root):
    # `Grid.filled(2, 2)`: 9 raw cells (row/col in [0, 3)) checked for
    # top/left wall bits -- 6 top walls + 6 left walls set (see the
    # module's own `Grid.filled` docstring for the padding scheme), 12
    # wall-bar lines total.
    maze = _maze(width=2, height=2)

    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)

    assert len(canvas.find_withtag("wall")) == 12


def test_entry_marker_is_a_single_filled_square_at_the_entry_cell(tk_root):
    maze = _maze(width=2, height=2)

    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)

    entry_items = canvas.find_withtag("entry-marker")
    assert len(entry_items) == 1
    assert canvas.type(entry_items[0]) == "rectangle"


def test_exit_marker_is_a_single_polygon_shape_distinct_from_the_entry_circle(tk_root):
    maze = _maze(width=2, height=2)

    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)

    exit_items = canvas.find_withtag("exit-marker")
    assert len(exit_items) == 1
    assert canvas.type(exit_items[0]) == "polygon"


def test_entry_and_exit_markers_use_distinct_colors(tk_root):
    maze = _maze(width=2, height=2)
    colors = colors_for(Theme.LIGHT)

    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)

    entry_item = canvas.find_withtag("entry-marker")[0]
    exit_item = canvas.find_withtag("exit-marker")[0]
    assert canvas.itemcget(entry_item, "fill") == colors.entry
    assert canvas.itemcget(exit_item, "fill") == colors.exit
    assert colors.entry != colors.exit


def test_ball_starts_at_the_given_position(tk_root):
    # The ball is deliberately smaller than a marker (`_BALL_SCALE <
    # _MARKER_SCALE`) so the entry marker's shape stays visible as a ring
    # around the ball rather than being fully occluded (NFR6: shape *and*
    # color distinguished) -- same center, smaller bounding box, not equal
    # coordinates.
    maze = _maze(width=2, height=2)

    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)

    ball_items = canvas.find_withtag("ball")
    assert len(ball_items) == 1
    entry_marker_coords = canvas.coords(canvas.find_withtag("entry-marker")[0])
    ball_coords = canvas.coords(ball_items[0])
    entry_x0, entry_y0, entry_x1, entry_y1 = entry_marker_coords
    ball_x0, ball_y0, ball_x1, ball_y1 = ball_coords
    entry_cx, entry_cy = (entry_x0 + entry_x1) / 2, (entry_y0 + entry_y1) / 2
    ball_cx, ball_cy = (ball_x0 + ball_x1) / 2, (ball_y0 + ball_y1) / 2
    assert (ball_cx, ball_cy) == (entry_cx, entry_cy)
    assert (ball_x1 - ball_x0) < (entry_x1 - entry_x0)


def test_set_ball_position_moves_only_the_ball_item(tk_root):
    maze = _maze(width=3, height=3)

    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    wall_coords_before = [canvas.coords(item) for item in canvas.find_withtag("wall")]
    entry_coords_before = canvas.coords(canvas.find_withtag("entry-marker")[0])
    exit_coords_before = canvas.coords(canvas.find_withtag("exit-marker")[0])

    canvas.set_ball_position(Position(row=1, col=1))

    wall_coords_after = [canvas.coords(item) for item in canvas.find_withtag("wall")]
    entry_coords_after = canvas.coords(canvas.find_withtag("entry-marker")[0])
    exit_coords_after = canvas.coords(canvas.find_withtag("exit-marker")[0])
    assert wall_coords_after == wall_coords_before
    assert entry_coords_after == entry_coords_before
    assert exit_coords_after == exit_coords_before

    ball_coords = canvas.coords(canvas.find_withtag("ball")[0])
    cell_size = _expected_cell_size(3, 3)
    expected_cx, expected_cy = 1 * cell_size + cell_size / 2, 1 * cell_size + cell_size / 2
    radius = cell_size * 0.42 / 2  # `_BALL_SCALE`, smaller than the 0.6 marker scale
    assert ball_coords == [
        expected_cx - radius,
        expected_cy - radius,
        expected_cx + radius,
        expected_cy + radius,
    ]


def test_set_ball_position_does_not_create_a_second_ball_item(tk_root):
    maze = _maze(width=2, height=2)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)

    canvas.set_ball_position(Position(row=1, col=1))

    assert len(canvas.find_withtag("ball")) == 1


def test_set_ball_offset_interpolates_between_cell_centers(tk_root):
    maze = _maze(width=3, height=3)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    cell_size = _expected_cell_size(3, 3)
    radius = cell_size * 0.42 / 2

    # A half-cell offset toward the east of (0, 0)'s center.
    canvas.set_ball_offset(Position(row=0, col=0), row_delta=0.0, col_delta=0.5)

    cx = 0 * cell_size + cell_size / 2 + 0.5 * cell_size
    cy = 0 * cell_size + cell_size / 2
    ball_coords = canvas.coords(canvas.find_withtag("ball")[0])
    assert ball_coords == [cx - radius, cy - radius, cx + radius, cy + radius]


def test_set_ball_offset_supports_negative_row_and_col_deltas(tk_root):
    maze = _maze(width=3, height=3)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    cell_size = _expected_cell_size(3, 3)
    radius = cell_size * 0.42 / 2

    canvas.set_ball_offset(Position(row=1, col=1), row_delta=-1.0, col_delta=-1.0)

    cx = 1 * cell_size + cell_size / 2 - 1.0 * cell_size
    cy = 1 * cell_size + cell_size / 2 - 1.0 * cell_size
    ball_coords = canvas.coords(canvas.find_withtag("ball")[0])
    assert ball_coords == [cx - radius, cy - radius, cx + radius, cy + radius]


def test_set_ball_position_is_equivalent_to_a_zero_offset(tk_root):
    maze = _maze(width=3, height=3)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    target = Position(row=1, col=1)

    canvas.set_ball_position(target)
    via_position = canvas.coords(canvas.find_withtag("ball")[0])

    canvas.set_ball_offset(target, row_delta=0.0, col_delta=0.0)
    via_offset = canvas.coords(canvas.find_withtag("ball")[0])

    assert via_offset == via_position


def test_canvas_size_matches_the_computed_cell_size_times_playable_dimensions(tk_root):
    maze = _maze(width=5, height=4)
    cell_size = _expected_cell_size(5, 4)

    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)

    assert int(canvas.cget("width")) == 5 * cell_size
    assert int(canvas.cget("height")) == 4 * cell_size


def test_cell_size_is_clamped_to_the_maximum_for_a_small_maze(tk_root):
    # `min(480 // 2, 480 // 2) == 240`, clamped down to the 40px maximum.
    maze = _maze(width=2, height=2)

    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)

    assert int(canvas.cget("width")) == 80  # 2 * 40
    assert int(canvas.cget("height")) == 80


def test_cell_size_is_clamped_to_the_minimum_for_a_large_maze(tk_root):
    # `min(480 // 50, 480 // 35) == 9`, clamped up to the 16px minimum.
    maze = _maze(width=50, height=35)

    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)

    assert int(canvas.cget("width")) == 50 * 16
    assert int(canvas.cget("height")) == 35 * 16


# -- redraw_structure (Story 2.6) ---------------------------------------


def test_redraw_structure_level_one_redraws_all_walls_and_no_contour(tk_root):
    maze = _maze(width=2, height=2)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    visibility = initial_level_visibility(maze, Level.ONE, Difficulty.ONE, maze.entry)

    canvas.redraw_structure(visibility)

    assert len(canvas.find_withtag("wall")) == 12
    assert len(canvas.find_withtag("contour")) == 0


def test_redraw_structure_level_two_shows_only_the_visited_partition_and_contour(tk_root):
    # 5x5 at Difficulty ONE -> (2, 2) partitions; entry partition 0 covers
    # raw rows/cols 0..2 -> 9 cells, 18 wall bars; Level 2 always draws the
    # contour around the playable area.
    maze = _maze(width=5, height=5)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    visibility = initial_level_visibility(maze, Level.TWO, Difficulty.ONE, maze.entry)

    canvas.redraw_structure(visibility)

    assert len(canvas.find_withtag("wall")) == 18
    assert len(canvas.find_withtag("contour")) > 0


def test_redraw_structure_level_three_shows_only_the_current_partition(tk_root):
    maze = _maze(width=5, height=5)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    visibility = initial_level_visibility(maze, Level.THREE, Difficulty.ONE, maze.entry)

    canvas.redraw_structure(visibility)

    assert len(canvas.find_withtag("wall")) == 18
    assert len(canvas.find_withtag("contour")) > 0


def test_redraw_structure_level_four_starts_with_no_walls_and_the_contour(tk_root):
    maze = _maze(width=5, height=5)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    visibility = initial_level_visibility(maze, Level.FOUR, Difficulty.ONE, maze.entry)

    canvas.redraw_structure(visibility)

    assert len(canvas.find_withtag("wall")) == 0
    assert len(canvas.find_withtag("contour")) > 0


def test_redraw_structure_level_max_has_no_walls_and_contour_only_while_shown(tk_root):
    maze = _maze(width=5, height=5)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    shown = initial_level_visibility(maze, Level.MAX, Difficulty.ONE, maze.entry)

    canvas.redraw_structure(shown)
    assert len(canvas.find_withtag("wall")) == 0
    assert len(canvas.find_withtag("contour")) > 0

    canvas.redraw_structure(advance_visibility(shown, maze, Position(row=0, col=1)))
    assert len(canvas.find_withtag("wall")) == 0
    assert len(canvas.find_withtag("contour")) == 0


def test_redraw_structure_is_idempotent(tk_root):
    maze = _maze(width=5, height=5)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    visibility = initial_level_visibility(maze, Level.TWO, Difficulty.ONE, maze.entry)

    canvas.redraw_structure(visibility)
    first = len(canvas.find_withtag("wall"))
    canvas.redraw_structure(visibility)
    second = len(canvas.find_withtag("wall"))

    assert first == second == 18


def test_redraw_structure_leaves_entry_exit_and_ball_untouched(tk_root):
    maze = _maze(width=5, height=5)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    entry_coords = canvas.coords(canvas.find_withtag("entry-marker")[0])
    exit_coords = canvas.coords(canvas.find_withtag("exit-marker")[0])
    ball_coords = canvas.coords(canvas.find_withtag("ball")[0])

    canvas.redraw_structure(initial_level_visibility(maze, Level.MAX, Difficulty.ONE, maze.entry))

    assert len(canvas.find_withtag("entry-marker")) == 1
    assert len(canvas.find_withtag("exit-marker")) == 1
    assert len(canvas.find_withtag("ball")) == 1
    assert canvas.coords(canvas.find_withtag("entry-marker")[0]) == entry_coords
    assert canvas.coords(canvas.find_withtag("exit-marker")[0]) == exit_coords
    assert canvas.coords(canvas.find_withtag("ball")[0]) == ball_coords


def test_redraw_structure_reopens_the_exit_side_with_a_corridor_bar(tk_root):
    # Exit on the bottom edge only (not a corner) -> one reopen bar + the
    # rectangle = 2 contour items, and the reopen bar uses the corridor color.
    maze = Maze(
        grid=Grid.filled(width=5, height=5),
        entry=Position(row=0, col=0),
        exit=Position(row=4, col=2),
        kind=MazeKind.CLASSIC,
        id=None,
    )
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    colors = colors_for(Theme.LIGHT)

    canvas.redraw_structure(initial_level_visibility(maze, Level.TWO, Difficulty.ONE, maze.entry))

    contour_items = canvas.find_withtag("contour")
    assert len(contour_items) == 2
    reopen = [item for item in contour_items if canvas.itemcget(item, "fill") == colors.corridor]
    assert len(reopen) == 1
    assert canvas.coords(reopen[0]) == [80, 200, 120, 200]


@pytest.mark.parametrize(
    ("exit", "expected_reopen_coords"),
    [
        # 5x5 maze, cell_size = 40; each bar spans one exit cell along its edge.
        (Position(row=4, col=2), [[80, 200, 120, 200]]),  # bottom edge
        (Position(row=0, col=2), [[80, 0, 120, 0]]),  # top edge
        (Position(row=2, col=4), [[200, 80, 200, 120]]),  # right edge
        (Position(row=2, col=0), [[0, 80, 0, 120]]),  # left edge
        (Position(row=0, col=0), [[0, 0, 40, 0], [0, 0, 0, 40]]),  # top-left corner
        (Position(row=4, col=4), [[160, 200, 200, 200], [200, 160, 200, 200]]),  # bottom-right
    ],
)
def test_redraw_structure_reopens_every_exit_edge_with_corridor_bars(
    tk_root, exit, expected_reopen_coords
):
    maze = Maze(
        grid=Grid.filled(width=5, height=5),
        entry=Position(row=0, col=0),
        exit=exit,
        kind=MazeKind.CLASSIC,
        id=None,
    )
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    colors = colors_for(Theme.LIGHT)

    canvas.redraw_structure(initial_level_visibility(maze, Level.TWO, Difficulty.ONE, maze.entry))

    contour_items = canvas.find_withtag("contour")
    reopen = [item for item in contour_items if canvas.itemcget(item, "fill") == colors.corridor]
    assert sorted(canvas.coords(item) for item in reopen) == sorted(expected_reopen_coords)


# -- HARD mode fog (Story 2.8) ----------------------------------------


def test_fog_item_spans_the_canvas_is_filled_with_bg_and_hidden_by_default(tk_root):
    maze = _maze(width=2, height=2)
    colors = colors_for(Theme.LIGHT)

    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)

    fog_items = canvas.find_withtag("fog")
    assert len(fog_items) == 1
    assert canvas.type(fog_items[0]) == "rectangle"
    assert canvas.itemcget(fog_items[0], "fill") == colors.bg
    assert canvas.itemcget(fog_items[0], "state") == "hidden"
    assert canvas.coords(fog_items[0]) == [
        0,
        0,
        int(canvas.cget("width")),
        int(canvas.cget("height")),
    ]


def test_fog_item_stacks_below_the_first_wall_item(tk_root):
    # The fog scrim sits above the corridor plane but below every wall bar /
    # marker / ball. On a `tk.Canvas` items draw in creation order and later
    # items stack on top, so the fog must be the *first* item created.
    maze = _maze(width=2, height=2)

    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)

    order = canvas.find_all()
    fog_index = min(order.index(item) for item in canvas.find_withtag("fog"))
    wall_index = min(order.index(item) for item in canvas.find_withtag("wall"))
    assert fog_index < wall_index


def test_fog_stays_below_walls_after_redraw_structure(tk_root):
    maze = _maze(width=2, height=2)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    canvas.redraw_structure(initial_level_visibility(maze, Level.ONE, Difficulty.ONE, maze.entry))

    order = canvas.find_all()
    fog_index = min(order.index(item) for item in canvas.find_withtag("fog"))
    wall_index = min(order.index(item) for item in canvas.find_withtag("wall"))
    assert fog_index < wall_index


def test_set_hard_mode_moving_true_hides_the_ball_and_shows_the_fog(tk_root):
    maze = _maze(width=2, height=2)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    ball = canvas.find_withtag("ball")[0]

    canvas.set_hard_mode_moving(True)

    assert canvas.itemcget("fog", "state") == "normal"
    assert canvas.itemcget(ball, "state") == "hidden"


def test_set_hard_mode_moving_false_restores_ball_and_hides_the_fog(tk_root):
    maze = _maze(width=2, height=2)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    ball = canvas.find_withtag("ball")[0]

    canvas.set_hard_mode_moving(True)
    canvas.set_hard_mode_moving(False)

    assert canvas.itemcget("fog", "state") == "hidden"
    assert canvas.itemcget(ball, "state") == "normal"


def test_set_hard_mode_moving_is_idempotent(tk_root):
    maze = _maze(width=2, height=2)
    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)
    ball = canvas.find_withtag("ball")[0]

    canvas.set_hard_mode_moving(True)
    canvas.set_hard_mode_moving(True)

    assert canvas.itemcget("fog", "state") == "normal"
    assert canvas.itemcget(ball, "state") == "hidden"
