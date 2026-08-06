"""Application layer: persistence port interfaces, no concrete storage.

Imports nothing from `adapters/` or any UI framework (AD-1). Each port has
exactly one concrete implementation under `adapters/storage/` (Story 1.4/1.5).
"""

from labyrinthes.application.errors import MazeNotFoundError, SettingNotFoundError
from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.application.settings_repository import (
    SettingsRepository,
    SettingsScope,
    SettingValue,
)

__all__ = [
    "MazeNotFoundError",
    "MazeRepository",
    "SettingNotFoundError",
    "SettingsRepository",
    "SettingsScope",
    "SettingValue",
]
