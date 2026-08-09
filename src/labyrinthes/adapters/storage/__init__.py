"""Storage adapters: the single `MazeRepository`/`SettingsRepository` implementations
(Stories 1.4/1.5).

Imports only `domain/`/`application/` -- never `adapters/tkinter/` (AD-1).
"""

from labyrinthes.adapters.storage.csv_maze_repository import CsvMazeRepository
from labyrinthes.adapters.storage.errors import InvalidMazeNameError, InvalidSettingKeyError
from labyrinthes.adapters.storage.json_settings_repository import JsonSettingsRepository
from labyrinthes.adapters.storage.maze_id_minting import mint_maze_id
from labyrinthes.adapters.storage.paths import DEFAULT_MAZES_ROOT, MAZE_FILE_SUFFIX, maze_file_path
from labyrinthes.adapters.storage.settings_paths import (
    DEFAULT_SETTINGS_ROOT,
    SETTING_FILE_SUFFIX,
    setting_file_path,
)

__all__ = [
    "DEFAULT_MAZES_ROOT",
    "DEFAULT_SETTINGS_ROOT",
    "MAZE_FILE_SUFFIX",
    "SETTING_FILE_SUFFIX",
    "CsvMazeRepository",
    "InvalidMazeNameError",
    "InvalidSettingKeyError",
    "JsonSettingsRepository",
    "maze_file_path",
    "mint_maze_id",
    "setting_file_path",
]
