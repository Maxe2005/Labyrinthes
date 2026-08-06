import pytest

from labyrinthes.adapters.storage.csv_maze_repository import CsvMazeRepository
from labyrinthes.adapters.storage.errors import InvalidMazeNameError
from labyrinthes.application.errors import MazeNotFoundError
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.maze_id import MazeId
from labyrinthes.domain.position import Position


def _maze(kind: MazeKind, maze_id: MazeId | None = None) -> Maze:
    return Maze(
        grid=Grid.filled(width=2, height=2),
        entry=Position(row=0, col=0),
        exit=Position(row=1, col=2),
        kind=kind,
        id=maze_id,
    )


@pytest.mark.parametrize("kind", [MazeKind.CLASSIC, MazeKind.SAVED_RANDOM])
def test_save_mints_a_maze_id_for_a_new_id_eligible_maze(tmp_path, kind):
    repository = CsvMazeRepository(root=tmp_path)
    maze = _maze(kind, maze_id=None)

    saved = repository.save(maze, "foo")

    assert saved.id is not None
    assert isinstance(saved.id, MazeId)


@pytest.mark.parametrize("kind", [MazeKind.CLASSIC, MazeKind.SAVED_RANDOM])
def test_save_carries_forward_an_existing_maze_id_unchanged(tmp_path, kind):
    repository = CsvMazeRepository(root=tmp_path)
    maze = _maze(kind, maze_id=MazeId(value="existing-id"))

    saved = repository.save(maze, "foo")

    assert saved.id == MazeId(value="existing-id")


@pytest.mark.parametrize("kind", [MazeKind.SKETCH, MazeKind.GENERATED])
def test_save_writes_no_maze_id_line_for_id_ineligible_kinds(tmp_path, kind):
    repository = CsvMazeRepository(root=tmp_path)
    maze = _maze(kind, maze_id=None)

    repository.save(maze, "foo")

    path = tmp_path / kind.value / "foo.csv"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 + maze.grid.height + 1


@pytest.mark.parametrize(
    "kind", [MazeKind.CLASSIC, MazeKind.SKETCH, MazeKind.SAVED_RANDOM, MazeKind.GENERATED]
)
def test_load_round_trips_a_saved_maze(tmp_path, kind):
    repository = CsvMazeRepository(root=tmp_path)
    maze = _maze(kind, maze_id=None)

    saved = repository.save(maze, "foo")
    loaded = repository.load("foo", kind)

    assert loaded == saved


def test_save_overwrites_an_existing_maze_with_different_content(tmp_path):
    repository = CsvMazeRepository(root=tmp_path)
    first = Maze(
        grid=Grid.filled(width=4, height=4),
        entry=Position(row=0, col=0),
        exit=Position(row=1, col=2),
        kind=MazeKind.SKETCH,
        id=None,
    )
    second = _maze(MazeKind.SKETCH, maze_id=None)  # a smaller grid

    repository.save(first, "foo")
    repository.save(second, "foo")
    loaded = repository.load("foo", MazeKind.SKETCH)

    # The second, smaller save must fully replace the first -- no stale
    # trailing rows left over from the larger previous grid.
    assert loaded.grid.width == second.grid.width
    assert loaded.grid.height == second.grid.height


def test_load_missing_maze_raises_maze_not_found_error(tmp_path):
    repository = CsvMazeRepository(root=tmp_path)

    with pytest.raises(MazeNotFoundError):
        repository.load("missing", MazeKind.CLASSIC)


def test_load_missing_maze_when_kind_folder_does_not_exist_raises_maze_not_found_error(tmp_path):
    repository = CsvMazeRepository(root=tmp_path)

    with pytest.raises(MazeNotFoundError):
        repository.load("missing", MazeKind.SAVED_RANDOM)


@pytest.mark.parametrize("kind", [MazeKind.CLASSIC, MazeKind.SAVED_RANDOM])
def test_find_by_id_returns_the_matching_maze(tmp_path, kind):
    repository = CsvMazeRepository(root=tmp_path)
    saved = repository.save(_maze(kind, maze_id=None), "foo")

    found = repository.find_by_id(saved.id)

    assert found == saved


def test_find_by_id_returns_none_when_nothing_matches(tmp_path):
    repository = CsvMazeRepository(root=tmp_path)
    repository.save(_maze(MazeKind.CLASSIC, maze_id=None), "foo")

    found = repository.find_by_id(MazeId(value="unknown-id"))

    assert found is None


def test_find_by_id_returns_none_when_no_kind_folders_exist_yet(tmp_path):
    repository = CsvMazeRepository(root=tmp_path)

    found = repository.find_by_id(MazeId(value="unknown-id"))

    assert found is None


def test_find_by_id_skips_an_unrelated_file_that_fails_to_parse(tmp_path):
    repository = CsvMazeRepository(root=tmp_path)
    saved = repository.save(_maze(MazeKind.CLASSIC, maze_id=None), "good")
    corrupt_path = tmp_path / "classic" / "corrupt.csv"
    corrupt_path.write_text("not,a,valid,maze,file\n", encoding="utf-8")

    found = repository.find_by_id(saved.id)

    assert found == saved


@pytest.mark.parametrize("name", ["", "a/b"])
def test_save_rejects_invalid_names(tmp_path, name):
    repository = CsvMazeRepository(root=tmp_path)
    maze = _maze(MazeKind.SKETCH, maze_id=None)

    with pytest.raises(InvalidMazeNameError):
        repository.save(maze, name)


@pytest.mark.parametrize("name", ["", "a/b"])
def test_load_rejects_invalid_names(tmp_path, name):
    repository = CsvMazeRepository(root=tmp_path)

    with pytest.raises(InvalidMazeNameError):
        repository.load(name, MazeKind.SKETCH)
