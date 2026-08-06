"""The single composition root: builds the one `tk.Tk()` root and wires up the router.

The only module allowed to import concrete screen modules directly (AD-10) --
`Router` itself never imports one, so the "screens never import each other"
boundary stays trivially true rather than merely tested.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass

from labyrinthes.adapters.tkinter.builder.screen import mount as mount_builder
from labyrinthes.adapters.tkinter.home.screen import mount as mount_home
from labyrinthes.adapters.tkinter.player.screen import mount as mount_player
from labyrinthes.app.router import Router, ScreenId

__all__ = ["App", "build_app", "main"]


@dataclass(frozen=True)
class App:
    """The built application: its `Tk` root and the `Router` mounted inside it."""

    root: tk.Tk
    router: Router


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
        router.register(ScreenId.HOME, mount_home)
        router.register(ScreenId.BUILDER, mount_builder)
        router.register(ScreenId.PLAYER, mount_player)
        router.navigate(ScreenId.HOME)
    except Exception:
        root.destroy()
        raise

    return App(root=root, router=router)


def main() -> None:
    """Build the app and run its Tk main loop."""
    app = build_app()
    app.root.mainloop()
