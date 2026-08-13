"""`MovementSpeed` + `cell_crossing_duration` -- the one speed setting (Story 2.5).

The single configurable speed tier (`SLOW`/`NORMAL`/`FAST`), mapped to a
pure `Duration` for crossing one cell. Both `DISCRETE` and `SMOOTH` movement
modes share this same mapping, so a speed change is reflected identically in
both modes' tick/animation rate.

`NORMAL == 225ms` reproduces the legacy default: `vitesse deplacement (45)`
ms per sub-step times `decoupe du deplacement (5)` sub-steps per cell. The
`SLOW`/`FAST` tiers are this story's own design choice; the mapping below is
the single source of truth and keeps every `Duration` non-negative.
"""

from __future__ import annotations

import enum

from labyrinthes.domain.duration import Duration

__all__ = ["MovementSpeed", "cell_crossing_duration"]


class MovementSpeed(enum.Enum):
    """The speed tier for crossing a single cell."""

    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"


_DURATIONS: dict[MovementSpeed, int] = {
    MovementSpeed.SLOW: 375,
    MovementSpeed.NORMAL: 225,
    MovementSpeed.FAST: 150,
}


def cell_crossing_duration(speed: MovementSpeed) -> Duration:
    """How long it takes the ball to cross exactly one cell at `speed`."""
    return Duration(milliseconds=_DURATIONS[speed])
