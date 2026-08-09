"""`KbdTag` -- the always-visible shortcut pill (Story 1.6).

Per `EXPERIENCE.md`'s `kbd-tag` row, the shortcut stays printed on its
control at all times -- never hover-only. This module only renders that
printed label; it registers no key binding (Story 1.10's job).
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for

__all__ = ["KbdTag"]


def KbdTag(parent: tk.Widget, shortcut: str, *, theme: Theme) -> tk.Label:
    """A small always-visible pill printing `shortcut`, styled from `theme`.

    Background is a low-opacity tint matched to whatever panel/window
    surface it typically sits on; `DESIGN.md → components.kbd-tag` pins
    radius/text/padding but leaves the exact surface color to the
    embedding component, so `colors.panel` is used as that neutral tint.
    """
    colors = colors_for(theme)
    return tk.Label(
        parent,
        text=shortcut,
        font=TYPOGRAPHY.kbd.to_tk_font(),
        background=colors.panel,
        foreground=colors.ink_soft,
        padx=SPACING["xs"],
        pady=0,
    )
