"""Difficulty ordinal type.

The unified threshold formula is not this story's concern (Story 2.7) —
this only pins the ordinal shape.
"""

import enum


class Difficulty(enum.IntEnum):
    """Difficulty tier, 1–3."""

    ONE = 1
    TWO = 2
    THREE = 3
