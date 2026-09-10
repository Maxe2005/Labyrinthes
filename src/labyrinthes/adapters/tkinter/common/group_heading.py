"""`build_group_heading` -- the small uppercase label above a panel's button
group (Story 4.10).

Mirrors `settings_window.py`'s category-nav label (`TYPOGRAPHY.label`, the
10px/700 nav-label token) and `HudChip`'s `.upper()` convention (Tk fakes
CSS `text-transform` in Python since it has no native support -- applied
here, at the component level, never in `tokens.py` itself). A plain
function rather than a widget class: a group heading has no state or
behavior beyond its one-time text/font/color, so a `tk.Label` factory is
all every caller (`builder/edit_area.py`, `player/gameplay/sidebar.py`)
needs.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import TYPOGRAPHY, ColorTokens

__all__ = ["build_group_heading"]


def build_group_heading(parent: tk.Widget, text: str, colors: ColorTokens) -> tk.Label:
    """A small uppercase `tk.Label` heading for a panel's button group."""
    return tk.Label(
        parent,
        text=text.upper(),
        font=TYPOGRAPHY.label.to_tk_font(),
        background=colors.window,
        foreground=colors.ghost,
        anchor="w",
    )
