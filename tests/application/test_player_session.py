from labyrinthes.application.player_session import (
    STEPS_PER_CELL,
    advance_step,
    request_move,
    set_level,
    set_mode,
    set_speed,
    start_session,
    tick,
)
from labyrinthes.domain.cell import Cell
from labyrinthes.domain.difficulty import Difficulty
from labyrinthes.domain.duration import Duration
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level import Level
from labyrinthes.domain.level_visibility import Wall
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


def _redirect_win_maze() -> Maze:
    # Same geometry as `_redirect_maze` (right then banked DOWN onto (1,1)),
    # but the exit sits on the redirect target so the win fires at the commit
    # of the redirected leg, not the initial straight leg.
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
        exit=Position(row=1, col=1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def _partition_maze() -> Maze:
    # 5x3 playable, corridor along row 0. Difficulty ONE partitions are
    # (2, 2) here, so (0,0)-(0,1) sit in partition 0 and (0,2)-(0,3) in
    # partition 1 -- open enough to move the ball across a partition
    # boundary, walled enough to exercise blocked moves at rest.
    grid = Grid(
        cells=(
            (Cell("0"), Cell("0"), Cell("0"), Cell("0"), Cell("0"), Cell("2")),
            (Cell("3"), Cell("3"), Cell("3"), Cell("3"), Cell("3"), Cell("2")),
            (Cell("3"), Cell("3"), Cell("3"), Cell("3"), Cell("3"), Cell("2")),
            (Cell("1"), Cell("1"), Cell("1"), Cell("1"), Cell("1"), Cell("0")),
        )
    )
    return Maze(
        grid=grid,
        entry=Position(row=0, col=0),
        exit=Position(row=0, col=4),
        kind=MazeKind.GENERATED,
        id=None,
    )


def _stopping_maze() -> Maze:
    # Corridor along row 0 that ends against an interior wall: (0,1) going
    # right is blocked by the left wall of (0,2), which is not a border.
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
        kind=MazeKind.GENERATED,
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
    assert session.level is Level.ONE
    assert session.difficulty is Difficulty.ONE
    assert session.visibility.level is Level.ONE
    assert session.visibility.current_partition == 0


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


def test_smooth_stops_in_a_corner_when_both_the_banked_turn_and_straight_are_blocked():
    maze = _deadend_maze()
    session = request_move(start_session(maze), Direction.RIGHT)
    session = request_move(session, Direction.DOWN)

    session = _advance_n(session, STEPS_PER_CELL)

    assert session.position == Position(row=0, col=1)
    assert session.moving_direction is None
    assert session.leg_target is None
    assert session.pending_direction is None


def test_smooth_win_is_detected_when_a_banked_redirect_commits_onto_the_exit():
    maze = _redirect_win_maze()
    session = request_move(start_session(maze), Direction.RIGHT)
    session = request_move(session, Direction.DOWN)

    session = _advance_n(session, STEPS_PER_CELL)
    assert session.position == Position(row=0, col=1)
    assert session.solved is False
    assert session.moving_direction is Direction.DOWN

    session = _advance_n(session, STEPS_PER_CELL)
    assert session.position == maze.exit
    assert session.solved is True


# -- mode / speed ------------------------------------------------------


def test_set_mode_replaces_the_mode_without_touching_an_in_flight_leg():
    maze = _open_maze(width=3)
    session = request_move(start_session(maze), Direction.RIGHT)

    session = set_mode(session, MovementMode.DISCRETE)

    assert session.mode is MovementMode.DISCRETE
    assert session.moving_direction is Direction.RIGHT
    assert session.leg_target == Position(row=0, col=1)


def test_discrete_leg_switched_to_smooth_mid_flight_continues_straight_at_commit():
    maze = _open_maze(width=3)
    session = _discrete(maze)
    session = request_move(session, Direction.RIGHT)
    session = set_mode(session, MovementMode.SMOOTH)

    session = _advance_n(session, STEPS_PER_CELL)

    assert session.position == Position(row=0, col=1)
    assert session.moving_direction is Direction.RIGHT
    assert session.leg_target == Position(row=0, col=2)


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


# -- level / visibility -------------------------------------------------


def test_set_level_reinitializes_visibility_from_the_current_position():
    maze = _partition_maze()
    session = _discrete(maze)
    session = request_move(session, Direction.RIGHT)
    session = _settle(session)
    assert session.position == Position(row=0, col=1)
    assert session.moving_direction is None

    session = set_level(session, Level.MAX)

    assert session.level is Level.MAX
    assert session.position == Position(row=0, col=1)
    assert session.solved is False
    assert session.visibility.level is Level.MAX
    assert session.visibility.contour_shown is True


def test_set_level_preserves_elapsed_mode_and_speed():
    maze = _partition_maze()
    session = _discrete(maze)
    session = set_speed(session, MovementSpeed.FAST)
    session = tick(session, Duration(milliseconds=5000))
    session = request_move(session, Direction.RIGHT)
    session = _settle(session)
    assert session.elapsed == Duration(milliseconds=5000)
    assert session.mode is MovementMode.DISCRETE
    assert session.speed is MovementSpeed.FAST

    session = set_level(session, Level.FOUR)

    assert session.elapsed == Duration(milliseconds=5000)
    assert session.mode is MovementMode.DISCRETE
    assert session.speed is MovementSpeed.FAST


def test_set_level_preserves_an_in_flight_leg():
    maze = _partition_maze()
    session = _discrete(maze)
    session = request_move(session, Direction.RIGHT)
    assert session.moving_direction is Direction.RIGHT
    assert session.leg_target == Position(row=0, col=1)
    assert session.step == 0

    session = set_level(session, Level.FOUR)

    assert session.moving_direction is Direction.RIGHT
    assert session.leg_target == Position(row=0, col=1)
    assert session.step == 0
    assert session.pending_direction is None

    session = _settle(session)
    assert session.position == Position(row=0, col=1)
    assert session.moving_direction is None
    assert session.level is Level.FOUR


def test_set_level_is_a_no_op_once_solved():
    maze = _open_maze(width=2)
    session = _discrete(maze)
    session = request_move(session, Direction.RIGHT)
    session = _settle(session)
    assert session.solved is True

    result = set_level(session, Level.MAX)

    assert result is session


def test_discrete_leg_commit_advances_level_two_partition_tracking():
    maze = _partition_maze()
    session = set_level(_discrete(maze), Level.TWO)

    session = request_move(session, Direction.RIGHT)
    session = _settle(session)
    assert session.position == Position(row=0, col=1)
    assert session.visibility.visited == frozenset({0})

    session = request_move(session, Direction.RIGHT)
    session = _settle(session)
    assert session.position == Position(row=0, col=2)
    assert session.visibility.visited == frozenset({0, 1})


def test_level_four_blocked_at_rest_reveals_the_collided_wall():
    maze = _partition_maze()
    session = set_level(_discrete(maze), Level.FOUR)
    session = request_move(session, Direction.RIGHT)
    session = _settle(session)
    assert session.position == Position(row=0, col=1)

    result = request_move(session, Direction.DOWN)

    assert result is not session
    assert result.visibility.discovered_walls == frozenset({Wall(row=1, col=1, side="top")})


def test_blocked_at_rest_at_levels_one_to_three_is_a_no_op():
    maze = _partition_maze()
    for level in (Level.ONE, Level.TWO, Level.THREE):
        session = set_level(_discrete(maze), level)
        session = request_move(session, Direction.RIGHT)
        session = _settle(session)
        assert session.position == Position(row=0, col=1)

        result = request_move(session, Direction.DOWN)

        assert result is session
        assert session.visibility.discovered_walls == frozenset()


def test_level_max_contour_is_hidden_after_a_move_and_reshown_on_collision():
    maze = _partition_maze()
    session = set_level(_discrete(maze), Level.MAX)
    assert session.visibility.contour_shown is True

    session = request_move(session, Direction.RIGHT)
    session = _settle(session)
    assert session.position == Position(row=0, col=1)
    assert session.visibility.contour_shown is False

    session = request_move(session, Direction.DOWN)

    assert session.visibility.contour_shown is True
    assert session.position == Position(row=0, col=1)
    assert session.moving_direction is None


def test_smooth_boundary_stop_reveals_the_collided_wall_at_level_four():
    maze = _stopping_maze()
    session = set_level(start_session(maze), Level.FOUR)
    session = request_move(session, Direction.RIGHT)

    session = _advance_n(session, STEPS_PER_CELL)

    assert session.position == Position(row=0, col=1)
    assert session.moving_direction is None
    assert session.visibility.discovered_walls == frozenset({Wall(row=0, col=2, side="left")})
