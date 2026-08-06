"""Builder screen placeholder (Story 1.7).

Registers Builder with the router ahead of Epic 2's real maze-editing
content. Never imports `home`/`player` or `adapters/storage/` (AD-1, AD-9).
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.domain.maze import Maze

__all__ = ["mount"]


def mount(parent: tk.Widget, state: Maze | None) -> tk.Frame:
    """Build the placeholder Builder screen `Frame`, parented under `parent`.

    `state` is accepted per the shared `mount(parent, state)` interface
    (AD-10) but unused here -- Epic 2 wires the real edit-a-maze hand-off.
    """
    frame = tk.Frame(parent)
    tk.Label(frame, text="Builder").pack()
    return frame
