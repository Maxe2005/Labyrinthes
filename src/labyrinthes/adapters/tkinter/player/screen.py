"""Player screen: classic-maze selection (Story 2.1), wired into navigation (Story 1.8).

Never imports `home`/`builder` or `adapters/storage/` directly (AD-1, AD-9)
-- maze access goes through the `MazeRepository` port (`application/`).
Carries a "Home / Player" breadcrumb: the Home segment is always clickable,
the trailing "Player" segment (this screen itself) never is. That
breadcrumb stays exactly 2 segments in both the selection and
gameplay-placeholder views -- no dynamic 3-segment label (e.g. "Classic
Maze 4") yet, deferred to Story 2.4 (see the story's Boundaries &
Constraints).

`mount()` dispatches purely on `state`: `state is None` mounts
`ClassicMazeGallery` (browsing); `state is not None` mounts a
`GameplayPlaceholder` -- still just a plain text summary of that `Maze`,
plus a Save action when it's `GENERATED` (Story 2.3) -- real gameplay
rendering (walls, ball, HUD) is Story 2.4's job.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common import (
    SPACING,
    BreadcrumbSegment,
    NavigateFn,
    ScreenId,
    SettingsWindow,
    Theme,
    ToggleThemeFn,
    TopBar,
)
from labyrinthes.adapters.tkinter.player.classic_gallery import ClassicMazeGallery
from labyrinthes.adapters.tkinter.player.gameplay_placeholder import GameplayPlaceholder
from labyrinthes.application.maze_repository import MazeRepository
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
    maze_repository: MazeRepository,
    settings_repository: SettingsRepository,
) -> tk.Frame:
    """Build the Player screen `Frame`, parented under `parent`.

    Keeps the shared 5-positional-arg `ScreenMountFn` shape (`parent, state,
    navigate, theme, toggle_theme`) untouched, plus two required,
    keyword-only ports -- `maze_repository` (Story 2.1) and
    `settings_repository` (Story 2.2, for the FR-4 random-maze size
    bounds) -- `composition_root.build_app()` binds both in via
    `functools.partial` before handing this to `_bind_screen()`, so
    Home/Builder/`ScreenMountFn` stay untouched (see the story's Design
    Notes).

    `state is None` mounts the classic-maze selection gallery. `state is
    not None` mounts a gameplay-placeholder summary of that `Maze` --
    picking a maze in the gallery calls `navigate(ScreenId.PLAYER, maze)`,
    which re-runs this very `mount()` with `state=maze`, taking this
    branch.
    """
    frame = tk.Frame(parent)

    def open_settings() -> None:
        # `parent` (not `frame`) as the `Toplevel`'s master (Story 1.11):
        # `parent` is the app's persistent container, never destroyed by
        # `Router.navigate()`, so `SettingsWindow` survives navigating away
        # from Player instead of being torn down as a cascade side effect
        # of `frame.destroy()`. See `SettingsWindow`'s module docstring.
        SettingsWindow(parent, theme=theme)

    breadcrumb_segments = [
        BreadcrumbSegment("Home", on_click=lambda: navigate(ScreenId.HOME, None)),
        BreadcrumbSegment("Player"),
    ]
    top_bar = TopBar(
        frame,
        theme=theme,
        breadcrumb_segments=breadcrumb_segments,
        on_settings=open_settings,
        on_theme_toggle=toggle_theme,
    )
    top_bar.pack(fill="x")

    if state is None:
        gallery = ClassicMazeGallery(
            frame,
            theme=theme,
            maze_repository=maze_repository,
            settings_repository=settings_repository,
            navigate=navigate,
        )
        gallery.pack(
            fill="both",
            expand=True,
            padx=SPACING["page-margin"],
            pady=SPACING["section-gap"],
        )
    else:
        placeholder = GameplayPlaceholder(frame, state, theme, maze_repository=maze_repository)
        placeholder.pack(
            fill="both",
            expand=True,
            padx=SPACING["page-margin"],
            pady=SPACING["section-gap"],
        )

    return frame
