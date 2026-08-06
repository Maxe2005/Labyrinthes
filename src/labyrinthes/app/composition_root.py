"""The single composition root: builds the one `tk.Tk()` root and wires up the router.

The only module allowed to import concrete screen modules directly (AD-10) --
`Router` itself never imports one, so the "screens never import each other"
boundary stays trivially true rather than merely tested.

Story 1.8 adds one more piece of wiring: `Router`/`Router.register`/
`MountFn` stayed exactly as Story 1.7 left them (2-arg, `(parent, state)`),
but every screen's `mount()` now takes a third `navigate: NavigateFn`
parameter. This module is what bridges the gap -- it builds one `navigate`
closure over `router.navigate` and binds it into each screen's 3-arg
`mount` before `register()`-ing the resulting 2-arg adapter, so `Router`
itself never needs to know `navigate` exists.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass

from labyrinthes.adapters.tkinter.builder.screen import mount as mount_builder
from labyrinthes.adapters.tkinter.common.navigation import NavigateFn, ScreenMountFn
from labyrinthes.adapters.tkinter.home.screen import mount as mount_home
from labyrinthes.adapters.tkinter.player.screen import mount as mount_player
from labyrinthes.app.router import MountFn, Router, ScreenId
from labyrinthes.domain.maze import Maze

__all__ = ["App", "build_app", "main"]


@dataclass(frozen=True)
class App:
    """The built application: its `Tk` root and the `Router` mounted inside it."""

    root: tk.Tk
    router: Router


def _bind_navigate(mount: ScreenMountFn, navigate: NavigateFn) -> MountFn:
    """Adapt a screen's 3-arg `mount` into the 2-arg `MountFn` `Router.register()` expects.

    Binds the same `navigate` closure into every screen rather than each
    screen threading it through by hand -- `Router`'s own contract/tests
    (Story 1.7) stay untouched by this story.
    """

    def bound(parent: tk.Widget, state: Maze | None) -> tk.Frame:
        return mount(parent, state, navigate)

    return bound


def build_app() -> App:
    """Create the single `Tk()` root, register all three screens, and navigate to Home.

    If wiring fails partway through (e.g. Home's `mount()` raises), the
    just-created `root` is destroyed before the exception propagates rather
    than being leaked as an orphaned, never-shown window.
    """
    root = tk.Tk()
    try:
        container = tk.Frame(root)
        container.pack(fill="both", expand=True)

        router = Router(container)

        def navigate(screen_id: ScreenId, state: Maze | None = None) -> None:
            router.navigate(screen_id, state)

        router.register(ScreenId.HOME, _bind_navigate(mount_home, navigate))
        router.register(ScreenId.BUILDER, _bind_navigate(mount_builder, navigate))
        router.register(ScreenId.PLAYER, _bind_navigate(mount_player, navigate))
        router.navigate(ScreenId.HOME)
    except Exception:
        root.destroy()
        raise

    return App(root=root, router=router)


def main() -> None:
    """Build the app and run its Tk main loop."""
    app = build_app()
    app.root.mainloop()
