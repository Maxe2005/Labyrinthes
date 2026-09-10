"""`Stage` -- the grid-background container framing the HUD + `maze-frame`
column between a screen's two labeled side panels (Story 4.10).

Tk has no CSS-gradient/background-pattern equivalent, so the light
horizontal/vertical grid lines are hand-drawn on a plain `tk.Canvas` at a
fixed spacing, redrawn on every `<Configure>` (a resize invalidates the
previous line positions). Regular child widgets (the HUD row, the bordered
`maze-frame`) cannot be layered *over* canvas-drawn lines via `pack`/`grid`
-- Tk has no z-index across geometry managers -- so they are instead placed
inside one `content` frame embedded with `create_window()`. But `content`
is an opaque `tk.Frame` (same `colors.window` background as everything
else), and `create_window()` items always paint *above* canvas primitives
-- so sizing it to the canvas's full 0,0..width,height would hide every
gridline underneath it, defeating the whole point of a visible grid
backdrop. `_redraw()` therefore insets `content` by `_GRID_SPACING` on all
four sides, leaving a visible gridline margin around it; the `maze-frame`
packed inside `content` (`expand=True`, no `fill`, per Story 4.10's
follow-up -- Story 4.8 originally had it stretch with `fill="both"`) still
sizes its own fit-to-space baseline off `content`'s real available space --
just the inset area's, not the full canvas's -- while staying snug around
the drawn maze and centered in that space, via its own `<Configure>`
binding on `content` (not the canvas itself, and not the `maze-frame`/
canvas, which no longer resize with their parent).
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import ColorTokens

__all__ = ["Stage"]

# Fixed grid-line spacing, px -- an approximation of the locked mockups'
# CSS background-grid (Design Notes); not a `DESIGN.md`/`SPACING` token.
# Doubles as `content`'s inset margin on every side, so at least one full
# row/column of gridlines is always visible around it (see module
# docstring).
_GRID_SPACING = 22


class Stage(tk.Canvas):
    """A grid-background `tk.Canvas` hosting one inset `content` frame."""

    def __init__(self, parent: tk.Widget, *, colors: ColorTokens) -> None:
        super().__init__(parent, background=colors.window, highlightthickness=0)
        self._colors = colors
        self._content = tk.Frame(self, background=colors.window)
        self._window_id = self.create_window(0, 0, window=self._content, anchor="nw")
        self.bind("<Configure>", self._redraw)

    @property
    def content(self) -> tk.Widget:
        """The frame every caller packs its HUD/`maze-frame` column into."""
        return self._content

    def _redraw(self, event: tk.Event) -> None:
        inset = _GRID_SPACING
        content_width = max(0, event.width - 2 * inset)
        content_height = max(0, event.height - 2 * inset)
        self.coords(self._window_id, inset, inset)
        self.itemconfigure(self._window_id, width=content_width, height=content_height)
        self._redraw_lines(event.width, event.height)

    def _redraw_lines(self, width: int, height: int) -> None:
        self.delete("gridline")
        for x in range(0, width, _GRID_SPACING):
            self.create_line(x, 0, x, height, fill=self._colors.border, tags="gridline")
        for y in range(0, height, _GRID_SPACING):
            self.create_line(0, y, width, y, fill=self._colors.border, tags="gridline")
        # Grid lines are drawn behind the embedded `content` window either
        # way (canvas primitives always sit under `create_window()` items),
        # but `tag_lower` also keeps them behind each other consistently
        # and under any future non-window canvas item.
        self.tag_lower("gridline")
