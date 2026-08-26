"""Zoom/fit unit tests for `_BuilderMazeCanvas` (Story 4.8).

Every other Builder canvas behavior (wall/zone/marker editing) is already
covered end to end through `mount()` in the sibling `test_builder_*.py`
files via `_helpers.py`'s click/drag simulation -- this file is scoped to
the resize-fit + zoom mechanics `edit_area.py` wires up on `<Configure>`
and Ctrl+wheel/`+`/`-`.
"""

import pytest

from labyrinthes.adapters.tkinter.builder.maze_canvas import _BuilderMazeCanvas
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.domain.position import Position
from tests.adapters.tkinter.builder._helpers import _classic_maze


def _canvas(tk_root, maze, *, cursor=None):
    return _BuilderMazeCanvas(
        tk_root,
        maze=maze,
        cursor=cursor if cursor is not None else maze.entry,
        theme=Theme.LIGHT,
        on_wall_clicked=lambda wall: None,
        on_zone_dragged=lambda tool, anchor, end: None,
        on_cell_clicked=lambda tool, position: None,
        capture_tool=lambda: None,
    )


def test_fit_to_space_recomputes_the_cell_size_from_available_pixels(tk_root):
    # 20x20 at construction: `min(480 // 20, 480 // 20) == 24`, unclamped.
    maze = _classic_maze(columns=20, rows=20)
    canvas = _canvas(tk_root, maze)
    assert canvas._cell_size == 24

    canvas.fit_to_space(400, 400)  # min(400 // 20, 400 // 20) == 20

    assert canvas._cell_size == 20


def test_fit_to_space_clamps_to_the_minimum_for_a_very_small_available_space(tk_root):
    maze = _classic_maze(columns=20, rows=20)
    canvas = _canvas(tk_root, maze)

    canvas.fit_to_space(10, 10)

    assert canvas._cell_size == 16


def test_fit_to_space_clamps_to_the_maximum_for_a_large_available_space(tk_root):
    maze = _classic_maze(columns=5, rows=5)
    canvas = _canvas(tk_root, maze)

    canvas.fit_to_space(5000, 5000)

    assert canvas._cell_size == 40


def test_zoom_increases_the_cell_size(tk_root):
    maze = _classic_maze(columns=20, rows=20)
    canvas = _canvas(tk_root, maze)

    canvas.zoom(2)

    assert canvas._cell_size == 26


def test_zoom_decreases_the_cell_size(tk_root):
    maze = _classic_maze(columns=20, rows=20)
    canvas = _canvas(tk_root, maze)

    canvas.zoom(-2)

    assert canvas._cell_size == 22


def test_zoom_beyond_the_maximum_clamps_and_is_a_no_op(tk_root):
    # Already at the 40px maximum by construction (2x2 -> `min(240, 240)`
    # clamped down) -- zooming in further must stay clamped, not crash.
    maze = _classic_maze(columns=2, rows=2)
    canvas = _canvas(tk_root, maze)
    before = canvas.coords(canvas._cursor_id)

    canvas.zoom(2)

    assert canvas._cell_size == 40
    assert canvas.coords(canvas._cursor_id) == before


def test_zoom_beyond_the_minimum_clamps_and_is_a_no_op(tk_root):
    # Already at the 16px minimum by construction (50x35 -> `min(9, 13)`
    # clamped up) -- zooming out further must stay clamped, not crash.
    maze = _classic_maze(columns=50, rows=35)
    canvas = _canvas(tk_root, maze)
    before = canvas.coords(canvas._cursor_id)

    canvas.zoom(-2)

    assert canvas._cell_size == 16
    assert canvas.coords(canvas._cursor_id) == before


def test_resizing_does_not_reset_the_zoom_offset(tk_root):
    # Design Notes: "Resize doesn't reset the user's zoom offset -- only
    # the fit baseline moves."
    maze = _classic_maze(columns=20, rows=20)
    canvas = _canvas(tk_root, maze)
    canvas.zoom(4)  # fit 24 + offset 4 -> 28
    assert canvas._cell_size == 28

    canvas.fit_to_space(500, 500)  # new fit: min(500 // 20, 500 // 20) == 25

    assert canvas._cell_size == 29  # 25 + the same offset of 4


def test_a_stale_zoom_offset_does_not_stick_the_canvas_at_the_maximum_after_shrinking(
    tk_root,
):
    # Regression: `_zoom_offset` used to keep growing unbounded while
    # already clamped at `_MAX_CELL_SIZE`, so a big shrink left the
    # effective size stuck at 40 and unresponsive to the *next* zoom-out --
    # `fit_to_space` must re-clamp the offset to the new baseline's range.
    maze = _classic_maze(columns=20, rows=20)
    canvas = _canvas(tk_root, maze)
    canvas.zoom(32)  # fit 24 + offset 32 -> clamped to 40
    assert canvas._cell_size == 40

    canvas.fit_to_space(10, 10)  # new fit: clamped up to 16 (min(0, 0) -> 16)
    canvas.zoom(-2)  # one zoom-out press after the shrink

    # Without re-clamping the stale offset, this would still read 40.
    assert canvas._cell_size == 38


def test_zoom_rescales_every_drawn_item_by_the_size_ratio(tk_root):
    maze = _classic_maze(columns=20, rows=20)
    canvas = _canvas(tk_root, maze)
    before = canvas.coords(canvas._cursor_id)

    canvas.zoom(4)  # 24 -> 28

    after = canvas.coords(canvas._cursor_id)
    factor = 28 / 24
    assert after == pytest.approx([c * factor for c in before])


def test_a_marker_drawn_after_zoom_uses_the_rescaled_marker_radius(tk_root):
    # Regression: `_marker_radius` is cached at construction and must move
    # in lockstep with `self._cell_size`, or a marker drawn *after* a
    # zoom/resize would mismatch every already-rescaled item on the canvas.
    maze = _classic_maze(columns=20, rows=20)
    canvas = _canvas(tk_root, maze)

    canvas.zoom(4)  # 24 -> 28
    canvas.refresh_markers(Position(row=0, col=0), None, None, None)

    x0, y0, x1, y1 = canvas.coords(canvas.find_withtag("marker")[0])
    radius = (x1 - x0) / 2
    # `_marker_radius` is cached as a rounded `int` (see `_draw_cursor`'s
    # own `int(round(...))`), not the raw float scale.
    assert radius == pytest.approx(int(round(canvas._cell_size * 0.6 / 2)))
