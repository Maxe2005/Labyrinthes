from labyrinthes.adapters.tkinter.common.tokens import Theme, colors_for
from labyrinthes.adapters.tkinter.player.maze_canvas import MazeCanvas
from labyrinthes.domain.grid import Grid
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


def test_entry_marker_is_a_single_filled_circle_at_the_entry_cell(tk_root):
    maze = _maze(width=2, height=2)

    canvas = MazeCanvas(tk_root, maze, maze.entry, theme=Theme.LIGHT)

    entry_items = canvas.find_withtag("entry-marker")
    assert len(entry_items) == 1
    assert canvas.type(entry_items[0]) == "oval"


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
