"""Player screen placeholder (Story 1.7), now wired into navigation (Story 1.8).

Never imports `home`/`builder` or `adapters/storage/` (AD-1, AD-9). Carries a
"Home / Player" breadcrumb: the Home segment is always clickable, the
trailing "Player" segment (this screen itself) never is.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common import (
    BreadcrumbSegment,
    NavigateFn,
    ScreenId,
    SettingsWindow,
    Theme,
    TopBar,
)
from labyrinthes.domain.maze import Maze

__all__ = ["mount"]


def mount(parent: tk.Widget, state: Maze | None, navigate: NavigateFn) -> tk.Frame:
    """Build the placeholder Player screen `Frame`, parented under `parent`.

    `state` is accepted per the shared `mount(parent, state, navigate)`
    interface (AD-10) but unused here -- Epic 3 wires the real
    test-in-Player maze hand-off.
    """
    theme = Theme.LIGHT
    frame = tk.Frame(parent)

    def open_settings() -> None:
        SettingsWindow(frame, theme=theme)

    breadcrumb_segments = [
        BreadcrumbSegment("Home", on_click=lambda: navigate(ScreenId.HOME, None)),
        BreadcrumbSegment("Player"),
    ]
    top_bar = TopBar(
        frame,
        theme=theme,
        breadcrumb_segments=breadcrumb_segments,
        on_settings=open_settings,
    )
    top_bar.pack(fill="x")

    tk.Label(frame, text="Player").pack()
    return frame
