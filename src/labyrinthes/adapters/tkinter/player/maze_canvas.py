"""`MazeCanvas` -- wall/entry/exit/ball rendering for `GameplayScreen` (Story 2.4).

Draws the whole maze once from a `Maze`: wall-bars (tag `"wall"`), an
entry marker (tag `"entry-marker"`, filled circle) and an exit marker
(tag `"exit-marker"`, filled diamond) -- shape *and* color distinguished,
never color alone (NFR6) -- plus the ball (tag `"ball"`, filled circle,
a distinct color from the entry marker, deliberately *smaller* than a
marker -- `_BALL_SCALE < _MARKER_SCALE` -- so a marker's shape stays
visible as a ring around the ball at rest on entry, and around exit at
the instant of winning, instead of being fully occluded). Only the ball
moves after construction, via `set_ball_position()`/`set_ball_offset()`
which reposition the existing canvas item through `canvas.coords(...)`
rather than clearing and redrawing everything on every keypress.

Story 2.6 adds `redraw_structure(visibility)`: when the session's
`LevelVisibility` changes identity (a level switch or a visibility
advance/collision), it replaces the `"wall"` bars with exactly
`visible_walls(visibility, grid)` and draws the playable-area contour
(`"contour"`, tag cleared first so calls are idempotent) whenever
`show_contour(visibility)` says so -- a faithful port of the legacy
`trace_contours_lab`, which reopens the exit side(s) with a
corridor-colored bar (`colors.corridor`). The constructor still draws the
whole Level-ONE grid once; `redraw_structure` is only called on a
visibility *change*.

Cell sizing is this story's own decision (no locked design token exists
for it, see `tokens.py`'s own `RADII` note) -- `cell_size = clamp(min(480
// width, 480 // height), 16, 40)` px, legible for both a small classic
maze and a 50x35 random one.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import ColorTokens, Theme, colors_for
from labyrinthes.domain.level_visibility import (
    LevelVisibility,
    Wall,
    show_contour,
    visible_walls,
)
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

        # The HARD-mode fog scrim must be the *first* item created: Tk canvas
        # items draw in creation order, so a first-created rectangle sits above
        # the corridor background (the canvas itself) and below every wall
        # bar/marker/ball, and `redraw_structure`'s later wall recreations keep
        # stacking above it -- the load-bearing z-order that keeps the
        # structure crisp on top of the scrim. It is hidden by default; the
        # screen shows it only while HARD mode is active and the ball moves.
        self._draw_fog(colors)
        self._draw_walls(colors)
        self._draw_entry_marker(colors)
        self._draw_exit_marker(colors)
        self._ball_id = self._draw_ball(position, colors)

    # -- drawing -------------------------------------------------------

    def _draw_fog(self, colors: ColorTokens) -> None:
        """The HARD-mode scrim: a full-canvas `colors.bg` rectangle (tag `"fog"`).

        Tk `Canvas` items have no per-item alpha channel, so DESIGN.md's
        `opacity: 0.85` is approximated with a solid `colors.bg` fill -- the
        scrim reads as a translucent veil because the corridor is the
        lightest/darkest surface and the hex is still the design token.
        Show/hide is an instant `state` toggle, never an animation.
        """
        self.create_rectangle(
            0,
            0,
            self._maze.grid.width * self._cell_size,
            self._maze.grid.height * self._cell_size,
            fill=colors.bg,
            outline="",
            tags=("fog",),
            state="hidden",
        )

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

    def _draw_wall_bar(self, wall: Wall, colors: ColorTokens) -> None:
        """Draw the single wall segment `wall` (raw coordinates) as a wall bar."""
        size = self._cell_size
        x0, y0 = wall.col * size, wall.row * size
        if wall.side == "top":
            self.create_line(
                x0, y0, x0 + size, y0, width=_WALL_WIDTH, fill=colors.wall, tags=("wall",)
            )
        else:
            self.create_line(
                x0, y0, x0, y0 + size, width=_WALL_WIDTH, fill=colors.wall, tags=("wall",)
            )

    def redraw_structure(self, visibility: LevelVisibility) -> None:
        """Replace the wall bars/contour with exactly what `visibility` shows.

        Deletes the existing `"wall"`/`"contour"` items first, so repeated
        calls are idempotent; entry/exit markers and the ball are left
        untouched. The contour is the legacy `trace_contours_lab` port: a
        rectangle around the playable area with the exit side(s) reopened.
        """
        self.delete("wall")
        self.delete("contour")
        colors = colors_for(self._theme)
        for wall in visible_walls(visibility, self._maze.grid):
            self._draw_wall_bar(wall, colors)
        if show_contour(visibility):
            self._draw_contour(colors)

    def _draw_contour(self, colors: ColorTokens) -> None:
        """The playable-area contour (legacy `trace_contours_lab`).

        A wall-colored rectangle around the playable area, with the exit
        side(s) reopened by a corridor-colored bar spanning the exit cell.
        """
        size = self._cell_size
        grid = self._maze.grid
        x_max = grid.width * size
        y_max = grid.height * size
        self.create_rectangle(
            0, 0, x_max, y_max, outline=colors.wall, width=_WALL_WIDTH, tags=("contour",)
        )
        exit_row, exit_col = self._maze.exit.row, self._maze.exit.col
        exit_span_start = exit_col * size
        exit_span_end = (exit_col + 1) * size
        if exit_row == 0:
            self.create_line(
                exit_span_start, 0, exit_span_end, 0, fill=colors.corridor, tags=("contour",)
            )
        if exit_row == grid.height - 1:
            self.create_line(
                exit_span_start,
                y_max,
                exit_span_end,
                y_max,
                fill=colors.corridor,
                tags=("contour",),
            )
        exit_span_start = exit_row * size
        exit_span_end = (exit_row + 1) * size
        if exit_col == 0:
            self.create_line(
                0, exit_span_start, 0, exit_span_end, fill=colors.corridor, tags=("contour",)
            )
        if exit_col == grid.width - 1:
            self.create_line(
                x_max,
                exit_span_start,
                x_max,
                exit_span_end,
                fill=colors.corridor,
                tags=("contour",),
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

    def set_ball_offset(self, position: Position, row_delta: float, col_delta: float) -> None:
        """Reposition the ball to an interpolated point near `position`.

        `row_delta`/`col_delta` are fractions of one cell (in units of
        `self._cell_size`) from `position`'s center -- `0`/`0` is exactly
        the cell center. Lets `GameplayScreen` render the in-flight position
        of a partially-completed leg each animation tick.
        """
        cx = (position.col + col_delta) * self._cell_size + self._cell_size / 2
        cy = (position.row + row_delta) * self._cell_size + self._cell_size / 2
        radius = self._radius(_BALL_SCALE)
        self.coords(self._ball_id, cx - radius, cy - radius, cx + radius, cy + radius)

    def set_ball_position(self, position: Position) -> None:
        """Move the ball item to `position`'s cell center, without redrawing anything else."""
        self.set_ball_offset(position, 0, 0)

    def set_hard_mode_moving(self, moving: bool) -> None:
        """Toggle HARD-mode rendering for a moving (True) or resting (False) ball.

        While moving, the ball is genuinely not rendered (`state="hidden"`,
        not merely occluded) and the fog scrim is shown above the
        corridor/ball plane and below every wall bar/marker. Callable
        repeatedly; idempotent. When HARD mode is off the screen never calls
        it with `True`, so the ball stays visible and the fog hidden.
        """
        self.itemconfigure("fog", state="normal" if moving else "hidden")
        self.itemconfigure(self._ball_id, state="hidden" if moving else "normal")
