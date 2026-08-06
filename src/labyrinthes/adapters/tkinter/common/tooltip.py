"""`Tooltip` -- a generic hover-attach popup (Story 1.6).

Every primitive that needs a hover description (`tool-btn`, `icon-btn`,
`pill-btn`, ...) reuses this one class rather than reimplementing its own
`<Enter>`/`<Leave>` handling. Per `EXPERIENCE.md`'s `kbd-tag` row, the
tooltip text is always a plain-language description of the action's
*effect* -- it must never restate the printed shortcut; that restatement
rule is the caller's responsibility (the text passed in), not something
this class can enforce.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for

__all__ = ["Tooltip"]


class Tooltip:
    """Shows a small `Toplevel` popup near `widget` on hover, hides it on leave."""

    def __init__(self, widget: tk.Widget, text: str, *, theme: Theme) -> None:
        self._widget = widget
        self._text = text
        self._theme = theme
        self._popup: tk.Toplevel | None = None
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")

    def _on_enter(self, _event: tk.Event | None = None) -> None:
        if self._popup is not None:
            return
        colors = colors_for(self._theme)
        popup = tk.Toplevel(self._widget)
        popup.wm_overrideredirect(True)
        x = self._widget.winfo_rootx()
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + SPACING["xs"]
        popup.wm_geometry(f"+{x}+{y}")
        tk.Label(
            popup,
            text=self._text,
            font=TYPOGRAPHY.body_secondary.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            highlightthickness=1,
            highlightbackground=colors.border,
            highlightcolor=colors.border,
            padx=SPACING["sm"],
            pady=SPACING["xs"],
            wraplength=240,
            justify="left",
        ).pack()
        self._popup = popup

    def _on_leave(self, _event: tk.Event | None = None) -> None:
        if self._popup is not None:
            self._popup.destroy()
            self._popup = None
