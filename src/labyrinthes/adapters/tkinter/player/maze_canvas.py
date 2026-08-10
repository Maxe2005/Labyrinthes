"""`MazeCanvas` -- wall/entry/exit/ball rendering for `GameplayScreen` (Story 2.4).

Draws the whole maze once from a `Maze`: wall-bars (tag `"wall"`), an
entry marker (tag `"entry-marker"`, filled circle) and an exit marker
(tag `"exit-marker"`, filled diamond) -- shape *and* color distinguished,
never color alone (NFR6) -- plus the ball (tag `"ball"`, filled circle,
a distinct color from the entry marker, deliberately *smaller* than a
marker -- `_BALL_SCALE < _MARKER_SCALE` -- so a marker's shape stays
visible as a ring around the ball at rest on entry, and around exit at
the instant of winning, instead of being fully occluded). Walls/markers
never change after construction in this story (no Level/Difficulty
visibility rules yet -- Stories 2.6/2.7); only the ball moves, via
`set_ball_position()` which repositions the existing canvas item through
`canvas.coords(...)` rather than clearing and redrawing everything on
every keypress.

Cell sizing is this story's own decision (no locked design token exists
for it, see `tokens.py`'s own `RADII` note) -- `cell_size = clamp(min(480
// width, 480 // height), 16, 40)` px, legible for both a small classic
maze and a 50x35 random one.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import ColorTokens, Theme, colors_for
from labyrinthes.domain.maze import Maze
from labyrinthes.domain.position import Position

__all__ = ["MazeCanvas"]

_MAX_CANVAS_SPAN = 480
_MIN_CELL_SIZE = 16
_MAX_CELL_SIZE = 40
_WALL_WIDTH = 2
_MARKER_SCALE = 0.6
_BALL_SCALE = 0.42


def _cell_size(width: int, height: int) -> int:
    """`clamp(min(480 // width, 480 // height), 16, 40)` -- see the module docstring."""
    raw = min(_MAX_CANVAS_SPAN // width, _MAX_CANVAS_SPAN // height)
    return max(_MIN_CELL_SIZE, min(_MAX_CELL_SIZE, raw))


class MazeCanvas(tk.Canvas):
    """Renders `maze`'s walls/entry/exit once, then tracks the ball's position."""

    def __init__(
        self,
        parent: tk.Widget,
        maze: Maze,
        position: Position,
        *,
        theme: Theme,
    ) -> None:
        self._maze = maze
        self._theme = theme
        self._cell_size = _cell_size(maze.grid.width, maze.grid.height)
        colors = colors_for(theme)

        super().__init__(
            parent,
            width=maze.grid.width * self._cell_size,
            height=maze.grid.height * self._cell_size,
            background=colors.corridor,
            highlightthickness=0,
            bd=0,
        )

        self._draw_walls(colors)
        self._draw_entry_marker(colors)
        self._draw_exit_marker(colors)
        self._ball_id = self._draw_ball(position, colors)

    # -- drawing -------------------------------------------------------

    def _draw_walls(self, colors: ColorTokens) -> None:
        grid = self._maze.grid
        size = self._cell_size
        for row in range(grid.height + 1):
            for col in range(grid.width + 1):
                cell = grid.cell_at(Position(row=row, col=col))
                x0, y0 = col * size, row * size
                if cell.has_top_wall:
                    self.create_line(
                        x0, y0, x0 + size, y0, width=_WALL_WIDTH, fill=colors.wall, tags=("wall",)
                    )
                if cell.has_left_wall:
                    self.create_line(
                        x0, y0, x0, y0 + size, width=_WALL_WIDTH, fill=colors.wall, tags=("wall",)
                    )

    def _cell_center(self, position: Position) -> tuple[float, float]:
        size = self._cell_size
        return (position.col * size + size / 2, position.row * size + size / 2)

    def _radius(self, scale: float) -> float:
        """`scale` fraction of `self._cell_size`, as a radius -- shared by every drawn shape."""
        return self._cell_size * scale / 2

    def _draw_entry_marker(self, colors: ColorTokens) -> None:
        cx, cy = self._cell_center(self._maze.entry)
        radius = self._radius(_MARKER_SCALE)
        self.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            fill=colors.entry,
            outline="",
            tags=("entry-marker",),
        )

    def _draw_exit_marker(self, colors: ColorTokens) -> None:
        cx, cy = self._cell_center(self._maze.exit)
        radius = self._radius(_MARKER_SCALE)
        # A rotated square (diamond), shape-distinct from the entry circle
        # and the ball circle -- never color alone (NFR6).
        self.create_polygon(
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

    def _draw_ball(self, position: Position, colors: ColorTokens) -> int:
        cx, cy = self._cell_center(position)
        radius = self._radius(_BALL_SCALE)
        return self.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            fill=colors.ball,
            outline="",
            tags=("ball",),
        )

    # -- movement --------------------------------------------------------

    def set_ball_position(self, position: Position) -> None:
        """Move the ball item to `position`'s cell center, without redrawing anything else."""
        cx, cy = self._cell_center(position)
        radius = self._radius(_BALL_SCALE)
        self.coords(self._ball_id, cx - radius, cy - radius, cx + radius, cy + radius)
