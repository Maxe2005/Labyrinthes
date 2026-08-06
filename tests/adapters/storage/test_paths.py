import pytest

from labyrinthes.adapters.storage.errors import InvalidMazeNameError
from labyrinthes.adapters.storage.paths import maze_file_path
from labyrinthes.domain.maze import MazeKind


@pytest.mark.parametrize(
    ("kind", "expected_subfolder"),
    [
        (MazeKind.CLASSIC, "classic"),
        (MazeKind.SKETCH, "sketch"),
        (MazeKind.SAVED_RANDOM, "saved-random"),
        (MazeKind.GENERATED, "generated"),
    ],
)
def test_maze_file_path_uses_one_subfolder_per_kind_value(tmp_path, kind, expected_subfolder):
    path = maze_file_path(tmp_path, kind, "foo")

    assert path == tmp_path / expected_subfolder / "foo.csv"


def test_maze_file_path_rejects_empty_name(tmp_path):
    with pytest.raises(InvalidMazeNameError):
        maze_file_path(tmp_path, MazeKind.CLASSIC, "")


@pytest.mark.parametrize("name", ["a/b", "/a", "a/", "a\\b"])
def test_maze_file_path_rejects_path_separators_in_name(tmp_path, name):
    with pytest.raises(InvalidMazeNameError):
        maze_file_path(tmp_path, MazeKind.CLASSIC, name)
