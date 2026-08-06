import tkinter as tk

from labyrinthes.adapters.tkinter.builder.screen import mount
from labyrinthes.adapters.tkinter.common import SettingsWindow, Theme, TopBar
from labyrinthes.adapters.tkinter.common.navigation import ScreenId


def test_mount_returns_a_frame_parented_under_the_given_parent(
    tk_root, navigate_stub, toggle_theme_stub
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(tk_root, None, navigate, Theme.LIGHT, toggle_theme)

    assert isinstance(frame, tk.Frame)
    assert frame.master is tk_root


def test_mount_renders_a_home_builder_breadcrumb(
    tk_root, navigate_stub, toggle_theme_stub, find_all
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(tk_root, None, navigate, Theme.LIGHT, toggle_theme)

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert breadcrumb is not None
    assert [label.cget("text") for label in breadcrumb._labels] == ["Home", "Builder"]


def test_breadcrumb_home_segment_is_clickable_and_navigates_home(
    tk_root, navigate_stub, toggle_theme_stub, find_all
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(tk_root, None, navigate, Theme.LIGHT, toggle_theme)

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    # `tk_root` is withdrawn, so real X11 button-press synthesis isn't
    # reliable; invoke the bound handler directly (see test_icon_btn.py).
    breadcrumb._segment_handlers[0]()

    assert calls == [(ScreenId.HOME, None)]


def test_breadcrumb_trailing_builder_segment_has_no_click_handler(
    tk_root, navigate_stub, toggle_theme_stub, find_all
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(tk_root, None, navigate, Theme.LIGHT, toggle_theme)

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert breadcrumb._segment_handlers[1] is None


def test_settings_icon_click_opens_a_non_modal_settings_window_leaving_builder_mounted(
    tk_root, navigate_stub, toggle_theme_stub, find_all
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(tk_root, None, navigate, Theme.LIGHT, toggle_theme)

    top_bar = find_all(frame, TopBar)[0]
    top_bar._settings_button._on_click()

    settings_windows = [c for c in frame.winfo_children() if isinstance(c, SettingsWindow)]
    assert len(settings_windows) == 1
    assert settings_windows[0].grab_status() is None
    assert frame.winfo_exists()


def test_theme_toggle_icon_click_invokes_the_passed_in_toggle_theme_callable(
    tk_root, navigate_stub, toggle_theme_stub, find_all
):
    navigate, _ = navigate_stub
    toggle_theme, calls = toggle_theme_stub
    frame = mount(tk_root, None, navigate, Theme.LIGHT, toggle_theme)

    top_bar = find_all(frame, TopBar)[0]
    top_bar._theme_toggle_button._on_click()

    assert calls == [1]
