"""Storage-adapter errors.

Subclasses `LabyrinthesError` (`domain/errors.py`) -- the project's one
typed exception hierarchy -- rather than introducing a bespoke shape here.
"""

from labyrinthes.domain.errors import LabyrinthesError


class InvalidMazeNameError(LabyrinthesError):
    """Raised when a maze `name` would break the on-disk `<name>.csv` mapping.

    Narrow on purpose: only empty names and path-separator-containing names
    are rejected here. Length/character-set limits and duplicate-name
    prevention are `BuilderService` concerns (Story 3.6), not this adapter's.
    """
