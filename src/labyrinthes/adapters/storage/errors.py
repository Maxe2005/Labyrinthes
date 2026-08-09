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


class InvalidSettingKeyError(LabyrinthesError):
    """Raised when a setting `key` would break the on-disk `<key>.json` mapping.

    Narrow on purpose: only empty keys and path-separator-containing keys are
    rejected here. Settings keys are programmer-chosen constants, not
    end-user input, so this is a defensive floor, not a general validation
    feature.
    """
