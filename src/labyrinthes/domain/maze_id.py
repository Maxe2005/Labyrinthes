"""MazeId value object — an opaque identifier only.

Minting/generation is a single shared function consumed by `MazeRepository`
(Story 1.4) and the migration script (Epic 4) — not implemented here.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MazeId:
    """An opaque identifier for a persisted `Maze` (`classic`/`saved-random`)."""

    value: str
