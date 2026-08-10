from labyrinthes.application.player_session import move, start_session, tick
from labyrinthes.domain.cell import Cell
from labyrinthes.domain.duration import Duration
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.position import Position


def _open_maze(width=3) -> Maze:
    """A `width`x1 maze with every cell connected in a straight line, entry at
    the left, exit at the right -- lets tests move the ball through several
    open cells with a single `Direction.RIGHT` in a row."""
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


def test_start_session_places_the_ball_at_entry_zero_elapsed_not_solved():
    maze = _walled_maze()

    session = start_session(maze)

    assert session.maze == maze
    assert session.position == maze.entry
    assert session.elapsed == Duration(milliseconds=0)
    assert session.solved is False


def test_move_through_an_open_passage_updates_position():
    maze = _open_maze(width=3)
    session = start_session(maze)

    session = move(session, Direction.RIGHT)

    assert session.position == Position(row=0, col=1)
    assert session.solved is False


def test_move_blocked_by_a_wall_leaves_position_unchanged():
    maze = _walled_maze()
    session = start_session(maze)

    session = move(session, Direction.UP)

    assert session.position == maze.entry
    assert session.solved is False


def test_move_reaching_the_exit_marks_the_session_solved():
    maze = _open_maze(width=3)
    session = start_session(maze)

    session = move(session, Direction.RIGHT)
    session = move(session, Direction.RIGHT)

    assert session.position == maze.exit
    assert session.solved is True


def test_move_is_a_no_op_once_solved():
    maze = _open_maze(width=2)
    session = start_session(maze)
    session = move(session, Direction.RIGHT)
    assert session.solved is True

    result = move(session, Direction.LEFT)

    assert result is session


def test_tick_replaces_the_elapsed_duration():
    maze = _walled_maze()
    session = start_session(maze)

    session = tick(session, Duration(milliseconds=1000))

    assert session.elapsed == Duration(milliseconds=1000)


def test_tick_is_a_no_op_once_solved():
    maze = _open_maze(width=2)
    session = start_session(maze)
    session = move(session, Direction.RIGHT)
    assert session.solved is True

    result = tick(session, Duration(milliseconds=5000))

    assert result is session
