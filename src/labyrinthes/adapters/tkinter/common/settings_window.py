"""`SettingsWindow` -- the non-modal Settings dialog every screen's icon opens (Story 1.8).

Left-hand category navigation holding category content: "Appearance"
(placeholder) and "Confirmation" (Story 2.10's four per-action toggles).
Ball/Difficulty/Shortcuts don't exist as domain concepts yet (Epics 2/3,
Story 1.10) -- stubbing categories with nothing behind them would invite
dead UI, so only the category-nav *structure* is built now (see the spec's
Design Notes). Never calls `grab_set()`: the screen that opened this
window stays fully mounted and interactive behind it.

Lifecycle (Story 1.11): each screen's `open_settings()` constructs this as
`SettingsWindow(parent, theme=theme, settings_repository=...)` -- a real Tk
child `Toplevel` of the app's persistent container (the same `parent`
`Router` passes into every screen's `mount()`), not of the screen's own
`frame`. Earlier (Stories
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

Story 2.10 gives this window its first real content and the port it
previously lacked. `__init__` now takes a required, keyword-only
`settings_repository: SettingsRepository`; the category nav becomes a real
focusable control (NFR6) -- `<Button-1>`/`<Return>`/`<Space>` select a
category, the active one renders in `colors.accent`, a focus ring follows
`<FocusIn>` (Story 1.10 tokens); and a new "Confirmation" category holds
four themed `tk.Checkbutton` rows, one per Player action, each initialized
from its `read_confirm_*` reader and persisted via its `write_confirm_*`
writer on toggle. Each reader is called at window-construction time, so a
window opened *after* a toggle reflects the stored value (AC-3's
persistence surface); the `JsonSettingsRepository` reads fresh from disk
on every call, and the gated Player actions read fresh at action time --
see the story's Design Notes on AC-3 being structural.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import (
    FOCUS_RING_THICKNESS,
    RESTING_RING_THICKNESS,
    SPACING,
    TYPOGRAPHY,
    Theme,
    colors_for,
)
from labyrinthes.application.confirmation_settings import (
    read_confirm_invalid_input,
    read_confirm_level_change,
    read_confirm_restart,
    read_confirm_switch_maze,
    write_confirm_invalid_input,
    write_confirm_level_change,
    write_confirm_restart,
    write_confirm_switch_maze,
)
from labyrinthes.application.settings_repository import SettingsRepository

__all__ = ["SettingsWindow"]

_CATEGORIES = ("Appearance", "Confirmation")
_APPEARANCE_PLACEHOLDER = "Appearance settings are coming soon."

# `(row text, reader, writer)` for the four Confirmation toggles -- one per
# Player action, in the order the spec's AC-1 action list names them.
_CONFIRMATION_TOGGLES = (
    ("Confirm before switching/restarting mazes", read_confirm_switch_maze, write_confirm_switch_maze),
    ("Confirm before restarting", read_confirm_restart, write_confirm_restart),
    ("Confirm before changing level", read_confirm_level_change, write_confirm_level_change),
    ("Alert me about invalid input", read_confirm_invalid_input, write_confirm_invalid_input),
)


class SettingsWindow(tk.Toplevel):
    """A non-modal Settings dialog: left-hand category list, right-hand content pane."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        settings_repository: SettingsRepository,
    ) -> None:
        super().__init__(parent)
        self.title("Settings")
        self._theme = theme
        self._settings_repository = settings_repository
        self._nav_focused: dict[str, bool] = {}
        colors = colors_for(theme)
        self.configure(background=colors.window)

        nav = tk.Frame(self, background=colors.panel)
        nav.pack(side="left", fill="y")
        self._category_labels: dict[str, tk.Label] = {}
        for category in _CATEGORIES:
            # `TYPOGRAPHY.label` (10px/700), not `.body` -- `DESIGN.md`'s
            # `settings-window` component spec calls for category-nav text
            # in the small nav-label token, the same one used for other
            # group-label elements in the design system.
            label = tk.Label(
                nav,
                text=category,
                font=TYPOGRAPHY.label.to_tk_font(),
                background=colors.panel,
                foreground=colors.ink,
                anchor="w",
                takefocus=True,
                highlightthickness=RESTING_RING_THICKNESS,
                cursor="hand2",
            )
            label.pack(fill="x", padx=SPACING["lg"], pady=SPACING["sm"])
            label.bind("<Button-1>", self._make_select_handler(category))
            label.bind("<Return>", self._make_select_handler(category))
            label.bind("<space>", self._make_select_handler(category))
            label.bind("<FocusIn>", self._make_focus_handler(category, True))
            label.bind("<FocusOut>", self._make_focus_handler(category, False))
            self._category_labels[category] = label

        self._content = tk.Frame(self, background=colors.window)
        self._content.pack(side="left", fill="both", expand=True)
        self._select_category(_CATEGORIES[0])

    def _make_select_handler(self, category: str):
        def _select(_event: tk.Event | None = None) -> None:
            self._select_category(category)

        return _select

    def _make_focus_handler(self, category: str, focused: bool):
        def _on_focus(_event: tk.Event | None = None) -> None:
            self._nav_focused[category] = focused
            self._apply_nav_style(category)

        return _on_focus

    def _apply_nav_style(self, category: str) -> None:
        label = self._category_labels[category]
        colors = colors_for(self._theme)
        active = category == self._active_category
        foreground = colors.accent if active else colors.ink
        if self._nav_focused.get(category, False):
            label.configure(
                foreground=foreground,
                highlightthickness=FOCUS_RING_THICKNESS,
                highlightbackground=colors.accent,
                highlightcolor=colors.accent,
            )
        else:
            label.configure(
                foreground=foreground,
                highlightthickness=RESTING_RING_THICKNESS,
                highlightbackground=colors.panel,
                highlightcolor=colors.panel,
            )

    def _select_category(self, name: str) -> None:
        self._active_category = name
        for category in _CATEGORIES:
            self._apply_nav_style(category)

        for child in self._content.winfo_children():
            child.destroy()
        self._confirmation_rows = {}
        if name == "Appearance":
            self._build_appearance(self._content)
        else:
            self._build_confirmation(self._content)

    def _build_appearance(self, container: tk.Frame) -> None:
        colors = colors_for(self._theme)
        tk.Label(
            container,
            text=_APPEARANCE_PLACEHOLDER,
            font=TYPOGRAPHY.body_secondary.to_tk_font(),
            background=colors.window,
            foreground=colors.ink_soft,
            wraplength=280,
            justify="left",
        ).pack(padx=SPACING["2xl"], pady=SPACING["2xl"])

    def _build_confirmation(self, container: tk.Frame) -> None:
        colors = colors_for(self._theme)
        self._confirmation_rows: dict[str, tk.BooleanVar] = {}
        for text, reader, writer in _CONFIRMATION_TOGGLES:
            variable = tk.BooleanVar(value=reader(self._settings_repository))
            checkbutton = tk.Checkbutton(
                container,
                text=text,
                variable=variable,
                command=lambda v=variable, w=writer: w(self._settings_repository, v.get()),
                background=colors.window,
                foreground=colors.ink,
                activebackground=colors.window,
                activeforeground=colors.ink,
                selectcolor=colors.panel,
                font=TYPOGRAPHY.body.to_tk_font(),
            )
            checkbutton.pack(anchor="w", fill="x", padx=SPACING["2xl"], pady=SPACING["sm"])
            self._confirmation_rows[text] = variable
