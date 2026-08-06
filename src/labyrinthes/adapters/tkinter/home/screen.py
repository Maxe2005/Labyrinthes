"""Home screen: the app's sole general navigation hub (Story 1.8).

Never imports `builder`/`player` or `adapters/storage/` (AD-1, AD-9). Renders
no `Breadcrumb` of its own -- navigation depth 0, matching the locked
`key-home.html` mockup (see the spec's Design Notes) -- only the `TopBar`'s
brand mark/wordmark plus two `PillButton` entry points into Builder/Player.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common import (
    SPACING,
    NavigateFn,
    PillButton,
    ScreenId,
    SettingsWindow,
    Theme,
    TopBar,
)
from labyrinthes.domain.maze import Maze

__all__ = ["mount"]


def mount(parent: tk.Widget, state: Maze | None, navigate: NavigateFn) -> tk.Frame:
    """Build the Home screen `Frame`, parented under `parent`.

    `state` is accepted per the shared `mount(parent, state, navigate)`
    interface (AD-10) but unused here -- Home has no maze state to receive.
    """
    theme = Theme.LIGHT
    frame = tk.Frame(parent)

    def open_settings() -> None:
        # `frame` (not `parent`) as the `Toplevel`'s master: closing Home
        # never has to hunt this window down separately, and it never
        # touches the router -- the screen underneath stays mounted.
        SettingsWindow(frame, theme=theme)

    top_bar = TopBar(frame, theme=theme, breadcrumb_segments=None, on_settings=open_settings)
    top_bar.pack(fill="x")

    entry_points = tk.Frame(frame)
    entry_points.pack(pady=SPACING["5xl"])

    PillButton(
        entry_points,
        "Open Builder",
        theme=theme,
        command=lambda: navigate(ScreenId.BUILDER, None),
    ).pack(side="left", padx=SPACING["sm"])
    PillButton(
        entry_points,
        "Open Player",
        theme=theme,
        command=lambda: navigate(ScreenId.PLAYER, None),
    ).pack(side="left", padx=SPACING["sm"])

    return frame
