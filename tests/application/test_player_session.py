from labyrinthes.application.player_session import (
    STEPS_PER_CELL,
    advance_step,
    request_move,
    set_mode,
    set_speed,
    start_session,
    tick,
)
from labyrinthes.domain.cell import Cell
from labyrinthes.domain.duration import Duration
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.movement_mode import MovementMode
from labyrinthes.domain.movement_speed import MovementSpeed
from labyrinthes.domain.position import Position


def _open_maze(width=3) -> Maze:
    """A `width`x1 maze with every cell connected in a straight line, entry at
    the left, exit at the right -- lets tests move the ball through several
    open cells with a single `Direction.RIGHT`."""
    real_cells = tuple(Cell("1") for _ in range(width))  # top wall only: left clear
    row = real_cells + (Cell("2"),)
    padding_row = tuple(Cell("1") for _ in range(width)) + (Cell("0"),)
    grid = Grid(cells=(row, padding_row))
    return Maze(
        grid=grid,
        entry=Position(row=0, col=0),
        exit=Position(row=0, col=width - 1),
        kind=MazeKind.GENERATED,
        id=None,
    )


def _walled_maze(width=3, height=3) -> Maze:
    return Maze(
        grid=Grid.filled(width=width, height=height),
        entry=Position(row=0, col=0),
        exit=Position(row=height - 1, col=width - 1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def _redirect_maze() -> Maze:
    # (0,0) -> right open to (0,1); at (0,1) right is blocked (padding col)
    # but down to (1,1) is open, letting a banked DOWN redirect at the boundary.
    grid = Grid(
        cells=(
            (Cell("0"), Cell("1"), Cell("2")),
            (Cell("0"), Cell("0"), Cell("2")),
            (Cell("1"), Cell("1"), Cell("0")),
        )
    )
    return Maze(
        grid=grid,
        entry=Position(row=0, col=0),
        exit=Position(row=1, col=0),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def _retry_maze() -> Maze:
    # (0,0)->right open to (0,1), continue right to (0,2); at (0,1) down is
    # blocked but at (0,2) down opens -- a banked DOWN must be retried there.
    grid = Grid(
        cells=(
            (Cell("0"), Cell("1"), Cell("1"), Cell("2")),
            (Cell("0"), Cell("3"), Cell("2"), Cell("2")),
            (Cell("1"), Cell("1"), Cell("1"), Cell("0")),
        )
    )
    return Maze(
        grid=grid,
        entry=Position(row=0, col=0),
        exit=Position(row=1, col=0),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def _deadend_maze() -> Maze:
    # (0,0) -> right open to (0,1), which is a dead end (right and down blocked).
    grid = Grid(
        cells=(
            (Cell("0"), Cell("1"), Cell("2")),
            (Cell("3"), Cell("3"), Cell("2")),
            (Cell("1"), Cell("1"), Cell("0")),
        )
    )
    return Maze(
        grid=grid,
        entry=Position(row=0, col=0),
        exit=Position(row=1, col=1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def _discrete(maze: Maze):
    return set_mode(start_session(maze), MovementMode.DISCRETE)


def _advance_n(session, n: int):
    for _ in range(n):
        session = advance_step(session)
    return session


def _settle(session):
    while session.moving_direction is not None and not session.solved:
        session = advance_step(session)
    return session


def test_start_session_places_the_ball_at_entry_with_plain_defaults():
    maze = _walled_maze()
    session = start_session(maze)

    assert session.maze == maze
    assert session.position == maze.entry
    assert session.elapsed == Duration(milliseconds=0)
    assert session.solved is False
    assert session.mode is MovementMode.SMOOTH
    assert session.speed is MovementSpeed.NORMAL
    assert session.moving_direction is None
    assert session.leg_target is None
    assert session.pending_direction is None
    assert session.step == 0


# -- discrete ----------------------------------------------------------


def test_discrete_request_move_through_an_open_passage_starts_a_one_cell_leg():
    maze = _open_maze(width=3)
    session = _discrete(maze)

    session = request_move(session, Direction.RIGHT)

    assert session.moving_direction is Direction.RIGHT
    assert session.leg_target == Position(row=0, col=1)
    assert session.step == 0
    assert session.position == Position(row=0, col=0)
    assert session.solved is False


def test_discrete_leg_commits_after_steps_per_cell_advance_steps():
    maze = _open_maze(width=3)
    session = _discrete(maze)
    session = request_move(session, Direction.RIGHT)

    session = _settle(session)

    assert session.position == Position(row=0, col=1)
    assert session.moving_direction is None
    assert session.leg_target is None


def test_discrete_request_move_blocked_by_a_wall_is_a_silent_no_op():
    maze = _walled_maze()
    session = _discrete(maze)

    result = request_move(session, Direction.UP)

    assert result is session
    assert session.moving_direction is None


def test_discrete_mid_leg_press_is_ignored():
    maze = _open_maze(width=3)
    session = _discrete(maze)
    session = request_move(session, Direction.RIGHT)

    result = request_move(session, Direction.DOWN)

    assert result is session
    assert session.pending_direction is None


def test_discrete_win_is_detected_at_leg_completion():
    maze = _open_maze(width=2)
    session = _discrete(maze)
    session = request_move(session, Direction.RIGHT)

    session = _settle(session)

    assert session.position == maze.exit
    assert session.solved is True


def test_request_move_is_a_no_op_once_solved():
    maze = _open_maze(width=2)
    session = _discrete(maze)
    session = request_move(session, Direction.RIGHT)
    session = _settle(session)
    assert session.solved is True

    result = request_move(session, Direction.LEFT)

    assert result is session


# -- smooth ------------------------------------------------------------


def test_smooth_continues_straight_past_a_cell_boundary():
    maze = _open_maze(width=3)
    session = request_move(start_session(maze), Direction.RIGHT)

    session = _advance_n(session, STEPS_PER_CELL)

    assert session.position == Position(row=0, col=1)
    assert session.moving_direction is Direction.RIGHT
    assert session.leg_target == Position(row=0, col=2)


def test_smooth_redirects_into_an_open_banked_direction_at_a_boundary():
    maze = _redirect_maze()
    session = request_move(start_session(maze), Direction.RIGHT)
    session = request_move(session, Direction.DOWN)

    session = _advance_n(session, STEPS_PER_CELL)

    assert session.position == Position(row=0, col=1)
    assert session.moving_direction is Direction.DOWN
    assert session.leg_target == Position(row=1, col=1)
    assert session.pending_direction is None


def test_smooth_blocked_redirect_continues_straight_and_keeps_it_banked():
    maze = _open_maze(width=3)
    session = request_move(start_session(maze), Direction.RIGHT)
    session = request_move(session, Direction.DOWN)

    session = _advance_n(session, STEPS_PER_CELL)

    assert session.position == Position(row=0, col=1)
    assert session.moving_direction is Direction.RIGHT
    assert session.leg_target == Position(row=0, col=2)
    assert session.pending_direction is Direction.DOWN


def test_smooth_retries_a_blocked_banked_turn_at_the_following_boundary():
    maze = _retry_maze()
    session = request_move(start_session(maze), Direction.RIGHT)
    session = request_move(session, Direction.DOWN)

    session = _advance_n(session, STEPS_PER_CELL)
    assert session.position == Position(row=0, col=1)
    assert session.pending_direction is Direction.DOWN

    session = _advance_n(session, STEPS_PER_CELL)
    assert session.position == Position(row=0, col=2)
    assert session.moving_direction is Direction.DOWN
    assert session.leg_target == Position(row=1, col=2)
    assert session.pending_direction is None


def test_smooth_stops_when_the_heading_hits_a_wall():
    maze = _deadend_maze()
    session = request_move(start_session(maze), Direction.RIGHT)

    session = _advance_n(session, STEPS_PER_CELL)

    assert session.position == Position(row=0, col=1)
    assert session.moving_direction is None
    assert session.leg_target is None
    assert session.pending_direction is None


# -- mode / speed ------------------------------------------------------


def test_set_mode_replaces_the_mode_without_touching_an_in_flight_leg():
    maze = _open_maze(width=3)
    session = request_move(start_session(maze), Direction.RIGHT)

    session = set_mode(session, MovementMode.DISCRETE)

    assert session.mode is MovementMode.DISCRETE
    assert session.moving_direction is Direction.RIGHT
    assert session.leg_target == Position(row=0, col=1)


def test_set_speed_replaces_the_speed():
    maze = _walled_maze()

    session = set_speed(start_session(maze), MovementSpeed.FAST)

    assert session.speed is MovementSpeed.FAST


def test_set_mode_is_a_no_op_once_solved():
    maze = _open_maze(width=2)
    session = _discrete(maze)
    session = request_move(session, Direction.RIGHT)
    session = _settle(session)
    assert session.solved is True

    result = set_mode(session, MovementMode.DISCRETE)

    assert result is session


# -- elapsed -----------------------------------------------------------


def test_tick_replaces_the_elapsed_duration():
    maze = _walled_maze()

    session = tick(start_session(maze), Duration(milliseconds=1000))

    assert session.elapsed == Duration(milliseconds=1000)


def test_tick_is_a_no_op_once_solved():
    maze = _open_maze(width=2)
    session = _discrete(maze)
    session = request_move(session, Direction.RIGHT)
    session = _settle(session)
    assert session.solved is True

    result = tick(session, Duration(milliseconds=5000))

    assert result is session
