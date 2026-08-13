"""`MovementMode` -- how the ball advances through a maze (Story 2.5).

Two modes: `DISCRETE` (one cell per key press) and `SMOOTH` (continuous
movement, redirectable mid-cell). The member `.value` strings are what get
persisted as `game`-scoped settings, matching `SettingValue`'s string
convention.
"""

from __future__ import annotations

import enum

__all__ = ["MovementMode"]


class MovementMode(enum.Enum):
    """How one key press advances the ball: discrete (per cell) or smooth (continuous)."""

    DISCRETE = "discrete"
    SMOOTH = "smooth"
