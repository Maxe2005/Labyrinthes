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

from labyrinthes.adapters.tkinter.common.tokens import (
    FOCUS_RING_THICKNESS,
    RESTING_RING_THICKNESS,
    SPACING,
    TYPOGRAPHY,
    ColorTokens,
    Theme,
    colors_for,
)

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
        # `(on_focus_in, on_focus_out)` per clickable segment, `None` for
        # the trailing/current one -- same indexing convention as
        # `_hover_handlers`, so tests can invoke a focus transition
        # directly instead of relying on real Tab traversal (which never
        # takes on a withdrawn `tk_root`).
        self._focus_handlers: list[tuple[Callable[[], None], Callable[[], None]] | None] = []

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
            focus: tuple[Callable[[], None], Callable[[], None]] | None = None
            if segment.on_click is not None:
                handler = segment.on_click
                label.configure(
                    cursor="hand2",
                    takefocus=True,
                    highlightthickness=RESTING_RING_THICKNESS,
                    # Resting ring matches the breadcrumb's own background
                    # (`colors.window`), so it's invisible until focused.
                    highlightbackground=colors.window,
                    highlightcolor=colors.window,
                )
                label.bind("<Button-1>", self._click_handler(handler))
                label.bind("<Return>", self._click_handler(handler))
                label.bind("<space>", self._click_handler(handler))

                on_enter, on_leave, on_focus_in, on_focus_out = self._segment_interactions(
                    label, colors
                )
                label.bind("<Enter>", self._click_handler(on_enter), add="+")
                label.bind("<Leave>", self._click_handler(on_leave), add="+")
                label.bind("<FocusIn>", self._click_handler(on_focus_in), add="+")
                label.bind("<FocusOut>", self._click_handler(on_focus_out), add="+")
                hover = (on_enter, on_leave)
                focus = (on_focus_in, on_focus_out)

            self._labels.append(label)
            self._segment_handlers.append(handler)
            self._hover_handlers.append(hover)
            self._focus_handlers.append(focus)

    def set_label(self, index: int, label: str) -> None:
        """Update segment `index`'s displayed text in place.

        Leaves that segment's click/hover/focus wiring untouched -- only
        the `tk.Label`'s own `text` changes. For a screen whose trailing
        segment's label can go stale after construction (e.g. Player's
        kind-derived label, which the maze's own `kind` can outlive once a
        `GENERATED` maze is saved into `SAVED_RANDOM` mid-session).
        """
        self._labels[index].configure(text=label)

    @staticmethod
    def _click_handler(callback: Callable[[], None]) -> Callable[[tk.Event | None], None]:
        def _on_click(_event: tk.Event | None = None) -> None:
            callback()

        return _on_click

    @staticmethod
    def _segment_interactions(
        label: tk.Label, colors: ColorTokens
    ) -> tuple[Callable[[], None], Callable[[], None], Callable[[], None], Callable[[], None]]:
        """Build one clickable segment's `(on_enter, on_leave, on_focus_in,
        on_focus_out)` closures, sharing local hover/focus state.

        Hover and keyboard focus both recolor the same label text, and only
        focus additionally shows a ring. Tracking both as shared state here
        -- instead of each transition unconditionally overwriting the
        other's effect -- is what keeps them from fighting: text stays
        `colors.accent` as long as *either* is true, and losing one doesn't
        clobber the other still being active (e.g. tabbing away while the
        mouse is still hovering keeps the hover color instead of reverting
        to resting; moving the mouse off while focus remains keeps the
        focus color and ring).
        """
        state = {"hovered": False, "focused": False}

        def _apply() -> None:
            active = state["hovered"] or state["focused"]
            label.configure(foreground=colors.accent if active else colors.ink_soft)
            if state["focused"]:
                label.configure(
                    highlightthickness=FOCUS_RING_THICKNESS,
                    highlightbackground=colors.accent,
                    highlightcolor=colors.accent,
                )
            else:
                # Resting ring matches the breadcrumb's own background, so
                # it's invisible whenever keyboard focus isn't present --
                # hover alone never shows a ring, only a text recolor.
                label.configure(
                    highlightthickness=RESTING_RING_THICKNESS,
                    highlightbackground=colors.window,
                    highlightcolor=colors.window,
                )

        def on_enter() -> None:
            state["hovered"] = True
            _apply()

        def on_leave() -> None:
            state["hovered"] = False
            _apply()

        def on_focus_in() -> None:
            state["focused"] = True
            _apply()

        def on_focus_out() -> None:
            state["focused"] = False
            _apply()

        return on_enter, on_leave, on_focus_in, on_focus_out
