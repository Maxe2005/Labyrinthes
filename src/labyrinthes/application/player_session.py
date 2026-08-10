"""`PlayerSession` -- immutable gameplay-run state, plus `start_session`/`move`/`tick`.

Free functions over a frozen dataclass, matching `maze_size_bounds.
read_maze_size_bounds`'s established style (not a stateless class): no
Tkinter, no wall-clock reads (`time.monotonic()` stays entirely in
`adapters/tkinter/player/gameplay_screen.py`, which passes the already-
computed elapsed `Duration` in). `move`/`tick` are both no-ops -- return
`session` unchanged -- once `session.solved` is `True`, which is what
lets `GameplayScreen` keep calling them after a win without any special
casing of its own (see the story's Design Notes).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from labyrinthes.domain.duration import Duration
from labyrinthes.domain.maze import Maze
from labyrinthes.domain.movement import Direction, attempt_move
from labyrinthes.domain.position import Position

__all__ = ["PlayerSession", "move", "start_session", "tick"]


@dataclass(frozen=True)
class PlayerSession:
    """One gameplay run's state: the `Maze` being played, the ball's `Position`,
    elapsed `Duration`, and whether the exit has been reached."""

    maze: Maze
    position: Position
    elapsed: Duration
    solved: bool


def start_session(maze: Maze) -> PlayerSession:
    """A fresh `PlayerSession` for `maze`: ball at `maze.entry`, zero elapsed, not solved."""
    return PlayerSession(
        maze=maze,
        position=maze.entry,
        elapsed=Duration(milliseconds=0),
        solved=False,
    )


def move(session: PlayerSession, direction: Direction) -> PlayerSession:
    """`session` after one `attempt_move` in `direction`; a no-op once solved.

    Sets `solved=True` when the resulting position equals `session.maze.exit`
    -- a blocked move (the candidate equals the current position) still
    routes through here, it just leaves `position` unchanged.
    """
    if session.solved:
        return session

    new_position = attempt_move(session.maze.grid, session.position, direction)
    solved = new_position == session.maze.exit
    return replace(session, position=new_position, solved=solved)


def tick(session: PlayerSession, elapsed: Duration) -> PlayerSession:
    """`session` with `elapsed` replacing its current elapsed time; a no-op once solved."""
    if session.solved:
        return session
    return replace(session, elapsed=elapsed)
