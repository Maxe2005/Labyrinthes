"""`ToolButton` + `ToolButtonGroup` -- the side-bar tool control (Story 1.6).

Native `tk.Button` cannot host a left-aligned label plus a right-aligned
`kbd-tag` side by side, so `ToolButton` is a small `tk.Frame` composite
that behaves like a button (click anywhere on it fires `command`) instead.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.kbd_tag import KbdTag
from labyrinthes.adapters.tkinter.common.tokens import (
    FOCUS_RING_THICKNESS,
    RESTING_RING_THICKNESS,
    SPACING,
    TYPOGRAPHY,
    Theme,
    colors_for,
)
from labyrinthes.adapters.tkinter.common.tooltip import Tooltip

__all__ = ["ToolButton", "ToolButtonGroup"]


class ToolButton(tk.Frame):
    """A single tool-bar button: label left, optional `kbd-tag` right.

    Active styling (background/border/text) is driven entirely by
    `set_active()` -- callers that need mutual exclusivity across several
    `ToolButton`s should register them all with one `ToolButtonGroup`
    rather than tracking `active` by hand.
    """

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        *,
        theme: Theme,
        shortcut: str | None = None,
        tooltip: str | None = None,
        command: Callable[[], None] | None = None,
        group: ToolButtonGroup | None = None,
    ) -> None:
        super().__init__(parent, bd=0, takefocus=True, highlightthickness=RESTING_RING_THICKNESS)
        self._theme = theme
        self._command = command
        self._group = group
        self._active = False
        self._focused = False
        self._enabled = True

        self._label = tk.Label(
            self,
            text=text,
            font=TYPOGRAPHY.body.to_tk_font(),
            anchor="w",
        )
        self._label.pack(side="left", padx=(SPACING["md"], SPACING["xs"]), pady=SPACING["sm"])

        self._kbd: tk.Label | None = None
        if shortcut is not None:
            self._kbd = KbdTag(self, shortcut, theme=theme)
            self._kbd.pack(side="right", padx=(SPACING["xs"], SPACING["md"]))

        for widget in self._clickable_widgets():
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", self._on_click)

        self.bind("<Return>", self._on_click)
        self.bind("<space>", self._on_click)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

        if tooltip is not None:
            Tooltip(self, tooltip, theme=theme)

        if group is not None:
            group.add(self)

        self._apply_style()

    def _clickable_widgets(self) -> tuple[tk.Widget, ...]:
        widgets: tuple[tk.Widget, ...] = (self, self._label)
        if self._kbd is not None:
            widgets += (self._kbd,)
        return widgets

    @property
    def active(self) -> bool:
        return self._active

    def set_text(self, text: str) -> None:
        """Replace the button's label text in place (e.g. a speed tier label)."""
        self._label.configure(text=text)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the button (a real disabled state).

        A disabled button is non-focusable (`takefocus=False`), ignores
        clicks/Enter/Space (`_on_click` returns early), and renders in the
        `colors.ghost` palette -- the design system's "disabled or not-yet-
        set state" token. Re-enabling restores focusability, activation,
        and normal styling.
        """
        if enabled == self._enabled:
            return
        self._enabled = enabled
        self.configure(takefocus=enabled)
        for widget in self._clickable_widgets():
            widget.configure(cursor="hand2" if enabled else "")
        self._apply_style()

    def set_active(self, active: bool) -> None:
        """Set this button's active state.

        Activating a grouped button routes through its `ToolButtonGroup`
        so the mutual-exclusivity guarantee holds even when called
        directly, not only via a click or `group.activate()`.
        Deactivation never needs routing -- it can't create a second
        active member.
        """
        if active and self._group is not None:
            self._group.activate(self)
            return
        self._set_active_direct(active)

    def _set_active_direct(self, active: bool) -> None:
        """Set `_active` without group routing -- used by the group itself
        to avoid `set_active()`/`activate()` recursing into each other."""
        self._active = active
        self._apply_style()

    def _on_click(self, _event: tk.Event | None = None) -> None:
        if not self._enabled:
            return
        if self._group is not None:
            self._group.activate(self)
        else:
            self.set_active(True)
        if self._command is not None:
            self._command()

    def _on_focus_in(self, _event: tk.Event | None = None) -> None:
        if not self._enabled:
            return
        self._focused = True
        self._apply_style()

    def _on_focus_out(self, _event: tk.Event | None = None) -> None:
        if not self._enabled:
            return
        self._focused = False
        self._apply_style()

    def _apply_style(self) -> None:
        colors = colors_for(self._theme)
        if not self._enabled:
            background = colors.window
            border = colors.ghost
            text_color = colors.ghost
        elif self._active:
            background = colors.accent_bg
            border = colors.accent
            text_color = colors.accent_on_tint if self._theme is Theme.LIGHT else colors.accent
        else:
            background = colors.window
            border = colors.border
            text_color = colors.ink

        # `border` (accent when active, resting `colors.border` otherwise)
        # is the resting-ring color. Focus only changes *how thick* the
        # ring is and, while focused, forces both highlight colors to
        # `colors.accent` -- explicit thickness toggling (not just relying
        # on Tk's automatic highlightcolor/highlightbackground swap) is
        # what keeps an active-but-unfocused button (1px accent border)
        # visibly distinct from an active-and-focused one (2px accent ring).
        if self._focused:
            highlightthickness = FOCUS_RING_THICKNESS
            highlightbackground = colors.accent
            highlightcolor = colors.accent
        else:
            highlightthickness = RESTING_RING_THICKNESS
            highlightbackground = border
            highlightcolor = border
        self.configure(
            background=background,
            highlightthickness=highlightthickness,
            highlightbackground=highlightbackground,
            highlightcolor=highlightcolor,
        )
        self._label.configure(background=background, foreground=text_color)
        if self._kbd is not None:
            self._kbd.configure(background=background)


class ToolButtonGroup:
    """Guarantees exactly one member `ToolButton` shows active styling."""

    def __init__(self) -> None:
        self._buttons: list[ToolButton] = []

    def add(self, button: ToolButton) -> None:
        self._buttons.append(button)

    def activate(self, button: ToolButton) -> None:
        """Make `button` the sole active member; deactivate every other one."""
        for candidate in self._buttons:
            candidate._set_active_direct(candidate is button)
