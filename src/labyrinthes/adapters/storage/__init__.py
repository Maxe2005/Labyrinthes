"""Storage adapters: the single `MazeRepository` implementation (Story 1.4).

Imports only `domain/`/`application/` -- never `adapters/tkinter/` (AD-1).
"""

from labyrinthes.adapters.storage.csv_maze_repository import CsvMazeRepository
from labyrinthes.adapters.storage.errors import InvalidMazeNameError
from labyrinthes.adapters.storage.maze_id_minting import mint_maze_id
from labyrinthes.adapters.storage.paths import DEFAULT_MAZES_ROOT, MAZE_FILE_SUFFIX, maze_file_path

__all__ = [
    "DEFAULT_MAZES_ROOT",
    "MAZE_FILE_SUFFIX",
    "CsvMazeRepository",
    "InvalidMazeNameError",
    "maze_file_path",
    "mint_maze_id",
]
