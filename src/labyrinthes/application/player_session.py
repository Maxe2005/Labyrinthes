"""`PlayerSession` -- immutable gameplay-run state, plus pure orchestration.

Free functions over a frozen dataclass, matching `maze_size_bounds.
read_maze_size_bounds`'s established style (not a stateless class): no
Tkinter, no wall-clock reads (`time.monotonic()` stays entirely in
`adapters/tkinter/player/gameplay_screen.py`, which passes the already-
computed elapsed `Duration` in).

Story 2.5 reworks the keypress-snap model into a leg/animation model. A
movement now starts a *leg* (a crossing of exactly one cell, `STEPS_PER_CELL`
uniform sub-steps) that the screen advances tick-by-tick via
`advance_step()`. `DISCRETE` legs are exactly one cell (one press = one
cell, no queuing, no mid-leg redirect); `SMOOTH` legs continue past a cell
boundary unless a banked `pending_direction` redirects them, matching the
legacy "banked turn" retry semantics (a blocked `pending_direction` is not
cleared, so it's retried at the following boundary). Both modes share the
same engine and the same `cell_crossing_duration(speed)` tick rate, so the
one configurable `speed` is reflected identically in both.

`request_move`/`advance_step`/`set_mode`/`set_speed`/`set_level`/`tick`
are all no-ops -- return `session` unchanged -- once `session.solved` is
`True` (except `advance_step`/`request_move` which return unchanged once at
rest where applicable), which is what lets `GameplayScreen` keep calling
them after a win without any special casing of its own.

Story 2.6 threads the play level through the session. Every leg commit
advances `visibility` via `advance_visibility`; a blocked direction at rest
-- and Smooth's stop-at-boundary -- feeds `note_collision` instead, and the
Level MAX contour is re-shown on such a collision. `set_level` re-initializes
`visibility` from the current position, letting the screen re-render the
structure for the new level without restarting the run.

Story 2.7 threads the difficulty through the session the same way:
`set_difficulty` re-initializes `visibility` from the current position with
the new partition sizing/reveal threshold, so a mid-run difficulty change
re-renders the structure without restarting the run (an identity change on
`visibility` is what drives the screen's redraw).

Story 2.8 adds HARD mode: `set_hard_mode` mirrors `set_mode`/`set_speed` --
session-scoped, never persisted, a no-op once solved. HARD is purely
presentational (the screen hides the ball and draws a fog scrim while
moving) and never changes movement math, so no visibility re-init is
needed; a fresh mount starts with HARD off.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from labyrinthes.domain.difficulty import Difficulty
from labyrinthes.domain.duration import Duration
from labyrinthes.domain.level import Level
from labyrinthes.domain.level_visibility import (
    LevelVisibility,
    advance_visibility,
    initial_level_visibility,
    note_collision,
)
from labyrinthes.domain.maze import Maze
from labyrinthes.domain.movement import Direction, attempt_move
from labyrinthes.domain.movement_mode import MovementMode
from labyrinthes.domain.movement_speed import MovementSpeed
from labyrinthes.domain.position import Position

__all__ = [
    "STEPS_PER_CELL",
    "PlayerSession",
    "advance_step",
    "request_move",
    "set_difficulty",
    "set_hard_mode",
    "set_level",
    "set_mode",
    "set_speed",
    "start_session",
    "tick",
    "ignore_timeout",
    "set_time_limit",
]

# The fixed number of uniform sub-steps in a one-cell leg (the legacy
# `decoupe du deplacement` default, deliberately not user-configurable --
# the one speed setting is the tier, not this count).
STEPS_PER_CELL = 5


@dataclass(frozen=True)
class PlayerSession:
    """One gameplay run's state: the `Maze`, the ball, elapsed time, and
    the in-flight movement leg (mode/speed + the `DISCRETE`/`SMOOTH` leg)."""

    maze: Maze
    position: Position
    elapsed: Duration
    solved: bool
    mode: MovementMode
    speed: MovementSpeed
    moving_direction: Direction | None
    leg_target: Position | None
    step: int
    pending_direction: Direction | None
    level: Level
    difficulty: Difficulty
    visibility: LevelVisibility
    hard_mode: bool
    time_limit: Duration | None
    timed_out: bool


def start_session(maze: Maze) -> PlayerSession:
    """A fresh `PlayerSession` for `maze`: ball at `maze.entry`, zero elapsed,
    at rest, with the plain defaults `SMOOTH`/`NORMAL` and Level ONE.

    The screen applies settings-loaded mode/speed by chaining `set_mode`/
    `set_speed` on the result -- `start_session` itself stays pure with
    plain defaults and never reads the repository. Level is session state
    (not persisted); it always starts at `Level.ONE`.

    Timer limit defaults to `None` (disabled) and `timed_out` to `False`.
    """
    return PlayerSession(
        maze=maze,
        position=maze.entry,
        elapsed=Duration(milliseconds=0),
        solved=False,
        mode=MovementMode.SMOOTH,
        speed=MovementSpeed.NORMAL,
        moving_direction=None,
        leg_target=None,
        step=0,
        pending_direction=None,
        level=Level.ONE,
        difficulty=Difficulty.ONE,
        visibility=initial_level_visibility(maze, Level.ONE, Difficulty.ONE, maze.entry),
        hard_mode=False,
        time_limit=None,
        timed_out=False,
    )


def _start_leg(session: PlayerSession, direction: Direction) -> PlayerSession:
    """Start a one-cell leg in `direction`; the caller guarantees it is open."""
    target = attempt_move(session.maze.grid, session.position, direction)
    return replace(
        session,
        moving_direction=direction,
        leg_target=target,
        step=0,
    )


def request_move(session: PlayerSession, direction: Direction) -> PlayerSession:
    """`session` after the player requests movement in `direction`.

    At rest, an open passage starts a one-cell leg (both modes alike --
    Discrete's leg is exactly one cell). Mid-leg, Discrete silently ignores
    the press (one press = one cell, no queuing), while Smooth banks
    `pending_direction` for resolution at the next cell boundary. A blocked
    direction at rest is a silent no-op. A no-op once solved or timed out.
    """
    if session.solved or session.timed_out:
        return session

    if session.moving_direction is None:
        target = attempt_move(session.maze.grid, session.position, direction)
        if target == session.position:
            visibility = note_collision(
                session.visibility, session.maze, session.position, direction
            )
            if visibility is session.visibility:
                return session
            return replace(session, visibility=visibility)
        return _start_leg(session, direction)

    if session.mode is MovementMode.DISCRETE:
        return session
    return replace(session, pending_direction=direction)


def advance_step(session: PlayerSession) -> PlayerSession:
    """`session` after one fixed-duration animation tick of the in-flight leg.

    A pure, fixed-duration tick: it never reads elapsed time, it simply
    advances the in-flight leg by one of `STEPS_PER_CELL` uniform sub-steps.
    A no-op once solved and a no-op when at rest. On the final sub-step the
    leg commits (`position = leg_target`), advances `visibility`, checks the
    win, and -- for Smooth only -- resolves the next heading at the boundary:
    redirect into an open `pending_direction`, else continue straight, else
    stop (`note_collision`). A blocked `pending_direction` is kept for retry
    at the following boundary (legacy "banked turn" semantics);
    `pending_direction` never applies in Discrete.

    Also a no-op once timed out.
    """
    if session.solved or session.timed_out:
        return session

    new_step = session.step + 1
    if new_step < STEPS_PER_CELL:
        return replace(session, step=new_step)

    position = session.leg_target
    solved = position == session.maze.exit
    if solved:
        return replace(
            session,
            position=position,
            solved=True,
            moving_direction=None,
            leg_target=None,
            pending_direction=None,
            step=0,
            visibility=advance_visibility(session.visibility, session.maze, position),
        )

    if session.mode is MovementMode.DISCRETE:
        return replace(
            session,
            position=position,
            moving_direction=None,
            leg_target=None,
            pending_direction=None,
            step=0,
            visibility=advance_visibility(session.visibility, session.maze, position),
        )

    committed = replace(
        session,
        position=position,
        visibility=advance_visibility(session.visibility, session.maze, position),
    )
    return _resolve_smooth_next(committed)


def _resolve_smooth_next(session: PlayerSession) -> PlayerSession:
    """Resolve Smooth's heading at a just-committed cell boundary (not solved)."""
    position = session.position
    pending = session.pending_direction
    heading = session.moving_direction

    if pending is not None and attempt_move(session.maze.grid, position, pending) != position:
        return replace(_start_leg(session, pending), pending_direction=None)
    # Blocked: keep `pending_direction` banked for retry; fall through
    # to the straight-continuation check below.

    if attempt_move(session.maze.grid, position, heading) != position:
        return _start_leg(session, heading)

    visibility = note_collision(session.visibility, session.maze, position, heading)
    return replace(
        session,
        moving_direction=None,
        leg_target=None,
        pending_direction=None,
        step=0,
        visibility=visibility,
    )


def set_mode(session: PlayerSession, mode: MovementMode) -> PlayerSession:
    """`session` with `mode` replaced. A no-op once solved.

    Mid-leg behavior is the *engine's* choice, not this function's: an
    in-flight leg keeps its `moving_direction`/`leg_target`; the next
    `request_move`/`advance_step` behaves per the new `mode`.
    """
    if session.solved:
        return session
    return replace(session, mode=mode)


def set_speed(session: PlayerSession, speed: MovementSpeed) -> PlayerSession:
    """`session` with `speed` replaced. A no-op once solved.

    The in-flight leg's geometry is unaffected; the screen recomputes the
    per-step delay from the new `cell_crossing_duration(speed)` on its next
    reschedule, so the change applies to both modes immediately.
    """
    if session.solved:
        return session
    return replace(session, speed=speed)


def set_hard_mode(session: PlayerSession, enabled: bool) -> PlayerSession:
    """`session` with `hard_mode` replaced. A no-op once solved.

    HARD is purely presentational -- the screen hides the ball and draws a
    fog scrim while the ball moves -- and never changes movement math, so
    unlike `set_level`/`set_difficulty` there is no visibility re-init. The
    flag is session-scoped and not persisted; a fresh mount starts HARD off.
    """
    if session.solved:
        return session
    return replace(session, hard_mode=enabled)


def set_level(session: PlayerSession, level: Level) -> PlayerSession:
    """`session` with `level` replaced; a no-op once solved.

    The session's difficulty is left untouched -- the persistence grid keeps
    the create-time difficulty, only the *played* level changes. The level
    change re-initializes `visibility` from the current position, so the
    structure re-renders per the new level without restarting the run.
    """
    if session.solved:
        return session
    visibility = initial_level_visibility(session.maze, level, session.difficulty, session.position)
    return replace(session, level=level, visibility=visibility)


def set_difficulty(session: PlayerSession, difficulty: Difficulty) -> PlayerSession:
    """`session` with `difficulty` replaced; a no-op once solved.

    Mirrors `set_level`: the difficulty change re-initializes `visibility`
    from the current position, so the structure re-renders with the new
    partition sizing/reveal threshold without restarting the run. The
    in-flight leg's geometry is unaffected -- the next commit re-applies
    against the freshly re-initialized visibility.
    """
    if session.solved:
        return session
    visibility = initial_level_visibility(session.maze, session.level, difficulty, session.position)
    return replace(session, difficulty=difficulty, visibility=visibility)


def tick(session: PlayerSession, elapsed: Duration) -> PlayerSession:
    """`session` with `elapsed` replacing its current elapsed time; a no-op once solved.

    If `time_limit` is set and `elapsed >= time_limit`, sets `timed_out=True`.
    """
    if session.solved:
        return session
    new_session = replace(session, elapsed=elapsed)
    limit_exceeded = (
        new_session.time_limit is not None
        and elapsed.milliseconds >= new_session.time_limit.milliseconds
    )
    if limit_exceeded:
        return replace(new_session, timed_out=True)
    return new_session


def set_time_limit(session: PlayerSession, limit: Duration | None) -> PlayerSession:
    """`session` with `time_limit` replaced.

    No-op once solved or timed out.
    """
    if session.solved or session.timed_out:
        return session
    return replace(session, time_limit=limit)


def ignore_timeout(session: PlayerSession) -> PlayerSession:
    """`session` with `timed_out` cleared to `False` and `time_limit` removed (set to `None`).

    Allows the player to continue without further pressure after a timeout.
    """
    return replace(session, timed_out=False, time_limit=None)
