"""Shared test doubles/fixtures for Player-screen tests (Story 2.1).

`FakeMazeRepository` is an in-memory `MazeRepository` -- no filesystem I/O
-- so `ClassicMazeGallery`/Player-screen tests never need a `tmp_path` just
to exercise the pager/jump/restart/play behavior against a repository.
Story 3.6 hoisted it into `tests/adapters/tkinter/conftest.py` (the shared
conftest, mirroring the Story 2.10/`FakeSettingsRepository` hoist precedent
below), now that the Builder screen also takes a `MazeRepository` port --
this module imports and re-exports it so the existing `fake_maze_repository`
fixture and `classic_maze`/`saved_random_maze` helpers keep resolving for
Player tests without a second definition.

`FakeSettingsRepository` (Story 2.2) is the equivalent in-memory
`SettingsRepository` double, for tests exercising `GenerateRandomDialog`'s
FR-4 size-bounds reads without a `tmp_path`-backed `JsonSettingsRepository`.
Story 2.10 hoisted it into `tests/adapters/tkinter/conftest.py` (the shared
conftest, mirroring the Story 1.7 hoist precedent) -- this module imports
and re-exports it so the existing `fake_settings_repository` fixture keeps
resolving for Player tests without a second definition.
"""

from tests.adapters.tkinter.conftest import (
    FakeMazeRepository,
    FakeSettingsRepository,
    classic_maze,
    fake_maze_repository,
    fake_settings_repository,
    saved_random_maze,
    seeded_maze_repository,
    seeded_maze_repository_with_saved_random,
)

__all__ = [
    "FakeMazeRepository",
    "FakeSettingsRepository",
    "classic_maze",
    "fake_maze_repository",
    "fake_settings_repository",
    "saved_random_maze",
    "seeded_maze_repository",
    "seeded_maze_repository_with_saved_random",
]
