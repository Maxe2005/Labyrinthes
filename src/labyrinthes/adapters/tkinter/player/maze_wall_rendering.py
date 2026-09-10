"""Wall/entry/exit drawing routines shared by `MazeCanvas` and `MazeCard` (Story 4.14).

Extracted verbatim (modulo becoming free functions instead of `MazeCanvas`
methods) from `maze_canvas.py`'s `_draw_walls`/`_draw_entry_marker`/
`_draw_exit_marker` -- `MazeCanvas` itself now delegates to these, so
gameplay rendering and `MazeCard`'s small thumbnail rendering share one
implementation instead of two independently-maintained copies. Every
function takes `cell_size`/`wall_width` as plain parameters (never reads an
owning widget's `self`), which is exactly what lets `MazeCard` call them at
card scale (a small `_THUMBNAIL_SPAN`-clamped cell size, `wall_width=1`)
while `MazeCanvas` keeps calling them at its own gameplay scale.

`_draw_wall_bar`/`redraw_structure`/`_draw_contour`/ball drawing stay in
`maze_canvas.py` -- they are structural-visibility/gameplay-only concerns
(progressive wall reveal, the playable-area contour, the moving ball), not
something a static thumbnail needs.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import ColorTokens
from labyrinthes.domain.maze import Maze
from labyrinthes.domain.position import Position

__all__ = ["draw_entry_marker", "draw_exit_marker", "draw_walls"]

# Entry/exit marker size as a fraction of `cell_size` -- the same 0.6 ratio
# `MazeCanvas` has always drawn markers at (see its own `_MARKER_SCALE`),
# kept here as the shared default so a caller that doesn't care about
# marker sizing (e.g. `MazeCard`) gets identical proportions for free.
_MARKER_SCALE = 0.6


def _cell_center(position: Position, cell_size: int) -> tuple[float, float]:
    return (position.col * cell_size + cell_size / 2, position.row * cell_size + cell_size / 2)


def draw_walls(
    canvas: tk.Canvas,
    maze: Maze,
    cell_size: int,
    colors: ColorTokens,
    wall_width: int = 2,
) -> None:
    """Draw every wall bar (tag `"wall"`) of `maze`'s grid onto `canvas`."""
    grid = maze.grid
    for row in range(grid.height + 1):
        for col in range(grid.width + 1):
            cell = grid.cell_at(Position(row=row, col=col))
            x0, y0 = col * cell_size, row * cell_size
            if cell.has_top_wall:
                canvas.create_line(
                    x0,
                    y0,
                    x0 + cell_size,
                    y0,
                    width=wall_width,
                    fill=colors.wall,
                    tags=("wall",),
                )
            if cell.has_left_wall:
                canvas.create_line(
                    x0,
                    y0,
                    x0,
                    y0 + cell_size,
                    width=wall_width,
                    fill=colors.wall,
                    tags=("wall",),
                )


def draw_entry_marker(
    canvas: tk.Canvas,
    maze: Maze,
    cell_size: int,
    colors: ColorTokens,
    marker_scale: float = _MARKER_SCALE,
    min_radius: float = 0.0,
) -> None:
    """Draw `maze.entry`'s filled-square marker (tag `"entry-marker"`) onto `canvas`.

    `min_radius` floors the drawn radius below what `marker_scale` alone
    would give at a very small `cell_size` (e.g. a thumbnail's clamped
    minimum) -- default `0.0` never raises it, so `MazeCanvas`'s own
    gameplay-scale calls (which never pass it) are unaffected. Without a
    floor, the entry-square/exit-diamond shape distinction (NFR6) becomes
    imperceptible at a couple of pixels' radius.
    """
    cx, cy = _cell_center(maze.entry, cell_size)
    radius = max(min_radius, cell_size * marker_scale / 2)
    # Filled square (entry = square, exit = diamond, player = circle) --
    # shape *and* color distinguished, never color alone (NFR6).
    canvas.create_rectangle(
        cx - radius,
        cy - radius,
        cx + radius,
        cy + radius,
        fill=colors.entry,
        outline="",
        tags=("entry-marker",),
    )


def draw_exit_marker(
    canvas: tk.Canvas,
    maze: Maze,
    cell_size: int,
    colors: ColorTokens,
    marker_scale: float = _MARKER_SCALE,
    min_radius: float = 0.0,
) -> None:
    """Draw `maze.exit`'s filled-diamond marker (tag `"exit-marker"`) onto `canvas`.

    `min_radius` -- see `draw_entry_marker`'s docstring.
    """
    cx, cy = _cell_center(maze.exit, cell_size)
    radius = max(min_radius, cell_size * marker_scale / 2)
    # A rotated square (diamond), shape-distinct from the entry square and
    # the ball circle -- never color alone (NFR6).
    canvas.create_polygon(
        cx,
        cy - radius,
        cx + radius,
        cy,
        cx,
        cy + radius,
        cx - radius,
        cy,
        fill=colors.exit,
        outline="",
        tags=("exit-marker",),
    )
