"""Level visibility engine -- pure, immutable progressive-visibility rules.

Five progressive-visibility Levels (Story 2.6), all derived from the same
0/1/2/3 grid (no separate abstraction layer):

- ONE: the whole grid is always visible (the Story 2.4 baseline).
- TWO: the maze is split into rectangular partitions; partitions the ball
  has entered stay shown until the number of visited partitions crosses a
  reveal threshold, then all hide again and accumulation restarts from the
  current one.
- THREE: only the partition the ball is currently inside is visible.
- FOUR: walls stay invisible until the ball collides with one; past a
  discovered-wall threshold all discovered walls hide again.
- MAX: all interior walls are permanently invisible; the playable-area
  outer contour is the only navigation aid (shown at start, re-shown on
  each collision, hidden again on the next move -- the legacy
  `contours_visibles` semantics).

`LevelVisibility` is a frozen dataclass advanced by the pure functions
`initial_level_visibility`, `advance_visibility`, and `note_collision`, so
a visibility *change* is exactly an object-identity change -- the screen
redraws structure only then. No Tk, no wall-clock reads, no repository
access (AD-1..AD-3, NFR1).

`Wall` addresses a wall segment in **raw** grid coordinates (`0..grid.height`
x `0..grid.width`, the space `MazeCanvas._draw_walls` draws in). Partitions
live in **playable** coordinates (`0..grid.width` x `0..grid.height`), so
`partition_grid` is a direct port of the legacy `decoupage_du_lab` on the
playable dimensions -- no `-1` compensation is reintroduced.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from labyrinthes.domain.difficulty import Difficulty
from labyrinthes.domain.errors import DomainValidationError
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level import Level
from labyrinthes.domain.maze import Maze
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.position import Position

__all__ = [
    "LevelVisibility",
    "Partition",
    "Wall",
    "advance_visibility",
    "initial_level_visibility",
    "is_border_wall",
    "note_collision",
    "partition_grid",
    "partition_size_for_difficulty",
    "reveal_threshold",
    "show_contour",
    "total_interior_walls",
    "visible_walls",
]


@dataclass(frozen=True)
class Wall:
    """One wall segment, in raw grid coordinates (`row`/`col` range over
    `0..grid.height`/`0..grid.width`), identified by its `side`."""

    row: int
    col: int
    side: Literal["top", "left"]

    def __post_init__(self) -> None:
        if self.side not in ("top", "left"):
            raise DomainValidationError(f"Invalid wall side: {self.side!r}")


@dataclass(frozen=True)
class Partition:
    """A rectangular partition of the playable area, `bottom_right` exclusive."""

    top_left: Position
    bottom_right: Position

    def __post_init__(self) -> None:
        if self.top_left.row >= self.bottom_right.row or self.top_left.col >= self.bottom_right.col:
            raise DomainValidationError(f"Degenerate partition: {self!r}")


@dataclass(frozen=True)
class LevelVisibility:
    """The visibility state of one run, entirely determined by the current
    Level/Difficulty and the ball's movement/collision history."""

    level: Level
    difficulty: Difficulty
    partition_size: tuple[int, int]
    partitions: tuple[Partition, ...]
    visited: frozenset[int]
    current_partition: int
    discovered_walls: frozenset[Wall]
    contour_shown: bool
    total_interior_walls: int


def partition_size_for_difficulty(
    width: int, height: int, difficulty: Difficulty
) -> tuple[int, int]:
    """Square partition size `(cols, rows)` for the playable `width`/`height`.

    Faithful port of the legacy `init_taille_partition_par_difficultées`:
    `D1 -> petit_cote//2`, `D2 -> grand_cote//4`, `D3 -> grand_cote//8`,
    clamped to a minimum of 2 on each axis.
    """
    grand_cote = max(width, height)
    petit_cote = min(width, height)
    if difficulty is Difficulty.ONE:
        raw = petit_cote // 2
    elif difficulty is Difficulty.TWO:
        raw = grand_cote // 4
    else:
        raw = grand_cote // 8
    size = max(2, raw)
    return (size, size)


def partition_grid(
    width: int, height: int, partition_cols: int, partition_rows: int
) -> tuple[Partition, ...]:
    """The flat `Partition` tiling of the playable area, row-major.

    Faithful port of the legacy `decoupage_du_lab` (its remainder-edge
    `x_modif`/`y_modif` adjustments included) operating on the *playable*
    dimensions. The `bottom_right` coordinate is exclusive. Legacy stored
    its tuples as `(x, y) = (col, row)`; this port translates them into
    `Position(row, col)`.
    """
    partitions: list[Partition] = []

    def _x_modif() -> int:
        return (
            1 if width % partition_cols != 0 and width % partition_cols < partition_cols / 2 else 0
        )

    y_modif = (
        1 if height % partition_rows != 0 and height % partition_rows < partition_rows / 2 else 0
    )
    o = -1
    for o in range((height // partition_rows) - y_modif):
        x_modif = _x_modif()
        a = -1
        for a in range((width // partition_cols) - x_modif):
            partitions.append(
                Partition(
                    Position(o * partition_rows, a * partition_cols),
                    Position((o + 1) * partition_rows, (a + 1) * partition_cols),
                )
            )
        if width % partition_cols != 0:
            partitions.append(
                Partition(
                    Position(o * partition_rows, (a + 1) * partition_cols),
                    Position(
                        (o + 1) * partition_rows,
                        ((a + 1 + x_modif) * partition_cols) + (width % partition_cols),
                    ),
                )
            )
    if height % partition_rows != 0:
        x_modif = _x_modif()
        a = -1
        for a in range((width // partition_cols) - x_modif):
            partitions.append(
                Partition(
                    Position((o + 1) * partition_rows, a * partition_cols),
                    Position(
                        ((o + 1 + y_modif) * partition_rows) + (height % partition_rows),
                        (a + 1) * partition_cols,
                    ),
                )
            )
        if width % partition_cols != 0:
            partitions.append(
                Partition(
                    Position((o + 1) * partition_rows, (a + 1) * partition_cols),
                    Position(
                        ((o + 1 + y_modif) * partition_rows) + (height % partition_rows),
                        ((a + 1 + x_modif) * partition_cols) + (width % partition_cols),
                    ),
                )
            )
    return tuple(partitions)


def reveal_threshold(axis_counts: tuple[int, int], difficulty: Difficulty) -> int:
    """The single shared reveal threshold, `round(cols*rows / (difficulty+1))`.

    Applied to both Level 2's visited-partition count and Level 4's
    discovered-wall count (Level 4 passes its `total_interior_walls` as the
    `(count, 1)` axis pair), so the legacy FR-13 formula inconsistency is
    not reproduced. Story 2.7 finalizes this function.
    """
    axis_cols, axis_rows = axis_counts
    return round(axis_cols * axis_rows / (difficulty + 1))


def is_border_wall(grid: Grid, wall: Wall) -> bool:
    """`True` for a wall segment on the playable-area contour."""
    if wall.side == "top":
        return wall.row == 0 or wall.row == grid.height
    return wall.col == 0 or wall.col == grid.width


def total_interior_walls(grid: Grid) -> int:
    """The count of all non-border wall segments (the Level-4 threshold base)."""
    count = 0
    for row in range(grid.height + 1):
        for col in range(grid.width + 1):
            cell = grid.cell_at(Position(row=row, col=col))
            if cell.has_top_wall and not is_border_wall(grid, Wall(row, col, "top")):
                count += 1
            if cell.has_left_wall and not is_border_wall(grid, Wall(row, col, "left")):
                count += 1
    return count


def _blocked_wall(position: Position, direction: Direction) -> Wall:
    """The raw-coordinate `Wall` a blocked move from `position` in `direction`
    runs into (see the Code Map's mapping)."""
    if direction is Direction.UP:
        return Wall(position.row, position.col, "top")
    if direction is Direction.DOWN:
        return Wall(position.row + 1, position.col, "top")
    if direction is Direction.LEFT:
        return Wall(position.row, position.col, "left")
    return Wall(position.row, position.col + 1, "left")


def _partition_index(partitions: tuple[Partition, ...], position: Position) -> int:
    for index, partition in enumerate(partitions):
        if (
            partition.top_left.row <= position.row < partition.bottom_right.row
            and partition.top_left.col <= position.col < partition.bottom_right.col
        ):
            return index
    raise DomainValidationError(f"Position {position!r} is outside every partition")


def _partition_counts(partitions: tuple[Partition, ...]) -> tuple[int, int]:
    """The partition-grid `(cols, rows)` counts, derived from the flat tiling."""
    if not partitions:
        return (0, 0)
    first_row_top = partitions[0].top_left.row
    cols = sum(1 for p in partitions if p.top_left.row == first_row_top)
    return (cols, len(partitions) // cols)


def initial_level_visibility(
    maze: Maze, level: Level, difficulty: Difficulty, position: Position
) -> LevelVisibility:
    """A fresh visibility state for `level` at `position`.

    Partitions are sized per `difficulty`; the ball's partition is the
    `current_partition` and the only visited one (Levels 2/3 start showing
    the ball's partition). Discovered walls start empty; the contour starts
    shown for Level Max.
    """
    partition_size = partition_size_for_difficulty(maze.grid.width, maze.grid.height, difficulty)
    partitions = partition_grid(maze.grid.width, maze.grid.height, *partition_size)
    current = _partition_index(partitions, position)
    return LevelVisibility(
        level=level,
        difficulty=difficulty,
        partition_size=partition_size,
        partitions=partitions,
        visited=frozenset({current}),
        current_partition=current,
        discovered_walls=frozenset(),
        contour_shown=level is Level.MAX,
        total_interior_walls=total_interior_walls(maze.grid) if level is Level.FOUR else 0,
    )


def advance_visibility(
    visibility: LevelVisibility, maze: Maze, position: Position
) -> LevelVisibility:
    """`visibility` after the ball reaches `position` (a leg commit).

    Level 2 adds the newly-entered partition to the visited set and, past
    the reveal threshold, clears it down to only the current partition.
    Level 3 makes the ball's partition the sole visible one. Level Max
    hides the navigation contour once the ball moves. Levels 1/4 are
    no-ops. Returns `visibility` unchanged when nothing visible changes.
    """
    if visibility.level is Level.TWO:
        current = _partition_index(visibility.partitions, position)
        if current in visibility.visited:
            if current == visibility.current_partition:
                return visibility
            return replace(visibility, current_partition=current)
        visited = visibility.visited | {current}
        threshold = reveal_threshold(
            _partition_counts(visibility.partitions), visibility.difficulty
        )
        if len(visited) > threshold:
            visited = frozenset({current})
        return replace(visibility, visited=visited, current_partition=current)
    if visibility.level is Level.THREE:
        current = _partition_index(visibility.partitions, position)
        if current == visibility.current_partition:
            return visibility
        return replace(visibility, current_partition=current, visited=frozenset({current}))
    if visibility.level is Level.MAX:
        if not visibility.contour_shown:
            return visibility
        return replace(visibility, contour_shown=False)
    return visibility


def note_collision(
    visibility: LevelVisibility, maze: Maze, position: Position, direction: Direction
) -> LevelVisibility:
    """`visibility` after a blocked move against the wall in `direction`.

    Level 4 adds the collided interior wall to the discovered set (border
    walls are never discovered -- the contour already shows them) and, past
    the discovered-wall threshold, clears it down to just that wall. Level
    Max re-shows the navigation contour on a collision. Levels 1/2/3 are
    no-ops. Idempotent: an already-discovered or border wall is a no-op.
    """
    if visibility.level is Level.FOUR:
        wall = _blocked_wall(position, direction)
        if is_border_wall(maze.grid, wall) or wall in visibility.discovered_walls:
            return visibility
        discovered = visibility.discovered_walls | {wall}
        threshold = reveal_threshold((visibility.total_interior_walls, 1), visibility.difficulty)
        if len(discovered) > threshold:
            discovered = frozenset({wall})
        return replace(visibility, discovered_walls=discovered)
    if visibility.level is Level.MAX:
        if visibility.contour_shown:
            return visibility
        return replace(visibility, contour_shown=True)
    return visibility


def _all_walls(grid: Grid) -> frozenset[Wall]:
    walls: set[Wall] = set()
    for row in range(grid.height + 1):
        for col in range(grid.width + 1):
            cell = grid.cell_at(Position(row=row, col=col))
            if cell.has_top_wall:
                walls.add(Wall(row, col, "top"))
            if cell.has_left_wall:
                walls.add(Wall(row, col, "left"))
    return frozenset(walls)


def visible_walls(visibility: LevelVisibility, grid: Grid) -> frozenset[Wall]:
    """The exact wall segments to render under `visibility`.

    ONE -> every wall segment; TWO -> walls of the visited partitions;
    THREE -> walls of the current partition; FOUR -> `discovered_walls`;
    MAX -> none. Partition walls include the partition's own boundary (the
    raw padding row/column carries the bottom/right edge bits), so a
    visible partition is drawn closed.
    """
    if visibility.level is Level.ONE:
        return _all_walls(grid)
    if visibility.level in (Level.TWO, Level.THREE):
        if visibility.level is Level.THREE:
            visible_indices = frozenset({visibility.current_partition})
        else:
            visible_indices = visibility.visited
        walls: set[Wall] = set()
        for index in visible_indices:
            partition = visibility.partitions[index]
            for row in range(partition.top_left.row, partition.bottom_right.row + 1):
                for col in range(partition.top_left.col, partition.bottom_right.col + 1):
                    cell = grid.cell_at(Position(row=row, col=col))
                    if cell.has_top_wall:
                        walls.add(Wall(row, col, "top"))
                    if cell.has_left_wall:
                        walls.add(Wall(row, col, "left"))
        return frozenset(walls)
    if visibility.level is Level.FOUR:
        return visibility.discovered_walls
    return frozenset()


def show_contour(visibility: LevelVisibility) -> bool:
    """`True` when the playable-area contour must be drawn under `visibility`.

    Levels 2/3/4 always draw it; Level Max draws it only while
    `contour_shown`; Level 1 never draws a separate contour (its border
    walls are drawn as ordinary walls).
    """
    if visibility.level is Level.ONE:
        return False
    if visibility.level is Level.MAX:
        return visibility.contour_shown
    return True
