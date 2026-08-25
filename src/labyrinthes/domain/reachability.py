"""Reachability computation — pure BFS through open passages (Story 4.5).

Returns the set of cells that cannot be reached from the entry by following
open passages (walls that are broken). The maze's outer border is always
closed, so the search is naturally bounded.
"""

from __future__ import annotations

from collections import deque

from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze
from labyrinthes.domain.position import Position

__all__ = ["inaccessible_cells"]


def _neighbors(grid: Grid, position: Position) -> list[Position]:
    """Return playable neighbors reachable through open passages from `position`."""
    result = []
    row, col = position.row, position.col

    # Up: check if top wall is absent
    if row > 0:
        top_wall = grid.cell_at(Position(row, col))
        if not top_wall.has_top_wall:
            result.append(Position(row - 1, col))

    # Down: check if bottom wall (of current cell's top bit in next row) is absent
    if row < grid.height - 1:
        bottom_wall = grid.cell_at(Position(row + 1, col))
        if not bottom_wall.has_top_wall:
            result.append(Position(row + 1, col))

    # Left: check if left wall is absent
    if col > 0:
        left_wall = grid.cell_at(Position(row, col))
        if not left_wall.has_left_wall:
            result.append(Position(row, col - 1))

    # Right: check if right wall (of current cell's left bit in next col) is absent
    if col < grid.width - 1:
        right_wall = grid.cell_at(Position(row, col + 1))
        if not right_wall.has_left_wall:
            result.append(Position(row, col + 1))

    return result


def inaccessible_cells(maze: Maze, entry: Position | None) -> frozenset[Position]:
    """Return the set of playable cells unreachable from `entry` through open passages.

    If `entry` is None, returns an empty frozenset (no reachability computation).

    The search follows open passages: a move from cell A to adjacent cell B is
    allowed iff the wall between them is broken (absent). Border walls are
    always present by invariant, so the search never escapes the playable area.

    Returns a frozenset of Position for immutability (domain value object).
    """
    if entry is None:
        return frozenset()

    grid = maze.grid
    visited: set[Position] = set()
    queue: deque[Position] = deque()

    # Validate entry is within playable bounds
    if not (0 <= entry.row < grid.height and 0 <= entry.col < grid.width):
        # Entry out of bounds — nothing is reachable
        all_cells = {Position(r, c) for r in range(grid.height) for c in range(grid.width)}
        return frozenset(all_cells)

    visited.add(entry)
    queue.append(entry)

    while queue:
        current = queue.popleft()
        for neighbor in _neighbors(grid, current):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    # Inaccessible = all playable cells - visited
    all_cells = {Position(r, c) for r in range(grid.height) for c in range(grid.width)}
    inaccessible = all_cells - visited
    return frozenset(inaccessible)
