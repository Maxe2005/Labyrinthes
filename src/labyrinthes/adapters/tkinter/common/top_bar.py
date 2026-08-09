"""`TopBar` -- brand mark + optional breadcrumb + Settings/theme-toggle icons (Story 1.8/1.9).

Composed by every screen's `mount()`. Per the epic's top-bar pattern: the
brand mark/wordmark always sits left, an optional `Breadcrumb` sits next to
it, and the `icon-btn`s (Settings, theme toggle) sit right, in that
left-to-right order.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.breadcrumb import Breadcrumb, BreadcrumbSegment
from labyrinthes.adapters.tkinter.common.icon_btn import IconButton
from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for

__all__ = ["TopBar"]

_BRAND_TEXT = "Labyrinthes"


class TopBar(tk.Frame):
    """The persistent top bar every screen mounts at the top of its frame.

    `breadcrumb_segments=None` (Home's case) renders no `Breadcrumb` at
    all, rather than an empty one -- there is nothing meaningful to show at
    navigation depth 0 (see `breadcrumb.py`'s module docstring).
    """

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        breadcrumb_segments: list[BreadcrumbSegment] | None = None,
        on_settings: Callable[[], None] | None = None,
        on_theme_toggle: Callable[[], None] | None = None,
    ) -> None:
        colors = colors_for(theme)
        super().__init__(
            parent,
            background=colors.window,
            bd=0,
            highlightthickness=1,
            highlightbackground=colors.border,
            highlightcolor=colors.border,
        )

        tk.Label(
            self,
            text=_BRAND_TEXT,
            font=TYPOGRAPHY.heading_sm.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
        ).pack(side="left", padx=SPACING["lg"], pady=SPACING["sm"])

        self._breadcrumb: Breadcrumb | None = None
        if breadcrumb_segments is not None:
            self._breadcrumb = Breadcrumb(self, breadcrumb_segments, theme=theme)
            self._breadcrumb.pack(side="left", padx=(0, SPACING["lg"]))

        # Packed before the Settings button: with `side="right"`, the first
        # widget packed lands nearest the right edge, so packing this one
        # first is what puts it to the *right* of Settings in the final
        # left-to-right layout (see this module's docstring).
        self._theme_toggle_button = IconButton(
            self,
            glyph="🌙",  # moon, same glyph in both themes per the locked mockups
            theme=theme,
            tooltip="Toggle theme.",
            command=on_theme_toggle,
        )
        self._theme_toggle_button.pack(side="right", padx=SPACING["lg"], pady=SPACING["sm"])

        self._settings_button = IconButton(
            self,
            glyph="⚙",  # gear
            theme=theme,
            tooltip="Open settings.",
            command=on_settings,
        )
        self._settings_button.pack(side="right", padx=SPACING["lg"], pady=SPACING["sm"])
