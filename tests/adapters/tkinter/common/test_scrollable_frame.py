import tkinter as tk

from labyrinthes.adapters.tkinter.common.scrollable_frame import ScrollableFrame
from labyrinthes.adapters.tkinter.common.tokens import Theme, colors_for


def _pack_fixed_height_children(content: tk.Widget, colors, *, count: int, height: int) -> list:
    children = []
    for _ in range(count):
        child = tk.Frame(content, height=height, width=80, background=colors.window)
        child.pack_propagate(False)
        child.pack(fill="x")
        children.append(child)
    return children


def test_scrollable_frame_is_a_canvas_scrollbar_and_content_frame(tk_root):
    frame = ScrollableFrame(tk_root, colors=colors_for(Theme.LIGHT))

    assert isinstance(frame._canvas, tk.Canvas)
    assert isinstance(frame._scrollbar, tk.Scrollbar)
    assert isinstance(frame.content, tk.Frame)
    # `.content` is the canvas's own embedded window, not a sibling of it.
    assert frame.content.master is frame._canvas


def test_bind_wheel_recursive_binds_the_widget_and_every_descendant(tk_root):
    colors = colors_for(Theme.LIGHT)
    frame = ScrollableFrame(tk_root, colors=colors)
    parent = tk.Frame(frame.content, background=colors.window)
    child = tk.Label(parent, text="child")
    grandchild = tk.Label(child, text="grandchild")

    frame.bind_wheel_recursive(parent)

    for widget in (parent, child, grandchild):
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            assert widget.bind(sequence) != ""


# -- scroll_into_view: real geometry, not stubbed -------------------------------------
#
# `scroll_into_view` reads `self._canvas.winfo_height()` -- the canvas's own
# *allocated* pixel size, confirmed by the window manager, not merely its
# requested size. `tests/conftest.py`'s shared `tk_root` fixture withdraws
# the root (this suite's usual, deliberate way to dodge X11 event-synthesis
# flakiness elsewhere), but a withdrawn/unmapped toplevel never gets real
# allocated geometry back from the window manager either -- every widget
# under it reports a stale `winfo_height() == 1` regardless of any
# `configure(height=...)` or `update()`/`update_idletasks()` call, which
# would make a real assertion here vacuous. These three tests explicitly
# `deiconify()` the root first (this suite's only place that does) so the
# geometry this method actually depends on is real -- confirmed against a
# live X display, not stubbed away with a spy.


def test_scroll_into_view_moves_the_canvas_to_reveal_a_widget_below_the_fold(tk_root):
    tk_root.deiconify()
    colors = colors_for(Theme.LIGHT)
    frame = ScrollableFrame(tk_root, colors=colors)
    frame.pack()
    frame._canvas.configure(width=100, height=50)  # a small fixed viewport

    children = _pack_fixed_height_children(frame.content, colors, count=10, height=40)
    tk_root.update()
    target = children[8]  # y == 320..360, far below the 50px-tall viewport

    frame.scroll_into_view(target)
    tk_root.update()

    view_top = frame._canvas.canvasy(0)
    view_bottom = view_top + frame._canvas.winfo_height()
    widget_top = frame._offset_within_content(target)
    widget_bottom = widget_top + target.winfo_height()
    assert view_top <= widget_top
    assert widget_bottom <= view_bottom


def test_scroll_into_view_moves_the_canvas_back_up_to_reveal_a_widget_above_the_fold(tk_root):
    tk_root.deiconify()
    colors = colors_for(Theme.LIGHT)
    frame = ScrollableFrame(tk_root, colors=colors)
    frame.pack()
    frame._canvas.configure(width=100, height=50)

    children = _pack_fixed_height_children(frame.content, colors, count=10, height=40)
    tk_root.update()
    # Scroll all the way down first, so the top of the content is off-screen.
    frame._canvas.yview_moveto(1.0)
    tk_root.update()
    target = children[0]

    frame.scroll_into_view(target)
    tk_root.update()

    view_top = frame._canvas.canvasy(0)
    view_bottom = view_top + frame._canvas.winfo_height()
    widget_top = frame._offset_within_content(target)
    widget_bottom = widget_top + target.winfo_height()
    assert view_top <= widget_top
    assert widget_bottom <= view_bottom


def test_scroll_into_view_is_a_no_op_when_the_widget_is_already_fully_visible(tk_root):
    tk_root.deiconify()
    colors = colors_for(Theme.LIGHT)
    frame = ScrollableFrame(tk_root, colors=colors)
    frame.pack()
    frame._canvas.configure(width=100, height=200)

    children = _pack_fixed_height_children(frame.content, colors, count=3, height=40)
    tk_root.update()
    target = children[0]  # fully within the 200px viewport already
    before = frame._canvas.yview()

    frame.scroll_into_view(target)

    assert frame._canvas.yview() == before
