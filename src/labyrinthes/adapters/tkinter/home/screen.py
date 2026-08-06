"""Home screen placeholder (Story 1.7).

Just enough for the router to prove itself -- real breadcrumb navigation and
Settings access land in Story 1.8. Never imports `builder`/`player` or
`adapters/storage/` (AD-1, AD-9).
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.domain.maze import Maze

__all__ = ["mount"]


def mount(parent: tk.Widget, state: Maze | None) -> tk.Frame:
    """Build the placeholder Home screen `Frame`, parented under `parent`.

    `state` is accepted per the shared `mount(parent, state)` interface
    (AD-10) but unused here -- Home has no maze state to receive.
    """
    frame = tk.Frame(parent)
    tk.Label(frame, text="Home").pack()
    return frame
