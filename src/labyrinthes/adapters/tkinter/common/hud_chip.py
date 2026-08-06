"""`HudChip` -- the read-only HUD stat display (Story 1.6).

Per `EXPERIENCE.md`, all chips are read-only; only the caller decides when
to call `set_value()` (the Time chip on every tick, others on discrete
events). `typography.label`'s uppercase transform is applied here, in the
widget, per `DESIGN.md`'s explicit "apply at the component level" note --
`tokens.py` itself never mutates case.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for

__all__ = ["HudChip"]


class HudChip(tk.Frame):
    """A caption/value pair (e.g. "LEVEL" / "3"); `live=True` for the Time chip."""

    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        value: object,
        *,
        theme: Theme,
        live: bool = False,
    ) -> None:
        self._theme = theme
        self._live = live
        colors = colors_for(theme)
        background = colors.accent_bg if live else colors.panel
        super().__init__(
            parent,
            background=background,
            bd=0,
            highlightthickness=1,
            highlightbackground=colors.border,
            highlightcolor=colors.border,
        )

        self._caption = tk.Label(
            self,
            text=label.upper(),
            font=TYPOGRAPHY.label.to_tk_font(),
            background=background,
            foreground=colors.ink_soft,
            anchor="w",
        )
        self._caption.pack(anchor="w", padx=SPACING["xl"], pady=(SPACING["sm"], 0))

        value_color = colors.accent if live else colors.ink
        self._value_label = tk.Label(
            self,
            text=str(value),
            font=TYPOGRAPHY.hud_stat.to_tk_font(),
            background=background,
            foreground=value_color,
            anchor="w",
        )
        self._value_label.pack(anchor="w", padx=SPACING["xl"], pady=(0, SPACING["sm"]))

    def set_value(self, value: object) -> None:
        """Update the displayed value in place (the caption never changes)."""
        self._value_label.configure(text=str(value))
