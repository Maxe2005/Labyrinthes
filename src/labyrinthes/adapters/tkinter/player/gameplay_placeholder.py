"""`GameplayPlaceholder` -- Player's gameplay-placeholder view, plus Save (Story 2.3).

Replaces `screen.py`'s previous `_mount_gameplay_placeholder` free function
with a stateful `tk.Frame`: still just a plain-text summary of the mounted
`Maze` -- no wall/HUD/ball rendering, that's Story 2.4's job -- but now
owns a mutable `self._maze` so a save can swap it for the repository's
returned value and re-render in place, without re-navigating.

A "Save" `PillButton` (the `save_maze` keybinding, "s") is shown only when
`self._maze.kind is MazeKind.GENERATED` -- an already-`SAVED_RANDOM`/
`CLASSIC` maze reaching this placeholder shows no Save affordance at all,
matching this story's Boundaries & Constraints. Clicking it opens a
`SaveMazeDialog` (parented to `self`, not the app's persistent container --
nothing here is worth surviving a navigate-away), pre-loaded with
`maze_repository.list_names(MazeKind.SAVED_RANDOM)` for its own arm/confirm
overwrite check. Confirming it transitions the maze via
`dataclasses.replace(maze, kind=MazeKind.SAVED_RANDOM, id=None)` -- never
an in-place mutation, and never a transition performed by the repository
itself (`MazeRepository.save()`'s contract explicitly leaves `kind` alone)
-- calls `maze_repository.save(...)`, stores the returned `Maze` (carrying
the freshly minted `MazeId`), and re-renders, which destroys the Save
button since the maze is no longer `GENERATED`.

The "s" shortcut is bound to the Save button's own widget, not this frame,
via `bind_shortcut(self._save_button, ...)`: the button is conditionally
destroyed and rebuilt whenever `_build()` re-renders (any re-render after a
successful save, since the maze is no longer `GENERATED`), and
`bind_shortcut`'s existing per-sequence token/`<Destroy>` cleanup (see that
module's docstring) unregisters "s" automatically when the button
disappears -- binding to this longer-lived frame instead would leave a
stale binding able to re-open the dialog and re-mint an id for an
already-saved maze.
"""

from __future__ import annotations

import dataclasses
import tkinter as tk

from labyrinthes.adapters.tkinter.common.keybindings import bind_shortcut, keybinding
from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for
from labyrinthes.adapters.tkinter.player.save_maze_dialog import SaveMazeDialog
from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.domain.maze import Maze, MazeKind

__all__ = ["GameplayPlaceholder"]


class GameplayPlaceholder(tk.Frame):
    """Plain-text summary of the mounted `Maze`, plus Save when it's `GENERATED`."""

    def __init__(
        self,
        parent: tk.Widget,
        maze: Maze,
        theme: Theme,
        *,
        maze_repository: MazeRepository,
    ) -> None:
        colors = colors_for(theme)
        super().__init__(parent, background=colors.window)
        self._theme = theme
        self._maze_repository = maze_repository
        self._maze = maze
        self._build()

    def _build(self) -> None:
        for child in self.winfo_children():
            child.destroy()
        if hasattr(self, "_save_button"):
            del self._save_button

        colors = colors_for(self._theme)
        summary = (
            f"Gameplay placeholder — {self._maze.grid.width}×{self._maze.grid.height} maze, "
            f"kind={self._maze.kind.value}, entry={self._maze.entry!r}, exit={self._maze.exit!r}"
        )
        tk.Label(
            self,
            text=summary,
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            wraplength=600,
            justify="left",
        ).pack(anchor="w")

        if self._maze.kind is MazeKind.GENERATED:
            save_kb = keybinding("save_maze")
            self._save_button = PillButton(
                self,
                save_kb.label,
                theme=self._theme,
                primary=True,
                shortcut=save_kb.display,
                command=self._on_save_clicked,
            )
            self._save_button.pack(anchor="w", pady=(SPACING["lg"], 0))
            bind_shortcut(self._save_button, save_kb, self._on_save_clicked)

    def _on_save_clicked(self) -> None:
        existing_names = self._maze_repository.list_names(MazeKind.SAVED_RANDOM)
        SaveMazeDialog(
            self,
            theme=self._theme,
            existing_names=existing_names,
            on_confirm=self._on_save_confirmed,
        )

    def _on_save_confirmed(self, name: str) -> None:
        candidate = dataclasses.replace(self._maze, kind=MazeKind.SAVED_RANDOM, id=None)
        self._maze = self._maze_repository.save(candidate, name)
        self._build()
