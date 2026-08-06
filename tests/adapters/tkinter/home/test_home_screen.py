import tkinter as tk

from labyrinthes.adapters.tkinter.common import PillButton, SettingsWindow, TopBar
from labyrinthes.adapters.tkinter.common.navigation import ScreenId
from labyrinthes.adapters.tkinter.home.screen import mount


def test_mount_returns_a_frame_parented_under_the_given_parent(tk_root, navigate_stub):
    navigate, _ = navigate_stub
    frame = mount(tk_root, None, navigate)

    assert isinstance(frame, tk.Frame)
    assert frame.master is tk_root


def test_mount_renders_a_top_bar_with_no_breadcrumb(tk_root, navigate_stub, find_all):
    navigate, _ = navigate_stub
    frame = mount(tk_root, None, navigate)

    top_bars = find_all(frame, TopBar)
    assert len(top_bars) == 1
    assert top_bars[0]._breadcrumb is None


def test_mount_renders_the_brand_mark(tk_root, navigate_stub, find_all):
    navigate, _ = navigate_stub
    frame = mount(tk_root, None, navigate)

    labels = {label.cget("text") for label in find_all(frame, tk.Label)}
    assert "Labyrinthes" in labels


def test_mount_renders_open_builder_and_open_player_entry_points(tk_root, navigate_stub, find_all):
    navigate, _ = navigate_stub
    frame = mount(tk_root, None, navigate)

    labels = {button._label.cget("text") for button in find_all(frame, PillButton)}
    assert labels == {"Open Builder", "Open Player"}


def test_open_builder_button_navigates_to_builder_with_no_state(tk_root, navigate_stub, find_all):
    navigate, calls = navigate_stub
    frame = mount(tk_root, None, navigate)

    open_builder = next(
        b for b in find_all(frame, PillButton) if b._label.cget("text") == "Open Builder"
    )
    # `tk_root` is withdrawn, so real X11 button-press synthesis isn't
    # reliable; invoke the bound handler directly (see test_icon_btn.py).
    open_builder._on_click()

    assert calls == [(ScreenId.BUILDER, None)]


def test_open_player_button_navigates_to_player_with_no_state(tk_root, navigate_stub, find_all):
    navigate, calls = navigate_stub
    frame = mount(tk_root, None, navigate)

    open_player = next(
        b for b in find_all(frame, PillButton) if b._label.cget("text") == "Open Player"
    )
    open_player._on_click()

    assert calls == [(ScreenId.PLAYER, None)]


def test_settings_icon_click_opens_a_non_modal_settings_window_leaving_home_mounted(
    tk_root, navigate_stub, find_all
):
    navigate, _ = navigate_stub
    frame = mount(tk_root, None, navigate)

    top_bar = find_all(frame, TopBar)[0]
    top_bar._settings_button._on_click()

    settings_windows = [c for c in frame.winfo_children() if isinstance(c, SettingsWindow)]
    assert len(settings_windows) == 1
    assert settings_windows[0].grab_status() is None
    assert frame.winfo_exists()
