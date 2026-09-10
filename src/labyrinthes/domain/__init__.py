"""Domain model: immutable value objects shared by every screen.

Imports nothing from `adapters/` or any UI framework (AD-1).
"""

from labyrinthes.domain.cell import Cell
from labyrinthes.domain.difficulty import Difficulty
from labyrinthes.domain.duration import Duration
from labyrinthes.domain.errors import DomainValidationError, LabyrinthesError
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level import Level
from labyrinthes.domain.level_visibility import (
    LevelVisibility,
    Partition,
    Wall,
    advance_visibility,
    initial_level_visibility,
    is_border_wall,
    note_collision,
    partition_grid,
    partition_size_for_difficulty,
    reveal_threshold,
    show_contour,
    total_interior_walls,
    visible_walls,
)
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.maze_generation import generate_random_maze, validate_start_position
from labyrinthes.domain.maze_id import MazeId
from labyrinthes.domain.maze_size_bounds import (
    DEFAULT_MAZE_SIZE_BOUNDS,
    MazeSizeBounds,
    validate_dimensions,
)
from labyrinthes.domain.movement import Direction, attempt_move
from labyrinthes.domain.movement_mode import MovementMode
from labyrinthes.domain.movement_speed import MovementSpeed, cell_crossing_duration
from labyrinthes.domain.position import Position
from labyrinthes.domain.reachability import inaccessible_cells

__all__ = [
    "DEFAULT_MAZE_SIZE_BOUNDS",
    "Cell",
    "Difficulty",
    "Direction",
    "DomainValidationError",
    "Duration",
    "Grid",
    "LabyrinthesError",
    "Level",
    "LevelVisibility",
    "Maze",
    "MazeId",
    "MazeKind",
    "MazeSizeBounds",
    "MovementMode",
    "MovementSpeed",
    "Partition",
    "Position",
    "Wall",
    "advance_visibility",
    "attempt_move",
    "cell_crossing_duration",
    "generate_random_maze",
    "initial_level_visibility",
    "inaccessible_cells",
    "is_border_wall",
    "note_collision",
    "partition_grid",
    "partition_size_for_difficulty",
    "reveal_threshold",
    "show_contour",
    "total_interior_walls",
    "validate_dimensions",
    "validate_start_position",
    "visible_walls",
]
