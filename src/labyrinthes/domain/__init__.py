"""Domain model: immutable value objects shared by every screen.

Imports nothing from `adapters/` or any UI framework (AD-1).
"""

from labyrinthes.domain.cell import Cell
from labyrinthes.domain.difficulty import Difficulty
from labyrinthes.domain.duration import Duration
from labyrinthes.domain.errors import DomainValidationError, LabyrinthesError
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level import Level
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.maze_generation import generate_random_maze, validate_start_position
from labyrinthes.domain.maze_id import MazeId
from labyrinthes.domain.maze_size_bounds import (
    DEFAULT_MAZE_SIZE_BOUNDS,
    MazeSizeBounds,
    validate_dimensions,
)
from labyrinthes.domain.movement import Direction, attempt_move
from labyrinthes.domain.position import Position

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
    "Maze",
    "MazeId",
    "MazeKind",
    "MazeSizeBounds",
    "Position",
    "attempt_move",
    "generate_random_maze",
    "validate_dimensions",
    "validate_start_position",
]
