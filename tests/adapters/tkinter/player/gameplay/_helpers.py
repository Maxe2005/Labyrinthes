"""Shared `GameplayScreen` test helpers: maze fixtures + a repository double.

Every `test_*.py` in this package mounts `GameplayScreen` end-to-end and
drives it through the same handful of small hand-built mazes -- these
helpers are the common vocabulary every one of those files imports from,
rather than each redefining its own.
"""

from __future__ import annotations

from labyrinthes.application.settings_keys import MOVEMENT_MODE
from labyrinthes.application.settings_repository import SettingsScope
from labyrinthes.domain.cell import Cell
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.position import Position

__all__ = [
    "ExplodingMazeRepository",
    "_classic_maze",
    "_corridor_maze",
    "_generated_maze",
    "_open_maze",
    "_settle",
    "_stopping_maze",
    "_use_discrete",
]


def _generated_maze(width=4, height=3) -> Maze:
    return Maze(
        grid=Grid.filled(width=width, height=height),
        entry=Position(row=0, col=0),
        exit=Position(row=height - 1, col=width - 1),
        kind=MazeKind.GENERATED,
        id=None,
    )


def _classic_maze(width=4, height=3) -> Maze:
    return Maze(
        grid=Grid.filled(width=width, height=height),
        entry=Position(row=0, col=0),
        exit=Position(row=height - 1, col=width - 1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def _open_maze(width=2) -> Maze:
    """A `width`x1 maze, every cell connected in a straight line, entry at the
    left, exit at the right -- lets movement tests reach the exit in `width -
    1` `Direction.RIGHT` presses."""
    real_cells = tuple(Cell("1") for _ in range(width))  # top wall only: left clear
    row = real_cells + (Cell("2"),)
    padding_row = tuple(Cell("1") for _ in range(width)) + (Cell("0"),)
    grid = Grid(cells=(row, padding_row))
    return Maze(
        grid=grid,
        entry=Position(row=0, col=0),
        exit=Position(row=0, col=width - 1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def _corridor_maze(width=4) -> Maze:
    """A 2-row corridor: row 0 open left-to-right, exit at the far right,
    everything below walled -- open enough to move across partition
    boundaries, walled enough to exercise blocked moves."""
    row0 = tuple(Cell("0") for _ in range(width)) + (Cell("2"),)
    row1 = tuple(Cell("3") for _ in range(width)) + (Cell("2"),)
    padding_row = tuple(Cell("1") for _ in range(width)) + (Cell("0"),)
    grid = Grid(cells=(row0, row1, padding_row))
    return Maze(
        grid=grid,
        entry=Position(row=0, col=0),
        exit=Position(row=0, col=width - 1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def _stopping_maze() -> Maze:
    """Corridor along row 0 that ends against an interior wall: (0,1) going
    right is blocked by the left wall of (0,2), which is not a border."""
    grid = Grid(
        cells=(
            (Cell("0"), Cell("0"), Cell("3"), Cell("0"), Cell("0"), Cell("2")),
            (Cell("3"), Cell("3"), Cell("3"), Cell("3"), Cell("3"), Cell("2")),
            (Cell("3"), Cell("3"), Cell("3"), Cell("3"), Cell("3"), Cell("2")),
            (Cell("1"), Cell("1"), Cell("1"), Cell("1"), Cell("1"), Cell("0")),
        )
    )
    return Maze(
        grid=grid,
        entry=Position(row=0, col=0),
        exit=Position(row=0, col=4),
        kind=MazeKind.CLASSIC,
        id=None,
    )


class ExplodingMazeRepository:
    def save(self, maze, name):
        raise AssertionError("save() must not be called")

    def load(self, name, kind):
        raise AssertionError("load() must not be called")

    def find_by_id(self, maze_id):
        raise AssertionError("find_by_id() must not be called")

    def list_names(self, kind):
        raise AssertionError("list_names() must not be called")


def _settle(screen) -> None:
    """Drive the animation loop until the in-flight leg completes (or the run
    is solved), so tests no longer assert an instant post-keypress state."""
    while screen._session.moving_direction is not None:
        screen._on_animation_tick()


def _use_discrete(fake_settings_repository) -> None:
    fake_settings_repository.set(SettingsScope.GAME, MOVEMENT_MODE, "discrete")
