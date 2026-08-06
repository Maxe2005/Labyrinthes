"""`SettingsWindow` -- the non-modal Settings dialog every screen's icon opens (Story 1.8).

Left-hand category navigation with exactly one category, "Appearance",
holding placeholder content. Ball/Difficulty/Shortcuts don't exist as
domain concepts yet (Epics 2/3, Story 1.10) -- stubbing categories with
nothing behind them would invite dead UI, so only the category-nav
*structure* is built now (see the spec's Design Notes). Never calls
`grab_set()`: the screen that opened this window stays fully mounted and
interactive behind it.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for

__all__ = ["SettingsWindow"]

_CATEGORIES = ("Appearance",)
_APPEARANCE_PLACEHOLDER = "Appearance settings are coming soon."


class SettingsWindow(tk.Toplevel):
    """A non-modal Settings dialog: left-hand category list, right-hand content pane."""

    def __init__(self, parent: tk.Widget, *, theme: Theme) -> None:
        super().__init__(parent)
        self.title("Settings")
        colors = colors_for(theme)
        self.configure(background=colors.window)

        nav = tk.Frame(self, background=colors.panel)
        nav.pack(side="left", fill="y")
        for category in _CATEGORIES:
            # `TYPOGRAPHY.label` (10px/700), not `.body` -- `DESIGN.md`'s
            # `settings-window` component spec calls for category-nav text
            # in the small nav-label token, the same one used for other
            # group-label elements in the design system.
            tk.Label(
                nav,
                text=category,
                font=TYPOGRAPHY.label.to_tk_font(),
                background=colors.panel,
                foreground=colors.ink,
                anchor="w",
            ).pack(fill="x", padx=SPACING["lg"], pady=SPACING["sm"])

        content = tk.Frame(self, background=colors.window)
        content.pack(side="left", fill="both", expand=True)
        tk.Label(
            content,
            text=_APPEARANCE_PLACEHOLDER,
            font=TYPOGRAPHY.body_secondary.to_tk_font(),
            background=colors.window,
            foreground=colors.ink_soft,
            wraplength=280,
            justify="left",
        ).pack(padx=SPACING["2xl"], pady=SPACING["2xl"])
