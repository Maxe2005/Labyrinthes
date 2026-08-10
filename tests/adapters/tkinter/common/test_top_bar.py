import tkinter as tk

from labyrinthes.adapters.tkinter.common.breadcrumb import Breadcrumb, BreadcrumbSegment
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.adapters.tkinter.common.top_bar import TopBar


def test_top_bar_renders_the_brand_mark_and_wordmark(tk_root):
    top_bar = TopBar(tk_root, theme=Theme.LIGHT)

    children = top_bar.winfo_children()
    labels = {child.cget("text") for child in children if isinstance(child, tk.Label)}
    assert "Labyrinthes" in labels


def test_top_bar_with_no_segments_renders_no_breadcrumb(tk_root):
    top_bar = TopBar(tk_root, theme=Theme.LIGHT, breadcrumb_segments=None)

    assert top_bar._breadcrumb is None


def test_top_bar_with_segments_renders_a_breadcrumb_with_those_segments(tk_root):
    segments = [
        BreadcrumbSegment("Home", on_click=lambda: None),
        BreadcrumbSegment("Builder"),
    ]
    top_bar = TopBar(tk_root, theme=Theme.LIGHT, breadcrumb_segments=segments)

    assert isinstance(top_bar._breadcrumb, Breadcrumb)
    assert [label.cget("text") for label in top_bar._breadcrumb._labels] == ["Home", "Builder"]


def test_set_breadcrumb_label_updates_the_given_segment(tk_root):
    segments = [
        BreadcrumbSegment("Home", on_click=lambda: None),
        BreadcrumbSegment("Random Maze"),
    ]
    top_bar = TopBar(tk_root, theme=Theme.LIGHT, breadcrumb_segments=segments)

    top_bar.set_breadcrumb_label(1, "Saved Random Maze")

    assert top_bar._breadcrumb._labels[1].cget("text") == "Saved Random Maze"


def test_set_breadcrumb_label_is_a_no_op_when_there_is_no_breadcrumb(tk_root):
    top_bar = TopBar(tk_root, theme=Theme.LIGHT, breadcrumb_segments=None)

    top_bar.set_breadcrumb_label(0, "Anything")  # must not raise


def test_settings_icon_buttons_command_fires_on_click(tk_root):
    calls = []
    top_bar = TopBar(tk_root, theme=Theme.LIGHT, on_settings=lambda: calls.append(1))

    # `tk_root` is withdrawn, so real X11 button-press synthesis isn't
    # reliable; invoke the bound handler directly (see test_icon_btn.py).
    top_bar._settings_button._on_click()

    assert calls == [1]


def test_settings_icon_button_with_no_command_does_not_raise_on_click(tk_root):
    top_bar = TopBar(tk_root, theme=Theme.LIGHT)

    top_bar._settings_button._on_click()


def test_theme_toggle_icon_buttons_command_fires_on_click(tk_root):
    calls = []
    top_bar = TopBar(tk_root, theme=Theme.LIGHT, on_theme_toggle=lambda: calls.append(1))

    # `tk_root` is withdrawn, so real X11 button-press synthesis isn't
    # reliable; invoke the bound handler directly (see test_icon_btn.py).
    top_bar._theme_toggle_button._on_click()

    assert calls == [1]


def test_theme_toggle_icon_button_with_no_command_does_not_raise_on_click(tk_root):
    top_bar = TopBar(tk_root, theme=Theme.LIGHT)

    top_bar._theme_toggle_button._on_click()


def test_theme_toggle_button_is_visually_right_of_the_settings_button(tk_root):
    # `tk_root` is withdrawn and never given real screen geometry, so
    # `winfo_x()` can't be trusted to reflect final on-screen position
    # here; instead assert via `pack_slaves()` order, which directly
    # reflects what `side="right"` packing renders left-to-right -- the
    # first widget packed with `side="right"` ends up nearest the right
    # edge, so the theme-toggle button (packed first) must appear earlier
    # in `pack_slaves()` than the Settings button (packed second).
    top_bar = TopBar(tk_root, theme=Theme.LIGHT)

    slaves = top_bar.pack_slaves()

    assert slaves.index(top_bar._theme_toggle_button) < slaves.index(top_bar._settings_button)
