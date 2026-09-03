import tkinter as tk

from labyrinthes.adapters.tkinter.common.stage import Stage
from labyrinthes.adapters.tkinter.common.tokens import Theme, colors_for


class _FakeConfigureEvent:
    """A minimal stand-in for a `<Configure>` event: `Stage._redraw` only
    reads `.width`/`.height` -- real X11 `<Configure>` synthesis isn't
    reliable under a withdrawn `tk_root` (mirrors
    `test_builder_shell_windowing.py`'s own `_FakeConfigureEvent`)."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height


def test_stage_is_a_canvas_hosting_a_content_frame(tk_root):
    stage = Stage(tk_root, colors=colors_for(Theme.LIGHT))

    assert isinstance(stage, tk.Canvas)
    assert isinstance(stage.content, tk.Frame)
    # The content frame is the canvas's own embedded window, not a sibling.
    assert stage.content.master is stage


def test_stage_background_matches_the_given_theme(tk_root):
    light_stage = Stage(tk_root, colors=colors_for(Theme.LIGHT))
    dark_stage = Stage(tk_root, colors=colors_for(Theme.DARK))

    assert light_stage.cget("background") == colors_for(Theme.LIGHT).window
    assert dark_stage.cget("background") == colors_for(Theme.DARK).window
    assert light_stage.content.cget("background") == colors_for(Theme.LIGHT).window


def test_configure_draws_gridlines_and_insets_the_content_window_from_the_canvas_edges(tk_root):
    stage = Stage(tk_root, colors=colors_for(Theme.LIGHT))

    stage._redraw(_FakeConfigureEvent(200, 150))

    assert len(stage.find_withtag("gridline")) > 0
    # `content` must be inset (smaller than the full canvas, off the 0,0
    # origin), never sized to cover the whole canvas -- otherwise it would
    # paint over every gridline (`create_window()` items always render
    # above canvas primitives), leaving the grid backdrop permanently
    # invisible regardless of size/theme.
    x, y = stage.coords(stage._window_id)
    assert (x, y) != (0, 0)
    width = int(stage.itemcget(stage._window_id, "width"))
    height = int(stage.itemcget(stage._window_id, "height"))
    assert width < 200
    assert height < 150
    # And at least one gridline must fall outside `content`'s bounding box
    # (before `content`'s left edge, i.e. within the inset margin) --
    # otherwise "smaller than the canvas" alone wouldn't prove any line is
    # actually visible.
    gridline_xs = [stage.coords(item)[0] for item in stage.find_withtag("gridline")]
    assert any(gx < x for gx in gridline_xs)


def test_configure_redraws_gridlines_on_resize_without_accumulating_old_ones(tk_root):
    stage = Stage(tk_root, colors=colors_for(Theme.LIGHT))
    stage._redraw(_FakeConfigureEvent(200, 150))
    first_count = len(stage.find_withtag("gridline"))

    stage._redraw(_FakeConfigureEvent(400, 300))

    # Redrawn (not accumulated): a bigger canvas needs more lines, but the
    # old set is deleted first (`_redraw_lines`'s `self.delete("gridline")`).
    assert len(stage.find_withtag("gridline")) > first_count
