"""`SettingsWindow` -- the non-modal Settings dialog every screen's icon opens (Story 1.8).

Left-hand category navigation with exactly one category, "Appearance",
holding placeholder content. Ball/Difficulty/Shortcuts don't exist as
domain concepts yet (Epics 2/3, Story 1.10) -- stubbing categories with
nothing behind them would invite dead UI, so only the category-nav
*structure* is built now (see the spec's Design Notes). Never calls
`grab_set()`: the screen that opened this window stays fully mounted and
interactive behind it.

Lifecycle (Story 1.11): each screen's `open_settings()` constructs this as
`SettingsWindow(parent, theme=theme)` -- a real Tk child `Toplevel` of the
app's persistent container (the same `parent` `Router` passes into every
screen's `mount()`), not of the screen's own `frame`. Earlier (Stories
1.8, 1.9, 1.10) it was parented to `frame` instead, so `Router.navigate()`
mounting the next screen and then calling `previous_frame.destroy()` would
cascade-destroy this window too, via Tk's ordinary parent-child `Toplevel`
semantics -- silently closing any open `SettingsWindow` as a side effect
of navigating away from the screen that opened it. That was deferred three
times as "nothing stateful to lose yet" (`deferred-work.md`'s Story 1.8
and 1.10 entries; Story 1.9 hit the identical mechanism but never got its
own ledger entry -- see the 1.10 entry's cross-reference), until the Epic
1 retrospective judged the deferral no longer safe once Epic 2 lands real
stateful gameplay UI. Story 1.11 fixes it: `parent` outlives every
`previous_frame.destroy()` call, so a `SettingsWindow` opened on any
screen now survives navigating away from it, staying open and interactive
over whichever screen is mounted next.

Residual gap, deliberately not fixed here: a `SettingsWindow` that
survives a theme toggle keeps rendering the `Theme` it was constructed
with -- nothing re-themes it in place, since it's no longer torn down and
rebuilt by the toggle's full re-navigate the way the screen underneath it
is. Not reachable in a way that matters yet ("Appearance" is still only
`_APPEARANCE_PLACEHOLDER`, so there's no themed control whose staleness
would be visible beyond the window's own background/text colors); revisit
once `SettingsWindow` has content worth keeping in sync live.
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
