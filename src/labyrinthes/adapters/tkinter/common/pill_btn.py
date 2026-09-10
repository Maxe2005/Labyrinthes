"""`PillButton` -- the top-bar action button, default + primary variants (Story 1.6).

Per `EXPERIENCE.md`, at most one `primary` pill sits on a screen at a time
(the single most likely next action); every other pill stays in the
default (non-filled) style.
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
        super().__init__(parent, bd=0, takefocus=True, highlightthickness=RESTING_RING_THICKNESS)
        self._theme = theme
        self._primary = primary
        self._command = command
        self._focused = False

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
            widget.configure(cursor="hand2")  # type: ignore[call-arg]
            widget.bind("<Button-1>", self._on_click)

        self.bind("<Return>", self._on_click)
        self.bind("<space>", self._on_click)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

        self._apply_style()

    def set_text(self, text: str) -> None:
        """Replace the pill's label text in place (e.g. "Save" -> "Overwrite")."""
        self._label.configure(text=text)

    def _clickable_widgets(self) -> tuple[tk.Widget, ...]:
        widgets: tuple[tk.Widget, ...] = (self, self._label)
        if self._kbd is not None:
            widgets += (self._kbd,)
        return widgets

    def _on_click(self, _event: tk.Event | None = None) -> None:
        if self._command is not None:
            self._command()

    def _on_focus_in(self, _event: tk.Event | None = None) -> None:
        self._focused = True
        self._apply_style()

    def _on_focus_out(self, _event: tk.Event | None = None) -> None:
        self._focused = False
        self._apply_style()

    def _apply_style(self) -> None:
        colors = colors_for(self._theme)
        if self._primary:
            background = colors.accent if self._theme is Theme.LIGHT else colors.accent_strong_dark
            # `colors.window` would resolve against *this widget's own*
            # theme -- white (`#ffffff`) in light mode, but near-black
            # (`#12161d`) in dark mode, which would land dark-mode primary
            # text on the `accent_strong_dark` fill at ~2.1:1 contrast, far
            # under AA. `DESIGN.md`'s own rationale for that fill assumes
            # white text (~8.7:1), so resolve the light-mode literal
            # unconditionally instead -- same already-declared `#ffffff`,
            # just independent of the widget's own theme.
            text_color = colors_for(Theme.LIGHT).window
        else:
            background = colors.panel
            text_color = colors.ink
        border = background if self._primary else colors.border

        if self._focused:
            highlightthickness = FOCUS_RING_THICKNESS
            # A primary pill's own fill already *is* `colors.accent`
            # (light) or `accent_strong_dark` (dark) -- reusing
            # `colors.accent` as the focus ring there would fuse the ring
            # into the fill (~1.00:1 contrast in light mode, effectively
            # invisible as a distinct ring). Reuse the same always-white
            # literal as the primary-text fix above instead, which
            # contrasts well against both primary fills (~5.17:1 light,
            # ~8.72:1 dark); the default variant's `colors.panel` fill has
            # no such collision, so it keeps the standard `colors.accent`
            # ring every other focusable `common/` widget uses.
            ring_color = text_color if self._primary else colors.accent
            highlightbackground = ring_color
            highlightcolor = ring_color
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
            if self._primary:
                # `KbdTag`'s own default foreground (`colors.ink_soft`)
                # measures ~1.06:1 (light) / ~2.94:1 (dark) against a
                # primary fill -- the same AA failure class as the label
                # fix above, just one widget over -- so override it too.
                self._kbd.configure(background=background, foreground=text_color)
            else:
                self._kbd.configure(background=background)
