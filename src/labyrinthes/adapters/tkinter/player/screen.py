"""Player screen: maze selection (Story 2.1, rebuilt as a grid by Story 4.14),
wired into navigation (Story 1.8).

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

When the mounted maze's own saved name is already known -- a gallery card
carries `(name, maze)` together (`MazeWithName`, Story 4.13) -- the
breadcrumb gains a further trailing segment carrying that name, after the
kind-derived one, never clickable. A freshly `GENERATED` maze (no gallery
card, no name yet) gets no such segment until it's saved mid-session via
the existing Save Maze flow, at which point `GameplayScreen`'s
`on_name_saved` callback appends it in place (`TopBar.append_breadcrumb_segment`)
without disturbing the first 3 segments.

A `BuilderTestLaunch` state (Builder's "Test in Player", Story 3.8)
mounts gameplay with a "Builder" breadcrumb segment -- clickable, back to
the Builder restoring the session's markers -- in place of the "Player"
one, plus an `on_back_to_builder` callback so the test-mode win banner's
"Back to Builder" pill returns the same way.

`mount()` dispatches purely on `state`: `state is None` mounts
`MazeSelectionGallery` (browsing -- a scrollable Classic/Creations/Random
card grid, Story 4.14); `state is not None` mounts `GameplayScreen` -- real
wall/HUD/ball rendering, movement, and win detection (Story 2.4).
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common import (
    SPACING,
    BreadcrumbSegment,
    BuilderTestLaunch,
    MazeWithName,
    NavigateFn,
    ScreenId,
    SettingsWindow,
    Theme,
    ToggleThemeFn,
    TopBar,
    load_logo_image,
)
from labyrinthes.adapters.tkinter.player.gameplay import GameplayScreen
from labyrinthes.adapters.tkinter.player.maze_selection_gallery import MazeSelectionGallery
from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.domain.maze import Maze, MazeKind

__all__ = ["mount"]


_KIND_LABELS: dict[MazeKind, str] = {
    MazeKind.CLASSIC: "Classic Maze",
    MazeKind.SAVED_RANDOM: "Saved Random Maze",
    MazeKind.GENERATED: "Random Maze",
    MazeKind.SKETCH: "Sketch",
    MazeKind.CREATION: "Creation",
}


def mount(
    parent: tk.Widget,
    state: Maze | None | BuilderTestLaunch | MazeWithName,
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

    `state is None` mounts the maze-selection gallery (`MazeSelectionGallery`,
    a scrollable Classic/Creations/Random card grid). `state is not None`
    mounts `GameplayScreen` for that `Maze` -- picking a maze in the gallery
    calls `navigate(ScreenId.PLAYER, MazeWithName(maze, name))`, which
    re-runs this very `mount()` with `state=MazeWithName(...)`, taking this
    branch and unwrapping both the `maze` and its `name` (Story 4.13). A
    `BuilderTestLaunch` state (Builder's "Test in Player", Story 3.8)
    mounts the same gameplay view but with a "Builder" breadcrumb segment
    (clickable -- back to the Builder, restoring the session's markers from
    the payload) in place of the "Player" one, and hands `GameplayScreen`
    an `on_back_to_builder` callback so the test-mode win banner's "Back to
    Builder" pill navigates the same way. Builder never tracks a name, so a
    `BuilderTestLaunch`-originated maze never gets a name segment.
    """
    frame = tk.Frame(parent)

    logo_image = load_logo_image(settings_repository)

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
        )

    is_test_launch = isinstance(state, BuilderTestLaunch)
    test_launch = state if is_test_launch else None
    named_state = state if isinstance(state, MazeWithName) else None

    # `maze`/`maze_name` unwrap every non-`None` `state` shape into the two
    # things the rest of `mount()` needs -- `maze_name` is only ever
    # non-`None` for a gallery-originated `MazeWithName` (Story 4.13): a
    # `BuilderTestLaunch` maze has no name (Builder never tracks one), and a
    # bare `Maze` (a freshly `generated`, unsaved maze) has none yet either.
    if state is None:
        maze: Maze | None = None
        maze_name: str | None = None
    elif is_test_launch:
        assert test_launch is not None
        maze = test_launch.maze
        maze_name = None
    elif named_state is not None:
        maze = named_state.maze
        maze_name = named_state.name
    else:
        assert isinstance(state, Maze)
        maze = state
        maze_name = None

    if state is None:
        breadcrumb_segments = [
            BreadcrumbSegment("Home", on_click=lambda: navigate(ScreenId.HOME, None)),
            BreadcrumbSegment("Player"),
        ]
    elif is_test_launch:
        assert test_launch is not None
        breadcrumb_segments = [
            BreadcrumbSegment("Home", on_click=lambda: navigate(ScreenId.HOME, None)),
            BreadcrumbSegment("Builder", on_click=lambda: navigate(ScreenId.BUILDER, test_launch)),
            BreadcrumbSegment(_KIND_LABELS[test_launch.maze.kind]),
        ]
    else:
        assert maze is not None
        breadcrumb_segments = [
            BreadcrumbSegment("Home", on_click=lambda: navigate(ScreenId.HOME, None)),
            BreadcrumbSegment("Player", on_click=lambda: navigate(ScreenId.PLAYER, None)),
            BreadcrumbSegment(_KIND_LABELS[maze.kind]),
        ]
        if maze_name is not None:
            # Trailing 4th segment, appended *after* the kind-derived one --
            # never clickable, same as the kind segment (Story 4.13).
            breadcrumb_segments.append(BreadcrumbSegment(maze_name))
    top_bar = TopBar(
        frame,
        theme=theme,
        breadcrumb_segments=breadcrumb_segments,
        on_settings=open_settings,
        on_theme_toggle=toggle_theme,
        logo=logo_image,
    )
    top_bar.pack(fill="x")

    if state is None:
        gallery = MazeSelectionGallery(
            frame,
            theme=theme,
            maze_repository=maze_repository,
            settings_repository=settings_repository,
            navigate=navigate,
        )
        # Story 4.14: matches the Story 4.10 follow-up's gameplay/edit-area
        # margin (`SPACING["lg"]`/`["xl"]`) instead of the much larger
        # page-level `page-margin`/`section-gap` pair, closing the named
        # deferred-work item (navigating gallery -> gameplay no longer jumps
        # between two very different outer margins).
        gallery.pack(
            fill="both",
            expand=True,
            padx=SPACING["lg"],
            pady=SPACING["xl"],
        )
    else:
        assert maze is not None

        def on_name_saved(name: str) -> None:
            # Fires once, the first time a `generated` maze is saved
            # mid-session (Story 4.13) -- the breadcrumb has no 4th segment
            # yet at that point (an unsaved `generated` maze never gets a
            # `MazeWithName` state), so this always *appends*, never
            # overwrites. `on_kind_changed` (below) keeps growing the
            # existing kind segment in sync the same way it always has.
            top_bar.append_breadcrumb_segment(BreadcrumbSegment(name))

        gameplay = GameplayScreen(
            frame,
            maze,
            theme,
            maze_repository=maze_repository,
            settings_repository=settings_repository,
            navigate=navigate,
            initial_name=maze_name,
            # Saving a `GENERATED` maze transitions its `kind` to
            # `SAVED_RANDOM` mid-session -- without this, the trailing
            # kind-derived breadcrumb segment (built once above, from the
            # *original* `state.kind`) would keep showing "Random Maze"
            # forever.
            on_kind_changed=lambda kind: top_bar.set_breadcrumb_label(2, _KIND_LABELS[kind]),
            on_name_saved=on_name_saved,
            on_back_to_builder=(
                (lambda: navigate(ScreenId.BUILDER, test_launch)) if is_test_launch else None
            ),
        )
        # Story 4.10 follow-up: a small fixed margin around the whole
        # three-panel layout, not the page-level `page-margin`/
        # `section-gap` pair (that reads as a big blank border outside the
        # panels -- see the spec's Intent). Story 4.14 brings the gallery's
        # own `gallery.pack()` above in line with this same margin, closing
        # that follow-up's own deferred-work item.
        gameplay.pack(
            fill="both",
            expand=True,
            padx=SPACING["lg"],
            pady=SPACING["xl"],
        )

    return frame
