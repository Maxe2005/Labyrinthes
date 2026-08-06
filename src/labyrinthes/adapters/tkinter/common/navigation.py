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

from labyrinthes.domain.maze import Maze

__all__ = ["NavigateFn", "ScreenId", "ScreenMountFn"]


class ScreenId(enum.Enum):
    """Stable identity for a screen the router can navigate to."""

    HOME = "home"
    BUILDER = "builder"
    PLAYER = "player"


# The narrow capability `mount()` receives instead of a full `Router`
# reference -- enough to trigger a screen swap, nothing that would let a
# screen `register()` a new screen or read `current_screen_id` (see the
# spec's Design Notes on why not just pass `Router` itself).
NavigateFn = Callable[[ScreenId, Maze | None], None]

# Every screen's `mount()` signature (Story 1.8): `Router`'s own `MountFn`
# (`app/router.py`) stays the unchanged 2-arg shape from Story 1.7;
# `composition_root.build_app()` is what bridges the two, wrapping each
# `ScreenMountFn` into a `MountFn` bound to one `NavigateFn` closure.
ScreenMountFn = Callable[[tk.Widget, Maze | None, NavigateFn], tk.Frame]
