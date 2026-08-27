"""`MazeRepository` port — the single interface for persisting/loading mazes.

Storage-agnostic: consumers address a maze by `name` + `MazeKind`, never a
raw filesystem `Path`. The on-disk format and folder layout are Story 1.4's
concern; this port only pins the method signatures every screen and Story
1.4's concrete implementation must agree on.
"""

import abc

from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.maze_id import MazeId


class MazeRepository(abc.ABC):
    """Port for saving/loading a `Maze` and looking one up by `MazeId`."""

    @abc.abstractmethod
    def save(self, maze: Maze, name: str) -> Maze:
        """Persist `maze` under `name`, returning the (possibly updated) `Maze`.

        For `MazeKind`s eligible for an id (`CLASSIC`/`SAVED_RANDOM`/`CREATION`) with
        `maze.id is None`, a fresh `MazeId` is minted and carried by the
        returned `Maze`; an already-set id is carried forward unchanged.

        `maze.kind` is saved as-is — a kind transition (e.g. an unsaved
        `GENERATED` maze becoming `SAVED_RANDOM`) is the caller's
        responsibility to make *before* calling `save()`, by constructing
        a `Maze` that already carries the target kind; this method never
        infers or rewrites `kind`. Saving over an already-occupied
        `name`+`kind` overwrites it — duplicate-name *prevention* (e.g.
        prompting the author) is a caller/service concern, not this port's.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def load(self, name: str, kind: MazeKind) -> Maze:
        """Load the maze saved under `name` for `kind`.

        Raises `MazeNotFoundError` if no such maze exists.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def find_by_id(self, maze_id: MazeId) -> Maze | None:
        """Look up a maze by its `MazeId`, or `None` if it no longer exists.

        `MazeId` values are unique across all id-eligible kinds combined
        (`CLASSIC`, `SAVED_RANDOM`, and `CREATION`) — this is a single global lookup,
        not scoped or repeated per kind.

        Unlike `load()`, absence is an expected outcome here (e.g. resolving
        a `Record.maze_id` that may reference a since-deleted maze), so this
        returns `None` rather than raising.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def list_names(self, kind: MazeKind) -> list[str]:
        """The names of every persisted maze of `kind`, sorted lexicographically.

        Lexicographic, not numeric-aware, sorting (e.g. `"10"` sorts before
        `"2"`) — no naming convention for classic/saved-random mazes is
        established yet (Epic 4's migration concern), so this makes no
        assumption about one. Returns `[]` if `kind`'s folder doesn't exist
        yet, rather than raising — an empty library is an expected state
        (e.g. a fresh install with no classic mazes), not an error.
        """
        raise NotImplementedError
