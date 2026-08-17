"""Home screen: the app's sole general navigation hub (Story 1.8).

Never imports `builder`/`player` or `adapters/storage/` (AD-1, AD-9). Renders
no `Breadcrumb` of its own -- navigation depth 0, matching the locked
`key-home.html` mockup (see the spec's Design Notes) -- only the `TopBar`'s
brand mark/wordmark plus `PillButton` entry points into Builder/Player/a new
sketch.

Story 1.10 wires the Builder/Player entry points to the canonical keybinding
table (`keybindings.py`): each `PillButton`'s printed `kbd-tag` and its real
`bind_shortcut()` registration both derive from the same `Keybinding`, and
each navigate action is a single named function passed to both, so the
`command=` click path and the "B"/"P" key-press path can never diverge.

Story 2.10 threads a required, keyword-only `settings_repository` port
through `mount()` (same shape Player already had, Story 2.1/2.2) so Home's
`open_settings()` can hand it to `SettingsWindow` -- the Settings dialog is
reachable from any screen's top bar, so its confirmation toggles must work
from Home too (AC-3). `composition_root.build_app()` partial-binds it in.

Story 3.1 adds a third entry point, "New Maze" (keybinding "C"): it opens
`NewMazeDialog`, a `tk.Toplevel` parented to `frame` (Home's own screen
frame -- the calling widget), not `parent` (the app's persistent
container) -- unlike `SettingsWindow`, nothing about this dialog is worth
surviving a navigate-away, so it is torn down along with `frame` if the
user navigates away from Home while it's still open (see
`new_maze_dialog.py`'s module docstring). On confirm, the dialog hands
back a fully-formed `Maze` (`kind=MazeKind.SKETCH`, `id=None`,
`grid=Grid.filled(columns, rows)`) that Home simply forwards to
`navigate(ScreenId.PLAYER, maze)` -- Home never constructs the `Maze`
itself, keeping that domain-shaping logic inside the dialog.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common import (
    SPACING,
    NavigateFn,
    NewMazeDialog,
    PillButton,
    ScreenId,
    SettingsWindow,
    Theme,
    ToggleThemeFn,
    TopBar,
    bind_shortcut,
    keybinding,
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
    """Build the Home screen `Frame`, parented under `parent`.

    `state` is accepted per the shared `mount(parent, state, navigate,
    theme, toggle_theme)` interface (AD-10) but unused here -- Home has no
    maze state to receive. `settings_repository` (Story 2.10) is required
    and keyword-only, bound by `composition_root` via `functools.partial`.
    """
    frame = tk.Frame(parent)

    def open_settings() -> None:
        # `parent` (not `frame`) as the `Toplevel`'s master (Story 1.11):
        # `parent` is the app's persistent container, never destroyed by
        # `Router.navigate()`, so `SettingsWindow` survives navigating away
        # from Home instead of being torn down as a cascade side effect of
        # `frame.destroy()`. See `SettingsWindow`'s module docstring.
        SettingsWindow(parent, theme=theme, settings_repository=settings_repository)

    top_bar = TopBar(
        frame,
        theme=theme,
        breadcrumb_segments=None,
        on_settings=open_settings,
        on_theme_toggle=toggle_theme,
    )
    top_bar.pack(fill="x")

    entry_points = tk.Frame(frame)
    entry_points.pack(pady=SPACING["5xl"])

    def go_to_builder() -> None:
        navigate(ScreenId.BUILDER, None)

    def go_to_player() -> None:
        navigate(ScreenId.PLAYER, None)

    def go_to_new_maze() -> None:
        NewMazeDialog(
            frame,
            theme=theme,
            settings_repository=settings_repository,
            on_confirm=lambda maze: navigate(ScreenId.PLAYER, maze),
        )

    # Looked up once each so the printed button text, the printed kbd-tag,
    # and the real binding all read from the exact same `Keybinding` entry
    # -- not just the same *key*, but the same *label* too.
    open_builder_kb = keybinding("open_builder")
    open_player_kb = keybinding("open_player")
    open_new_maze_kb = keybinding("open_new_maze")

    PillButton(
        entry_points,
        open_builder_kb.label,
        theme=theme,
        shortcut=open_builder_kb.display,
        command=go_to_builder,
    ).pack(side="left", padx=SPACING["sm"])
    PillButton(
        entry_points,
        open_player_kb.label,
        theme=theme,
        shortcut=open_player_kb.display,
        command=go_to_player,
    ).pack(side="left", padx=SPACING["sm"])
    PillButton(
        entry_points,
        open_new_maze_kb.label,
        theme=theme,
        shortcut=open_new_maze_kb.display,
        command=go_to_new_maze,
    ).pack(side="left", padx=SPACING["sm"])

    bind_shortcut(frame, open_builder_kb, go_to_builder)
    bind_shortcut(frame, open_player_kb, go_to_player)
    bind_shortcut(frame, open_new_maze_kb, go_to_new_maze)

    return frame
