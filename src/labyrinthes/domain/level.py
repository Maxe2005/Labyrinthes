"""Level ordinal type.

Partition-size/reveal-threshold logic is not this story's concern
(Story 2.6/2.7) — this only pins the ordinal shape.
"""

import enum


class Level(enum.IntEnum):
    """Progressive visibility level, 1–4, plus `MAX` above them all."""

    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    MAX = 5
