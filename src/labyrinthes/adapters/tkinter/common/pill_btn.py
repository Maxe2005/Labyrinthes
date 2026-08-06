"""`PillButton` -- the top-bar action button, default + primary variants (Story 1.6).

Per `EXPERIENCE.md`, at most one `primary` pill sits on a screen at a time
(the single most likely next action); every other pill stays in the
default (non-filled) style.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.kbd_tag import KbdTag
from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for

__all__ = ["PillButton"]


class PillButton(tk.Frame):
    """A rounded-look action pill: label plus an optional trailing `kbd-tag`."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        *,
        theme: Theme,
        primary: bool = False,
        shortcut: str | None = None,
        command: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent, bd=0, highlightthickness=1)
        self._theme = theme
        self._primary = primary
        self._command = command

        self._label = tk.Label(self, text=text, font=TYPOGRAPHY.body.to_tk_font())
        self._label.pack(side="left", padx=(SPACING["lg"], SPACING["xs"]), pady=SPACING["xs"])

        self._kbd: tk.Label | None = None
        if shortcut is not None:
            self._kbd = KbdTag(self, shortcut, theme=theme)
            self._kbd.pack(side="right", padx=(0, SPACING["lg"]))
        else:
            # No trailing kbd-tag: give the label its own right-hand padding
            # instead of the tighter kbd-tag gap above.
            self._label.pack_configure(padx=(SPACING["lg"], SPACING["lg"]))

        for widget in self._clickable_widgets():
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", self._on_click)

        self._apply_style()

    def _clickable_widgets(self) -> tuple[tk.Widget, ...]:
        widgets: tuple[tk.Widget, ...] = (self, self._label)
        if self._kbd is not None:
            widgets += (self._kbd,)
        return widgets

    def _on_click(self, _event: tk.Event | None = None) -> None:
        if self._command is not None:
            self._command()

    def _apply_style(self) -> None:
        colors = colors_for(self._theme)
        if self._primary:
            background = colors.accent if self._theme is Theme.LIGHT else colors.accent_strong_dark
            text_color = colors.window
        else:
            background = colors.panel
            text_color = colors.ink
        border = background if self._primary else colors.border
        self.configure(background=background, highlightbackground=border, highlightcolor=border)
        self._label.configure(background=background, foreground=text_color)
        if self._kbd is not None:
            self._kbd.configure(background=background)
