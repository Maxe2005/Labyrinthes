"""Builder screen placeholder (Story 1.7), now wired into navigation (Story 1.8).

Never imports `home`/`player` or `adapters/storage/` (AD-1, AD-9). Carries a
"Home / Builder" breadcrumb: the Home segment is always clickable, the
trailing "Builder" segment (this screen itself) never is.

Story 2.10 threads a required, keyword-only `settings_repository` port
through `mount()` (same shape as Home/Player) so Builder's `open_settings()`
can hand it to `SettingsWindow` -- the confirmation toggles must work from
every screen's Settings (AC-3).
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
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.domain.maze import Maze

__all__ = ["mount"]


def mount(
    parent: tk.Widget,
    state: Maze | None,
    navigate: NavigateFn,
    theme: Theme,
    toggle_theme: ToggleThemeFn,
    *,
    settings_repository: SettingsRepository,
) -> tk.Frame:
    """Build the placeholder Builder screen `Frame`, parented under `parent`.

    `state` is accepted per the shared `mount(parent, state, navigate,
    theme, toggle_theme)` interface (AD-10) but unused here -- Epic 2 wires
    the real edit-a-maze hand-off. `settings_repository` (Story 2.10) is
    required and keyword-only, bound by `composition_root` via
    `functools.partial`.
    """
    frame = tk.Frame(parent)

    def open_settings() -> None:
        # `parent` (not `frame`) as the `Toplevel`'s master (Story 1.11):
        # `parent` is the app's persistent container, never destroyed by
        # `Router.navigate()`, so `SettingsWindow` survives navigating away
        # from Builder instead of being torn down as a cascade side effect
        # of `frame.destroy()`. See `SettingsWindow`'s module docstring.
        SettingsWindow(parent, theme=theme, settings_repository=settings_repository)

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
