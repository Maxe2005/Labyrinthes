import dataclasses

import pytest

from labyrinthes.domain.errors import DomainValidationError
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.maze_id import MazeId
from labyrinthes.domain.position import Position


def _grid() -> Grid:
    return Grid.filled(width=4, height=3)


@pytest.mark.parametrize("kind", [MazeKind.CLASSIC, MazeKind.SAVED_RANDOM])
def test_id_eligible_kinds_accept_none_id(kind):
    maze = Maze(
        grid=_grid(),
        entry=Position(row=0, col=0),
        exit=Position(row=2, col=3),
        kind=kind,
        id=None,
    )

    assert maze.id is None


@pytest.mark.parametrize("kind", [MazeKind.CLASSIC, MazeKind.SAVED_RANDOM])
def test_id_eligible_kinds_accept_a_maze_id(kind):
    maze = Maze(
        grid=_grid(),
        entry=Position(row=0, col=0),
        exit=Position(row=2, col=3),
        kind=kind,
        id=MazeId(value="abc"),
    )

    assert maze.id == MazeId(value="abc")


@pytest.mark.parametrize("kind", [MazeKind.SKETCH, MazeKind.GENERATED])
def test_id_ineligible_kinds_reject_a_maze_id(kind):
    with pytest.raises(DomainValidationError):
        Maze(
            grid=_grid(),
            entry=Position(row=0, col=0),
            exit=Position(row=2, col=3),
            kind=kind,
            id=MazeId(value="abc"),
        )


@pytest.mark.parametrize("kind", [MazeKind.SKETCH, MazeKind.GENERATED])
def test_id_ineligible_kinds_accept_none_id(kind):
    maze = Maze(
        grid=_grid(),
        entry=Position(row=0, col=0),
        exit=Position(row=2, col=3),
        kind=kind,
        id=None,
    )

    assert maze.id is None


def test_maze_is_immutable():
    maze = Maze(
        grid=_grid(),
        entry=Position(row=0, col=0),
        exit=Position(row=2, col=3),
        kind=MazeKind.SKETCH,
        id=None,
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        maze.id = MazeId(value="abc")


@pytest.mark.parametrize(
    "entry",
    [Position(row=-1, col=0), Position(row=99, col=0)],
)
def test_maze_rejects_entry_out_of_grid_bounds(entry):
    with pytest.raises(DomainValidationError):
        Maze(
            grid=_grid(),
            entry=entry,
            exit=Position(row=2, col=3),
            kind=MazeKind.SKETCH,
            id=None,
        )


@pytest.mark.parametrize(
    "exit_",
    [Position(row=0, col=-1), Position(row=0, col=99)],
)
def test_maze_rejects_exit_out_of_grid_bounds(exit_):
    with pytest.raises(DomainValidationError):
        Maze(
            grid=_grid(),
            entry=Position(row=0, col=0),
            exit=exit_,
            kind=MazeKind.SKETCH,
            id=None,
        )
