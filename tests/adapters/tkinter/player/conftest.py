"""Shared test doubles/fixtures for Player-screen tests (Story 2.1).

`FakeMazeRepository` is an in-memory `MazeRepository` -- no filesystem I/O
-- so `ClassicMazeGallery`/Player-screen tests never need a `tmp_path` just
to exercise the pager/jump/restart/play behavior against a repository.

`FakeSettingsRepository` (Story 2.2) is the equivalent in-memory
`SettingsRepository` double, for tests exercising `GenerateRandomDialog`'s
FR-4 size-bounds reads without a `tmp_path`-backed `JsonSettingsRepository`.

`saved_random_maze()` (Story 2.3) is `classic_maze()`'s `SAVED_RANDOM`
counterpart, for seeding `ClassicMazeGallery`'s combined-listing tests.
"""

import dataclasses
import uuid

import pytest

from labyrinthes.application.errors import MazeNotFoundError, SettingNotFoundError
from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.maze_id import MazeId
from labyrinthes.domain.position import Position

_ID_ELIGIBLE_KINDS = frozenset({MazeKind.CLASSIC, MazeKind.SAVED_RANDOM})


class FakeMazeRepository(MazeRepository):
    """In-memory `MazeRepository` test double, keyed by `(kind, name)`."""

    def __init__(self) -> None:
        self._store: dict[tuple[MazeKind, str], Maze] = {}

    def save(self, maze: Maze, name: str) -> Maze:
        # Mirrors `CsvMazeRepository.save()`'s own id-minting contract (Story
        # 1.4) so tests can assert on a freshly minted id, not just on kind.
        if maze.kind in _ID_ELIGIBLE_KINDS and maze.id is None:
            maze = dataclasses.replace(maze, id=MazeId(value=uuid.uuid4().hex))
        self._store[(maze.kind, name)] = maze
        return maze

    def load(self, name: str, kind: MazeKind) -> Maze:
        try:
            return self._store[(kind, name)]
        except KeyError:
            raise MazeNotFoundError(f"No {kind.value} maze named {name!r}") from None

    def find_by_id(self, maze_id: MazeId) -> Maze | None:
        for maze in self._store.values():
            if maze.id == maze_id:
                return maze
        return None

    def list_names(self, kind: MazeKind) -> list[str]:
        return sorted(name for (stored_kind, name) in self._store if stored_kind == kind)


def classic_maze(width: int, height: int) -> Maze:
    """A `CLASSIC` `Maze` of the given size, entry top-left, exit bottom-right."""
    return Maze(
        grid=Grid.filled(width=width, height=height),
        entry=Position(row=0, col=0),
        exit=Position(row=height - 1, col=width - 1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def saved_random_maze(width: int, height: int) -> Maze:
    """A `SAVED_RANDOM` `Maze` of the given size, entry top-left, exit bottom-right."""
    return Maze(
        grid=Grid.filled(width=width, height=height),
        entry=Position(row=0, col=0),
        exit=Position(row=height - 1, col=width - 1),
        kind=MazeKind.SAVED_RANDOM,
        id=None,
    )


@pytest.fixture
def fake_maze_repository() -> FakeMazeRepository:
    """A bare `FakeMazeRepository`, nothing seeded -- the empty-state case."""
    return FakeMazeRepository()


@pytest.fixture
def seeded_maze_repository() -> FakeMazeRepository:
    """A `FakeMazeRepository` pre-seeded with 3 classic mazes: alpha, bravo, charlie."""
    repository = FakeMazeRepository()
    repository.save(classic_maze(width=4, height=3), "alpha")
    repository.save(classic_maze(width=5, height=5), "bravo")
    repository.save(classic_maze(width=6, height=4), "charlie")
    return repository


@pytest.fixture
def seeded_maze_repository_with_saved_random() -> FakeMazeRepository:
    """`seeded_maze_repository`'s 3 classics, plus 2 saved-random mazes: delta, echo."""
    repository = FakeMazeRepository()
    repository.save(classic_maze(width=4, height=3), "alpha")
    repository.save(classic_maze(width=5, height=5), "bravo")
    repository.save(classic_maze(width=6, height=4), "charlie")
    repository.save(saved_random_maze(width=7, height=6), "delta")
    repository.save(saved_random_maze(width=8, height=7), "echo")
    return repository


class FakeSettingsRepository(SettingsRepository):
    """In-memory `SettingsRepository` test double, keyed by `(scope, key)`."""

    def __init__(self) -> None:
        self._store: dict[tuple[SettingsScope, str], object] = {}

    def get(self, scope: SettingsScope, key: str):
        try:
            return self._store[(scope, key)]
        except KeyError:
            raise SettingNotFoundError(f"No {scope.value} setting named {key!r}") from None

    def set(self, scope: SettingsScope, key: str, value) -> None:
        self._store[(scope, key)] = value


@pytest.fixture
def fake_settings_repository() -> FakeSettingsRepository:
    """A bare `FakeSettingsRepository`, nothing seeded -- the FR-4 defaults apply."""
    return FakeSettingsRepository()
