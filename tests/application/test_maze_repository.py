import pytest

from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.maze_id import MazeId


class _CompleteMazeRepository(MazeRepository):
    def save(self, maze: Maze, name: str) -> Maze:
        return maze

    def load(self, name: str, kind: MazeKind) -> Maze:
        raise NotImplementedError

    def find_by_id(self, maze_id: MazeId) -> Maze | None:
        return None


class _IncompleteMazeRepository(MazeRepository):
    def save(self, maze: Maze, name: str) -> Maze:
        return maze

    def load(self, name: str, kind: MazeKind) -> Maze:
        raise NotImplementedError

    # find_by_id intentionally omitted


def test_maze_repository_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        MazeRepository()


def test_complete_subclass_instantiates_and_is_a_maze_repository():
    repository = _CompleteMazeRepository()

    assert isinstance(repository, MazeRepository)


def test_incomplete_subclass_cannot_be_instantiated():
    with pytest.raises(TypeError):
        _IncompleteMazeRepository()
