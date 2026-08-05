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
from labyrinthes.domain.maze_id import MazeId
from labyrinthes.domain.position import Position

__all__ = [
    "Cell",
    "Difficulty",
    "DomainValidationError",
    "Duration",
    "Grid",
    "LabyrinthesError",
    "Level",
    "Maze",
    "MazeId",
    "MazeKind",
    "Position",
]
