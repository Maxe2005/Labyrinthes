"""The single composition root: builds the one `tk.Tk()` root and wires up the router.

The only module allowed to import concrete screen modules directly (AD-10) --
`Router` itself never imports one, so the "screens never import each other"
boundary stays trivially true rather than merely tested.

Story 1.8 added one piece of wiring: `Router`/`Router.register`/`MountFn`
stayed exactly as Story 1.7 left them (2-arg, `(parent, state)`), but every
screen's `mount()` took a third `navigate: NavigateFn` parameter, bridged
here. Story 1.9 extends the same bridge: `mount()` now also takes
`theme: Theme` and `toggle_theme: ToggleThemeFn`, sourced from one
`ThemeController` built from a `SettingsRepository`. This module also
tracks the `state` most recently passed to `navigate()` and subscribes a
listener that re-navigates the currently-mounted screen with that state
whenever the theme changes -- `Tk` widgets have no reactive re-theming
primitive, so a full re-navigate (already `Router.navigate()`'s only mode
of operation) is the smallest correct way to apply a new theme's tokens.

Story 2.1 adds one more piece of wiring, scoped to Player only: its
`mount()` takes a required, keyword-only `maze_repository: MazeRepository`
that Home/Builder don't need. Rather than widening the shared
`ScreenMountFn` (which would force Home/Builder to accept-but-ignore a
port they don't use, and touch `_bind_screen()`/every existing screen
test), `mount_player` is wrapped in `functools.partial(mount_player,
maze_repository=...)` *before* it reaches the untouched `_bind_screen()`
-- see the story's Design Notes. Story 2.2 widens that same partial with
one more keyword-only port, `settings_repository` (already a `build_app()`
parameter for `ThemeController`, just not yet threaded to Player) -- for
reading the FR-4 random-maze size bounds.

Story 2.10 widens the same partial pattern to Home and Builder: their
`mount()`s now also take a required, keyword-only `settings_repository`
(for `SettingsWindow`'s confirmation toggles, reachable from every screen's
top bar), so `mount_home`/`mount_builder` are each `partial`-bound with it
here, mirroring Player's Story 2.2 binding below.

Story 4.10's follow-up fixes the root window's size once, at creation, from
a `shared`-scope `window_width`/`window_height` setting
(`application/window_settings.py`) instead of letting it take whatever size
the just-mounted screen naturally requests (Story 4.8's approach, which
visibly jumped between Home's small size and Builder/Player's larger one on
every navigation). `root.geometry()` is called exactly once, with both size
and centered position together, before Home is ever mounted -- the window
never auto-resizes again across navigation; every screen still fills
whatever that fixed size is via the existing `fill="both", expand=True`
pack chain.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from functools import partial

from labyrinthes.adapters.storage.csv_maze_repository import CsvMazeRepository
from labyrinthes.adapters.storage.json_settings_repository import JsonSettingsRepository
from labyrinthes.adapters.tkinter.builder.screen import mount as mount_builder
from labyrinthes.adapters.tkinter.common.keybindings import bind_shortcut, keybinding
from labyrinthes.adapters.tkinter.common.navigation import (
    BuilderTestLaunch,
    NavigateFn,
    ScreenMountFn,
)
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.adapters.tkinter.home.screen import mount as mount_home
from labyrinthes.adapters.tkinter.player.screen import mount as mount_player
from labyrinthes.app.router import MountFn, Router, ScreenId
from labyrinthes.app.theme_controller import ThemeController
from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.application.window_settings import read_window_size
from labyrinthes.domain.maze import Maze

__all__ = ["App", "build_app", "main"]


@dataclass(frozen=True)
class App:
    """The built application: its `Tk` root and the `Router` mounted inside it."""

    root: tk.Tk
    router: Router


def _bind_screen(
    mount: ScreenMountFn, navigate: NavigateFn, theme_controller: ThemeController
) -> MountFn:
    """Adapt a screen's 5-arg `mount` into the 2-arg `MountFn` `Router.register()` expects.

    Binds the same `navigate` closure into every screen rather than each
    screen threading it through by hand -- `Router`'s own contract/tests
    (Story 1.7) stay untouched by this story. `theme_controller.theme` is
    read fresh inside `bound()` on every call (not captured once at
    registration time), so a re-navigate triggered after a theme toggle
    picks up the live value rather than whatever theme was active when
    `register()` ran.
    """

    def bound(parent: tk.Widget, state: Maze | None | BuilderTestLaunch) -> tk.Frame:
        return mount(parent, state, navigate, theme_controller.theme, theme_controller.toggle)

    return bound


def build_app(
    settings_repository: SettingsRepository | None = None,
    maze_repository: MazeRepository | None = None,
) -> App:
    """Create the single `Tk()` root, register all three screens, and navigate to Home.

    `settings_repository` defaults to a real `JsonSettingsRepository()`
    (the default, relative `./settings/` root); `maze_repository` mirrors
    that default, a real `CsvMazeRepository()`. Tests inject a
    `tmp_path`-rooted or in-memory instance of either instead so they never
    touch those real on-disk locations.

    If wiring fails partway through (e.g. Home's `mount()` raises), the
    just-created `root` is destroyed before the exception propagates rather
    than being leaked as an orphaned, never-shown window.
    """
    if settings_repository is None:
        settings_repository = JsonSettingsRepository()
    if maze_repository is None:
        maze_repository = CsvMazeRepository()

    root = tk.Tk()
    try:
        # Story 4.10 follow-up (FR-31 superseding Story 4.8's natural-size
        # approach): read the fixed initial size once, before anything is
        # mounted, and set it -- together with a centered position -- in
        # one `.geometry()` call. `winfo_screenwidth()`/`winfo_screenheight()`
        # are available immediately after `Tk()` construction (screen
        # dimensions, not a layout result), unlike `winfo_width()`/
        # `winfo_height()` which need a real geometry pass first.
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        width, height = read_window_size(settings_repository, screen_width, screen_height)
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")

        container = tk.Frame(root)
        container.pack(fill="both", expand=True)

        router = Router(container)
        theme_controller = ThemeController(settings_repository)

        last_state: Maze | None | BuilderTestLaunch = None

        def navigate(screen_id: ScreenId, state: Maze | None | BuilderTestLaunch = None) -> None:
            nonlocal last_state
            last_state = state
            router.navigate(screen_id, state)

        def on_theme_change(new_theme: Theme) -> None:
            # No-op before the first `navigate()` (`current_screen_id`
            # still `None`) -- not reachable in practice since `build_app`
            # always navigates to Home before returning, but guarded per
            # the spec's I/O matrix all the same.
            current_screen_id = router.current_screen_id
            if current_screen_id is not None:
                navigate(current_screen_id, last_state)

        theme_controller.subscribe(on_theme_change)

        router.register(
            ScreenId.HOME,
            _bind_screen(
                partial(mount_home, settings_repository=settings_repository),
                navigate,
                theme_controller,
            ),
        )
        router.register(
            ScreenId.BUILDER,
            _bind_screen(
                partial(
                    mount_builder,
                    maze_repository=maze_repository,
                    settings_repository=settings_repository,
                ),
                navigate,
                theme_controller,
            ),
        )
        router.register(
            ScreenId.PLAYER,
            _bind_screen(
                partial(
                    mount_player,
                    maze_repository=maze_repository,
                    settings_repository=settings_repository,
                ),
                navigate,
                theme_controller,
            ),
        )
        # Through the `navigate` closure, not `router.navigate()` directly,
        # so `last_state` is tracked from the very first screen onward --
        # correctness here would otherwise depend on Home always being
        # stateless rather than being structurally guaranteed.
        navigate(ScreenId.HOME)

        # Resizable + F11 fullscreen on the one `Tk()` root (Story 4.8).
        # The window's size/position was already fixed above, before this
        # point -- Tk's default is already resizable in both directions;
        # `.resizable(True, True)` makes that explicit rather than assumed.
        root.resizable(True, True)

        is_fullscreen = False

        def toggle_root_fullscreen() -> None:
            # Tracked as a plain bool, not read back from Tk (`.attributes
            # ("-fullscreen")` has no reliable getter across window
            # managers -- see the story's Design Notes) -- this closure is
            # the single source of truth for whether the root is currently
            # fullscreen.
            nonlocal is_fullscreen
            is_fullscreen = not is_fullscreen
            root.attributes("-fullscreen", is_fullscreen)

        bind_shortcut(root, keybinding("toggle_fullscreen"), toggle_root_fullscreen)
    except Exception:
        root.destroy()
        raise

    return App(root=root, router=router)


def main() -> None:
    """Build the app and run its Tk main loop."""
    app = build_app()
    app.root.mainloop()
