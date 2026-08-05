"""Grid value object — a rectangular arrangement of `Cell`s.

Internally stores `(height + 1)` rows x `(width + 1)` columns — one extra
padding row/column, mirroring the legacy `grille_pleine`'s closed-border
scheme. This is load-bearing for lossless round-trips through the maze
CSV format (NFR2/AD-6) in Story 1.4: the extra row/column exists purely
so the right-most/bottom-most real cells can express a right/bottom wall
via the *padding* cell's left/top bit (right and bottom walls are never
stored directly on a cell; they're always read off a neighbor).

`width`/`height` are the *playable* dimensions a user configures — not
the raw array size. No downstream `-1` compensation should ever be
needed to get from one to the other.
"""

from dataclasses import dataclass

from labyrinthes.domain.cell import Cell
from labyrinthes.domain.errors import DomainValidationError
from labyrinthes.domain.position import Position


@dataclass(frozen=True)
class Grid:
    """A rectangular grid of `Cell`s, with a closed-border padding row/column."""

    cells: tuple[tuple[Cell, ...], ...]

    def __post_init__(self) -> None:
        if not self.cells or not self.cells[0]:
            raise DomainValidationError("Grid.cells must be a non-empty rectangular grid of Cell")
        row_length = len(self.cells[0])
        if any(len(row) != row_length for row in self.cells):
            raise DomainValidationError(
                "Grid.cells must be rectangular: every row must have the same length"
            )

    @property
    def height(self) -> int:
        """The playable height — the raw array has one extra padding row."""
        return len(self.cells) - 1

    @property
    def width(self) -> int:
        """The playable width — the raw array has one extra padding column."""
        return len(self.cells[0]) - 1

    def cell_at(self, position: Position) -> Cell:
        """Return the `Cell` at `position`, addressed by raw grid indices.

        Raw indices include the closed-border padding row/column (see module
        docstring) — `position.row == height` or `position.col == width` are
        valid, in-range accesses that return a padding `Cell`, not an error.
        """
        row_in_range = 0 <= position.row < len(self.cells)
        col_in_range = row_in_range and 0 <= position.col < len(self.cells[0])
        if not (row_in_range and col_in_range):
            raise DomainValidationError(f"Position {position!r} is out of range for this grid")
        return self.cells[position.row][position.col]

    @staticmethod
    def filled(width: int, height: int) -> "Grid":
        """Build an all-filled grid of the given playable size, closed border in place.

        Real cells are `"3"` (top and left walls — fully walled, as a maze
        generator's starting point to carve passages into). The padding row
        is `"1"` (top wall only), the padding column is `"2"` (left wall
        only), and the corner cell is `"0"`.
        """
        if width <= 0 or height <= 0:
            raise DomainValidationError(
                f"Grid.filled requires width > 0 and height > 0, got width={width}, height={height}"
            )

        rows = []
        for _ in range(height):
            real_cells = tuple(Cell("3") for _ in range(width))
            rows.append(real_cells + (Cell("2"),))

        padding_row = tuple(Cell("1") for _ in range(width)) + (Cell("0"),)
        rows.append(padding_row)

        return Grid(cells=tuple(rows))
