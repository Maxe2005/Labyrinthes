"""`Router` -- the screen-swap mechanism every screen navigates through.

`Router` never imports a concrete screen module (`composition_root.py` is the
only place that does, AD-10) -- it only knows about `MountFn` callables
registered against a `ScreenId`, keeping the "screens never import each
other" boundary trivially true rather than merely tested.

`ScreenId` itself is defined in `adapters/tkinter/common/navigation.py`
(Story 1.8) -- screens need real, runtime access to its members, which
would require importing `app/` if it stayed here, inverting the epic's
one-way `app/ -> adapters/ -> application/ -> domain/` dependency
direction. It is re-exported unchanged below so
`from labyrinthes.app.router import ScreenId` keeps working.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.navigation import ScreenId
from labyrinthes.app.errors import UnregisteredScreenError
from labyrinthes.domain.maze import Maze

__all__ = ["MountFn", "Router", "ScreenId"]

MountFn = Callable[[tk.Widget, Maze | None], tk.Frame]


class Router:
    """Swaps the single mounted screen inside `container` (AD-10).

    `navigate()` mounts and packs the target screen before destroying the
    previously-mounted frame (new-before-old), so there's never a
    frame-less gap mid-swap -- see the spec's Design Notes for why this
    ordering, not requirement, is the implementation choice made here.
    """

    def __init__(self, container: tk.Widget) -> None:
        self._container = container
        self._mounts: dict[ScreenId, MountFn] = {}
        self._current_screen_id: ScreenId | None = None
        self._current_frame: tk.Frame | None = None

    def register(self, screen_id: ScreenId, mount: MountFn) -> None:
        """Associate `screen_id` with the `mount` callable that builds its `Frame`."""
        self._mounts[screen_id] = mount

    def navigate(self, screen_id: ScreenId, state: Maze | None = None) -> None:
        """Mount `screen_id`'s screen, passing `state`, and tear down the previous one.

        Raises `UnregisteredScreenError` -- leaving the currently-mounted
        screen untouched -- if `screen_id` was never `register()`-ed.
        """
        try:
            mount = self._mounts[screen_id]
        except KeyError:
            raise UnregisteredScreenError(f"No screen registered for {screen_id!r}") from None

        new_frame = mount(self._container, state)
        new_frame.pack(fill="both", expand=True)

        previous_frame = self._current_frame
        if previous_frame is not None:
            previous_frame.destroy()

        self._current_screen_id = screen_id
        self._current_frame = new_frame

    @property
    def current_screen_id(self) -> ScreenId | None:
        """The currently-mounted screen's id, or `None` before the first `navigate()`."""
        return self._current_screen_id
