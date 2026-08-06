"""`BreadcrumbSegment` + `Breadcrumb` -- the "Home / <Screen>" navigation trail (Story 1.8).

Per the epic's top-bar pattern, every non-Home screen carries a clickable
Home segment plus its own, non-clickable current-screen segment; Home
itself renders no `Breadcrumb` at all (depth 0) -- callers with nothing to
show simply never construct one (see `TopBar`'s `breadcrumb_segments=None`).
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for

__all__ = ["Breadcrumb", "BreadcrumbSegment"]


@dataclass(frozen=True)
class BreadcrumbSegment:
    """One crumb: its label text, and an optional navigate callback.

    `on_click=None` marks the trailing/current segment -- the screen the
    breadcrumb is rendered on, which is never itself clickable.
    """

    label: str
    on_click: Callable[[], None] | None = None


class Breadcrumb(tk.Frame):
    """Renders `segments` left-to-right, " / "-separated.

    Each clickable segment's `<Button-1>` handler is kept in
    `_segment_handlers`, aligned index-for-index with `segments`/`_labels`
    (`None` for the non-clickable trailing segment) -- mirroring every other
    `common/` widget's `_on_click` convention, so tests can invoke a
    specific segment's handler directly instead of synthesizing an X11
    event (`tk_root` is withdrawn in tests).

    Clickable segments rest in `colors.ink_soft` and turn `colors.accent`
    on hover -- accent is a hover/active-only color per the locked mockups'
    `.crumb .seg`/`.crumb .seg:hover` rule, never the resting color.
    """

    def __init__(
        self, parent: tk.Widget, segments: list[BreadcrumbSegment], *, theme: Theme
    ) -> None:
        colors = colors_for(theme)
        super().__init__(parent, background=colors.window)
        self._labels: list[tk.Label] = []
        self._segment_handlers: list[Callable[[], None] | None] = []
        # `(on_enter, on_leave)` per clickable segment, `None` for the
        # trailing/current one -- indexed like `_labels`/`_segment_handlers`,
        # exposed so tests can invoke a hover transition directly instead of
        # synthesizing a pointer event (`tk_root` is withdrawn in tests).
        self._hover_handlers: list[tuple[Callable[[], None], Callable[[], None]] | None] = []

        for index, segment in enumerate(segments):
            if index > 0:
                tk.Label(
                    self,
                    text=" / ",
                    font=TYPOGRAPHY.body.to_tk_font(),
                    background=colors.window,
                    foreground=colors.ink_soft,
                ).pack(side="left")

            clickable = segment.on_click is not None
            label = tk.Label(
                self,
                text=segment.label,
                font=TYPOGRAPHY.body.to_tk_font(),
                background=colors.window,
                foreground=colors.ink_soft if clickable else colors.ink,
            )
            label.pack(side="left", padx=(SPACING["xs"], 0) if index == 0 else 0)

            handler: Callable[[], None] | None = None
            hover: tuple[Callable[[], None], Callable[[], None]] | None = None
            if segment.on_click is not None:
                handler = segment.on_click
                label.configure(cursor="hand2")
                label.bind("<Button-1>", self._click_handler(handler))

                on_enter = self._recolor(label, colors.accent)
                on_leave = self._recolor(label, colors.ink_soft)
                label.bind("<Enter>", self._click_handler(on_enter), add="+")
                label.bind("<Leave>", self._click_handler(on_leave), add="+")
                hover = (on_enter, on_leave)

            self._labels.append(label)
            self._segment_handlers.append(handler)
            self._hover_handlers.append(hover)

    @staticmethod
    def _click_handler(callback: Callable[[], None]) -> Callable[[tk.Event | None], None]:
        def _on_click(_event: tk.Event | None = None) -> None:
            callback()

        return _on_click

    @staticmethod
    def _recolor(label: tk.Label, color: str) -> Callable[[], None]:
        def _apply() -> None:
            label.configure(foreground=color)

        return _apply
