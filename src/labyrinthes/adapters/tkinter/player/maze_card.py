"""`MazeCard` -- one clickable maze card in `MazeSelectionGallery`'s grid (Story 4.14).

Mirrors the locked mockup's `.maze-card`: a small wall/entry/exit
thumbnail (`maze_wall_rendering`'s extracted drawing routines, called at
card scale), the maze's name, and its `W×H` dimensions. The focus-ring
recipe mirrors `IconButton`'s (`icon_btn.py:26-94`) rather than inventing
a new one: `takefocus=True`, `RESTING_RING_THICKNESS`/`FOCUS_RING_THICKNESS`
toggled on `<FocusIn>`/`<FocusOut>`, `<Return>`/`<space>` activation
alongside `<Button-1>` -- all three fire the caller-supplied `on_activate`.

Thumbnail sizing is this story's own decision (Design Notes, no locked
design token exists for it): a small fixed pixel budget
(`_THUMBNAIL_SPAN = 120`) with `cell_size = clamp(min(120 // w, 120 // h),
2, 10)` and `wall_width=1` (`MazeCanvas`'s `wall_width=2` reads as chunky
at this scale).
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.tokens import (
    FOCUS_RING_THICKNESS,
    RESTING_RING_THICKNESS,
    SPACING,
    TYPOGRAPHY,
    Theme,
    colors_for,
)
from labyrinthes.adapters.tkinter.player.maze_wall_rendering import (
    draw_entry_marker,
    draw_exit_marker,
    draw_walls,
)
from labyrinthes.domain.maze import Maze

__all__ = ["MazeCard"]

_THUMBNAIL_SPAN = 120
_MIN_CELL_SIZE = 2
_MAX_CELL_SIZE = 10
_WALL_WIDTH = 1
# A floor under the entry/exit marker radius, in px -- at the thumbnail's
# own smallest `cell_size` (2px), `marker_scale`'s usual 0.6 alone gives a
# ~0.6px radius, too small to tell the entry square from the exit diamond
# apart (NFR6). `1.5` is small enough to stay proportionate at the card's
# largest cell sizes too, where `marker_scale` already exceeds it.
_MIN_MARKER_RADIUS = 1.5


def _thumbnail_cell_size(width: int, height: int) -> int:
    """`clamp(min(120 // w, 120 // h), 2, 10)` -- see the module docstring."""
    raw = min(_THUMBNAIL_SPAN // width, _THUMBNAIL_SPAN // height)
    return max(_MIN_CELL_SIZE, min(_MAX_CELL_SIZE, raw))


class MazeCard(tk.Frame):
    """A focusable card: thumbnail + name + `W×H`, activated by click/Enter/Space."""

    def __init__(
        self,
        parent: tk.Widget,
        maze: Maze,
        name: str,
        *,
        theme: Theme,
        on_activate: Callable[[], None],
    ) -> None:
        colors = colors_for(theme)
        self._colors = colors
        self._maze = maze
        # `_maze_name`, not `_name` -- `tk.BaseWidget.__init__` (called
        # below via `super().__init__()`) sets its own `self._name` to the
        # widget's internal Tk pathname component, which would silently
        # clobber a same-named attribute set beforehand.
        self._maze_name = name
        self._on_activate = on_activate
        super().__init__(
            parent,
            background=colors.window,
            bd=0,
            takefocus=True,
            highlightthickness=RESTING_RING_THICKNESS,
            highlightbackground=colors.border,
            highlightcolor=colors.border,
        )

        cell_size = _thumbnail_cell_size(maze.grid.width, maze.grid.height)
        thumbnail = tk.Canvas(
            self,
            width=maze.grid.width * cell_size,
            height=maze.grid.height * cell_size,
            background=colors.corridor,
            highlightthickness=2,
            highlightbackground=colors.wall,
            highlightcolor=colors.wall,
            bd=0,
        )
        # Never `fill="x"` -- stretching the canvas widget past its drawn
        # content's own pixel size would leave a blank strip of exposed
        # corridor background beside the (fixed-coordinate) thumbnail
        # rather than rescaling it. Centered at its natural size instead.
        thumbnail.pack(padx=SPACING["sm"], pady=(SPACING["sm"], SPACING["xs"]))
        draw_walls(thumbnail, maze, cell_size, colors, wall_width=_WALL_WIDTH)
        draw_entry_marker(thumbnail, maze, cell_size, colors, min_radius=_MIN_MARKER_RADIUS)
        draw_exit_marker(thumbnail, maze, cell_size, colors, min_radius=_MIN_MARKER_RADIUS)

        name_label = tk.Label(
            self,
            text=name,
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            anchor="w",
            # No length ceiling exists anywhere in the save-name validation
            # -- an arbitrarily long name must wrap within the card's own
            # width instead of overflowing it and breaking the grid's
            # column alignment (mirrors the gallery's own empty-state
            # labels, which wrap at `wraplength=420`).
            wraplength=_THUMBNAIL_SPAN,
            justify="left",
        )
        name_label.pack(fill="x", padx=SPACING["sm"])

        meta_label = tk.Label(
            self,
            text=f"{maze.grid.width}×{maze.grid.height}",
            font=TYPOGRAPHY.body_secondary.to_tk_font(),
            background=colors.window,
            foreground=colors.ink_soft,
            anchor="w",
        )
        meta_label.pack(fill="x", padx=SPACING["sm"], pady=(0, SPACING["sm"]))

        for widget in (self, thumbnail, name_label, meta_label):
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", self._on_activated)

        self.bind("<Return>", self._on_activated)
        self.bind("<space>", self._on_activated)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_activated(self, _event: tk.Event | None = None) -> None:
        self._on_activate()

    def _on_focus_in(self, _event: tk.Event | None = None) -> None:
        self.configure(
            highlightthickness=FOCUS_RING_THICKNESS,
            highlightbackground=self._colors.accent,
            highlightcolor=self._colors.accent,
        )

    def _on_focus_out(self, _event: tk.Event | None = None) -> None:
        self.configure(
            highlightthickness=RESTING_RING_THICKNESS,
            highlightbackground=self._colors.border,
            highlightcolor=self._colors.border,
        )
