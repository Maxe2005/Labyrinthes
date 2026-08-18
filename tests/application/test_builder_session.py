from labyrinthes.application.builder_session import (
    BuilderSession,
    BuilderTool,
    apply_zone_operation,
    start_builder_session,
)
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.position import Position
from labyrinthes.domain.zone_editing import destroy_zone, restore_zone


def _sketch_maze(width: int = 5, height: int = 5) -> Maze:
    return Maze(
        grid=Grid.filled(width, height),
        entry=Position(row=0, col=0),
        exit=Position(row=height - 1, col=width - 1),
        kind=MazeKind.SKETCH,
        id=None,
    )


def _session_at(cursor: Position, tool: BuilderTool) -> BuilderSession:
    return BuilderSession(maze=_sketch_maze(), cursor=cursor, tool=tool)


# -- apply_zone_operation --------------------------------------------------


def test_apply_zone_operation_with_destroy_zone_tool_destroys_the_span():
    session = _session_at(Position(0, 0), BuilderTool.DESTROY_ZONE)

    result = apply_zone_operation(session, BuilderTool.DESTROY_ZONE, Position(1, 1), Position(3, 3))

    expected_grid = destroy_zone(session.maze.grid, Position(1, 1), Position(3, 3))
    assert result.maze.grid == expected_grid


def test_apply_zone_operation_with_restore_zone_tool_restores_the_span():
    destroyed_grid = destroy_zone(_sketch_maze().grid, Position(1, 1), Position(3, 3))
    session = BuilderSession(
        maze=Maze(
            grid=destroyed_grid,
            entry=Position(0, 0),
            exit=Position(4, 4),
            kind=MazeKind.SKETCH,
            id=None,
        ),
        cursor=Position(0, 0),
        tool=BuilderTool.RESTORE_ZONE,
    )

    result = apply_zone_operation(session, BuilderTool.RESTORE_ZONE, Position(1, 1), Position(3, 3))

    expected_grid = restore_zone(destroyed_grid, Position(1, 1), Position(3, 3))
    assert result.maze.grid == expected_grid


def test_apply_zone_operation_is_a_no_op_when_the_tool_is_break():
    session = _session_at(Position(0, 0), BuilderTool.BREAK)

    result = apply_zone_operation(session, BuilderTool.BREAK, Position(1, 1), Position(3, 3))

    assert result == session


def test_apply_zone_operation_is_a_no_op_when_the_tool_is_pass_through():
    session = _session_at(Position(0, 0), BuilderTool.PASS_THROUGH)

    result = apply_zone_operation(session, BuilderTool.PASS_THROUGH, Position(1, 1), Position(3, 3))

    assert result == session


def test_apply_zone_operation_leaves_the_cursor_unchanged():
    session = _session_at(Position(2, 2), BuilderTool.DESTROY_ZONE)

    result = apply_zone_operation(session, BuilderTool.DESTROY_ZONE, Position(0, 0), Position(1, 1))

    assert result.cursor == Position(2, 2)


def test_apply_zone_operation_dispatches_on_the_passed_in_tool_not_session_tool():
    # The whole point of taking `tool` as an explicit argument: a session
    # whose live `.tool` has drifted since press time (e.g. the user
    # switched tools mid-drag) must not change which operation runs --
    # only the `tool` argument decides.
    session = _session_at(Position(0, 0), BuilderTool.BREAK)  # live tool: BREAK

    result = apply_zone_operation(session, BuilderTool.DESTROY_ZONE, Position(1, 1), Position(3, 3))

    expected_grid = destroy_zone(session.maze.grid, Position(1, 1), Position(3, 3))
    assert result.maze.grid == expected_grid
    # `session.tool` itself is untouched by the dispatch.
    assert result.tool is BuilderTool.BREAK


def test_apply_zone_operation_does_not_mutate_the_original_session():
    session = _session_at(Position(0, 0), BuilderTool.DESTROY_ZONE)
    original_grid = session.maze.grid

    apply_zone_operation(session, BuilderTool.DESTROY_ZONE, Position(1, 1), Position(3, 3))

    assert session.maze.grid == original_grid


# -- start_builder_session (sanity, not otherwise covered here) -----------


def test_start_builder_session_defaults_to_the_break_tool():
    session = start_builder_session(_sketch_maze())

    assert session.tool is BuilderTool.BREAK
    assert session.cursor == session.maze.entry
