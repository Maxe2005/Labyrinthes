"""Player screen placeholder (Story 1.7).

Registers Player with the router ahead of Epic 3's real gameplay content.
Never imports `home`/`builder` or `adapters/storage/` (AD-1, AD-9).
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.domain.maze import Maze

__all__ = ["mount"]


def mount(parent: tk.Widget, state: Maze | None) -> tk.Frame:
    """Build the placeholder Player screen `Frame`, parented under `parent`.

    `state` is accepted per the shared `mount(parent, state)` interface
    (AD-10) but unused here -- Epic 3 wires the real test-in-Player
    maze hand-off.
    """
    frame = tk.Frame(parent)
    tk.Label(frame, text="Player").pack()
    return frame
