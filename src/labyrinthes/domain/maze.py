"""Maze value object — a `Grid` plus its entry/exit, kind tag, and identity."""

import enum
from dataclasses import dataclass

from labyrinthes.domain.errors import DomainValidationError
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze_id import MazeId
from labyrinthes.domain.position import Position


class MazeKind(enum.Enum):
    """What kind of maze this is, and where it came from."""

    CLASSIC = "classic"
    SKETCH = "sketch"
    SAVED_RANDOM = "saved-random"
    GENERATED = "generated"


_ID_ELIGIBLE_KINDS = frozenset({MazeKind.CLASSIC, MazeKind.SAVED_RANDOM})


@dataclass(frozen=True)
class Maze:
    """A maze: its `Grid`, entry/exit `Position`s, kind, and optional identity.

    The id-eligibility rule is one-directional: a non-`None` id requires
    `kind` to be `CLASSIC` or `SAVED_RANDOM`. The reverse does not hold —
    a freshly-transitioned, not-yet-persisted `classic`/`saved-random`
    `Maze` may legitimately have `id=None` until `MazeRepository.save()`
    mints one.
    """

    grid: Grid
    entry: Position
    exit: Position
    kind: MazeKind
    id: MazeId | None

    def __post_init__(self) -> None:
        self.grid.cell_at(self.entry)
        self.grid.cell_at(self.exit)
        if self.id is not None and self.kind not in _ID_ELIGIBLE_KINDS:
            eligible = sorted(kind.name for kind in _ID_ELIGIBLE_KINDS)
            raise DomainValidationError(
                f"Maze.id may only be set for kind in {eligible}, got kind={self.kind.name}"
            )
