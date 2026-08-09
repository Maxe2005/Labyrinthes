"""Application-layer errors raised by the ports: not-found conditions and
corrupt/malformed persisted content.

All four subclass `LabyrinthesError` (`domain/errors.py`) — the project's
one typed exception hierarchy — rather than introducing a bespoke shape per
port.
"""

from labyrinthes.domain.errors import LabyrinthesError


class MazeNotFoundError(LabyrinthesError):
    """Raised by `MazeRepository.load()` when no matching maze exists."""


class MazeCorruptError(LabyrinthesError):
    """Raised when a maze's persisted content can't be parsed into a `Maze`.

    A port-level failure mode ("the port cannot return a valid value"), the
    same category as `MazeNotFoundError` -- not an adapter-implementation
    detail like `adapters/storage/errors.py`'s `InvalidMazeNameError`, which
    validates the on-disk name mapping rather than the content itself. Any
    future second `MazeRepository` implementation should raise this same
    error for unreadable content.
    """


class SettingNotFoundError(LabyrinthesError):
    """Raised by `SettingsRepository.get()` when no value is stored for the key."""


class SettingCorruptError(LabyrinthesError):
    """Raised when a setting's persisted content can't be parsed into a value.

    Same layering rationale as `MazeCorruptError`: a port-level failure
    mode, not an adapter-implementation detail.
    """
