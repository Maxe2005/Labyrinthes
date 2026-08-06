"""Application-layer errors: not-found conditions raised by the ports.

Both subclass `LabyrinthesError` (`domain/errors.py`) — the project's one
typed exception hierarchy — rather than introducing a bespoke shape per port.
"""

from labyrinthes.domain.errors import LabyrinthesError


class MazeNotFoundError(LabyrinthesError):
    """Raised by `MazeRepository.load()` when no matching maze exists."""


class SettingNotFoundError(LabyrinthesError):
    """Raised by `SettingsRepository.get()` when no value is stored for the key."""
