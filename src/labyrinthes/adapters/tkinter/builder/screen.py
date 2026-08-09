"""Builder screen placeholder (Story 1.7), now wired into navigation (Story 1.8).

Never imports `home`/`player` or `adapters/storage/` (AD-1, AD-9). Carries a
"Home / Builder" breadcrumb: the Home segment is always clickable, the
trailing "Builder" segment (this screen itself) never is.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common import (
    BreadcrumbSegment,
    NavigateFn,
    ScreenId,
    SettingsWindow,
    Theme,
    ToggleThemeFn,
    TopBar,
)
from labyrinthes.domain.maze import Maze

__all__ = ["mount"]


def mount(
    parent: tk.Widget,
    state: Maze | None,
    navigate: NavigateFn,
    theme: Theme,
    toggle_theme: ToggleThemeFn,
) -> tk.Frame:
    """Build the placeholder Builder screen `Frame`, parented under `parent`.

    `state` is accepted per the shared `mount(parent, state, navigate,
    theme, toggle_theme)` interface (AD-10) but unused here -- Epic 2 wires
    the real edit-a-maze hand-off.
    """
    frame = tk.Frame(parent)

    def open_settings() -> None:
        # `frame` (not `parent`) as the `Toplevel`'s master: closing Builder
        # never has to hunt this window down separately, and it never
        # touches the router -- the screen underneath stays mounted.
        SettingsWindow(frame, theme=theme)

    breadcrumb_segments = [
        BreadcrumbSegment("Home", on_click=lambda: navigate(ScreenId.HOME, None)),
        BreadcrumbSegment("Builder"),
    ]
    top_bar = TopBar(
        frame,
        theme=theme,
        breadcrumb_segments=breadcrumb_segments,
        on_settings=open_settings,
        on_theme_toggle=toggle_theme,
    )
    top_bar.pack(fill="x")

    tk.Label(frame, text="Builder").pack()
    return frame
