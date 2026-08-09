"""Pure random-maze generation: an iterative randomized DFS backtracker.

`generate_random_maze` carves a spanning tree over a `width` x `height`
grid of real cells starting from `entry`, using the same wall-bit
semantics `Grid.filled`/`Cell` already define (see module docstrings
there): a "north" carve clears the top-wall bit on the *current* cell, a
"south" carve clears it on the *neighbor*; a "west" carve clears the
left-wall bit on the *current* cell, an "east" carve clears it on the
*neighbor*. The outer closed border (`Grid`'s padding row/column) is never
touched -- only real cells (`row in [0, height)`, `col in [0, width)`) are
ever carved into.

Deliberately an *iterative* stack-of-the-current-path backtracker, never
recursive (a maze up to 50x35 = 1750 cells would risk Python's recursion
limit), and deliberately *not* the legacy algorithm's random-frontier-pick
(Prim's-style) backtracking -- see the story's Design Notes for why a
single post-generation BFS-farthest-cell exit is chosen over the legacy's
border-dead-end/out-of-grid exit convention.

This module knows nothing about the FR-4 3-50/3-35 *policy* bounds
(`maze_size_bounds.py`) -- it only rejects structurally invalid input
(`width <= 0`, `height <= 0`, or `entry` outside the grid).
"""

from __future__ import annotations

import random
from collections import deque

from labyrinthes.domain.cell import Cell
from labyrinthes.domain.errors import DomainValidationError
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.position import Position

__all__ = ["generate_random_maze", "validate_start_position"]

# (row-delta, col-delta) for north/south/west/east -- the order candidates
# are considered in before `rng` picks one; deterministic given `rng`'s
# own sequence, not a source of extra randomness itself.
_DIRECTIONS: tuple[tuple[int, int], ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))

_TOP_WALL_BIT = 1
_LEFT_WALL_BIT = 2


def generate_random_maze(width: int, height: int, entry: Position, rng: random.Random) -> Maze:
    """A solvable `Maze` (`kind=GENERATED`, `id=None`) carved by a randomized DFS.

    Every real cell is reachable from `entry` by construction (the carve
    only ever visits an unvisited cell, producing a spanning tree -- no
    disconnected pockets are possible). The exit is the cell reached at
    maximum BFS distance from `entry` over the carved passages, ties
    broken by BFS visitation order, so the result is deterministic for a
    given `rng` sequence.

    Raises `DomainValidationError` for structurally invalid input:
    `width <= 0`, `height <= 0`, or `entry` outside `[0, width) x [0, height)`.
    This is *not* where the FR-4 3-50/3-35 policy bounds are enforced --
    see `maze_size_bounds.validate_dimensions` for that, a separate
    UI/settings concern.
    """
    if width <= 0 or height <= 0:
        raise DomainValidationError(
            f"generate_random_maze requires width > 0 and height > 0, "
            f"got width={width}, height={height}"
        )
    if not (0 <= entry.col < width and 0 <= entry.row < height):
        raise DomainValidationError(f"entry {entry!r} is outside the {width}x{height} grid")

    values = _carve_spanning_tree(width, height, entry, rng)
    grid = _build_grid(values, width, height)
    exit_position = _farthest_cell(grid, entry, width, height)

    return Maze(grid=grid, entry=entry, exit=exit_position, kind=MazeKind.GENERATED, id=None)


def _carve_spanning_tree(
    width: int, height: int, entry: Position, rng: random.Random
) -> list[list[int]]:
    """Randomized iterative DFS backtracker, returning each real cell's wall-bit int.

    `values[row][col]` starts at `3` (both bits set, fully walled -- same
    starting point as `Grid.filled`) and only ever has bits cleared, never
    set, so an already-open wall can never be re-closed.
    """
    values = [[3] * width for _ in range(height)]
    visited = [[False] * width for _ in range(height)]
    visited[entry.row][entry.col] = True
    # The backtracking stack holds the *current path* from `entry`, popped
    # on dead ends -- not a frontier of reachable-but-uncarved cells
    # (that would be Prim's-style, the legacy convention this deliberately
    # does not reproduce).
    stack: list[tuple[int, int]] = [(entry.row, entry.col)]

    while stack:
        row, col = stack[-1]
        candidates = [
            (dr, dc, row + dr, col + dc)
            for dr, dc in _DIRECTIONS
            if 0 <= row + dr < height and 0 <= col + dc < width and not visited[row + dr][col + dc]
        ]
        if not candidates:
            stack.pop()
            continue

        dr, dc, next_row, next_col = candidates[rng.randrange(len(candidates))]
        if dr == -1:  # north: current cell's top wall
            values[row][col] &= ~_TOP_WALL_BIT
        elif dr == 1:  # south: neighbor's top wall
            values[next_row][next_col] &= ~_TOP_WALL_BIT
        elif dc == -1:  # west: current cell's left wall
            values[row][col] &= ~_LEFT_WALL_BIT
        else:  # east: neighbor's left wall
            values[next_row][next_col] &= ~_LEFT_WALL_BIT

        visited[next_row][next_col] = True
        stack.append((next_row, next_col))

    return values


def _build_grid(values: list[list[int]], width: int, height: int) -> Grid:
    """A `Grid` from carved real-cell wall-bit `values`, padding row/column intact.

    Mirrors `Grid.filled`'s own padding construction exactly (padding
    column `"2"`, padding row `"1"`, corner `"0"`) -- carving never
    touches these, only the real `width`x`height` region.
    """
    rows = []
    for row in range(height):
        real_cells = tuple(Cell(str(values[row][col])) for col in range(width))
        rows.append(real_cells + (Cell("2"),))
    padding_row = tuple(Cell("1") for _ in range(width)) + (Cell("0"),)
    rows.append(padding_row)
    return Grid(cells=tuple(rows))


def _open_neighbors(grid: Grid, position: Position, width: int, height: int):
    """Every real-cell neighbor of `position` reachable through an open (carved) wall."""
    row, col = position.row, position.col
    for dr, dc in _DIRECTIONS:
        next_row, next_col = row + dr, col + dc
        if not (0 <= next_row < height and 0 <= next_col < width):
            continue
        if dr == -1:  # north: passage iff current cell's top wall is clear
            passage_open = not grid.cell_at(Position(row=row, col=col)).has_top_wall
        elif dr == 1:  # south: passage iff neighbor's top wall is clear
            passage_open = not grid.cell_at(Position(row=next_row, col=next_col)).has_top_wall
        elif dc == -1:  # west: passage iff current cell's left wall is clear
            passage_open = not grid.cell_at(Position(row=row, col=col)).has_left_wall
        else:  # east: passage iff neighbor's left wall is clear
            passage_open = not grid.cell_at(Position(row=next_row, col=next_col)).has_left_wall
        if passage_open:
            yield Position(row=next_row, col=next_col)


def _farthest_cell(grid: Grid, entry: Position, width: int, height: int) -> Position:
    """The cell at maximum BFS distance from `entry` over the carved passages.

    Ties are broken by BFS visitation order: the last cell dequeued is
    always at the maximum distance reached, and which cell that is is
    fully determined by `entry` and the carved grid -- deterministic, no
    `rng` involved here.
    """
    visited = {entry}
    queue: deque[Position] = deque([entry])
    farthest = entry
    while queue:
        current = queue.popleft()
        farthest = current
        for neighbor in _open_neighbors(grid, current, width, height):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return farthest


def validate_start_position(width: int, height: int, position: Position) -> list[str]:
    """Human-readable error messages for `position` outside `[0, width) x [0, height)`.

    Returns `[]` when both `position.col`/`position.row` are in range.
    Pure shape-checking against the *given* `width`/`height` -- callers
    (e.g. `GenerateRandomDialog`) are responsible for passing the
    currently-entered dimensions, not a stale last-confirmed pair.
    """
    errors: list[str] = []
    if not (0 <= position.col < width):
        errors.append(f"Start column must be between 0 and {width - 1}.")
    if not (0 <= position.row < height):
        errors.append(f"Start row must be between 0 and {height - 1}.")
    return errors
