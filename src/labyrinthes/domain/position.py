"""Position value object — shared by entry, exit, ball, and editing cursor."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    """A `(row, col)` location on a `Grid`.

    Not aware of any `Grid`'s size — bounds validation is a `Grid` concern.
    """

    row: int
    col: int
