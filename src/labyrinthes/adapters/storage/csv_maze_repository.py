"""`CsvMazeRepository` -- the single concrete `MazeRepository` (Story 1.4).

One CSV file per maze, one folder per `MazeKind`, under a single declared
root (see `paths.py`). `find_by_id` has no id index: it scans each
id-eligible kind's directory and opens every file's header to compare --
acceptable at this milestone's expected maze counts (tens, not thousands).
"""

import dataclasses
from pathlib import Path

from labyrinthes.adapters.storage.csv_maze_format import read_maze_csv, write_maze_csv
from labyrinthes.adapters.storage.maze_id_minting import mint_maze_id
from labyrinthes.adapters.storage.paths import DEFAULT_MAZES_ROOT, MAZE_FILE_SUFFIX, maze_file_path
from labyrinthes.application.errors import MazeNotFoundError
from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.domain.errors import LabyrinthesError
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.maze_id import MazeId

_ID_ELIGIBLE_KINDS = frozenset({MazeKind.CLASSIC, MazeKind.SAVED_RANDOM})
# Stable iteration order for find_by_id's directory scan.
_ID_LOOKUP_KINDS = (MazeKind.CLASSIC, MazeKind.SAVED_RANDOM)


class CsvMazeRepository(MazeRepository):
    """`MazeRepository` backed by one CSV file per maze under `root`."""

    def __init__(self, root: Path = DEFAULT_MAZES_ROOT) -> None:
        self._root = root

    def save(self, maze: Maze, name: str) -> Maze:
        if maze.kind in _ID_ELIGIBLE_KINDS and maze.id is None:
            maze = dataclasses.replace(maze, id=mint_maze_id())
        path = maze_file_path(self._root, maze.kind, name)
        write_maze_csv(path, maze)
        return maze

    def load(self, name: str, kind: MazeKind) -> Maze:
        path = maze_file_path(self._root, kind, name)
        if not path.is_file():
            raise MazeNotFoundError(f"No {kind.value} maze named {name!r}")
        return read_maze_csv(path, kind)

    def find_by_id(self, maze_id: MazeId) -> Maze | None:
        for kind in _ID_LOOKUP_KINDS:
            directory = self._root / kind.value
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob(f"*{MAZE_FILE_SUFFIX}")):
                try:
                    maze = read_maze_csv(path, kind)
                except (OSError, ValueError, LabyrinthesError):
                    # An unrelated file failing to parse (corrupt, hand-edited,
                    # mid-write) must not abort the whole id lookup -- skip it
                    # and keep scanning the rest of this kind's directory.
                    continue
                if maze.id == maze_id:
                    return maze
        return None

    def list_names(self, kind: MazeKind) -> list[str]:
        directory = self._root / kind.value
        if not directory.is_dir():
            return []
        return sorted(
            path.stem for path in directory.glob(f"*{MAZE_FILE_SUFFIX}") if path.is_file()
        )
