"""Player screen: classic-maze selection (Story 2.1), wired into navigation (Story 1.8).

Never imports `home`/`builder` or `adapters/storage/` directly (AD-1, AD-9)
-- maze access goes through the `MazeRepository` port (`application/`).
Carries a "Home / Player" breadcrumb when browsing (`state is None`): the
Home segment is always clickable, the trailing "Player" segment (this
screen itself) never is.

When gameplay is mounted (`state is not None`, Story 2.4), the breadcrumb
grows to 3 segments: "Home" (clickable), "Player" (now also clickable --
back to the gallery, via `navigate(ScreenId.PLAYER, None)`), and a
trailing kind-derived label ("Classic Maze"/"Saved Random Maze"/"Random
Maze"/"Sketch") that is never clickable. The label is derived from
`maze.kind`, not from the gallery's own browsed position/ordinal -- see
the story's Design Notes for why (`navigate(ScreenId.PLAYER, maze)` only
ever carries a bare `Maze`, no name/ordinal, and this view must never
read `maze_repository`). `GameplayScreen`'s `on_kind_changed` callback
keeps that trailing label in sync if the mounted maze's own `kind`
changes mid-session (saving a `GENERATED` maze into `SAVED_RANDOM`)
without a full re-navigate.

A `BuilderTestLaunch` state (Builder's "Test in Player", Story 3.8)
mounts gameplay with a "Builder" breadcrumb segment -- clickable, back to
the Builder restoring the session's markers -- in place of the "Player"
one, plus an `on_back_to_builder` callback so the test-mode win banner's
"Back to Builder" pill returns the same way.

`mount()` dispatches purely on `state`: `state is None` mounts
`ClassicMazeGallery` (browsing); `state is not None` mounts
`GameplayScreen` -- real wall/HUD/ball rendering, movement, and win
detection (Story 2.4).
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common import (
    SPACING,
    BreadcrumbSegment,
    BuilderTestLaunch,
    NavigateFn,
    ScreenId,
    SettingsWindow,
    Theme,
    ToggleThemeFn,
    TopBar,
)
from labyrinthes.adapters.tkinter.player.classic_gallery import ClassicMazeGallery
from labyrinthes.adapters.tkinter.player.gameplay import GameplayScreen
from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.domain.maze import Maze, MazeKind

__all__ = ["mount"]

_KIND_LABELS: dict[MazeKind, str] = {
    MazeKind.CLASSIC: "Classic Maze",
    MazeKind.SAVED_RANDOM: "Saved Random Maze",
    MazeKind.GENERATED: "Random Maze",
    MazeKind.SKETCH: "Sketch",
}


def mount(
    parent: tk.Widget,
    state: Maze | None | BuilderTestLaunch,
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
    not None` mounts `GameplayScreen` for that `Maze` -- picking a maze in
    the gallery calls `navigate(ScreenId.PLAYER, maze)`, which re-runs this
    very `mount()` with `state=maze`, taking this branch. A
    `BuilderTestLaunch` state (Builder's "Test in Player", Story 3.8)
    mounts the same gameplay view but with a "Builder" breadcrumb segment
    (clickable -- back to the Builder, restoring the session's markers from
    the payload) in place of the "Player" one, and hands `GameplayScreen`
    an `on_back_to_builder` callback so the test-mode win banner's "Back to
    Builder" pill navigates the same way.
    """
    frame = tk.Frame(parent)

    def open_settings() -> None:
        # `parent` (not `frame`) as the `Toplevel`'s master (Story 1.11):
        # `parent` is the app's persistent container, never destroyed by
        # `Router.navigate()`, so `SettingsWindow` survives navigating away
        # from Player instead of being torn down as a cascade side effect
        # of `frame.destroy()`. See `SettingsWindow`'s module docstring.
        SettingsWindow(
            parent,
            theme=theme,
            settings_repository=settings_repository,
            show_logo_picker=True,
        )

    is_test_launch = isinstance(state, BuilderTestLaunch)
    test_launch = state if is_test_launch else None

    if state is None:
        breadcrumb_segments = [
            BreadcrumbSegment("Home", on_click=lambda: navigate(ScreenId.HOME, None)),
            BreadcrumbSegment("Player"),
        ]
    elif is_test_launch:
        breadcrumb_segments = [
            BreadcrumbSegment("Home", on_click=lambda: navigate(ScreenId.HOME, None)),
            BreadcrumbSegment("Builder", on_click=lambda: navigate(ScreenId.BUILDER, test_launch)),
            BreadcrumbSegment(_KIND_LABELS[test_launch.maze.kind]),
        ]
    else:
        breadcrumb_segments = [
            BreadcrumbSegment("Home", on_click=lambda: navigate(ScreenId.HOME, None)),
            BreadcrumbSegment("Player", on_click=lambda: navigate(ScreenId.PLAYER, None)),
            BreadcrumbSegment(_KIND_LABELS[state.kind]),
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
        maze = test_launch.maze if is_test_launch else state
        gameplay = GameplayScreen(
            frame,
            maze,
            theme,
            maze_repository=maze_repository,
            settings_repository=settings_repository,
            navigate=navigate,
            # Saving a `GENERATED` maze transitions its `kind` to
            # `SAVED_RANDOM` mid-session -- without this, the trailing
            # breadcrumb segment (built once above, from the *original*
            # `state.kind`) would keep showing "Random Maze" forever.
            on_kind_changed=lambda kind: top_bar.set_breadcrumb_label(2, _KIND_LABELS[kind]),
            on_back_to_builder=(
                (lambda: navigate(ScreenId.BUILDER, test_launch)) if is_test_launch else None
            ),
        )
        gameplay.pack(
            fill="both",
            expand=True,
            padx=SPACING["page-margin"],
            pady=SPACING["section-gap"],
        )

    return frame
