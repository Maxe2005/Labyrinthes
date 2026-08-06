"""Application-shell errors.

Subclasses `LabyrinthesError` (`domain/errors.py`) -- the project's one
typed exception hierarchy -- rather than introducing a bespoke shape here.
"""

from labyrinthes.domain.errors import LabyrinthesError


class UnregisteredScreenError(LabyrinthesError):
    """Raised when `Router.navigate()` targets a `ScreenId` with no registered `mount`.

    Narrow on purpose: this only guards against navigating to a screen that
    was never `register()`-ed. It is a typed error rather than a bare
    `KeyError` so callers can catch it specifically without also swallowing
    unrelated lookup failures.
    """
