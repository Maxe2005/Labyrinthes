"""`IconButton` -- the 30x30 top-bar utility-action button (Story 1.6).

Per `EXPERIENCE.md`, this is reserved for Settings/theme-toggle in the top
bar -- tool side bars use `ToolButton` instead, for consistency of
shortcut/tooltip presentation.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.tokens import (
    FOCUS_RING_THICKNESS,
    RESTING_RING_THICKNESS,
    Theme,
    colors_for,
)
from labyrinthes.adapters.tkinter.common.tooltip import Tooltip

__all__ = ["IconButton"]

_SIZE = 30


class IconButton(tk.Frame):
    """A fixed 30x30px square button showing a single centered glyph."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        glyph: str,
        theme: Theme,
        tooltip: str | None = None,
        command: Callable[[], None] | None = None,
    ) -> None:
        colors = colors_for(theme)
        self._colors = colors
        self._focused = False
        super().__init__(
            parent,
            width=_SIZE,
            height=_SIZE,
            background=colors.panel,
            bd=0,
            takefocus=True,
            highlightthickness=RESTING_RING_THICKNESS,
            highlightbackground=colors.border,
            highlightcolor=colors.border,
        )
        self.pack_propagate(False)
        self._command = command

        self._label = tk.Label(
            self,
            text=glyph,
            background=colors.panel,
            foreground=colors.ink_soft,
        )
        self._label.pack(expand=True, fill="both")

        for widget in (self, self._label):
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", self._on_click)

        self.bind("<Return>", self._on_click)
        self.bind("<space>", self._on_click)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

        self._tooltip: Tooltip | None = None
        if tooltip is not None:
            self._tooltip = Tooltip(self, tooltip, theme=theme)

    def _on_click(self, _event: tk.Event | None = None) -> None:
        if self._command is not None:
            self._command()

    def _on_focus_in(self, _event: tk.Event | None = None) -> None:
        self._focused = True
        self.configure(
            highlightthickness=FOCUS_RING_THICKNESS,
            highlightbackground=self._colors.accent,
            highlightcolor=self._colors.accent,
        )

    def _on_focus_out(self, _event: tk.Event | None = None) -> None:
        self._focused = False
        self.configure(
            highlightthickness=RESTING_RING_THICKNESS,
            highlightbackground=self._colors.border,
            highlightcolor=self._colors.border,
        )
