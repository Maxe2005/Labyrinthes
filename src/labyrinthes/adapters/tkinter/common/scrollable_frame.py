"""`ScrollableFrame` -- this codebase's first scrollable container (Story 4.14).

Tk has no native scrollable container; the standard idiom is a `Canvas` +
inner `Frame` attached via `create_window()` (the same mechanism
`stage.py` already uses for its own embedded content frame) + a
`Scrollbar` wired to `yscrollcommand`, with `scrollregion` recomputed on
the inner frame's `<Configure>` -- resized content invalidates the
previous scroll extent. Callers pack/grid their content into `.content`,
never into the widget itself.

`scroll_into_view(widget)` matters because Tk's default Tab traversal
moves keyboard focus without scrolling anything -- without it, Tabbing to
a card below the fold would satisfy "reachable" but silently fail
"visible focus indicator" (NFR6). It walks `widget`'s parent chain up to
`.content` accumulating `winfo_y()` offsets (each `winfo_y()` is relative
to its own direct parent, not `.content`), then nudges the canvas's
`yview` only far enough to bring `widget`'s full vertical span inside the
visible viewport -- a no-op when it's already visible.

Tk delivers a mouse-wheel event to whichever widget is directly under the
pointer, not to whatever is bound to it elsewhere -- so binding the wheel
only on `self._canvas` (its own bare margin) leaves every widget packed
into `.content` dead to the wheel while the pointer is over it, nothing
forwards the event up. `bind_wheel_recursive(widget)` is the fix: callers
walk their own content tree (e.g. `MazeSelectionGallery` over each
`MazeCard` it builds) and bind the same wheel sequences onto every
descendant too.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import ColorTokens

__all__ = ["ScrollableFrame"]


class ScrollableFrame(tk.Frame):
    """A vertically scrollable `Canvas`+`Frame`+`Scrollbar`; children go in `.content`."""

    def __init__(self, parent: tk.Widget, *, colors: ColorTokens) -> None:
        super().__init__(parent, background=colors.window)

        self._canvas = tk.Canvas(self, background=colors.window, highlightthickness=0, bd=0)
        self._scrollbar = tk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._content = tk.Frame(self._canvas, background=colors.window)
        self._window_id = self._canvas.create_window(0, 0, window=self._content, anchor="nw")

        self._canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y")

        self._content.bind("<Configure>", self._on_content_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # `<MouseWheel>` (Windows/macOS) + `<Button-4>`/`<Button-5>` (X11)
        # cover every platform Tk runs the wheel event under.
        self._canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self._canvas.bind("<Button-4>", self._on_mouse_wheel)
        self._canvas.bind("<Button-5>", self._on_mouse_wheel)

    @property
    def content(self) -> tk.Widget:
        """The frame every caller packs/grids its scrollable content into."""
        return self._content

    def bind_wheel_recursive(self, widget: tk.Widget) -> None:
        """Bind the wheel sequences on `widget` and every descendant of it.

        Tk delivers `<MouseWheel>`/`<Button-4>`/`<Button-5>` to whatever
        widget the pointer is physically over, not to `self._canvas`
        regardless of where the pointer is -- so a card (or any other
        widget) packed into `.content` needs its own copy of the same
        binding to keep the wheel working while the pointer is over it.
        Callers invoke this once per content widget they build (e.g. each
        `MazeCard`, right after constructing it) -- it is not automatic for
        widgets already packed into `.content` before this is called.
        """
        widget.bind("<MouseWheel>", self._on_mouse_wheel)
        widget.bind("<Button-4>", self._on_mouse_wheel)
        widget.bind("<Button-5>", self._on_mouse_wheel)
        for child in widget.winfo_children():
            self.bind_wheel_recursive(child)

    def _on_content_configure(self, _event: tk.Event) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        # `.content` always spans the canvas's own width, so its children
        # can fill/wrap horizontally instead of being clipped at whatever
        # width they last requested.
        self._canvas.itemconfigure(self._window_id, width=event.width)

    def _on_mouse_wheel(self, event: tk.Event) -> None:
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -1 if event.delta > 0 else 1
        self._canvas.yview_scroll(delta, "units")

    def _offset_within_content(self, widget: tk.Widget) -> int:
        """`widget`'s y-offset from `.content`'s own top, walking up its parent chain."""
        offset = 0
        node: tk.Widget | None = widget
        while node is not None and node is not self._content:
            offset += node.winfo_y()
            node = node.master
        return offset

    def scroll_into_view(self, widget: tk.Widget) -> None:
        """Scroll the minimum amount to bring `widget` fully into the visible viewport."""
        self.update_idletasks()
        bbox = self._canvas.bbox("all")
        if bbox is None:
            return
        total_height = bbox[3]
        if total_height <= 0:
            return

        widget_top = self._offset_within_content(widget)
        widget_bottom = widget_top + widget.winfo_height()
        view_top = self._canvas.canvasy(0)
        visible_height = self._canvas.winfo_height()
        view_bottom = view_top + visible_height

        if widget_top < view_top:
            target = widget_top
        elif widget_bottom > view_bottom:
            target = widget_bottom - visible_height
        else:
            return  # already fully visible

        fraction = max(0.0, min(1.0, target / total_height))
        self._canvas.yview_moveto(fraction)
