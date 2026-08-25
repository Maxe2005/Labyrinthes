"""Builder edit screen entry point (Stories 3.2/3.3/3.4).

`mount()` dispatches on `state` exactly like `player/screen.py`: `state is
None` opens `NewMazeDialog` as the entry state (nothing else renders --
the maze-frame stays empty until the user confirms dimensions, mirroring
`home/screen.py`'s own "New Maze" entry point); `state is a Maze` builds
the full edit UI via `_BuilderEditArea` (`edit_area.py`). Confirming the
dialog forwards the freshly-built `Maze` to `navigate(ScreenId.BUILDER,
maze)`, re-running `mount()` with `state=maze` -- Builder never re-packs in
place. `state is a BuilderTestLaunch` (the "Test in Player" round-trip,
Story 3.8) renders the same edit UI with the launch's `maze` and restores
the session's `entry`/`exit` markers from the payload.

The rest of the screen lives in sibling modules:
- `edit_area.py` -- `_BuilderEditArea`, the tool sidebar + HUD + session
  orchestration.
- `maze_canvas.py` -- `_BuilderMazeCanvas`, wall/marker rendering and
  click/drag hit-testing.
- `save_dialog.py` -- `_SaveNameDialog`, the Save flow's name entry.

Never imports `home`/`player` or `adapters/storage/` (AD-1, AD-9).
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.builder.edit_area import _BuilderEditArea
from labyrinthes.adapters.tkinter.common import (
    SPACING,
    BreadcrumbSegment,
    BuilderTestLaunch,
    NavigateFn,
    NewMazeDialog,
    ScreenId,
    SettingsWindow,
    Theme,
    ToggleThemeFn,
    TopBar,
)
from labyrinthes.application.defaults_settings import read_builder_default_tool
from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.domain.maze import Maze

__all__ = ["mount"]


def mount(
    parent: tk.Widget,
    state: Maze | None | BuilderTestLaunch,
    navigate: NavigateFn,
    theme: Theme,
    toggle_theme: ToggleThemeFn,
    *,
    settings_repository: SettingsRepository,
    maze_repository: MazeRepository,
) -> tk.Frame:
    """Build the Builder edit screen `Frame`, parented under `parent`.

    `state is None` opens `NewMazeDialog` as the entry state; `state is a
    Maze` renders the maze-frame directly with that maze already loaded
    for editing (confirming the dialog re-enters this same branch via
    `navigate(ScreenId.BUILDER, maze)`); `state is a BuilderTestLaunch`
    (the "Test in Player" round-trip) renders the same edit UI with the
    launch's `maze` and restores the session's `entry`/`exit` markers from
    the payload.

    `maze_repository` (Story 3.6) is required and keyword-only, mirroring
    `player/screen.py`'s own `mount()` -- the Save flow needs it to persist
    Sketches/Mazes and to duplicate-name-check via `list_names()`/`load()`.
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

    if state is None:
        # Parented to `frame` (the calling widget), not `parent` -- like
        # Home's own `NewMazeDialog` (Story 3.1), nothing here is worth
        # surviving a navigate-away, so it is torn down with `frame` if the
        # user leaves Builder while it's still open.
        NewMazeDialog(
            frame,
            theme=theme,
            settings_repository=settings_repository,
            on_confirm=lambda maze: navigate(ScreenId.BUILDER, maze),
        )
        return frame

    maze = state.maze if isinstance(state, BuilderTestLaunch) else state
    entry = state.entry if isinstance(state, BuilderTestLaunch) else None
    exit_marker = state.exit if isinstance(state, BuilderTestLaunch) else None
    default_tool = read_builder_default_tool(settings_repository)
    edit_area = _BuilderEditArea(
        frame,
        maze,
        theme,
        navigate=navigate,
        settings_repository=settings_repository,
        maze_repository=maze_repository,
        entry=entry,
        exit=exit_marker,
        default_tool=default_tool,
    )
    edit_area.pack(
        fill="both",
        expand=True,
        padx=SPACING["page-margin"],
        pady=SPACING["section-gap"],
    )

    return frame
