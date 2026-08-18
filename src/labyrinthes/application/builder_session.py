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

Four tools:
- `BuilderTool.BREAK` -- `apply_wall_toggle(session, wall)` toggles the
  wall the adapter hit-tested from a click (breaks if present, restores
  if absent); the cursor never moves. `move_cursor` just moves the cursor,
  leaving every wall alone.
- `BuilderTool.PASS_THROUGH` -- `move_cursor` breaks whatever interior
  wall blocks the requested move, then moves the cursor into the target
  cell; a border wall stops the cursor without breaking anything (FR-2's
  closed-border invariant always wins).
- `BuilderTool.DESTROY_ZONE` / `BuilderTool.RESTORE_ZONE` (Story 3.3) --
  `apply_zone_operation(session, tool, corner_a, corner_b)` batches
  `domain.zone_editing.destroy_zone`/`restore_zone` over the rectangle the
  adapter's click-and-drag spanned; the cursor never moves. `tool` is
  taken as an explicit argument, not read off `session.tool`, so a caller
  can pass the tool captured at *press* time -- the tool that governs the
  whole press-to-release gesture -- even if the user switched tools (e.g.
  via a keybinding) while still holding the mouse button down. A live
  re-read of `session.tool` at release time would let a single continuous
  gesture be interpreted under two different tools.
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
from labyrinthes.domain.zone_editing import destroy_zone, restore_zone

__all__ = [
    "BuilderSession",
    "BuilderTool",
    "apply_wall_toggle",
    "apply_zone_operation",
    "broken_wall_count",
    "move_cursor",
    "set_tool",
    "start_builder_session",
]


class BuilderTool(enum.Enum):
    """The active tool in the Builder edit screen's tool side bar."""

    BREAK = "break"
    PASS_THROUGH = "pass-through"
    DESTROY_ZONE = "destroy-zone"
    RESTORE_ZONE = "restore-zone"


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


def apply_zone_operation(
    session: BuilderSession, tool: BuilderTool, corner_a: Position, corner_b: Position
) -> BuilderSession:
    """Destroy or restore the rectangular zone spanning `corner_a`/`corner_b`,
    per the given `tool` -- not `session.tool`.

    `BuilderTool.DESTROY_ZONE` calls `domain.zone_editing.destroy_zone`,
    `BuilderTool.RESTORE_ZONE` calls `restore_zone`; the cursor is left
    unchanged (mirrors `apply_wall_toggle`), and `session.tool` itself is
    also left unchanged -- `tool` only decides *this* dispatch, it never
    overwrites the session's live active tool. Border walls within the
    span are silently skipped by the domain functions themselves, never
    raised (Story 3.3's Boundaries). `tool` being neither zone tool is a
    no-op returning `session` unchanged (the adapter's own drag-release
    gating is what normally decides whether a zone operation happens at
    all; this is a defensive fallback, not the primary gate).
    """
    if tool is BuilderTool.DESTROY_ZONE:
        new_grid = destroy_zone(session.maze.grid, corner_a, corner_b)
    elif tool is BuilderTool.RESTORE_ZONE:
        new_grid = restore_zone(session.maze.grid, corner_a, corner_b)
    else:
        return session
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
