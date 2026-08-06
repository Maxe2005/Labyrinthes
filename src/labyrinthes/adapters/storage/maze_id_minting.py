"""Shared `MazeId` minting.

A single function so `CsvMazeRepository.save()` (Story 1.4) and Epic 4's
one-time migration script mint ids the exact same way -- never duplicated
per caller (AD-3/AD-8).
"""

import uuid

from labyrinthes.domain.maze_id import MazeId


def mint_maze_id() -> MazeId:
    """Mint a fresh, opaque `MazeId`."""
    return MazeId(value=uuid.uuid4().hex)
