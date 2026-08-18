"""`BuilderSession` -- immutable Builder-edit-session state, plus pure
orchestration (Story 3.2).

Free functions over a frozen dataclass, matching `player_session.py`'s
established style: no Tkinter, no wall-clock reads, no repository access
(AD-1..AD-3, NFR1). The session wraps the immutable `Maze` under edit plus
the adapter-local editing cursor and the active tool -- the Epic 3
Technical Decisions call this "an adapter-local mutable session wrapper
... around the immutable `Maze` value", and this module is where the
`application/`-layer half of that wrapper lives (only rendering/input
wiring stays in `adapters/tkinter/builder/`).

Two tools:
- `BuilderTool.BREAK` -- `apply_wall_toggle(session, wall)` toggles the
  wall the adapter hit-tested from a click (breaks if present, restores
  if absent); the cursor never moves. `move_cursor` just moves the cursor,
  leaving every wall alone.
- `BuilderTool.PASS_THROUGH` -- `move_cursor` breaks whatever interior
  wall blocks the requested move, then moves the cursor into the target
  cell; a border wall stops the cursor without breaking anything (FR-2's
  closed-border invariant always wins).
"""

from __future__ import annotations

import dataclasses
import enum
from dataclasses import dataclass, replace

from labyrinthes.domain.level_visibility import Wall, is_border_wall
from labyrinthes.domain.maze import Maze
from labyrinthes.domain.movement import Direction, attempt_move
from labyrinthes.domain.position import Position
from labyrinthes.domain.wall_editing import (
    break_wall,
    count_broken_walls,
    toggle_wall,
    wall_between,
)

__all__ = [
    "BuilderSession",
    "BuilderTool",
    "apply_wall_toggle",
    "broken_wall_count",
    "move_cursor",
    "set_tool",
    "start_builder_session",
]


class BuilderTool(enum.Enum):
    """The active tool in the Builder edit screen's tool side bar."""

    BREAK = "break"
    PASS_THROUGH = "pass-through"


@dataclass(frozen=True)
class BuilderSession:
    """One Builder edit session: the maze under edit, the editing cursor
    position, and the active tool."""

    maze: Maze
    cursor: Position
    tool: BuilderTool


def start_builder_session(maze: Maze) -> BuilderSession:
    """A fresh `BuilderSession` for `maze`: cursor at `maze.entry`, Break tool
    active (mirrors `player_session.start_session`'s "ball at `maze.entry`"
    convention)."""
    return BuilderSession(maze=maze, cursor=maze.entry, tool=BuilderTool.BREAK)


def set_tool(session: BuilderSession, tool: BuilderTool) -> BuilderSession:
    """Return `session` with the active tool replaced."""
    return replace(session, tool=tool)


def apply_wall_toggle(session: BuilderSession, wall: Wall) -> BuilderSession:
    """Toggle `wall`: breaks it if present, restores it if absent.

    The cursor is left unchanged. A border `wall` propagates
    `DomainValidationError` from `domain.wall_editing.toggle_wall` --
    the adapter's own hit-test never selects a border segment for
    clicking, so this only fires for interior walls in practice.
    """
    new_grid = toggle_wall(session.maze.grid, wall)
    new_maze = dataclasses.replace(session.maze, grid=new_grid)
    return replace(session, maze=new_maze)


def move_cursor(session: BuilderSession, direction: Direction) -> BuilderSession:
    """Move the editing cursor one cell in `direction`.

    In `BREAK` mode this is a plain `attempt_move` -- the cursor moves if
    open, stays put if blocked; no wall state changes.

    In `PASS_THROUGH` mode, a blocked move breaks the wall it ran into
    first (`domain.wall_editing.break_wall`, via `wall_between`), then
    moves the cursor into the now-open target cell. A blocked *border*
    wall leaves the cursor in place and breaks nothing.
    """
    grid = session.maze.grid
    target = attempt_move(grid, session.cursor, direction)

    if target != session.cursor or session.tool is not BuilderTool.PASS_THROUGH:
        return replace(session, cursor=target)

    wall = wall_between(session.cursor, direction)
    if is_border_wall(grid, wall):
        return session

    new_grid = break_wall(grid, wall)
    new_maze = dataclasses.replace(session.maze, grid=new_grid)
    new_target = attempt_move(new_grid, session.cursor, direction)
    return replace(session, maze=new_maze, cursor=new_target)


def broken_wall_count(session: BuilderSession) -> int:
    """The live "walls broken" count for `session`'s maze."""
    return count_broken_walls(session.maze.grid)
