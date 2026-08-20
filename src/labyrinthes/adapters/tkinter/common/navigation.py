"""The shared navigation contract every screen and `app/` depend on (Story 1.8).

`ScreenId` lives here rather than in `app/router.py` because screens need
real, runtime access to its members (e.g. `navigate(ScreenId.HOME, None)`
inside a button's `command`), not just a type hint -- and `common/` is the
one package every screen already imports from that never imports back from
them, so it's the cycle-free home for a contract both `app/` and
`home/`/`builder/`/`player/` share (see the spec's Design Notes).
`app/router.py` re-exports this `ScreenId` unchanged via its own `__all__`,
so `from labyrinthes.app.router import ScreenId` keeps working untouched.
"""

from __future__ import annotations

import enum
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.domain.maze import Maze
from labyrinthes.domain.position import Position

__all__ = ["BuilderTestLaunch", "NavigateFn", "ScreenId", "ScreenMountFn", "ToggleThemeFn"]


class ScreenId(enum.Enum):
    """Stable identity for a screen the router can navigate to."""

    HOME = "home"
    BUILDER = "builder"
    PLAYER = "player"


@dataclass(frozen=True)
class BuilderTestLaunch:
    """The Builder's "Test in Player" hand-off payload (Story 3.8 amendment).

    The Builder's `_test_in_player` hands the in-progress `Maze` plus the
    session's own `entry`/`exit` marker set-ness to the Player, so a
    round-trip back to the Builder restores exactly those markers (the
    "Back to Builder" top-bar segment / test-mode win-banner pill navigate
    back with this same payload, and the Builder's `mount()` rebuilds the
    session from it). Carrying `entry`/`exit` (not just `maze`) is what
    makes the restore faithful: `start_builder_session` alone would reset
    an unset exit to `None` and a set one to a fresh default.
    """

    maze: Maze
    entry: Position | None
    exit: Position | None


# The narrow capability `mount()` receives instead of a full `Router`
# reference -- enough to trigger a screen swap, nothing that would let a
# screen `register()` a new screen or read `current_screen_id` (see the
# spec's Design Notes on why not just pass `Router` itself).
NavigateFn = Callable[[ScreenId, Maze | None | BuilderTestLaunch], None]

# The narrow capability `mount()` receives to trigger a theme toggle
# (Story 1.9) -- a screen only ever needs to fire the toggle, never to
# `subscribe()` another listener or read `.theme` outside of what `mount()`
# already handed it (see the spec's Design Notes).
ToggleThemeFn = Callable[[], None]

# Every screen's `mount()` signature (Story 1.8, extended by Story 1.9):
# `Router`'s own `MountFn` (`app/router.py`) stays the unchanged 2-arg
# shape from Story 1.7; `composition_root.build_app()` is what bridges the
# two, wrapping each `ScreenMountFn` into a `MountFn` bound to one
# `NavigateFn` closure plus the live `theme`/`ToggleThemeFn` pair.
ScreenMountFn = Callable[
    [tk.Widget, Maze | None | BuilderTestLaunch, NavigateFn, Theme, ToggleThemeFn], tk.Frame
]
