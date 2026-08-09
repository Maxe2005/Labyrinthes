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

    def list_names(self, kind: MazeKind) -> list[str]:
        return []


class _IncompleteMazeRepositoryMissingFindById(MazeRepository):
    def save(self, maze: Maze, name: str) -> Maze:
        return maze

    def load(self, name: str, kind: MazeKind) -> Maze:
        raise NotImplementedError

    # find_by_id intentionally omitted

    def list_names(self, kind: MazeKind) -> list[str]:
        return []


class _IncompleteMazeRepositoryMissingListNames(MazeRepository):
    def save(self, maze: Maze, name: str) -> Maze:
        return maze

    def load(self, name: str, kind: MazeKind) -> Maze:
        raise NotImplementedError

    def find_by_id(self, maze_id: MazeId) -> Maze | None:
        return None

    # list_names intentionally omitted


def test_maze_repository_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        MazeRepository()


def test_complete_subclass_instantiates_and_is_a_maze_repository():
    repository = _CompleteMazeRepository()

    assert isinstance(repository, MazeRepository)


def test_subclass_missing_only_find_by_id_cannot_be_instantiated():
    with pytest.raises(TypeError):
        _IncompleteMazeRepositoryMissingFindById()


def test_subclass_missing_only_list_names_cannot_be_instantiated():
    with pytest.raises(TypeError):
        _IncompleteMazeRepositoryMissingListNames()
