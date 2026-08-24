"""Shared Builder-screen test helpers: maze fixtures + click/drag simulation.

Every `test_*.py` in this package mounts the Builder end-to-end (via
`mount()`) and drives it through simulated `_BuilderMazeCanvas` mouse
events -- these helpers are the common vocabulary every one of those files
imports from, rather than each redefining its own.
"""

from __future__ import annotations

from labyrinthes.adapters.tkinter.builder.maze_canvas import _BuilderMazeCanvas
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level_visibility import Wall
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.position import Position
from labyrinthes.domain.wall_editing import toggle_wall

__all__ = [
    "_FakeEvent",
    "_classic_maze",
    "_click_at_cell",
    "_click_wall",
    "_drag_zone",
    "_open_top_row_maze",
    "_release_at_cell",
    "_sketch_maze",
]


class _FakeEvent:
    """A minimal stand-in for `tk.Event`: `_on_click` only reads `.x`/`.y`,
    and real X11 click synthesis isn't reliable under a withdrawn `tk_root`
    (see e.g. `test_screen.test_settings_icon_click_...`'s comment)."""

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


def _sketch_maze(columns: int = 4, rows: int = 3) -> Maze:
    return Maze(
        grid=Grid.filled(columns, rows),
        entry=Position(row=0, col=0),
        exit=Position(row=rows - 1, col=columns - 1),
        kind=MazeKind.SKETCH,
        id=None,
    )


def _classic_maze(columns: int = 4, rows: int = 3) -> Maze:
    return Maze(
        grid=Grid.filled(columns, rows),
        entry=Position(row=0, col=0),
        exit=Position(row=rows - 1, col=columns - 1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def _open_top_row_maze() -> Maze:
    """A 4×3 sketch with an open corridor along the top row and one step
    down into the interior -- lets the cursor move between unmarked border
    cells and into an interior cell without needing to break walls first."""
    grid = Grid.filled(4, 3)
    grid = toggle_wall(grid, Wall(row=0, col=1, side="left"))  # (0,0)-(0,1)
    grid = toggle_wall(grid, Wall(row=0, col=2, side="left"))  # (0,1)-(0,2)
    grid = toggle_wall(grid, Wall(row=1, col=1, side="top"))  # (0,1)-(1,1)
    return Maze(
        grid=grid,
        entry=Position(row=0, col=0),
        exit=Position(row=2, col=3),
        kind=MazeKind.SKETCH,
        id=None,
    )


def _click_wall(canvas: _BuilderMazeCanvas, wall: Wall) -> None:
    """Simulate a click on `wall`'s bar/gap: the midpoint of its canvas item."""
    x0, y0, x1, y1 = canvas.coords(canvas._wall_items[wall])
    canvas._on_click(_FakeEvent(int((x0 + x1) / 2), int((y0 + y1) / 2)))


def _cell_center_event(canvas: _BuilderMazeCanvas, cell: Position) -> _FakeEvent:
    size = canvas._cell_size
    return _FakeEvent(cell.col * size + size // 2, cell.row * size + size // 2)


def _click_at_cell(canvas: _BuilderMazeCanvas, cell: Position) -> None:
    """Simulate a `<Button-1>` press at `cell`'s center."""
    canvas._on_click(_cell_center_event(canvas, cell))


def _release_at_cell(canvas: _BuilderMazeCanvas, cell: Position) -> None:
    """Simulate a `<ButtonRelease-1>` at `cell`'s center."""
    canvas._on_release(_cell_center_event(canvas, cell))


def _drag_zone(canvas: _BuilderMazeCanvas, anchor: Position, end: Position) -> None:
    """Simulate a press-drag-release gesture: press at `anchor`'s cell center,
    release at `end`'s cell center."""
    _click_at_cell(canvas, anchor)
    _release_at_cell(canvas, end)
