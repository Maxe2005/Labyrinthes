"""Filesystem layout for the maze CSV store.

One root directory (`DEFAULT_MAZES_ROOT`, overridable per `CsvMazeRepository`
instance), one subfolder per `MazeKind` named after `kind.value` (already the
intended English folder name: `classic`/`sketch`/`saved-random`/`generated`),
one `<name>.csv` file per maze. This is the single module Epic 4's migration
script also imports (AD-8) -- the path/naming scheme must not be duplicated
anywhere else.
"""

from pathlib import Path

from labyrinthes.adapters.storage.errors import InvalidMazeNameError
from labyrinthes.domain.maze import MazeKind

DEFAULT_MAZES_ROOT = Path("mazes")
MAZE_FILE_SUFFIX = ".csv"

_PATH_SEPARATORS = ("/", "\\")


def maze_file_path(root: Path, kind: MazeKind, name: str) -> Path:
    """The file path for maze `name` of `kind`, rooted at `root`.

    Raises `InvalidMazeNameError` for anything that would break the
    on-disk `<name>.csv` mapping: an empty name, or a name containing a
    path separator.
    """
    if not name:
        raise InvalidMazeNameError("Maze name must not be empty")
    if any(separator in name for separator in _PATH_SEPARATORS):
        raise InvalidMazeNameError(f"Maze name must not contain a path separator: {name!r}")
    return root / kind.value / f"{name}{MAZE_FILE_SUFFIX}"
